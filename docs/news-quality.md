# News publication quality

Discovery and publication are separate. RSS headlines and corroborating headlines
remain research leads in `publish/inbox/`; they are not source-reviewed articles.
Both scanners set `autoPublishEligible: false` and `contentStatus:
needs-source-enrichment`. No filler or generic analysis is generated.

When no primary/trusted headline qualifies, the scanner can enqueue one relevant
watchlist research lead per run: specialists and news wires need a score of at
least 6, unknown publishers at least 8. Low-trust publishers remain excluded
from this fallback. Promotion, community, duplicate, 48-hour freshness and valid
publication-date checks still apply. The original publisher tier is retained;
`discoveryMode: watchlist-research` is not corroboration or verification. These
leads enter the existing source-review queue without requiring additional
headline matches first. All content, source-evidence and publication gates below
continue to apply unchanged.

Before any article, image or social candidate is written, `news_quality.py` checks:

- A description with meaningful information beyond the headline.
- A distinct explanation of this story's relevance.
- Enough reported detail in the body (90 words is a minimum, not a target).
- No known boilerplate in the article, takeaways or supplied social copy.
- Named HTTPS sources linking directly to the publisher, not Google News RSS.
- For scanner discoveries, a source review recorded as `sourceReview` with
  `status: verified` and a non-empty `reviewedBy`.

The hourly source-review task now performs the missing enrichment through the
connected GitHub app. See [Source enrichment handoff](source-enrichment.md) for
the queue, required evidence ledger, integrity seal and held/rejected outcomes.
It updates existing leads; it does not create duplicate discoveries or approve
social distribution.

These conservative text checks are not a fact-check. A reviewing agent or editor must read the
original source, verify claims, and add supported details and a specific relevance
explanation. Only then record the source review. The source-trust score alone
cannot satisfy this requirement. Never set a review flag to bypass missing facts.

Update a held briefing in place after reviewing it. Keep the discovery metadata,
replace its source links with direct publisher links, and supply the substantive
description, body and relevance. The existing candidate workflow then evaluates
it again and routes it for editorial distribution approval. Do not turn on
`autoPublishEligible` just because the content checks pass.

Held items finish the candidate workflow successfully with `eligible=false`;
generation, deployment and distribution are skipped. Reasons appear in the
workflow log. Calling the generator directly enforces the same checks and fails
before writing public files.

Source enrichment uses the existing ChatGPT hourly task rather than a separately
billed model API. It reads public publisher sources through web research; the
checks themselves are offline. News discovery keeps its existing schedule.
