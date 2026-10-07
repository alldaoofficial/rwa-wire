# RWA Wire Weekly

Weekly editorial digest: up to five published news articles from the last seven days, their existing descriptions and first takeaway, plus one published beginner guide. No new factual claims are generated. Friday morning, Europe/Berlin. Public preview: `/newsletter/weekly/`; the static feed refreshes when the site builds. A feed older than 48 hours stops delivery.

## Activation

Production defaults to `enabled=false`, `approved=false`. Provide the sender's real operator name, postal business address and contact email. Set those values and an explicitly authorized, confirmed active `test_email` in `newsletter_private.weekly_config` using the connected database administrator. Never put API keys or subscriber addresses into GitHub variables, source control or public routes.

Run `select public.weekly_enqueue('preview');` for the HTML/plain-text preview; `select public.weekly_enqueue('test');` sends only to the configured active test subscriber. Inspect the corresponding `net._http_response` without printing subscriber data. Confirm rendering and unsubscribe work. Only after the user approves the test set `approved=true, enabled=true`. Pause immediately with `enabled=false`. The Friday automation invokes `weekly_enqueue('send')`; while disabled it reports the setup gate and sends nothing.

The job credential is generated in a private database schema, used by `pg_net`, and never returned by RPC. The Edge worker verifies its SHA-256 hash. Resend API key and newsletter sender use the existing Edge secrets `RESEND_API_KEY` and `NEWSLETTER_FROM`. The provider webhook requires a Svix signature and five-minute timestamp tolerance; its signing secret is stored only in the private configuration. The one-click unsubscribe endpoint accepts a 256-bit capability; GET only redirects to the confirmation page and cannot unsubscribe.

## Delivery behavior

Each issue and recipient payload is frozen before sending. The audience consists of active, confirmed subscribers at issue creation, excludes suppressed addresses, and checks the current consent again at claim time. Recipients are sent separately. Database locks and leases serialize workers; stable provider idempotency keys cover ambiguous retries. Retries stop after 20 hours, before Resend's 24-hour deduplication window. Each invocation handles at most 25 recipients at below two requests per second. A five-minute queue worker resumes unfinished production issues without creating a new issue. Fatal provider errors are recorded; temporary errors are retried. Signed delivery, bounce and complaint events are reconciled even if they arrive before the send response.

Every email includes HTML, plain text, the sender footer, an unsubscribe link and RFC 8058 headers. Tokens persist across issues but no longer unsubscribe a later consent. Suppressions prevent automatic retries to bounced or complained addresses, including after a subsequent signup. Do not clear a suppression without investigating the cause and permission.

Operational payloads, deliveries and webhook receipts expire after 90 days; suppression addresses remain to prevent further sending. Existing pending/unsubscribed signup retention remains unchanged. All operational tables have RLS, no browser grants, and service-role-only RPCs. Do not expose private logs through analytics.

## Validation

`node --test tests/newsletter.test.mjs tests/weekly.test.mjs` covers selection, escaping, consent, gates, idempotency, error classification, webhook authentication and one-click unsubscribe. `tests/weekly-database.sql` tests frozen issues, leases, early webhooks, suppression, consent token changes and browser permissions in a transaction that rolls back. `npm run build` verifies the static preview and feed.
