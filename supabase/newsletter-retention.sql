-- Run once after the initial schema on the project (pg_cron is already enabled).
select cron.schedule('newsletter-retention', '17 3 * * *', $job$
  delete from public.newsletter_subscribers
  where (status = 'pending' and expires_at < now() - interval '7 days')
     or (status = 'unsubscribed' and unsubscribed_at < now() - interval '30 days');
  delete from public.newsletter_rate_buckets where expires_at < now();
$job$);
