# Newsletter enrollment V2

The Astro site remains static. A Supabase Edge Function handles signup,
confirmation and unsubscribe. No email addresses or capability tokens are sent
to product analytics. Signup appears only when both public build variables are
configured. The backend independently requires its enable flag and all secrets.

## Activation (required before public signup)

1. Create a Resend account and verify the sending domain with its DNS records.
   Use a verified address such as `RWA Wire <news@therwawire.com>`.
2. Create a Cloudflare Turnstile widget restricted to `therwawire.com` and
   `www.therwawire.com`.
3. Set Supabase Edge Function secrets through the dashboard: `RESEND_API_KEY`,
   `NEWSLETTER_FROM`, `TURNSTILE_SECRET_KEY`, `NEWSLETTER_ENABLED=true`.
   Keep all of these out of Git and browser builds. Existing Supabase URL and
   service role secrets are supplied by the platform.
4. Set GitHub repository variables `PUBLIC_TURNSTILE_SITE_KEY` and
   `PUBLIC_NEWSLETTER_ENABLED=true`. Rebuild the site.
5. Use an email inbox you control to test signup, delivery, explicit confirmation,
   a consumed/expired link, unsubscribe and resubscription. Verify the Supabase
   row and that addresses/tokens never enter `growth_events`.
6. Open signup only after delivery is verified and the newsletter privacy notice
   has the actual operator/contact and processor details.

Deploy the function as `newsletter` with JWT verification disabled: Turnstile
validates signup requests; 256-bit capability tokens authorize confirmation and
unsubscribe. Both require explicit POST, so email scanners opening a link cannot
subscribe or unsubscribe a reader. Confirmation URLs use fragments, which do not
reach hosting request logs. The management page clears the fragment immediately.

`supabase/newsletter-schema.sql` is the version-controlled initial schema,
applied to the production project as `newsletter_double_opt_in`. Do not reapply
it to a database that already has these tables/functions.

## Storage and abuse controls

Tables and RPC functions grant access only to `service_role`; RLS is enabled.
Signup reserves atomically, allows one resend per email every 10 minutes and
limits each secret-salted daily IP bucket to five attempts. Captcha verification
checks hostname and action server-side. Only hashed confirmation and unsubscribe
tokens are stored. Confirmation expires after 24 hours and is consumed once.
Existing subscribers and cooldowns receive the same response. If sending fails,
no successful signup is reported; retry is available after the cooldown.

Pending rows older than eight days are pruned on signup. Rate buckets expire
within one day and are pruned on signup. The `newsletter-retention` Supabase Cron job runs the following
maintenance query daily at 03:17 UTC, including when no signups arrive:

```sql
delete from public.newsletter_subscribers
where (status = 'pending' and expires_at < now() - interval '7 days')
   or (status = 'unsubscribed' and unsubscribed_at < now() - interval '30 days');
delete from public.newsletter_rate_buckets where expires_at < now();
```

## Scope

This is the enrollment and consent flow, including the confirmation email.
Editorial newsletter campaigns and recurring delivery are a separate step.
Campaigns must send only to `status='active'` rows and include a working
unsubscribe link. Raw unsubscribe tokens are not retained: a campaign sender
must generate a fresh token and update its hash, or introduce a reviewed stable
signing mechanism before sending. Never export the whole table to public files.

Tests: `node --test tests/newsletter.test.mjs`. CI runs these before Astro build.
