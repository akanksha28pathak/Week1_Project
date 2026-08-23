from __future__ import annotations

import re
from collections import Counter
from io import BytesIO

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Research Impact Observatory",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "ink": "#17212b",
    "muted": "#607080",
    "teal": "#008f8c",
    "coral": "#ed6a5a",
    "gold": "#e0a458",
    "blue": "#3f72af",
    "cream": "#f6f1e9",
}


def make_demo_data() -> pd.DataFrame:
    papers = [
        ("P1", "Adaptive Systems for Noisy Data", 2019, "Journal of Intelligent Systems", "machine learning", ["A. Researcher", "M. Chen", "L. Okafor"]),
        ("P2", "A Practical Framework for Model Audits", 2020, "Data & Society Review", "responsible AI", ["A. Researcher", "M. Chen", "S. Patel"]),
        ("P3", "Learning from Sparse Clinical Signals", 2021, "Health AI", "healthcare", ["A. Researcher", "J. Williams"]),
        ("P4", "Transparent Evaluation of Generative Models", 2022, "ML Systems", "generative AI", ["A. Researcher", "S. Patel", "N. Garcia"]),
        ("P5", "Human-Centered Tools for Model Monitoring", 2024, "Applied AI Quarterly", "human-centered AI", ["A. Researcher", "N. Garcia"]),
    ]
    citing_authors = [
        ("R. Singh", "University of Toronto", "Canada", "methods", "P1", 2020),
        ("D. Müller", "TU Munich", "Germany", "background", "P1", 2021),
        ("K. Ito", "Kyoto Institute of Technology", "Japan", "methods", "P1", 2022),
        ("E. Brown", "University of Edinburgh", "United Kingdom", "methods", "P1", 2023),
        ("J. Lee", "Seoul National University", "South Korea", "application", "P1", 2024),
        ("T. Nguyen", "University of Melbourne", "Australia", "background", "P2", 2021),
        ("R. Singh", "University of Toronto", "Canada", "methods", "P2", 2022),
        ("C. Silva", "University of Sao Paulo", "Brazil", "application", "P2", 2023),
        ("F. Rossi", "University of Milan", "Italy", "comparison", "P2", 2024),
        ("H. Wilson", "University of Washington", "United States", "background", "P3", 2022),
        ("P. Adeyemi", "University of Lagos", "Nigeria", "application", "P3", 2023),
        ("G. Novak", "Charles University", "Czechia", "methods", "P3", 2024),
        ("Y. Zhang", "Tsinghua University", "China", "methods", "P4", 2023),
        ("A. Khan", "University of Cambridge", "United Kingdom", "comparison", "P4", 2024),
        ("B. Martin", "McGill University", "Canada", "application", "P5", 2025),
        ("M. Chen", "University of California", "United States", "methods", "P2", 2022),
        ("S. Patel", "University of California", "United States", "methods", "P4", 2023),
    ]
    records = []
    for paper_id, title, year, venue, topic, authors in papers:
        for author in authors:
            records.append({"paper_id": paper_id, "paper_title": title, "paper_year": year, "venue": venue, "topic": topic, "paper_authors": "; ".join(authors), "cited_author": author})
    citation_rows = []
    for author, _unused_affiliation, country, use_type, cited_paper, year in citing_authors:
        paper = next(item for item in papers if item[0] == cited_paper)
        citation_rows.append({"citing_author": author, "country": country, "use_type": use_type, "cited_paper_id": cited_paper, "cited_paper": paper[1], "paper_authors": "; ".join(paper[5]), "citing_year": year, "citing_title": f"{author.split()[1]}'s study of {paper[1]}", "citing_abstract": f"This study builds on {paper[1]} to examine new evidence and applications.", "is_self_citation": author in paper[5]})
    citation_df = pd.DataFrame(citation_rows)
    paper_df = pd.DataFrame([{key: value for key, value in zip(["paper_id", "paper_title", "paper_year", "venue", "topic", "paper_authors"], item)} for item in papers])
    return citation_df.merge(paper_df, on=["paper_id"], how="right") if False else (paper_df, citation_df)


def normalize_columns(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    renamed = {str(column).strip().lower().replace(" ", "_"): column for column in frame.columns}
    def get(*names: str, default: str = "") -> pd.Series:
        for name in names:
            if name in renamed:
                return frame[renamed[name]].fillna(default).astype(str)
        return pd.Series([default] * len(frame), index=frame.index)

    has_citation_targets = any(name in renamed for name in ("cited_paper", "cited_title", "your_paper"))
    if not has_citation_targets and "title" in renamed:
        profile_titles = get("title")
        profile_authors = get("authors", "author")
        profile_years = pd.to_numeric(get("year", "publication_year", default="0"), errors="coerce").fillna(0).astype(int)
        profile_ids = pd.Series([f"profile_{index}" for index in frame.index], index=frame.index)
        papers = pd.DataFrame({
            "paper_id": profile_ids,
            "paper_title": profile_titles,
            "paper_year": profile_years,
            "venue": get("publication", "venue", default="Unknown"),
            "topic": get("topic", default="Unclassified"),
            "paper_authors": profile_authors,
            "citation_count": pd.to_numeric(get("cited_by", "cited_by_count", "citations", "cites", default="0"), errors="coerce").fillna(0).astype(int),
        })
        return papers, pd.DataFrame(columns=[
            "citing_title", "citing_author", "citing_year", "country",
            "cited_paper", "cited_paper_id", "paper_authors", "citing_abstract", "use_type",
        ])

    citing = pd.DataFrame({
        "citing_title": get("citing_title", "title", "paper_title"),
        "citing_author": get("citing_author", "authors", "author"),
        "citing_year": pd.to_numeric(get("citing_year", "year", "publication_year", default="0"), errors="coerce").fillna(0).astype(int),
        "country": get("country", "citing_country", default="Unknown"),
        "cited_paper": get("cited_paper", "cited_title", "your_paper", default="Unknown paper"),
        "cited_paper_id": get("cited_paper_id", "cited_doi", default="Unknown"),
        "paper_year": pd.to_numeric(get("paper_year", "cited_paper_year", default="0"), errors="coerce").fillna(0).astype(int),
        "venue": get("venue", "cited_venue", default="Unknown"),
        "topic": get("topic", default="Unclassified"),
        "paper_authors": get("paper_authors", "your_paper_authors", default=""),
        "citing_abstract": get("citing_abstract", "abstract", default=""),
        "use_type": get("use_type", "citation_type", default="Unclassified"),
    })
    paper_records = citing[["cited_paper_id", "cited_paper", "paper_year", "venue", "topic", "paper_authors"]].drop_duplicates().rename(columns={"cited_paper_id": "paper_id", "cited_paper": "paper_title"})
    return paper_records, citing


def classify_use(text: str) -> str:
    text = text.lower()
    rules = {
        "methods": r"method|framework|algorithm|dataset|implement|pipeline|benchmark",
        "application": r"apply|application|clinical|deployed|case study|real-world",
        "comparison": r"compare|comparison|baseline|outperform|contrast|critique",
        "background": r"background|motivat|literature|prior work|overview|context",
    }
    for label, pattern in rules.items():
        if re.search(pattern, text):
            return label
    return "background"


def style_chart(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "DM Sans, sans-serif", "color": COLORS["ink"]},
        margin={"l": 10, "r": 10, "t": 35, "b": 10},
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e5e0d8", zeroline=False)
    return fig


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --ink:#17212b; --muted:#607080; --teal:#008f8c; --cream:#f6f1e9; --line:#ddd7cd; }
.stApp { background: var(--cream); color: var(--ink); font-family: 'DM Sans', sans-serif; }
.block-container { max-width: 1450px; padding-top: 2.5rem; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0; }
h1 { font-size: 3rem; line-height: 1.05; }
[data-testid='stMetric'] { background: white; border: 1px solid var(--line); border-radius: 6px; padding: 0.9rem 1rem; }
[data-testid='stMetricLabel'] { color: var(--muted); }
[data-testid='stMetricValue'] { color: var(--ink); }
[data-testid='stSidebar'] { background: #ebe6dc; border-right: 1px solid var(--line); }
.eyebrow { font-family: 'DM Mono', monospace; color: var(--teal); font-size: 0.75rem; letter-spacing: .08em; text-transform: uppercase; }
.subtle { color: var(--muted); font-size: 1.05rem; max-width: 720px; }
.source-note { color: var(--muted); font-family: 'DM Mono', monospace; font-size: .72rem; border-top: 1px solid var(--line); padding-top: .75rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="eyebrow">PERSONAL RESEARCH INTELLIGENCE / SCHOLAR IMPORT</div>', unsafe_allow_html=True)
st.title("Research Impact Observatory")
st.markdown('<p class="subtle">A living view of where your work travels, who carries it forward, and when the signal finally breaks through.</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Data room")
    uploaded = st.file_uploader("Upload Google Scholar export", type=["csv", "xlsx", "xls"])
    use_demo = st.toggle("Use demonstration dataset", value=uploaded is None)
    st.caption("Export results from Publish or Perish or Scholar, then upload the CSV here.")
    st.divider()
    st.markdown("### Filters")

if uploaded is not None and not use_demo:
    raw = pd.read_excel(uploaded) if uploaded.name.endswith((".xlsx", ".xls")) else pd.read_csv(uploaded)
    papers, citations = normalize_columns(raw)
    data_label = f"Scholar import: {uploaded.name}"
else:
    papers, citations = make_demo_data()
    data_label = "Demonstration dataset"

if citations.empty:
    st.warning("This looks like a Google Scholar publication-profile export. Your papers are loaded, but citation-detail analysis needs a separate citing-paper export.")
    display_columns = [column for column in ["paper_title", "paper_year", "venue", "paper_authors", "citation_count"] if column in papers]
    st.subheader("Papers from your Scholar profile")
    st.dataframe(papers[display_columns].sort_values(["paper_year", "paper_title"], ascending=[False, True]), use_container_width=True, hide_index=True)
    st.info("Upload a citation-results export containing one row per citing paper to populate trajectories, countries, self-citation, and citation-use tabs.")
    st.stop()

citations["is_self_citation"] = citations.apply(lambda row: any(name.strip().lower() in row["citing_author"].lower() for name in str(row.get("paper_authors", "")).split(";")) if "paper_authors" in row else False, axis=1)
citations["inferred_use_type"] = citations.apply(lambda row: row["use_type"] if row["use_type"] not in ("", "Unclassified") else classify_use(f"{row['citing_title']} {row['citing_abstract']}"), axis=1)

min_year = int(citations["citing_year"].replace(0, pd.NA).min()) if citations["citing_year"].replace(0, pd.NA).notna().any() else 2000
max_year = int(citations["citing_year"].max()) if citations["citing_year"].max() else 2026
with st.sidebar:
    year_range = st.slider("Citation years", min_value=min_year, max_value=max(max_year, min_year), value=(min_year, max(max_year, min_year)))
    selected_papers = st.multiselect("Papers", options=papers["paper_title"].dropna().tolist(), default=papers["paper_title"].dropna().tolist())

filtered = citations[citations["citing_year"].between(year_range[0], year_range[1])]
if selected_papers:
    filtered = filtered[filtered["cited_paper"].isin(selected_papers)]

st.caption(f"{data_label}  |  {len(filtered):,} citation records in view  |  Source values are anchored to your imported Scholar snapshot.")

tabs = st.tabs(["Overview", "Trajectories", "Who cites me", "Self-citation", "Topic drift", "Collaboration", "AI citation use"])

with tabs[0]:
    total = len(filtered)
    external = int((~filtered["is_self_citation"]).sum())
    top_paper = filtered["cited_paper"].value_counts().index[0] if total else "None"
    top_country = filtered["country"].value_counts().index[0] if total else "None"
    cols = st.columns(4)
    cols[0].metric("Citations in view", f"{total:,}")
    cols[1].metric("External citations", f"{external:,}", f"{external / total:.0%}" if total else None)
    cols[2].metric("Citing countries", f"{filtered['country'].nunique():,}")
    cols[3].metric("Leading paper", top_paper, help="Most frequently cited paper in the current filters")
    st.subheader("Citation momentum")
    yearly = filtered[filtered["citing_year"] > 0].groupby("citing_year").size().reset_index(name="citations")
    st.plotly_chart(style_chart(px.area(yearly, x="citing_year", y="citations", markers=True, color_discrete_sequence=[COLORS["teal"]], labels={"citing_year": "Year", "citations": "Citations"})), use_container_width=True)
    left, right = st.columns(2)
    with left:
        paper_counts = filtered["cited_paper"].value_counts().head(8).reset_index()
        paper_counts.columns = ["paper", "citations"]
        st.plotly_chart(style_chart(px.bar(paper_counts, x="citations", y="paper", orientation="h", color_discrete_sequence=[COLORS["coral"]])), use_container_width=True)
    with right:
        country_counts = filtered["country"].value_counts().head(8).reset_index()
        country_counts.columns = ["country", "citations"]
        st.plotly_chart(style_chart(px.bar(country_counts, x="country", y="citations", color_discrete_sequence=[COLORS["gold"]])), use_container_width=True)

with tabs[1]:
    st.subheader("Which paper waited for its moment?")
    trajectory = filtered[filtered["citing_year"] > 0].groupby(["cited_paper", "citing_year"]).size().reset_index(name="citations")
    if not trajectory.empty:
        st.plotly_chart(style_chart(px.line(trajectory, x="citing_year", y="citations", color="cited_paper", markers=True, labels={"citing_year": "Citation year", "citations": "Citations"})), use_container_width=True)
        first = trajectory.groupby("cited_paper").agg(first_citation=("citing_year", "min"), peak_year=("citations", lambda values: trajectory.loc[values.idxmax(), "citing_year"]), peak_citations=("citations", "max")).reset_index()
        first["sleeping_beauty_signal"] = (first["peak_year"] - first["first_citation"]).clip(lower=0)
        first = first.sort_values("sleeping_beauty_signal", ascending=False)
        st.dataframe(first, use_container_width=True, hide_index=True)
    else:
        st.info("Citation years are required for trajectory analysis.")

with tabs[2]:
    st.subheader("The network beyond your profile")
    left, right = st.columns(2)
    with left:
        authors = filtered["citing_author"].value_counts().head(12).reset_index()
        authors.columns = ["citing_author", "citations"]
        st.plotly_chart(style_chart(px.bar(authors, x="citations", y="citing_author", orientation="h", color_discrete_sequence=[COLORS["blue"]])), use_container_width=True)
    with right:
        countries = filtered["country"].value_counts().reset_index()
        countries.columns = ["country", "citations"]
        st.plotly_chart(style_chart(px.treemap(countries, path=["country"], values="citations", color="citations", color_continuous_scale=["#d8eee9", COLORS["teal"]])), use_container_width=True)
    st.dataframe(filtered.groupby(["citing_author", "country"]).agg(citations=("cited_paper", "size"), papers_cited=("cited_paper", "nunique")).reset_index().sort_values("citations", ascending=False), use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("How much of the signal is yours echoing back?")
    annual_self = filtered[filtered["citing_year"] > 0].groupby(["citing_year", "is_self_citation"]).size().reset_index(name="citations")
    annual_self["citation_type"] = annual_self["is_self_citation"].map({True: "Self-citation", False: "External citation"})
    st.plotly_chart(style_chart(px.bar(annual_self, x="citing_year", y="citations", color="citation_type", barmode="group", color_discrete_map={"Self-citation": COLORS["coral"], "External citation": COLORS["teal"]})), use_container_width=True)
    ratio = filtered["is_self_citation"].mean() if len(filtered) else 0
    st.metric("Self-citation ratio", f"{ratio:.1%}")
    st.caption("Self-citation is estimated by matching citing-author names against the paper-author field. Verify author identity before treating this as a formal bibliometric measure.")

with tabs[4]:
    st.subheader("Where the research is moving")
    topic_by_year = filtered[filtered["citing_year"] > 0].groupby(["citing_year", "inferred_use_type"]).size().reset_index(name="citations")
    if not topic_by_year.empty:
        st.plotly_chart(style_chart(px.area(topic_by_year, x="citing_year", y="citations", color="inferred_use_type", groupnorm="fraction", labels={"inferred_use_type": "Use type"})), use_container_width=True)
    topic_counts = papers[papers["paper_title"].isin(selected_papers)].groupby(["paper_year", "topic"]).size().reset_index(name="papers")
    if not topic_counts.empty and topic_counts["paper_year"].max() > 0:
        st.plotly_chart(style_chart(px.scatter(topic_counts, x="paper_year", y="topic", size="papers", color="topic", labels={"paper_year": "Publication year"})), use_container_width=True)
    else:
        st.info("Add topic and publication-year columns to your Scholar enrichment file to see portfolio drift.")

with tabs[5]:
    st.subheader("Collaboration graph")
    st.caption("The demo graph uses paper-author metadata. Scholar exports may require a separate author enrichment step.")
    graph = nx.Graph()
    for _, paper in papers.iterrows():
        authors = [a.strip() for a in str(paper.get("paper_authors", "")).split(";") if a.strip()]
        for author in authors:
            graph.add_node(author)
        for index, author in enumerate(authors):
            for coauthor in authors[index + 1:]:
                if graph.has_edge(author, coauthor):
                    graph[author][coauthor]["weight"] += 1
                else:
                    graph.add_edge(author, coauthor, weight=1)
    if graph.number_of_nodes() > 0:
        positions = nx.spring_layout(graph, seed=7, k=1.2)
        edge_x, edge_y = [], []
        for source, target in graph.edges():
            edge_x += [positions[source][0], positions[target][0], None]
            edge_y += [positions[source][1], positions[target][1], None]
        node_names = list(graph.nodes())
        node_x = [positions[name][0] for name in node_names]
        node_y = [positions[name][1] for name in node_names]
        degrees = [graph.degree[name] for name in node_names]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line={"color": "#c4c0b8", "width": 1}, hoverinfo="none"))
        fig.add_trace(go.Scatter(x=node_x, y=node_y, mode="markers+text", text=node_names, textposition="top center", marker={"size": [12 + d * 5 for d in degrees], "color": degrees, "colorscale": [[0, "#e0a458"], [1, "#008f8c"]], "showscale": True, "colorbar": {"title": "Collaborators"}}, hovertext=[f"{name}: {degree} collaborators" for name, degree in zip(node_names, degrees)], hoverinfo="text"))
        fig.update_layout(showlegend=False, xaxis={"visible": False}, yaxis={"visible": False}, height=560, margin={"l": 0, "r": 0, "t": 20, "b": 0}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        communities = list(nx.community.greedy_modularity_communities(graph)) if graph.number_of_edges() else []
        metrics = pd.DataFrame({"author": node_names, "collaborators": degrees}).sort_values("collaborators", ascending=False)
        st.dataframe(metrics, use_container_width=True, hide_index=True)
    else:
        st.info("Add a semicolon-separated paper_authors column to render the collaboration graph.")

with tabs[6]:
    st.subheader("How is the work being used?")
    st.caption("The first pass uses transparent keyword classification. Replace it with an LLM classifier after validating your imported abstracts and citation contexts.")
    use_counts = filtered["inferred_use_type"].value_counts().rename_axis("use_type").reset_index(name="citations")
    left, right = st.columns([1, 1.5])
    with left:
        st.plotly_chart(style_chart(px.pie(use_counts, names="use_type", values="citations", hole=.55, color_discrete_sequence=[COLORS["teal"], COLORS["coral"], COLORS["gold"], COLORS["blue"]])), use_container_width=True)
    with right:
        st.dataframe(filtered[["citing_title", "cited_paper", "inferred_use_type", "citing_abstract"]].sort_values("inferred_use_type"), use_container_width=True, hide_index=True)
    st.download_button("Download filtered citation records", data=filtered.to_csv(index=False).encode("utf-8"), file_name="filtered_citation_records.csv", mime="text/csv")

st.markdown(f'<div class="source-note">DATA SNAPSHOT: {data_label.upper()} · IMPORTED RECORDS ARE NOT LIVE-REFRESHED · VALIDATE IDENTITY MATCHES BEFORE REPORTING RESULTS</div>', unsafe_allow_html=True)
