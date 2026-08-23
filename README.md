# Research Impact Observatory

A Streamlit dashboard for analyzing a personal research portfolio from Google Scholar exports. The configured profile is [Google Scholar user S7Rii04AAAAJ](https://scholar.google.com/citations?user=S7Rii04AAAAJ&hl=en&oi=ao).

## Run locally

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit.

## Data import

Upload a Google Scholar export as CSV or Excel in the sidebar. The importer supports two export types:

- **Profile publication export:** the standard Scholar columns `title`, `authors`, `publication`, `year`, and `cited by`. This displays your papers and citation counts.
- **Citing-paper export:** one row per paper that cites your work. Export this from Publish or Perish or another Scholar results workflow to enable trajectories, citing countries, self-citation, and citation-use analysis.

The importer accepts common column names such as `title`, `authors`, `year`, `country`, `abstract`, `cited_paper`, and `cited_paper_id`.

For the richest analysis, enrich the export with:

- `cited_paper_id`
- `cited_paper`
- `paper_year`
- `venue`
- `topic`
- `paper_authors`
- `citing_abstract`
- `country`

The app includes a demonstration dataset so every tab can be explored before importing personal data.

## Tabs

- Overview
- Citation trajectories and delayed-impact signals
- Citing authors and countries
- Self-citation versus external citation
- Topic and usage drift
- Co-author collaboration graph
- Citation-use classification and evidence table

Google Scholar remains the primary citation source. The app intentionally uses imported snapshots rather than scraping Scholar pages: Scholar does not provide a stable public citation-analysis API, and automated scraping can be blocked or violate its terms. Use one of these collection workflows:

1. Export the profile's publications and citation results manually from Scholar, or use Publish or Perish to collect the citing-paper list.
2. Save each export with a date, for example `data/scholar_2026-08-23.csv`, so annual citation and self-citation trends remain reproducible.
3. Enrich the export with abstracts, citation context, paper publication year, venue, author list, country, and topic labels. The dashboard accepts these fields through the upload control.
4. Review identity matches and inferred citation-use labels before using results in a report. Keyword classification is intentionally transparent and is not a substitute for reading citation contexts.

## Analysis plan

### Phase 1: Reliable Scholar snapshot

- Build a canonical paper table from the profile: title, year, venue, DOI, authors, and Scholar citation count.
- Build a citation table with one row per citing paper and the cited paper, citing year, authors, abstract, affiliation, country, DOI, and source snapshot date.
- Deduplicate by DOI first, then normalized title and year. Keep the raw export so corrections are auditable.

### Phase 2: Core impact measures

- **Citation trajectory:** plot annual citations per paper and calculate first-citation delay, peak year, and the `sleeping_beauty_signal` used by the Trajectories tab. A stronger future version should also calculate a beauty coefficient from the full yearly curve rather than relying only on first-to-peak delay.
- **Who cites the work:** aggregate citing authors and countries. Country requires enrichment because Scholar's standard profile view does not provide it consistently.
- **Self versus external:** match citing authors against each cited paper's author identities, with manual review for ambiguous names. Report yearly counts and ratios, not only a lifetime percentage.
- **Venue and topic drift:** label each portfolio paper and citing paper with venue and topic taxonomy, then compare distributions by publication year and citation year.

### Phase 3: Networks and citation use

- Create a weighted co-author graph from paper author lists. Edge weight is the number of shared papers; node size is collaboration degree or weighted degree.
- Detect communities with modularity clustering and expose cluster membership in the table. The current prototype renders the graph and computes communities; the next step is to show cluster labels and allow filtering by year or topic.
- Classify citation contexts as methods, application, comparison, or background. Start with the transparent keyword baseline in the app, then add an optional LLM pass over abstracts and citation contexts. Store the model, prompt version, timestamp, and confidence with every label.

### Phase 4: Validation and refresh

- Compare imported totals with the Scholar profile's displayed totals and record the difference caused by coverage, duplicates, or missing years.
- Manually audit a sample of self-citation matches and AI-use classifications.
- Add a scheduled or repeatable import job only after the snapshot schema and deduplication rules are stable. Keep Scholar exports as the primary source and use Crossref/OpenAlex only to enrich missing metadata, never to silently replace Scholar counts.

## Data contract

The minimum useful citation record is `citing_title`, `citing_author`, `citing_year`, `cited_paper`, and `paper_authors`. For the complete analysis, also provide `cited_paper_id`, `paper_year`, `venue`, `topic`, `citing_abstract`, `country`, `field`, `doi`, and `snapshot_date`. Multiple authors may be separated with semicolons. Missing fields stay visible as `Unknown` or `Unclassified` rather than being guessed.
