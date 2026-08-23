from pathlib import Path

import pandas as pd


SOURCE_PAPERS = {
    "p1.csv": ("P1", "Gait identification using component based gait energy image analysis", 2014, "Nandy, Anup; Pathak, Akanksha; Chakraborty, Pavan; Nandi, GC"),
    "p2.csv": ("P2", "Transfer learning based heart valve disease classification from phonocardiogram signal", 2023, "Maity, Arnab; Pathak, Akanksha; Saha, Goutam"),
    "p3.csv": ("P3", "Fragment-level classification of ECG arrhythmia using wavelet scattering transform", 2023, "Nahak, Sudestna; Pathak, Akanksha; Saha, Goutam"),
    "p4.csv": ("P4", "Classification of coronary artery diseased and normal subjects using multi-channel phonocardiogram signal", 2019, "Samanta, Pranab; Pathak, Akanksha; Mandana, Kayapanda; Saha, Goutam"),
    "p5.csv": ("P5", "Ensembled transfer learning and multiple kernel learning for phonocardiogram based atherosclerotic coronary artery disease detection", 2022, "Pathak, Akanksha; Mandana, Kayapanda; Saha, Goutam"),
    "p6.csv": ("P6", "Evaluation of handcrafted features and learned representations for the classification of arrhythmia and congestive heart failure in ECG", 2023, "Nahak, Sudestna; Pathak, Akanksha; Saha, Goutam"),
    "p7.csv": ("P7", "An improved method to detect coronary artery disease using phonocardiogram signals in noisy environment", 2020, "Pathak, Akanksha; Samanta, Pranab; Mandana, Kayapanda; Saha, Goutam"),
    "p8.csv": ("P8", "Detection of coronary artery atherosclerotic disease using novel features from synchrosqueezing transform of phonocardiogram", 2020, "Pathak, Akanksha; Samanta, Pranab; Mandana, Kayapanda; Saha, Goutam"),
    "p9.csv": ("P9", "A study on gait entropy image analysis for clothing invariant human identification", 2017, "Nandy, Anup; Pathak, Akanksha; Chakraborty, Pavan"),
    "p10.csv": ("P10", "Identification of coronary artery diseased subjects using spectral featuries", 2018, "Samanta, Pranab; Pathak, Akanksha; Mandana, Kayapanda; Saha, Goutam"),
    "p11.csv": ("P11", "Atherosclerotic Coronary Artery Disease Detection using Multichannel Phonocardiogram Signals", 0, "Pathak, Akanksha"),
}


def prepare() -> pd.DataFrame:
    frames = []
    for filename, (paper_id, paper_title, _, _) in SOURCE_PAPERS.items():
        frame = pd.read_csv(filename)
        paper_year = SOURCE_PAPERS[filename][2]
        paper_authors = SOURCE_PAPERS[filename][3]
        frame.insert(0, "cited_paper_id", paper_id)
        frame.insert(1, "cited_paper", paper_title)
        frame.insert(2, "paper_year", paper_year)
        frame.insert(3, "paper_authors", paper_authors)
        frame["citing_title"] = frame["Title"].fillna("").astype(str)
        frame["citing_author"] = frame["Authors"].fillna("").astype(str)
        frame["citing_year"] = pd.to_numeric(frame["Year"], errors="coerce").fillna(0).astype(int)
        frame["citing_abstract"] = frame["Abstract"].fillna("").astype(str)
        frame["venue"] = frame["Source"].fillna("Unknown").astype(str)
        frame["country"] = "Unknown"
        frame["field"] = "Unknown"
        frame["use_type"] = "Unclassified"
        frame["snapshot_date"] = frame["QueryDate"].fillna("").astype(str)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    prepared = prepare()
    prepared.to_csv("prepared_citations.csv", index=False)
    print(f"Wrote prepared_citations.csv with {len(prepared)} rows from {len(SOURCE_PAPERS)} source files.")
    print(prepared.groupby(["cited_paper_id", "cited_paper"]).size().to_string())
