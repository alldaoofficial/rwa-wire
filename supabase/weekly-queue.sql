-- Queue retries do not create issues, and remain gated by enabled + approved.
select cron.schedule('weekly-newsletter-resume','*/5 * * * *',$job$
 select public.weekly_enqueue('resume') where exists(
 select 1 from newsletter_private.weekly_config where enabled and approved)
 and exists(select 1 from public.newsletter_issues i join public.newsletter_deliveries d on d.issue_id=i.id
 where not i.is_test and i.created_at>now()-interval '20 hours' and d.status in ('pending','retry','processing'));
$job$);
select cron.schedule('weekly-newsletter-retention','27 3 * * *',$job$
 delete from public.newsletter_issues where created_at<now()-interval '90 days';
 delete from public.newsletter_webhook_receipts where created_at<now()-interval '90 days';
 update public.newsletter_deliveries set status='review' where status in ('retry','processing') and first_attempt_at<now()-interval '20 hours';
$job$);
