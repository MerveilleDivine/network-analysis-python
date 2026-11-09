"""Analyse SNAP Facebook friend network 3980 (Python 3.12+).

Prepared for: Mervine Muganguzi

Run: python network_analysis.py
The bundled archive permits an offline rerun. All paths are relative to this file.
"""
from collections import Counter
from importlib.metadata import version
from itertools import combinations
from math import comb
from pathlib import Path
import csv
import hashlib
import json
import platform
import tarfile
from urllib.request import urlopen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

ROOT = Path(__file__).resolve().parent
DATA, OUT, FIG = [ROOT / x for x in ("data", "results", "figures")]
SOURCE = "https://snap.stanford.edu/data/facebook.tar.gz"
EGO, SEED = 3980, 42
COLORS = ["#197A78", "#DD8841", "#5774AE", "#AE5470", "#8A9545"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "savefig.facecolor": "white"})


def write_csv(name, rows, fields):
    """Write a table with an explicit column order."""
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def partition(graph, seed=SEED):
    """Sort Louvain communities so their displayed labels are reproducible."""
    groups = nx.community.louvain_communities(
        graph, weight=None, resolution=1, seed=seed)
    return sorted(groups, key=lambda c: (-len(c), min(c)))


def membership(groups):
    return {node: i + 1 for i, group in enumerate(groups) for node in group}


def adjusted_rand(a, b, nodes):
    """Chance-adjusted agreement of two community assignments."""
    if len(nodes) < 2:
        return 1.0
    pairs = lambda n: comb(n, 2)
    cells = Counter((a[v], b[v]) for v in nodes)
    score = sum(pairs(n) for n in cells.values())
    row = sum(pairs(n) for n in Counter(a[v] for v in nodes).values())
    col = sum(pairs(n) for n in Counter(b[v] for v in nodes).values())
    expected = row * col / pairs(len(nodes))
    limit = (row + col) / 2
    return (score - expected) / (limit - expected) if limit != expected else 1.0


def centralities(graph):
    """Calculate the five measures for the supplied graph and its scope."""
    return {
        "degree_centrality": nx.degree_centrality(graph),
        "closeness": nx.closeness_centrality(graph, wf_improved=True),
        "betweenness": nx.betweenness_centrality(graph, normalized=True),
        "eigenvector": nx.eigenvector_centrality(
            graph, max_iter=5000, tol=1e-12),
        "pagerank": nx.pagerank(graph, alpha=0.85, max_iter=5000, tol=1e-12),
    }


def save_figure(fig, name):
    fig.savefig(FIG / (name + ".pdf"), bbox_inches="tight")
    fig.savefig(FIG / (name + ".png"), dpi=210, bbox_inches="tight")
    plt.close(fig)


def plot_network(graph, pos, ax, color, title, highlighted=None, label_nodes=None):
    """Use a fixed size key; selectively label crowded plots for readability."""
    highlight = set() if highlighted is None else set(highlighted)
    nx.draw_networkx_edges(graph, pos, ax=ax, edge_color="#AEB8C2",
                           width=0.8, alpha=0.7)
    if highlight:
        internal = [(u, v) for u, v in graph.edges if u in highlight and v in highlight]
        nx.draw_networkx_edges(graph, pos, ax=ax, edgelist=internal,
                               edge_color="#C44941", width=2.1)
    nx.draw_networkx_nodes(
        graph, pos, ax=ax, node_size=[80 + 19 * graph.degree(v) for v in graph],
        node_color=color, edgecolors=["#C44941" if v in highlight else "white"
                                    for v in graph],
        linewidths=[2.2 if v in highlight else 0.7 for v in graph])
    labelled = graph if label_nodes is None else label_nodes
    labels = {v: str(v) for v in sorted(labelled) if v in graph}
    nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax,
                            font_size=9 if len(graph) > 10 else 10,
                            font_color="#172A3A",
                            bbox={"facecolor": "white", "edgecolor": "none",
                                  "alpha": 0.65, "pad": 0.25})
    ax.set_title(title, fontsize=12, pad=14)
    ax.margins(0.12)
    ax.axis("off")


def size_key(ax):
    handles = [ax.scatter([], [], s=80 + 19 * degree, facecolor="white",
                          edgecolors="#5C6C77", label=str(degree))
               for degree in (1, 10, 18)]
    ax.legend(handles=handles, title="Degree within this graph",
              loc="lower center", bbox_to_anchor=(0.5, -0.04),
              ncol=3, frameon=False, fontsize=8, title_fontsize=8)


def main():
    for folder in (DATA, OUT, FIG):
        folder.mkdir(exist_ok=True)
    archive = DATA / "facebook.tar.gz"
    if not archive.exists():
        with urlopen(SOURCE, timeout=60) as response:
            archive.write_bytes(response.read())
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    expected_hash = "78594c43169b698e99a77741bc298581af87146e4f3d3e8ad48a48361b5d92b6"
    if archive_hash != expected_hash:
        raise ValueError("The source archive differs from the audited snapshot.")
    # Read specific files in memory; never extract arbitrary archive paths.
    with tarfile.open(archive) as tar:
        files = {Path(m.name).name: m for m in tar if m.isfile()}
        edge_text = tar.extractfile(files[f"{EGO}.edges"]).read().decode()
        feat_text = tar.extractfile(files[f"{EGO}.feat"]).read().decode()
    nodes = sorted({int(line.split()[0]) for line in feat_text.splitlines() if line})
    raw_edges = [tuple(map(int, line.split())) for line in edge_text.splitlines()
                 if line.strip()]
    edges = sorted({tuple(sorted(edge)) for edge in raw_edges})
    assert set(Counter(tuple(sorted(e)) for e in raw_edges).values()) == {2}
    assert all(u != v for u, v in edges), "Unexpected self-loop in source"
    assert {v for edge in edges for v in edge} <= set(nodes)
    assert EGO not in nodes
    graph = nx.Graph()
    graph.add_nodes_from(nodes)  # Preserve seven isolates absent from .edges.
    graph.add_edges_from(edges)
    assert (len(graph), graph.number_of_edges()) == (59, 146)
    for name, fields, rows in [
        ("nodes.csv", ["node_id"], [[v] for v in nodes]),
        ("edges.csv", ["source", "target"], edges),
    ]:
        with (DATA / name).open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(fields)
            writer.writerows(rows)
    provenance = {
        "dataset": "SNAP Social circles: Facebook, friend network 3980",
        "source_page": "https://snap.stanford.edu/data/ego-Facebook.html",
        "archive_url": SOURCE,
        "source_documentation": "https://snap.stanford.edu/data/readme-Ego.txt",
        "citation": "J. McAuley and J. Leskovec (2012), Learning to Discover "
                    "Social Circles in Ego Networks, NIPS 25.",
        "accessed_date": "2026-11-06",
        "archive_sha256": archive_hash,
        "scope": "Friends of ego 3980; ego excluded; profile values not used",
        "unused_source_fields": ["profile feature values", "ego-defined circle memberships"],
        "roster_file": "3980.feat", "relationship_file": "3980.edges",
        "raw_edge_rows": len(raw_edges), "unique_undirected_edges": len(edges),
        "node_count": len(nodes), "anonymized_original_ids_retained": True,
    }
    (DATA / "source.json").write_text(json.dumps(provenance, indent=2))
    components = sorted(nx.connected_components(graph),
                        key=lambda c: (-len(c), min(c)))
    component_id = membership(components)
    main_graph = graph.subgraph(components[0]).copy()
    full_groups, main_groups = partition(graph), partition(main_graph)
    full_labels, main_labels = membership(full_groups), membership(main_groups)
    full_scores, main_scores = centralities(graph), centralities(main_graph)
    fields = ["node_id", "degree", "degree_centrality", "closeness",
              "betweenness", "eigenvector", "pagerank", "component",
              "full_community", "main_community"]
    for g, scores, filename in [(graph, full_scores, "centrality_all_nodes.csv"),
                                (main_graph, main_scores, "centrality_main_component.csv")]:
        rows = [{"node_id": v, "degree": g.degree(v),
                 **{key: value[v] for key, value in scores.items()},
                 "component": component_id[v], "full_community": full_labels[v],
                 "main_community": main_labels.get(v, "")} for v in sorted(g)]
        write_csv(filename, rows, fields)
    maximal = sorted((sorted(c) for c in nx.find_cliques(graph)),
                     key=lambda c: (-len(c), c))
    clique_counts = Counter(len(c) for c in nx.enumerate_all_cliques(graph))
    maximum_size = max(map(len, maximal))
    largest = [c for c in maximal if len(c) == maximum_size]
    assert all(graph.has_edge(u, v) for c in maximal for u, v in combinations(c, 2))
    write_csv("maximal_cliques.csv", [{"clique_id": i + 1, "size": len(c),
              "node_ids": " ".join(map(str, c))} for i, c in enumerate(maximal)],
              ["clique_id", "size", "node_ids"])
    write_csv("clique_counts.csv", [{"size": k, "all_cliques": clique_counts[k],
              "maximal_cliques": sum(len(c) == k for c in maximal)}
              for k in range(1, maximum_size + 1)],
              ["size", "all_cliques", "maximal_cliques"])
    community_stats = []
    for scope, g, groups in [("full", graph, full_groups),
                              ("main", main_graph, main_groups)]:
        for i, group in enumerate(groups, 1):
            internal = g.subgraph(group).number_of_edges()
            external = sum(1 for u, v in g.edges if (u in group) != (v in group))
            community_stats.append({"scope": scope, "community": i,
                "nodes": len(group), "internal_edges": internal,
                "external_edges": external, "density": nx.density(g.subgraph(group)),
                "node_ids": " ".join(map(str, sorted(group)))})
    write_csv("communities.csv", community_stats, list(community_stats[0]))
    sensitivity = []
    for seed in range(30):
        groups = partition(main_graph, seed)
        sensitivity.append({"seed": seed, "communities": len(groups),
            "modularity": nx.community.modularity(main_graph, groups, weight=None),
            "adjusted_rand_vs_seed42": adjusted_rand(
                membership(groups), main_labels, list(main_graph))})
    write_csv("community_sensitivity.csv", sensitivity, list(sensitivity[0]))
    summary = {
        "nodes": len(graph), "edges": len(edges), "density": nx.density(graph),
        "raw_edge_rows": len(raw_edges), "duplicate_edge_rows_removed": len(raw_edges)-len(edges),
        "average_degree": 2 * len(edges) / len(graph),
        "degree_range": [min(dict(graph.degree()).values()), max(dict(graph.degree()).values())],
        "component_sizes": [len(c) for c in components],
        "isolates": sorted(nx.isolates(graph)),
        "main_nodes": len(main_graph), "main_edges": main_graph.number_of_edges(),
        "main_diameter": nx.diameter(main_graph),
        "main_average_distance": nx.average_shortest_path_length(main_graph),
        "average_clustering": nx.average_clustering(graph),
        "transitivity": nx.transitivity(graph), "triangles": clique_counts[3],
        "maximum_clique_size": maximum_size, "maximum_cliques": largest,
        "people_in_maximum_cliques": len(set().union(*map(set, largest))),
        "maximal_cliques_size3plus": sum(len(c) >= 3 for c in maximal),
        "full_community_sizes": [len(c) for c in full_groups],
        "full_modularity": nx.community.modularity(graph, full_groups, weight=None),
        "main_community_sizes": [len(c) for c in main_groups],
        "main_modularity": nx.community.modularity(main_graph, main_groups, weight=None),
        "seed": SEED, "resolution": 1, "sensitivity_seeds": [0, 29],
        "sensitivity_counts": dict(Counter(r["communities"] for r in sensitivity)),
        "sensitivity_modularity_range": [min(r["modularity"] for r in sensitivity),
                                         max(r["modularity"] for r in sensitivity)],
        "sensitivity_ari_range": [min(r["adjusted_rand_vs_seed42"] for r in sensitivity),
                                  max(r["adjusted_rand_vs_seed42"] for r in sensitivity)],
        "top5": {key: sorted(values, key=lambda v: (-values[v], v))[:5]
                 for key, values in full_scores.items()},
        "versions": {p: version(p) for p in ("networkx", "matplotlib", "numpy", "scipy")},
        "python": platform.python_version(),
    }
    assert abs(sum(full_scores["pagerank"].values()) - 1) < 1e-9
    assert sum(dict(graph.degree()).values()) == 2 * len(edges)
    assert clique_counts[3] == sum(nx.triangles(graph).values()) // 3
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    # Use the same main-component layout in all network figures.
    main_pos = nx.spring_layout(main_graph, seed=SEED, iterations=500, k=0.48)
    key_nodes = set(summary["top5"]["degree_centrality"])
    key_nodes.update(summary["top5"]["betweenness"])
    key_nodes.update(v for v in graph if graph.degree(v) >= 10)
    # Separate panels express disconnectedness, not geographic separation.
    fig = plt.figure(figsize=(11.0, 7.4))
    grid = fig.add_gridspec(4, 4, width_ratios=[1, 1, 1, 0.9])
    ax = fig.add_subplot(grid[:, :3])
    plot_network(main_graph, main_pos, ax, COLORS[0],
                 "Main component: 44 people, 138 friendships", label_nodes=key_nodes)
    size_key(ax)
    for i, component in enumerate(components[1:4]):
        small = graph.subgraph(component)
        ax = fig.add_subplot(grid[i, 3])
        plot_network(small, nx.circular_layout(small), ax, "#9CA7B2",
                     f"Component {i + 2}: {len(small)} people")
    isolated = graph.subgraph(summary["isolates"])
    ax = fig.add_subplot(grid[3, 3])
    pos = {v: (i % 4, -(i // 4)) for i, v in enumerate(isolated)}
    plot_network(isolated, pos, ax, "#9CA7B2", "7 isolates\n(within this graph)")
    fig.subplots_adjust(wspace=0.35, hspace=0.6)
    save_figure(fig, "01_network_overview")
    fig, ax = plt.subplots(figsize=(10, 7.0))
    plot_network(main_graph, main_pos, ax,
                 [COLORS[main_labels[v] - 1] for v in main_graph],
                 "Louvain communities in the main component (seed 42)",
                 label_nodes=key_nodes)
    handles = [Line2D([], [], marker="o", linestyle="", color=COLORS[i],
               label=f"M{i+1}: {len(c)} people", markersize=9)
               for i, c in enumerate(main_groups)]
    ax.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
              bbox_to_anchor=(0.5, -0.03))
    save_figure(fig, "02_communities")
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.3))
    for ax, key, title in zip(axes, ["degree_centrality", "betweenness"],
                               ["Direct connections (degree)", "Shortest-path bridging (betweenness)"]):
        selected = summary["top5"][key][::-1]
        values = [graph.degree(v) if key == "degree_centrality" else full_scores[key][v]
                  for v in selected]
        ax.barh([str(v) for v in selected], values, color=COLORS[0 if key == "degree_centrality" else 1])
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Observed ties within this graph" if key == "degree_centrality"
                      else "Normalized betweenness")
        ax.set_ylabel("Anonymised person ID")
        if key == "degree_centrality":
            upper = ((max(values) + 4) // 5) * 5
            ax.set_xticks(range(0, upper + 1, 5))
            ax.set_xlim(0, upper)
        ax.grid(axis="x", alpha=0.18)
    fig.tight_layout(w_pad=3)
    save_figure(fig, "03_centrality_comparison")
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 6.0),
                             gridspec_kw={"width_ratios": [1.8, 1]})
    plot_network(main_graph, main_pos, axes[0],
                 ["#EEB784" if v in largest[0] else "#D2DDE0" for v in main_graph],
                 "Location within the main component", largest[0], largest[0])
    clique_graph = graph.subgraph(largest[0])
    circle = nx.circular_layout(clique_graph)
    nx.draw_networkx_edges(clique_graph, circle, ax=axes[1], width=1.5,
                           edge_color="#C44941")
    nx.draw_networkx_nodes(clique_graph, circle, ax=axes[1], node_size=680,
                           node_color="#EEB784", edgecolors="white")
    nx.draw_networkx_labels(clique_graph, circle, ax=axes[1], font_size=9)
    axes[1].set_title("6 people, all 15 friendships", fontsize=11, pad=14)
    axes[1].margins(0.24)
    axes[1].set_aspect("equal")
    axes[1].axis("off")
    fig.tight_layout()
    save_figure(fig, "04_maximum_clique")
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.5))
    degrees = Counter(dict(graph.degree()).values())
    axes[0].bar(list(degrees), list(degrees.values()), color=COLORS[0])
    axes[0].set(xlabel="Degree (number of observed friends)", ylabel="People",
                title="Degree distribution", xticks=range(0, 19, 2))
    sizes = list(range(3, maximum_size + 1))
    axes[1].bar(sizes, [clique_counts[k] for k in sizes], color=COLORS[1])
    axes[1].set(xlabel="Clique size", ylabel="Number of cliques",
                title="All cliques of size 3 or more", xticks=sizes)
    fig.tight_layout(w_pad=3)
    save_figure(fig, "05_distributions")
    print(json.dumps(summary, indent=2))
    print("Finished: prepared data in data/, tables in results/, plots in figures/.")


if __name__ == "__main__":
    main()
