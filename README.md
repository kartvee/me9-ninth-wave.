# ME9 — Ninth Wave

English-language regional geopolitical news monitoring for the South Caucasus, Central Asia, Russia and Eastern Europe.

## Included
- Responsive editorial homepage with search and country/topic filters.
- Publisher-attributed headlines, short excerpts, publication timestamps and original links.
- RSS ingestion script with headline deduplication and basic country/topic classification.
- GitHub Actions workflow scheduled every 30 minutes.
- A transparent preview state when live ingestion has not yet populated the dataset.

## First-time setup
1. Enable GitHub Actions in repository settings.
2. Run the ME9 news ingestion workflow manually once; check its logs and generated data/news.json.
3. Enable GitHub Pages under Settings → Pages, selecting GitHub Actions as the publishing source.
4. Check the Actions tab for the first deployment.
5. Add additional feed URLs to scripts/ingest.py after verifying availability and reuse terms.

Feed availability varies by publisher. A source being listed on the homepage does not mean it is already connected. RSS excerpts are used only where exposed; original publisher links are preserved. Automated topic and country classification is approximate. Translation, AI-written summaries, database-backed archiving and editorial review are not yet configured.
