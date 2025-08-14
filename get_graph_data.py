from rdflib import Graph
from collections import defaultdict
import argparse
from itertools import combinations

def load_graph(file_path, format='ttl'):
    g = Graph()
    g.parse(file_path, format=format)
    return g

def get_entities_and_relationships(g):
    entities = set()
    predicates = set()
    for s, p, o in g:
        entities.add(s)
        entities.add(o)
        predicates.add(p)
    return entities, predicates

def compute_graph_density(g, entities):
    n = len(entities)
    if n <= 1:
        return 0
    total_edges = len(g)
    max_edges = n * (n - 1)
    return total_edges / max_edges

def compute_average_node_degree(g):
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)

    for s, p, o in g:
        out_degree[s] += 1
        in_degree[o] += 1

    all_nodes = set(in_degree.keys()) | set(out_degree.keys())
    total_degrees = sum(in_degree[n] + out_degree[n] for n in all_nodes)
    avg_node_degree = total_degrees / len(all_nodes) if all_nodes else 0
    return avg_node_degree

def compute_average_relationship_frequency(g):
    predicate_count = defaultdict(int)
    for _, p, _ in g:
        predicate_count[p] += 1

    if not predicate_count:
        return 0
    avg_frequency = sum(predicate_count.values()) / len(predicate_count)
    return avg_frequency

def compute_inverse_relationships(g):
    triple_set = set((str(s), str(p), str(o)) for s, p, o in g)
    inverse_relations = set()

    for s, p, o in g:
        for _, p2, _ in g.triples((o, None, s)):
            if p != p2:
                inverse_relations.add((str(p), str(p2)))
    return len(inverse_relations)

def compute_symmetric_asymmetric_relations(g):
    predicate_pairs = defaultdict(set)
    symmetric = set()
    asymmetric = set()

    for s, p, o in g:
        predicate_pairs[p].add((str(s), str(o)))

    for p, pairs in predicate_pairs.items():
        is_symmetric = all((o, s) in pairs for s, o in pairs)
        if is_symmetric:
            symmetric.add(p)
        else:
            asymmetric.add(p)

    return len(symmetric), len(asymmetric)

def analyze_rdf(file_path, fmt='ttl'):
    g = load_graph(file_path, format=fmt)
    entities, predicates = get_entities_and_relationships(g)
    density = compute_graph_density(g, entities)
    avg_degree = compute_average_node_degree(g)
    avg_freq = compute_average_relationship_frequency(g)
    inverse_rel_count = compute_inverse_relationships(g)
    sym_count, asym_count = compute_symmetric_asymmetric_relations(g)

    print("====== RDF Graph Analysis ======")
    print(f"Number of Entities: {len(entities)}")
    print(f"Number of Relationships: {len(predicates)}")
    print(f"Graph Density: {density:.4f}")
    print(f"Average Node Degree: {avg_degree:.2f}")
    print(f"Average Relationship Frequency: {avg_freq:.2f}")
    print(f"Number of Inverse Relationships: {inverse_rel_count}")
    print(f"Number of Symmetric Relationships: {sym_count}")
    print(f"Number of Asymmetric Relationships: {asym_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze RDF data.")
    parser.add_argument("file_path", help="Path to RDF file")
    parser.add_argument("--format", default="ttl", help="RDF file format (default: ttl)")
    args = parser.parse_args()

    analyze_rdf(args.file_path, fmt=args.format)
