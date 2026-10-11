# News publication quality

Discovery and publication are separate. RSS headlines and corroborating headlines
remain research leads in `publish/inbox/`; they are not source-reviewed articles.
Both scanners set `autoPublishEligible: false` and `contentStatus:
needs-source-enrichment`. No filler or generic analysis is generated.

Before any article, image or social candidate is written, `news_quality.py` checks:

- A description with meaningful information beyond the headline.
- A distinct explanation of this story's relevance.
- Enough reported detail in the body (90 words is a minimum, not a target).
- No known boilerplate in the article, takeaways or supplied social copy.
- Named HTTPS sources linking directly to the publisher, not Google News RSS.
- For scanner discoveries, a source review recorded as `sourceReview` with
  `status: verified` and a non-empty `reviewedBy`.

These conservative text checks are not a fact-check. An editor must read the
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

Existing published articles and already-created distribution packages are not
rewritten by this change. They require separate review. News discovery keeps its
existing schedule; no new paid service or external model call is introduced.
