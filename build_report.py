"""Build report tables and compile the PDF (requires pdflatex)."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "report_source"


def rows(name):
    with (ROOT / "results" / name).open() as stream:
        return list(csv.DictReader(stream))


def tabular(name, header, data, alignment):
    text = "\\begin{tabular}{" + alignment + "}\n\\toprule\n"
    text += " & ".join(header) + " \\\\\n\\midrule\n"
    text += "\n".join(" & ".join(map(str, r)) + " \\\\" for r in data)
    text += "\n\\bottomrule\n\\end{tabular}\n"
    (SRC / name).write_text(text)


def main():
    s = json.loads((ROOT / "results/summary.json").read_text())
    source = json.loads((ROOT / "data/source.json").read_text())
    digest = hashlib.sha256((ROOT / "data/facebook.tar.gz").read_bytes()).hexdigest()
    if digest != source["archive_sha256"]:
        raise ValueError("Source archive and provenance checksum disagree.")
    if s["seed"] != 42 or s["resolution"] != 1:
        raise ValueError("Review the case-specific report prose after changing Louvain settings.")
    versions = s["versions"]
    values = {
        "Nnodes": s["nodes"], "Nedges": s["edges"], "Rawrows": s["raw_edge_rows"],
        "MeanDistance": f'{s["main_average_distance"]:.3f}', "Diameter": s["main_diameter"],
        "MainQ": f'{s["main_modularity"]:.4f}', "FullQ": f'{s["full_modularity"]:.4f}',
        "Qlow": f'{s["sensitivity_modularity_range"][0]:.4f}',
        "Qhigh": f'{s["sensitivity_modularity_range"][1]:.4f}',
        "ARIlow": f'{s["sensitivity_ari_range"][0]:.3f}',
        "PythonVersion": s["python"], "NetworkXVersion": versions["networkx"],
        "MatplotlibVersion": versions["matplotlib"], "NumpyVersion": versions["numpy"],
        "ScipyVersion": versions["scipy"],
        "AverageClustering": f'{s["average_clustering"]:.4f}',
        "Transitivity": f'{s["transitivity"]:.4f}',
        "CliquePeople": s["people_in_maximum_cliques"],
        "FourRunCount": s["sensitivity_counts"].get("4", 0),
        "FiveRunCount": s["sensitivity_counts"].get("5", 0),
    }
    (SRC / "values.tex").write_text("\n".join(
        "\\newcommand{\\" + key + "}{" + str(value) + "}" for key, value in values.items()))
    metrics = [
        ["Whole graph", "People", s["nodes"]],
        ["", "Unique friendships", s["edges"]],
        ["", "Density", f'{s["density"]:.4f}'],
        ["", "Average degree", f'{s["average_degree"]:.3f}'],
        ["", "Connected components", len(s["component_sizes"])],
        ["", "Isolates", len(s["isolates"])],
        ["Main component", "People", s["main_nodes"]],
        ["", "Friendships", s["main_edges"]],
        ["", "Mean shortest-path distance", f'{s["main_average_distance"]:.3f}'],
        ["", "Diameter", s["main_diameter"]],
    ]
    tabular("structure_table.tex", ["Scope", "Statistic", "Value"], metrics, "llr")
    central = rows("centrality_all_nodes.csv")
    keys = ["degree_centrality", "closeness", "betweenness", "eigenvector", "pagerank"]
    ranked = sorted(central, key=lambda r: (-int(r["degree"]), int(r["node_id"])))[:10]
    tabular("centrality_top_table.tex", ["ID", "$k$", "$D$", "$C$", "$B$", "$E$", "$P$"],
            [[r["node_id"], r["degree"]] + [f'{float(r[k]):.4f}' for k in keys] for r in ranked],
            "rrrrrrr")
    clique_counts = [r for r in rows("clique_counts.csv") if int(r["size"]) >= 3]
    tabular("clique_counts_table.tex", ["Size", "All", "Maximal"],
            [[r["size"], r["all_cliques"], r["maximal_cliques"]] for r in clique_counts], "rrr")
    tabular("maximum_cliques_table.tex", ["Clique", "Anonymised person IDs"],
            [[i + 1, ", ".join(map(str, c))] for i, c in enumerate(s["maximum_cliques"])], "rl")
    communities = [r for r in rows("communities.csv") if r["scope"] == "main"]
    tabular("main_communities_table.tex", ["Group", "People", "Internal ties", "External ties", "Density"],
            [["M"+r["community"], r["nodes"], r["internal_edges"], r["external_edges"],
              f'{float(r["density"]):.3f}'] for r in communities], "lrrrr")
    header = "ID & $k$ & $D$ & $C$ & $B$ & $E$ & $P$ & Comp. & F & M \\\\"
    text = "\\begin{longtable}{rrrrrrrrrr}\n\\toprule\n" + header
    text += "\n\\midrule\n\\endfirsthead\n\\toprule\n" + header + "\n\\midrule\n\\endhead\n"
    text += "\\bottomrule\n\\endfoot\n"
    for r in central:
        vals = [r["node_id"], r["degree"]] + [f'{float(r[k]):.4f}' for k in keys]
        vals += [r["component"], r["full_community"], r["main_community"] or "--"]
        text += " & ".join(vals) + " \\\\\n"
    text += "\\end{longtable}\n"
    (SRC / "centrality_full_table.tex").write_text(text)
    for _ in range(2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "report.tex"],
            cwd=SRC, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if result.returncode:
            raise RuntimeError("LaTeX failed:\n" + result.stdout[-5000:])
    shutil.copy2(SRC / "report.pdf", ROOT / "Mervine_Muganguzi_Network_Analysis_Report.pdf")
    print(ROOT / "Mervine_Muganguzi_Network_Analysis_Report.pdf")


if __name__ == "__main__":
    main()
