# Research Impact Dashboard
## Project Report and Vibe-Coding Workflow

**Prepared:** August 23, 2026  
**Project:** Research Impact Observatory  
**Scholar profile:** https://scholar.google.com/citations?user=S7Rii04AAAAJ&hl=en&oi=ao

---

## 1. Project Overview

Research Impact Observatory is a Streamlit dashboard for understanding how a researcher's work travels beyond a basic Google Scholar citation count.

The dashboard was built to explore:

- Citation trajectories for individual papers
- Delayed-impact or "sleeping beauty" patterns
- Citing authors and countries
- Self-citation versus external citation
- Research-topic and usage drift
- Co-author collaboration networks
- How citing papers use the research: methods, application, comparison, or background

The application is implemented in `app.py` using Streamlit, Pandas, Plotly, and NetworkX. It has a demonstration dataset so the interface can be explored before personal data is uploaded.

The dashboard is intentionally snapshot-based. Google Scholar is used as the primary source, but the application does not scrape the live Scholar profile. Users upload Google Scholar or Publish or Perish exports, which makes each analysis reproducible and keeps the source snapshot visible.

## 2. What Was Built

### Dashboard interface

The application includes seven views:

1. **Overview:** citation totals, external citations, citing countries, leading papers, and annual citation momentum.
2. **Trajectories:** annual citations by paper and a delayed-impact signal based on the gap between first citation and peak citation year.
3. **Who cites me:** citing authors and country distributions.
4. **Self-citation:** yearly self-citation versus external citation counts and ratios.
5. **Topic drift:** citation-use distribution and portfolio topic changes over time.
6. **Collaboration:** a weighted co-author graph with NetworkX community detection.
7. **AI citation use:** abstract and citation-use classification, with a downloadable filtered CSV.

### Data handling

The importer accepts CSV and Excel files and normalizes common column names. It supports both:

- A publication-profile export containing a researcher's papers and citation totals.
- A citing-paper export containing papers that cite the researcher's work.

A profile export displays the publication list. A citing-paper export powers the deeper analysis.

### Country analysis

Institution information was deliberately removed from the app. The current geographic analysis focuses on the country of authors of citing papers. Country is retained as an explicit field and remains `Unknown` when the source data does not provide enough evidence.

## 3. Datasets Used

### Original files

The project used the following uploaded files:

- `PoPCites.csv`: Publish or Perish publication-results export containing 10 papers and their citation totals.
- `citations.csv`: a separate 15-row publication metadata file.
- `p1.csv` through `p11.csv`: individual Publish or Perish citation-result exports for 11 target papers.

The `p*.csv` files shared a common 26-column format, including:

- `Cites`
- `Authors`
- `Title`
- `Year`
- `Source`
- `Publisher`
- `ArticleURL`
- `CitesURL`
- `DOI`
- `Abstract`
- `QueryDate`

### Prepared dataset

The script `prepare_citations.py` combined the 11 citation-result files into:

- `prepared_citations.csv`
- 421 total citation rows
- 11 mapped target papers
- Target IDs from `P1` through `P11`
- 421 non-empty abstract values after CSV normalization
- Added target-paper title, year, and author metadata
- Added normalized fields required by the dashboard

The mapping was based on the `p1` through `p11` filenames and validated against the citation counts in each file. For example, a file containing 67 citing records was assigned to the target paper with the corresponding citation count.

The prepared dataset includes fields such as:

- `cited_paper_id`
- `cited_paper`
- `paper_year`
- `paper_authors`
- `citing_title`
- `citing_author`
- `citing_year`
- `citing_abstract`
- `venue`
- `country`
- `field`
- `use_type`
- `snapshot_date`

### Country enrichment dataset

The script `enrich_countries_openalex.py` was created as an automated enrichment method. It attempts to:

1. Match citing papers by DOI.
2. Fall back to title matching.
3. Read author affiliation country codes from OpenAlex.
4. Use the first author's primary affiliation country.
5. Preserve `Unknown` when no reliable match is found.
6. Store the lookup method and matched title for auditing.

A test run initially found 116 country matches out of 421 records. OpenAlex then returned HTTP 429 rate-limit responses, so the enrichment could not be completed reliably during the session. The script was hardened so API failures do not overwrite a usable previous output.

## 4. Prompts Used During Vibe Coding

The main user prompts that guided the build were:

### Initial product request

> Create a Research impact dashboard. Analyze citation trajectory per paper, who cites you, self-citation versus external citation, venue and topic drift, collaboration graph, and an AI stretch analysis of how citing papers use the work. Use Streamlit and Google Scholar. Plan how to do this.

### Project-flow request

> Show me the file structure, data storage, and overall flow of project.

This led to documenting the one-file Streamlit architecture, in-memory Pandas processing, upload flow, and absence of a database.

### Runtime troubleshooting prompts

> command to run the streamlit

> error: streamlit: command not found

These led to creating a project-local Conda environment, installing the dependencies, and switching to:

```bash
.venv/bin/python -m streamlit run app.py
```

### Scholar import troubleshooting prompts

> I dont see papers from my profile

> message on streamlit: This looks like a Google Scholar publication-profile export...

These led to adding a separate profile-export path that recognizes columns such as `title`, `authors`, `publication`, `year`, `cited by`, and `Cites`, then displays the user's papers even when citation-detail rows are not present.

### Citation-data preparation prompts

> check this new csv file. Does it have all info

> I have uploaded 11 csv files. Do the recommended preparation for working of app

These led to inspecting all files, identifying the `p1` through `p11` pattern, creating `prepare_citations.py`, and generating the combined dataset.

### Country-analysis prompts

> I want to include country of people who are citing. Remove the institute information from the app

> Can you fill the country column by opening the papers or suggest any other automated method

These led to removing institution support from the UI and schema, retaining country, and creating the OpenAlex enrichment workflow.

## 5. Iterations Tried

### Iteration 1: Initial dashboard prototype

The first implementation created a functional Streamlit dashboard with:

- Embedded demo data
- CSV and Excel upload
- Seven analysis tabs
- Plotly charts
- NetworkX collaboration graph
- Keyword-based citation-use classification

### Iteration 2: Importing a profile export

The original importer assumed that every upload was a citing-paper dataset. A normal profile export therefore failed to show the user's publications correctly.

The importer was changed to detect profile exports and display the publication catalog separately. The `Cites` column used by Publish or Perish was also added as a recognized citation-count alias.

### Iteration 3: Combining citation files

The 11 separate citation exports were combined into one file. Each row received a target-paper ID and target-paper title so the dashboard could distinguish which of the researcher's papers was cited.

Target-paper authors and years were also added to enable self-citation checks and collaboration analysis.

### Iteration 4: Removing institutions

Institution data was not present in the source exports and was not part of the requested final view. Institution was removed from:

- The overview metric
- The citing-author table
- The chart area
- The normalized schema
- The preparation script
- The README data contract

The overview now reports the number of citing countries, and the "Who cites me" tab displays citing authors and countries.

### Iteration 5: Automated country enrichment

OpenAlex was selected as an automated metadata source because it provides author affiliations and country codes. DOI matching was attempted first, with title matching as a fallback.

The first test worked and returned India for a sample paper. A batch run found 116 country matches. Later requests were rate-limited by OpenAlex, producing HTTP 429 responses. The script was updated to avoid publishing an all-`Unknown` dataset when the API is unavailable.

## 6. Learnings and Observations

### Data semantics matter more than charting

The most important distinction was between:

- A researcher's own publication list with aggregate citation counts.
- Individual papers that cite the researcher's work.

Both are valid Scholar exports, but they answer different questions. The dashboard needs both data types for a complete analysis.

### Filenames cannot replace explicit metadata

The `p1.csv` through `p11.csv` naming pattern was useful for organizing the exports, but the files did not contain the target paper they belonged to. Explicit fields such as `cited_paper_id` and `cited_paper` were therefore added during preparation.

### Missing values should stay visible

Institution, country, field, citation context, and author identity data were not available in the original exports. Marking these values as `Unknown` is more honest than guessing them from incomplete information.

### Google Scholar is valuable but not a complete research graph

Scholar provides useful citation counts and result links, but it does not consistently provide structured affiliations, countries, fields, or citation contexts in a stable export. External metadata sources can help, but they must be treated as enrichment and validated against the source records.

### Author-name matching is imperfect

The current self-citation estimate compares citing-author text with the target paper's author list. This can produce false matches for common names and false negatives for spelling or formatting differences. ORCID or another persistent author identifier would improve this analysis.

### Keyword classification is a transparent baseline

The current citation-use classifier searches titles and abstracts for terms related to methods, application, comparison, and background. This is explainable and easy to audit, but it is not equivalent to reading citation contexts. An LLM classifier should store its model, prompt version, timestamp, confidence, and evidence.

### Rate limits affect automated enrichment

OpenAlex returned useful country data for a test, but the batch API calls were later rate-limited. A production workflow should use caching, fewer repeated requests, a polite contact-enabled User-Agent, retry scheduling, and possibly an API key or another approved metadata provider.

### Reproducibility needs dated snapshots

Citation counts change over time. Saving files with a date such as `scholar_2026-08-23.csv` makes later comparisons meaningful and allows the researcher to distinguish real impact growth from a changed data snapshot.

## 7. Current Limitations and Next Steps

Current limitations:

- The app does not connect directly to the Scholar profile.
- Country enrichment is incomplete because of missing source affiliations and API rate limiting.
- Citation context is not included in the Publish or Perish exports used here.
- Institution information has intentionally been removed.
- Topic labels are not yet generated from a validated research taxonomy.
- The sleeping-beauty metric is a simple first-citation-to-peak-delay signal, not a full bibliometric beauty coefficient.
- There is no database or scheduled refresh process.

Recommended next steps:

1. Wait for the OpenAlex rate limit to reset, then rerun `enrich_countries_openalex.py`.
2. Review country matches manually for a sample of papers.
3. Add citation-context extraction where publisher or full-text access allows it.
4. Add a controlled topic taxonomy and validate labels.
5. Add cached API responses and retry scheduling.
6. Add snapshot storage under `data/raw/` and processed outputs under `data/processed/`.
7. Add a review screen for ambiguous author identity and country matches.
8. Add an optional LLM workflow for classifying how each citing paper uses the work.

## 8. How to Run the Project

From the project directory:

```bash
.venv/bin/python -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

To regenerate the combined citation file:

```bash
.venv/bin/python prepare_citations.py
```

To attempt country enrichment later:

```bash
.venv/bin/python enrich_countries_openalex.py
```

Upload `prepared_citations.csv` or the successful country-enriched output through the Streamlit sidebar.
