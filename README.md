# Friendship Network Analysis in Python

**Author: Mervine Muganguzi**

A reproducible network analysis project for Statistical Analysis and Forecasting. It studies **59 anonymised people and 146 observed friendship ties** from Stanford SNAP's public Facebook dataset. The focal user is excluded; all seven isolates are retained.

## Report and downloads

- [Read the full report](Mervine_Muganguzi_Network_Analysis_Report.pdf): equations, figures, results, limitations, all centrality values, and complete Python analysis code.
- Use **Code → Download ZIP** to download the repository. The **Releases** section also contains the named submission ZIP.
- [Open the notebook](run_analysis.ipynb) for a guided entry point.

## What the analysis covers

- Network visualisation and connectivity.
- Degree, corrected closeness, betweenness, eigenvector centrality, and PageRank.
- Exact clique enumeration: six maximum cliques of size six, overlapping across 15 people.
- Louvain community detection, with random-seed sensitivity checks.
- Independent verification using direct shortest-path enumeration, matrix solutions, and recursive clique enumeration.

Person 4030 has the highest degree and eigenvector centrality. Person 4023 leads corrected closeness, betweenness, and PageRank. Louvain finds four or five groups within the main 44-person component across the tested seeds, so these partitions are not treated as unique social groups. Source circle memberships are available but were not used for validation.

## Run the project

Use **Python 3.12 or later**. From the extracted or cloned repository directory:

```bash
python -m pip install -r requirements.txt
python network_analysis.py
python verify_results.py
```

The source archive is included for an offline analysis after installing the packages. The script reproduces the prepared CSVs in `data/`, numerical results in `results/`, and PDF/PNG figures in `figures/`. Package versions are pinned in `requirements.txt`.

To rebuild the report, additionally install a LaTeX distribution with `pdflatex`, then run:

```bash
python build_report.py
```

The report retains the original analysis date, 6 November 2026. See [README.txt](README.txt) for the complete file guide and [review_notes.txt](review_notes.txt) for the review corrections.

## Dataset and citation

- [Stanford SNAP dataset information](https://snap.stanford.edu/data/ego-Facebook.html)
- [Official source archive](https://snap.stanford.edu/data/facebook.tar.gz)
- [File-format documentation](https://snap.stanford.edu/data/readme-Ego.txt)
- [Local source notes](DATASET_LINKS.txt) and [provenance/checksum](data/source.json)

The selected files are `3980.edges` and the node IDs in `3980.feat`. Profile feature values are not analysed. The archive is a third-party dataset; the original source and attribution are preserved.

> J. McAuley and J. Leskovec (2012). *Learning to Discover Social Circles in Ego Networks*. Advances in Neural Information Processing Systems, 25.

This is one historical, anonymised friendship subgraph. Degree counts refer to ties inside this graph. They do not establish friendship strength, real-world influence, or representativeness of all Facebook users.

## Main files

| Path | Contents |
| --- | --- |
| `network_analysis.py` | Data preparation, calculations and figures |
| `verify_results.py` | Independent checks of the saved results |
| `run_analysis.ipynb` | Notebook entry point |
| `Mervine_Muganguzi_Network_Analysis_Report.pdf` | Named report |
| `data/` | Prepared CSVs, source archive and provenance |
| `results/` | Centrality, clique, community and verification results |
| `figures/` | Figures in PDF and PNG formats |
| `report_source/` | Editable LaTeX report and tables |
