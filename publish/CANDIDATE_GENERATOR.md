# Candidate Generator v1

Input is a fact-checked JSON brief under `publish/inbox/*.json`. The generator creates the MDX article, RWA Wire SVG visual and approval candidate, validates the site build, then commits the package. The existing Editorial Approval workflow automatically sends the private Telegram review card when the candidate lands on main.

Required brief fields: `title`, `description`, `why_it_matters`, `body` (Markdown), and `sources` (array of objects with `name` + HTTPS `url`). Optional: `slug`, `pubDate`, `category`, `tags`, `keyTakeaways`, `readingTime`, `caption`.

Research is deliberately upstream: no workflow invents facts or sources. The next integration should write a reviewed brief only after relevance, primary-source, recency and duplicate checks.
