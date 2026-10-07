begin;
update newsletter_private.weekly_config set enabled=true,approved=true,sender_name='Test',sender_address='Test address',sender_contact='test@example.invalid';
insert into public.newsletter_subscribers(email,status,unsubscribe_hash,expires_at,consent_version,consent_placement,consent_at,confirmed_at)
values('weekly-test@example.invalid','active','weekly-test-legacy',now()+interval '1 day','test','newsletter-page',now()-interval '2 days',now()-interval '1 day');
do $$ declare saved jsonb; claimed jsonb; begin
 if has_table_privilege('anon','public.newsletter_deliveries','SELECT') or has_function_privilege('authenticated','public.weekly_config()','EXECUTE') then raise exception 'privacy_grants'; end if;
 saved=public.weekly_prepare('test-database','{"stories":[{"title":"Frozen"}]}'::jsonb,false);
 saved=public.weekly_prepare('test-database','{"stories":[{"title":"Changed"}]}'::jsonb,false);
 if saved->'stories'->0->>'title'<>'Frozen' then raise exception 'issue_not_frozen'; end if;
 claimed=public.weekly_claim('test-database','weekly-test@example.invalid','{"subject":"Original"}'::jsonb,'weekly-test-token');
 if claimed->>'subject'<>'Original' then raise exception 'claim_failed'; end if;
 if public.weekly_claim('test-database','weekly-test@example.invalid','{}','x') is not null then raise exception 'lease_failed'; end if;
 perform public.weekly_event('weekly-test-receipt','email.bounced','weekly-test-provider');
 perform public.weekly_complete('test-database','weekly-test@example.invalid','accepted','weekly-test-provider',null);
 if not exists(select 1 from public.newsletter_deliveries where resend_id='weekly-test-provider' and status='bounced') then raise exception 'early_webhook_lost'; end if;
 if not exists(select 1 from public.newsletter_suppressions where email='weekly-test@example.invalid') then raise exception 'suppression_missing'; end if;
 if not public.newsletter_token_action('unsubscribe','weekly-test-token') then raise exception 'unsubscribe_failed'; end if;
 update public.newsletter_subscribers set status='active',consent_at=now(),unsubscribe_hash='new-legacy' where email='weekly-test@example.invalid';
 if public.newsletter_token_action('unsubscribe','weekly-test-token') then raise exception 'old_token_changed_new_consent'; end if;
end $$;
rollback;
