Prepared for: Mervine Muganguzi

FACEBOOK FRIENDSHIP NETWORK ANALYSIS
===================================

Start with Mervine_Muganguzi_Network_Analysis_Report.pdf. It contains the methods, equations,
figures, results, limitations, all 59 centrality rows, and the complete Python
analysis code. The first nine pages are the main report and references.

REQUIREMENTS AND RUNNING
------------------------
Use Python 3.12 or later. Python 3.12.14 was used for the supplied results.
Extract the complete ZIP, open a terminal in this project folder, and run:

    python -m pip install -r requirements.txt
    python network_analysis.py

A virtual environment is recommended if you already have other Python projects.
The bundled data/facebook.tar.gz lets the analysis run offline after package
installation. The program recreates the data CSVs, result tables and figures.
If the archive is missing, the script downloads it from the official SNAP site.

For a notebook interface, open run_analysis.ipynb in Jupyter or VS Code from
this extracted project folder and run the cells in order. The notebook runs
the same script, so there is only one implementation of the calculations.

FILES
-----
network_analysis.py                  Complete, commented analysis and plotting.
requirements.txt                     Exact versions used for scientific packages.
run_analysis.ipynb                    Notebook entry point and result viewer.
data/facebook.tar.gz                  Original public SNAP source archive.
data/nodes.csv                       All 59 anonymised person IDs.
data/edges.csv                       146 unique undirected friendship pairs.
data/source.json                     Source links, scope and archive checksum.
results/centrality_all_nodes.csv      Five centralities for the full 59-node graph.
results/centrality_main_component.csv Same measures recalculated on 44 nodes.
results/clique_counts.csv            All versus maximal clique counts by size.
results/maximal_cliques.csv          Every maximal clique, including sizes 1 and 2.
results/communities.csv              Membership and statistics for both scopes.
results/community_sensitivity.csv    Thirty random-seed checks on the main graph.
results/summary.json                 Summary numbers, parameters and versions.
results/verification.json            Independent numerical and clique checks.
figures/                             Five figures in vector PDF and PNG formats.
report_source/                       Editable LaTeX report and generated tables.
build_report.py                      Regenerate tables and compile the PDF.
verify_results.py                    Independent checks of the saved results.
review_notes.txt                     What was checked and clarified in this review.

OPTIONAL INDEPENDENT CHECKS
---------------------------
After running the analysis, run:

    python verify_results.py

This checks centralities through direct shortest-path enumeration and dense
matrix solutions, verifies clique counts through recursive enumeration, and
recalculates modularity as a sum over communities. It writes verification.json.

REBUILDING THE REPORT (OPTIONAL)
-------------------------------
The analysis does not require LaTeX. To regenerate the report PDF, install a
LaTeX distribution that provides pdflatex and the packages named in report.tex,
then run from the project directory:

    python build_report.py

Edit report_source/report.tex to add a student name or change the report text.
If you change the dataset or methods, review the prose as well: some explanatory
sentences describe this particular network and are intentionally not templates.

IMPORTANT INTERPRETATION DETAILS
--------------------------------
The ego user 3980 is excluded. The nodes are this user's friends; the edges
are recorded friendships among those friends. Numeric IDs are already anonymous.
Profile feature values and supplied social-circle labels are not analysed.
Seven isolates are preserved by loading the node roster before the edges.

Primary centralities use all 59 nodes. The main-component CSV is a separate
calculation with a different normalization denominator. Values should not be
mixed across these files. Corrected closeness accounts for reachability.
Full-graph eigenvector scores concentrate on the main component. PageRank
uses damping 0.85 and uniformly redistributes mass from isolated nodes.

Community seed = 42 and resolution = 1. The full graph and main component
are partitioned separately: F and M labels do not refer to the same partition.
Thirty additional seeds (0 through 29) give four or five main-component groups.
The fixed-seed plot is one reproducible partition, not a unique social truth.
Full-graph community count includes isolated people as singleton groups.
Their placement does not change modularity because their degree is zero.

Clique enumeration is exact for this small graph. A maximal clique cannot
be enlarged; a maximum clique has the largest size anywhere in the graph.
The CSV includes 64 maximal cliques in total, 44 of size at least three.
There are six maximum cliques, each of size six. Groups can overlap.
Together those six cliques cover 15 distinct people.

Network plots label selected people to remain readable at page size. In the
main overview and community plots, labels identify people with degree at least
ten or in the top five for betweenness. Small components show every ID. The
clique detail labels all six members. All 59 IDs and both community assignments
are available in the CSVs and the report appendix. Degree counts refer only
to ties inside this selected network, not a person's total Facebook friend count.

DATA SOURCE
-----------
Stanford Network Analysis Project, Social circles: Facebook.
https://snap.stanford.edu/data/ego-Facebook.html
https://snap.stanford.edu/data/readme-Ego.txt
https://snap.stanford.edu/data/facebook.tar.gz

J. McAuley and J. Leskovec (2012). Learning to Discover Social Circles in Ego
Networks. Advances in Neural Information Processing Systems, 25.

Source accessed on 6 November 2026. The source archive is included unchanged;
data/source.json records its SHA-256 checksum. The analysis checks this exact
audited archive snapshot before running. If a later download has different
bytes, it stops so that the changed source can be reviewed. Source attribution
is retained.
The findings describe one observed, historical friend network. They do not
identify real people or establish actual influence, friendship strength,
communication patterns, temporal change, or representativeness of Facebook.

Dataset source and download links are also in DATASET_LINKS.txt.
