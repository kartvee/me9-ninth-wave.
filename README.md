# ME9 — Ninth Wave

A responsive Reuters/POLITICO-inspired regional news monitor for the South Caucasus, Central Asia, Russia and Eastern Europe.

## Implemented in the current build
- Breaking-first editorial homepage with responsive story cards and publisher images when exposed in RSS.
- Search and country, topic, and publisher filters.
- Interactive schematic country selector, chronological timeline, and related-coverage comparison.
- Original headlines, publisher excerpts, source attribution, timestamps and original article links.
- RSS ingestion with deduplication, basic classification, optional image extraction, and optional AI-generated English summaries/translations.
- GitHub Actions ingestion schedule every 30 minutes and Pages deployment workflow.

## AI summaries and translated headlines
AI enrichment is optional. To enable it, add a repository Actions secret named `ME9_OPENAI_API_KEY` with an authorized OpenAI API key under Settings → Secrets and variables → Actions. Without that secret, ME9 displays publisher-provided excerpts and does not label them as AI-generated. Never put API keys in source files.

## Deployment and data caveats
Check Actions runs for successful ingestion and deployment. Feed availability varies; configured sources are not a guarantee that every publisher currently responds. RSS metadata may not include a publisher image. Automated country/topic classification can be imperfect. The regional explorer is a schematic selector, not a geographic boundary map. No database is required for the current static deployment; persistent history and editorial workflows are not configured.
