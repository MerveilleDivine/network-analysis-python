"""Independently check the saved analysis outputs; run after network_analysis.py."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import csv
import json

import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parent


def read(folder, name):
    with (ROOT / folder / name).open() as stream:
        return list(csv.DictReader(stream))


def main():
    nodes = [int(r["node_id"]) for r in read("data", "nodes.csv")]
    edges = [(int(r["source"]), int(r["target"])) for r in read("data", "edges.csv")]
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    rows = {int(r["node_id"]): r for r in read("results", "centrality_all_nodes.csv")}
    summary = json.loads((ROOT / "results/summary.json").read_text())
    n = len(nodes)
    a = nx.to_numpy_array(graph, nodelist=nodes)
    assert len(nodes) == len(set(nodes)) == summary["nodes"] == len(rows)
    assert len(edges) == graph.number_of_edges() == summary["edges"]
    assert abs(np.trace(a @ a @ a) / 6 - summary["triangles"]) < 1e-9
    errors = {"degree_formula": max(abs(float(rows[v]["degree_centrality"])
                                       - graph.degree(v) / (n - 1)) for v in nodes)}
    closeness = {}
    for v in nodes:
        distances = nx.single_source_shortest_path_length(graph, v)
        r = len(distances) - 1
        closeness[v] = (r / (n - 1)) * (r / sum(distances.values())) if r else 0
    errors["closeness_formula"] = max(abs(float(rows[v]["closeness"])
                                           - closeness[v]) for v in nodes)
    # Enumerate every shortest path, independently of Brandes' algorithm.
    between = dict.fromkeys(nodes, 0.0)
    for component in nx.connected_components(graph):
        for u, v in combinations(sorted(component), 2):
            paths = list(nx.all_shortest_paths(graph, u, v))
            for path in paths:
                for w in path[1:-1]:
                    between[w] += 1 / len(paths)
    scale = 2 / ((n - 1) * (n - 2))
    errors["betweenness_path_enumeration"] = max(
        abs(float(rows[v]["betweenness"]) - scale * between[v]) for v in nodes)
    # Dense eigen-decomposition checks the power-iteration result.
    _, vectors = np.linalg.eigh(a)
    eig = np.abs(vectors[:, -1])
    eig /= np.linalg.norm(eig)
    errors["eigenvector_dense_solution"] = max(
        abs(float(rows[v]["eigenvector"]) - eig[i]) for i, v in enumerate(nodes))
    # Solve PageRank's linear system, including uniform dangling redistribution.
    transition = np.zeros_like(a)
    for j in range(n):
        degree = a[:, j].sum()
        transition[:, j] = a[:, j] / degree if degree else 1 / n
    pr = np.linalg.solve(np.eye(n) - 0.85 * transition, np.full(n, 0.15 / n))
    errors["pagerank_linear_solution"] = max(
        abs(float(rows[v]["pagerank"]) - pr[i]) for i, v in enumerate(nodes))
    assert max(errors.values()) < 1e-8, errors
    # Recursive extension checks NetworkX's breadth-first clique enumeration.
    counts, maximal = Counter(), set()
    neighbours = {v: set(graph.neighbors(v)) for v in nodes}
    def visit(prefix, candidates):
        for i, v in enumerate(candidates):
            clique = prefix + (v,)
            counts[len(clique)] += 1
            common = set.intersection(*(neighbours[u] for u in clique))
            if not common:
                maximal.add(clique)
            visit(clique, [w for w in candidates[i + 1:] if w in neighbours[v]])
    visit((), sorted(nodes))
    expected = {int(r["size"]): int(r["all_cliques"])
                for r in read("results", "clique_counts.csv")}
    assert dict(counts) == expected
    saved = {tuple(map(int, r["node_ids"].split()))
             for r in read("results", "maximal_cliques.csv")}
    assert maximal == saved
    # Recalculate modularity as a sum over communities, not adjacency pairs.
    modularity_errors = {}
    community_rows = read("results", "communities.csv")
    for scope in ("full", "main"):
        groups = [set(map(int, r["node_ids"].split())) for r in community_rows
                  if r["scope"] == scope]
        included = set().union(*groups)
        h = graph.subgraph(included)
        assert sum(map(len, groups)) == len(included)
        m = h.number_of_edges()
        q = sum(h.subgraph(c).number_of_edges() / m
                - (sum(h.degree(v) for v in c) / (2 * m)) ** 2 for c in groups)
        modularity_errors[scope] = abs(q - summary[scope + "_modularity"])
    assert max(modularity_errors.values()) < 1e-12
    checks = {"all_checks_passed": True, "centrality_max_absolute_errors": errors,
              "clique_counts_by_recursive_enumeration": dict(counts),
              "maximal_cliques_verified": len(maximal),
              "modularity_absolute_errors": modularity_errors}
    (ROOT / "results/verification.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
