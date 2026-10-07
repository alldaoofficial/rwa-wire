-- Service-only newsletter storage. Never grant browser roles access.
create table public.newsletter_subscribers (
  email text primary key check (length(email) <= 254),
  status text not null check (status in ('pending','active','unsubscribed')),
  confirmation_hash text unique,
  unsubscribe_hash text unique not null,
  expires_at timestamptz not null,
  last_requested_at timestamptz not null default now(),
  consent_version text not null,
  consent_placement text not null,
  consent_at timestamptz not null default now(),
  confirmed_at timestamptz,
  unsubscribed_at timestamptz
);
alter table public.newsletter_subscribers enable row level security;
revoke all on public.newsletter_subscribers from public, anon, authenticated;
grant all on public.newsletter_subscribers to service_role;
create table public.newsletter_rate_buckets (
  bucket text primary key,
  attempts integer not null,
  expires_at timestamptz not null default now() + interval '1 day'
);
alter table public.newsletter_rate_buckets enable row level security;
revoke all on public.newsletter_rate_buckets from public, anon, authenticated;
grant all on public.newsletter_rate_buckets to service_role;

create function public.newsletter_rate_limit(p_bucket text) returns boolean
language plpgsql security invoker set search_path = '' as $$
declare n integer;
begin
  delete from public.newsletter_rate_buckets where expires_at < now();
  insert into public.newsletter_rate_buckets(bucket, attempts) values(p_bucket,1)
  on conflict(bucket) do update set attempts = public.newsletter_rate_buckets.attempts + 1
  returning attempts into n;
  return n <= 5;
end $$;

create function public.newsletter_reserve(p_email text, p_hash text, p_unsubscribe_hash text, p_placement text, p_consent_version text) returns boolean
language plpgsql security invoker set search_path = '' as $$
declare changed integer;
begin
  delete from public.newsletter_subscribers where status = 'pending' and expires_at < now() - interval '7 days';
  insert into public.newsletter_subscribers(email,status,confirmation_hash,unsubscribe_hash,expires_at,consent_version,consent_placement)
  values(p_email,'pending',p_hash,p_unsubscribe_hash,now()+interval '24 hours',p_consent_version,p_placement)
  on conflict(email) do update set status='pending',confirmation_hash=p_hash,unsubscribe_hash=p_unsubscribe_hash,
    expires_at=now()+interval '24 hours',last_requested_at=now(),consent_at=now(),consent_version=p_consent_version,
    consent_placement=p_placement,confirmed_at=null,unsubscribed_at=null
  where public.newsletter_subscribers.status <> 'active' and public.newsletter_subscribers.last_requested_at < now()-interval '10 minutes';
  get diagnostics changed = row_count;
  return changed = 1;
end $$;

create function public.newsletter_token_action(p_action text, p_hash text) returns boolean
language plpgsql security invoker set search_path = '' as $$
declare changed integer;
begin
  if p_action = 'confirm' then
    update public.newsletter_subscribers set status='active',confirmed_at=now(),confirmation_hash=null
    where confirmation_hash=p_hash and status='pending' and expires_at>now();
  elsif p_action = 'unsubscribe' then
    update public.newsletter_subscribers set status='unsubscribed',unsubscribed_at=coalesce(unsubscribed_at,now()),confirmation_hash=null
    where unsubscribe_hash=p_hash;
  else return false;
  end if;
  get diagnostics changed = row_count;
  return changed = 1;
end $$;
revoke all on function public.newsletter_rate_limit(text) from public, anon, authenticated;
revoke all on function public.newsletter_reserve(text,text,text,text,text) from public, anon, authenticated;
revoke all on function public.newsletter_token_action(text,text) from public, anon, authenticated;
grant execute on function public.newsletter_rate_limit(text), public.newsletter_reserve(text,text,text,text,text), public.newsletter_token_action(text,text) to service_role;
