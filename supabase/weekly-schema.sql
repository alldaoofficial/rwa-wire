create schema if not exists newsletter_private;
revoke all on schema newsletter_private from public,anon,authenticated;
grant usage on schema newsletter_private to service_role;
create table newsletter_private.weekly_config (
 id boolean primary key default true check(id), enabled boolean not null default false,
 approved boolean not null default false, sender_name text not null default '',
 sender_address text not null default '', sender_contact text not null default '', test_email text not null default '',
 job_secret text not null default encode(extensions.gen_random_bytes(32),'hex'),
 webhook_secret text not null default '', lock_id uuid, lock_until timestamptz
);
insert into newsletter_private.weekly_config(id) values(true);
alter table newsletter_private.weekly_config enable row level security;
revoke all on newsletter_private.weekly_config from public,anon,authenticated;
grant all on newsletter_private.weekly_config to service_role;
create table public.newsletter_issues (
 id text primary key, content jsonb not null, created_at timestamptz not null default now(), is_test boolean not null default false
);
create table public.newsletter_deliveries (
 issue_id text references public.newsletter_issues(id) on delete cascade,
 email text not null, consent_at timestamptz not null, payload jsonb,
 status text not null default 'pending' check(status in ('pending','processing','accepted','delivered','delayed','retry','failed','suppressed','bounced','complained','review','cancelled')),
 attempts integer not null default 0, first_attempt_at timestamptz, last_attempt_at timestamptz,
 resend_id text unique, error_code text, primary key(issue_id,email)
);
create table public.newsletter_unsubscribe_tokens (
 hash text primary key, email text references public.newsletter_subscribers(email) on delete cascade,
 consent_at timestamptz not null
);
create table public.newsletter_suppressions (email text primary key,reason text not null,created_at timestamptz not null default now());
create table public.newsletter_webhook_receipts (id text primary key,resend_id text not null,event_type text not null,created_at timestamptz not null default now());
do $$ declare t text; begin
 foreach t in array array['newsletter_issues','newsletter_deliveries','newsletter_unsubscribe_tokens','newsletter_suppressions','newsletter_webhook_receipts'] loop
 execute format('alter table public.%I enable row level security',t);
 execute format('revoke all on public.%I from public,anon,authenticated',t);
 execute format('grant all on public.%I to service_role',t);
 end loop;
end $$;
create function public.weekly_auth(p_hash text) returns boolean language sql security invoker set search_path='' as $$
 select exists(select 1 from newsletter_private.weekly_config where encode(sha256(convert_to(job_secret,'UTF8')),'hex')=p_hash)
$$;
create function public.weekly_config() returns jsonb language sql security invoker set search_path='' as $$
 select to_jsonb(c)-'job_secret'-'lock_id'-'lock_until' from newsletter_private.weekly_config c
$$;
create function public.weekly_lock(p_owner uuid) returns boolean language plpgsql security invoker set search_path='' as $$
declare n integer; begin
 update newsletter_private.weekly_config set lock_id=p_owner,lock_until=now()+interval '5 minutes' where lock_until is null or lock_until<now();
 get diagnostics n=row_count; return n=1;
end $$;
create function public.weekly_unlock(p_owner uuid) returns void language sql security invoker set search_path='' as $$
 update newsletter_private.weekly_config set lock_until=null,lock_id=null where lock_id=p_owner;
$$;
create function public.weekly_prepare(p_issue text,p_content jsonb,p_test boolean) returns jsonb language plpgsql security invoker set search_path='' as $$
declare c newsletter_private.weekly_config; saved public.newsletter_issues; begin
 select * into c from newsletter_private.weekly_config;
 if (not p_test and (not c.enabled or not c.approved)) or c.sender_name='' or c.sender_address='' or c.sender_contact='' then raise exception 'sender_setup_required'; end if;
 if p_test and c.test_email='' then raise exception 'test_recipient_required'; end if;
 insert into public.newsletter_issues(id,content,is_test) values(p_issue,p_content,p_test) on conflict do nothing;
 select * into saved from public.newsletter_issues where id=p_issue;
 if saved.is_test<>p_test then raise exception 'issue_mode_mismatch'; end if;
 insert into public.newsletter_deliveries(issue_id,email,consent_at)
 select p_issue,s.email,s.consent_at from public.newsletter_subscribers s
 where s.status='active' and s.confirmed_at<=saved.created_at and not exists(select 1 from public.newsletter_suppressions b where b.email=s.email)
 and (not p_test or s.email=c.test_email) on conflict do nothing;
 return saved.content;
end $$;
create function public.weekly_candidates(p_issue text) returns table(email text,consent_at timestamptz)
language sql security invoker set search_path='' as $$
 select d.email,d.consent_at from public.newsletter_deliveries d join public.newsletter_subscribers s on s.email=d.email
 where d.issue_id=p_issue and s.status='active' and s.consent_at=d.consent_at
 and not exists(select 1 from public.newsletter_suppressions b where b.email=d.email)
 and (d.status='pending' or (d.status in ('retry','processing') and d.last_attempt_at<now()-interval '5 minutes'))
 order by d.email limit 25
$$;
create function public.weekly_claim(p_issue text,p_email text,p_payload jsonb,p_hash text) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare d public.newsletter_deliveries; begin
 select * into d from public.newsletter_deliveries where issue_id=p_issue and email=p_email for update;
 if not found or d.status not in ('pending','retry','processing') then return null; end if;
 if d.status in ('retry','processing') and d.last_attempt_at>now()-interval '5 minutes' then return null; end if;
 if d.first_attempt_at<now()-interval '20 hours' then update public.newsletter_deliveries set status='review' where issue_id=p_issue and email=p_email; return null; end if;
 if not exists(select 1 from public.newsletter_subscribers s where s.email=p_email and s.status='active' and s.consent_at=d.consent_at)
 or exists(select 1 from public.newsletter_suppressions b where b.email=p_email) then
 update public.newsletter_deliveries set status='cancelled' where issue_id=p_issue and email=p_email; return null; end if;
 insert into public.newsletter_unsubscribe_tokens(hash,email,consent_at) values(p_hash,p_email,d.consent_at) on conflict do nothing;
 update public.newsletter_deliveries set status='processing',payload=coalesce(payload,p_payload),attempts=attempts+1,
 first_attempt_at=coalesce(first_attempt_at,now()),last_attempt_at=now() where issue_id=p_issue and email=p_email returning payload into p_payload;
 return p_payload;
end $$;
create or replace function public.newsletter_token_action(p_action text,p_hash text) returns boolean
language plpgsql security invoker set search_path='' as $$
declare n integer; begin
 if p_action='confirm' then
 update public.newsletter_subscribers set status='active',confirmed_at=now(),confirmation_hash=null where confirmation_hash=p_hash and status='pending' and expires_at>now();
 elsif p_action='unsubscribe' then
 update public.newsletter_subscribers s set status='unsubscribed',unsubscribed_at=coalesce(unsubscribed_at,now()),confirmation_hash=null
 where s.unsubscribe_hash=p_hash or exists(select 1 from public.newsletter_unsubscribe_tokens t where t.hash=p_hash and t.email=s.email and t.consent_at=s.consent_at);
 else return false; end if;
 get diagnostics n=row_count; return n=1;
end $$;
create function public.weekly_apply_event(p_type text,p_resend_id text) returns void language plpgsql security invoker set search_path='' as $$
declare n integer; e text; state text; begin
 state=case p_type when 'email.delivered' then 'delivered' when 'email.delivery_delayed' then 'delayed' when 'email.bounced' then 'bounced' when 'email.complained' then 'complained' when 'email.failed' then 'failed' when 'email.suppressed' then 'suppressed' else null end;
 if state is null then return; end if;
 select email into e from public.newsletter_deliveries where resend_id=p_resend_id;
 if e is null then return; end if;
 update public.newsletter_deliveries set status=state where resend_id=p_resend_id and status not in ('bounced','complained','suppressed') and (state<>'delayed' or status<>'delivered');
 if state in ('bounced','complained','suppressed') then
 insert into public.newsletter_suppressions(email,reason) values(e,state) on conflict(email) do nothing;
 end if;
end $$;

create function public.weekly_event(p_receipt text,p_type text,p_resend_id text) returns void language plpgsql security invoker set search_path='' as $$
begin
 insert into public.newsletter_webhook_receipts(id,resend_id,event_type) values(p_receipt,p_resend_id,p_type) on conflict do nothing;
 perform public.weekly_apply_event(event_type,resend_id) from public.newsletter_webhook_receipts where id=p_receipt;
end $$;
create function public.weekly_complete(p_issue text,p_email text,p_status text,p_resend_id text,p_error text) returns void
language plpgsql security invoker set search_path='' as $$
declare ev record; begin
 if p_status not in ('accepted','retry','failed') then raise exception 'invalid_status'; end if;
 update public.newsletter_deliveries set status=p_status,resend_id=p_resend_id,error_code=p_error where issue_id=p_issue and email=p_email and status='processing';
 if p_resend_id is not null then
 for ev in select event_type from public.newsletter_webhook_receipts where resend_id=p_resend_id order by created_at loop
 perform public.weekly_apply_event(ev.event_type,p_resend_id);
 end loop; end if;
end $$;
create function public.weekly_enqueue(p_mode text default 'preview') returns bigint language plpgsql security invoker set search_path='' as $$
declare secret text; begin
 if p_mode not in ('preview','test','send','resume') then raise exception 'invalid_mode'; end if;
 select job_secret into secret from newsletter_private.weekly_config;
 return net.http_post(url:='https://dqeakkrsbgxnexucuyld.supabase.co/functions/v1/weekly-newsletter',headers:=jsonb_build_object('Content-Type','application/json','Authorization','Bearer '||secret),body:=jsonb_build_object('mode',p_mode),timeout_milliseconds:=120000);
end $$;
create function public.weekly_status(p_issue text) returns jsonb language sql security invoker set search_path='' as $$
 select coalesce(jsonb_object_agg(status,n),'{}'::jsonb) from (select status,count(*) n from public.newsletter_deliveries where issue_id=p_issue group by status) q
$$;
create function public.weekly_resume() returns jsonb language sql security invoker set search_path='' as $$
 select content from public.newsletter_issues i where not is_test and created_at>now()-interval '20 hours'
 and exists(select 1 from public.newsletter_deliveries d where d.issue_id=i.id and d.status in ('pending','retry','processing')) order by created_at limit 1
$$;
-- Every public RPC is callable only by the server role (and database owner).
do $$ declare f record; begin
 for f in select p.oid::regprocedure as signature from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname like 'weekly_%' loop
 execute format('revoke all on function %s from public,anon,authenticated',f.signature);
 execute format('grant execute on function %s to service_role',f.signature);
 end loop;
end $$;
