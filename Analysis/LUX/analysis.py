import rdflib
import networkx as nx
from collections import defaultdict, Counter
import numpy as np

def load_rdf_graph(rdf_file):
    g = rdflib.Graph()
    g.parse(rdf_file, format="xml")
    return g

def build_nx_graph(rdf_graph):
    G = nx.DiGraph()
    for s, p, o in rdf_graph:
        G.add_edge(str(s), str(o), predicate=str(p))
    return G

def compute_statistics(rdf_graph, nx_graph):
    entities = set()
    predicates = Counter()
    object_properties = Counter()
    node_relation_cofreq = defaultdict(Counter)
    node_node_cofreq = Counter()

    # To track degree only for concepts (URIRefs, not literals)
    concept_degree_counter = Counter()

    for s, p, o in rdf_graph:
        s_str, p_str, o_str = str(s), str(p), str(o)
        entities.update([s_str, o_str])
        predicates[p_str] += 1
        node_relation_cofreq[s_str][p_str] += 1
        node_relation_cofreq[o_str][p_str] += 1
        node_node_cofreq[(s_str, o_str)] += 1
        node_node_cofreq[(o_str, s_str)] += 1

        if isinstance(o, rdflib.URIRef):
            object_properties[p_str] += 1
            concept_degree_counter[o_str] += 1  # Count degree only if object is a concept
        if isinstance(s, rdflib.URIRef):
            concept_degree_counter[s_str] += 1  # Count subject if it's a concept too

    degrees = dict(nx_graph.degree())
    degree_values = list(degrees.values())

    max_edges = len(entities) * (len(entities) - 1)
    actual_edges = nx_graph.number_of_edges()
    density = actual_edges / max_edges if max_edges > 0 else 0
    clustering = nx.average_clustering(nx_graph.to_undirected())

    degree_distribution_index = np.std(degree_values) / np.mean(degree_values) if np.mean(degree_values) > 0 else 0
    rel_freq_values = list(predicates.values())
    relation_type_index = np.std(rel_freq_values) / np.mean(rel_freq_values) if np.mean(rel_freq_values) > 0 else 0

    scc = list(nx.strongly_connected_components(nx_graph))
    num_scc = len(scc)

    # Top stats
    top_degrees = concept_degree_counter.most_common(10)  # Only concepts
    top_rels = predicates.most_common(10)
    top_obj_props = object_properties.most_common(10)

    top_node_rel_cofreq = sorted(
        [(n, p, c) for n, rels in node_relation_cofreq.items() for p, c in rels.items()],
        key=lambda x: x[2], reverse=True
    )[:10]

    top_node_node_cofreq = node_node_cofreq.most_common(10)

    return {
        "entity_count": len(entities),
        "relation_count": len(predicates),
        "node_count": len(nx_graph.nodes),
        "edge_count": actual_edges,
        "graph_density": density,
        "global_clustering_coefficient": clustering,
        "relation_type_count": len(predicates),
        "degree_distribution_index": degree_distribution_index,
        "relation_type_index": relation_type_index,
        "strongly_connected_components": num_scc,
        "top_10_highest_degree_concept_nodes": top_degrees,
        "top_10_most_frequent_relations": top_rels,
        "top_10_object_properties": top_obj_props,
        "top_10_node_relation_cofreq": top_node_rel_cofreq,
        "top_10_node_node_cofreq": top_node_node_cofreq,
    }

def save_statistics_to_file(stats, filename="rdf_graph_stats.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=== RDF Graph Statistics ===\n\n")
        for key, value in stats.items():
            f.write(f"{key}:\n")
            if isinstance(value, list):
                for item in value:
                    f.write(f"  {item}\n")
            else:
                f.write(f"  {value}\n")
            f.write("\n")

def main():
    rdf_file = "connected_sections.rdf"  # Replace with your RDF/XML file path
    rdf_graph = load_rdf_graph(rdf_file)
    nx_graph = build_nx_graph(rdf_graph)
    stats = compute_statistics(rdf_graph, nx_graph)
    save_statistics_to_file(stats, "rdf_graph_stats.txt")

if __name__ == "__main__":
    main()
