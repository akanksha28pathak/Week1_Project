from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

OPENALEX = "https://api.openalex.org/works"
COUNTRY_NAMES = {
    "AU": "Australia", "BR": "Brazil", "CA": "Canada", "CN": "China",
    "DE": "Germany", "ES": "Spain", "FR": "France", "GB": "United Kingdom",
    "IN": "India", "IT": "Italy", "JP": "Japan", "KR": "South Korea",
    "MY": "Malaysia", "NG": "Nigeria", "NL": "Netherlands", "PK": "Pakistan",
    "RU": "Russia", "SG": "Singapore", "TR": "Turkey", "TW": "Taiwan",
    "US": "United States", "ZA": "South Africa", "TN": "Tunisia", "EG": "Egypt",
    "IR": "Iran", "ID": "Indonesia", "DZ": "Algeria", "PS": "Palestine",
    "PT": "Portugal", "FI": "Finland", "GR": "Greece",
}


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "research-impact-dashboard/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def find_work(row: pd.Series) -> tuple[dict | None, str]:
    doi = str(row.get("DOI", "")).strip()
    if doi and doi.lower() != "nan":
        doi = re.sub(r"^https?://doi.org/", "", doi, flags=re.I)
        url = f"{OPENALEX}/{urllib.parse.quote('https://doi.org/' + doi, safe=':/')}"
        try:
            return fetch_json(url), "doi"
        except Exception:
            pass

    title = str(row.get("citing_title", row.get("Title", ""))).strip()
    if not title:
        return None, "none"
    params = urllib.parse.urlencode({"search": title, "per-page": 5})
    try:
        results = fetch_json(f"{OPENALEX}?{params}").get("results", [])
    except Exception:
        return None, "error"
    target = normalize_title(title)
    scored = [(SequenceMatcher(None, target, normalize_title(item.get("title", ""))).ratio(), item) for item in results]
    if not scored:
        return None, "none"
    score, work = max(scored, key=lambda pair: pair[0])
    if score < 0.88:
        return None, "low-confidence"
    return work, f"title:{score:.2f}"


def country_from_work(work: dict | None) -> str:
    if not work:
        return "Unknown"
    authorships = work.get("authorships", [])
    if not authorships:
        return "Unknown"
    first_author_countries = [
        institution.get("country_code")
        for institution in authorships[0].get("institutions", [])
        if institution.get("country_code")
    ]
    countries = first_author_countries or [
        institution.get("country_code")
        for authorship in authorships
        for institution in authorship.get("institutions", [])
        if institution.get("country_code")
    ]
    names = [COUNTRY_NAMES.get(code, code) for code in dict.fromkeys(countries)]
    return "; ".join(names) if names else "Unknown"


def main() -> None:
    source = Path("prepared_citations.csv")
    output = Path("prepared_citations_with_countries.csv")
    frame = pd.read_csv(source)
    countries, sources, matched_titles = [], [], []
    cache: dict[str, tuple[str, str, str]] = {}

    for index, row in frame.iterrows():
        title = str(row.get("citing_title", ""))
        key = normalize_title(title)
        if key not in cache:
            work, source_type = find_work(row)
            cache[key] = (country_from_work(work), source_type, work.get("title", "") if work else "")
            time.sleep(0.1)
        country, source_type, matched_title = cache[key]
        countries.append(country)
        sources.append(source_type)
        matched_titles.append(matched_title)
        if (index + 1) % 25 == 0:
            print(f"Processed {index + 1}/{len(frame)} rows")

    known_matches = sum(country != "Unknown" for country in countries)
    if known_matches == 0 and any(source == "error" for source in sources):
        print("OpenAlex did not return usable results; existing output was not overwritten.")
        return

    frame["country"] = countries
    frame["country_source"] = sources
    frame["country_matched_title"] = matched_titles
    frame.to_csv(output, index=False)
    counts = Counter(country for country in countries if country != "Unknown")
    print(f"Wrote {output} with {len(frame)} rows")
    print(f"Country matches: {known_matches}/{len(frame)}")
    print(f"Countries: {dict(counts)}")


if __name__ == "__main__":
    main()
