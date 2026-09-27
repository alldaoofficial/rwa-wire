# RWA Wire editorial approval pipeline

This layer sits before the existing `publish/approved/*.json` Telegram publisher.

## Candidate schema

Candidates live in `publish/candidates/<id>.json` and contain the complete editorial package:

- `id`
- `title`
- `category`
- `why_it_matters`
- `article_url`
- `image_url`
- `caption`
- `sources`

## Intended state machine

`candidate -> review -> approved/rejected -> website live check -> Telegram publisher -> posted`

The existing Telegram publisher remains the publication gate and duplicate guard.

## Required secret

Add `TELEGRAM_REVIEW_CHAT_ID` as a repository Actions secret. It should be the private Telegram chat ID that receives editorial review cards. Do not use the public channel ID.

## Current phase

The workflow can send a private review card with Preview, APPROVE and REJECT buttons. Buttons are callback buttons and require an HTTPS webhook listener before they can perform repository writes. Until that listener is connected, they are deliberately non-destructive.

Phase 2 connects Telegram callback queries to a small approval endpoint that authenticates Telegram, moves the candidate to `publish/approved/` on APPROVE, or records it under `publish/rejected/` on REJECT. Creating the approved manifest then automatically triggers the existing publisher.
