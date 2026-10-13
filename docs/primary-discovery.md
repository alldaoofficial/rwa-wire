# Direct primary-source discovery and distribution visibility

The existing News Watch now checks the official BIS media-release RSS, SEC
press-release RSS, ECB press RSS, Ondo blog and Chainlink blog before Google News.
RSS URLs were resolved from the institutions' official feed directories; newsroom
URLs were inspected directly. Sources may still deny automated access or change
their page structure. Errors are counted per publisher, not treated as evidence
that no news exists. No access controls are bypassed.

The parser supports RSS, Atom and HTML articles with publication dates in
JSON-LD or Open Graph metadata. Recent-post links take priority over older featured
articles. Each newsroom has a four-article request cap and all requests have time
and size limits. Redirects and discovered article URLs must remain on that
publisher's explicit HTTPS hostname; no arbitrary external crawling is allowed.

At most two recent, relevant direct-source leads are added per scan. Missing
dates, future dates, records older than 48 hours, irrelevant announcements and
known URLs/exact headlines are skipped. Shared topic/issuer keywords alone do
not reject a new milestone: related coverage is supplied to source review for an
actual event-level comparison. The source reviewer must still reject repeated
coverage and verify that a new launch, approval, funding round or rollout is
materially distinct. A quota is not a reason to publish weak stories.

Leads retain the direct publisher link and actual source timestamp. They contain
no invented article text and always require source enrichment. There is no
automatic editorial or social approval. The hourly source-review task consumes
these same inbox files; the existing candidate pipeline handles reviewed copy.

Every News Watch run also writes a read-only distribution status to its GitHub
job summary: awaiting editorial approval, approved but not yet posted to
Telegram, Telegram posted, and the separate X state. A prepared package is not
a published post. A green scanner run does not imply that either channel sent it.

X API publishing remains paused in `publish/channel-config.json` while credits
are depleted. Newly generated editorial cards provide a bounded, tracked X draft
that the operator can copy manually after approval. This does not spend credits,
grant approvals, send public posts or retry old posts. No approval cards are
resent by this change. Existing approval/rejection buttons remain unchanged.
