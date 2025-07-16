from rdflib import Graph, URIRef
from rdflib.namespace import RDF
import random
#THIS CODE IS USED TO EXTRACT 98 CONNECTED SECTIONS OF LINES AND ALL OPS AND TRACKS, SIDINGS... INCLUDED

for i in ["LUX", "NLD", "BEL", "FRA", "DEU", "SWE"]:
    
    # Load RDF graph
    g = Graph()
    g.parse(f"{i}/combined.rdf", format="xml")

    # Parameters
    N = 98  # Number of connected sections to collect
    output_file = f"{i}/connected_sections.rdf"

    # Namespaces
    section_type = URIRef("http://data.europa.eu/949/SectionOfLine")
    canonical_pred = URIRef("http://data.europa.eu/949/canonicalURI")
    op_start_pred = URIRef("http://data.europa.eu/949/opStart")
    op_end_pred = URIRef("http://data.europa.eu/949/opEnd")
    excluded_predicate = URIRef("http://data.europa.eu/949/notYetAvailable")

    # Resolve canonical URIs
    def resolve_uri(uri, graph):
        if any(graph.triples((uri, None, None))):
            return uri
        for s in graph.subjects(predicate=canonical_pred, object=uri):
            return s
        return uri

    # Build a map: operational point URI -> section(s)
    op_to_sections = {}
    section_to_ops = {}

    for s in g.subjects(RDF.type, section_type):
        ops = set()
        for p in [op_start_pred, op_end_pred]:
            for o in g.objects(s, p):
                resolved = resolve_uri(o, g)
                ops.add(resolved)
                op_to_sections.setdefault(resolved, set()).add(s)
        section_to_ops[s] = ops

    # Pick a random section to start
    start_section = random.choice(list(section_to_ops.keys()))
    connected_sections = set([start_section])
    queue = [start_section]

    # BFS to collect connected sections
    while queue and len(connected_sections) < N:
        current = queue.pop(0)
        for op in section_to_ops.get(current, []):
            for neighbor in op_to_sections.get(op, []):
                if neighbor not in connected_sections:
                    connected_sections.add(neighbor)
                    queue.append(neighbor)
                    if len(connected_sections) >= N:
                        break
            if len(connected_sections) >= N:
                break

    print(f"✅ Collected {len(connected_sections)} connected sections.")

    # Recursively collect triples with canonical URI resolution
    visited_global = set()
    final_graph = Graph()

    def collect_subgraph(start_uri, graph, visited=None):
        if visited is None:
            visited = set()
        subgraph = Graph()
        queue = [start_uri]
        while queue:
            current = resolve_uri(queue.pop(), graph)
            if current in visited:
                continue
            visited.add(current)
            for p, o in graph.predicate_objects(current):
                if p == excluded_predicate:
                    continue  # Skip excluded predicate
                subgraph.add((current, p, o))
                if isinstance(o, URIRef) and o not in visited:
                    queue.append(o)
        return subgraph

    # Add all connected sections and their linked resources
    for section_uri in connected_sections:
        subgraph = collect_subgraph(section_uri, g, visited_global)
        for triple in subgraph:
            final_graph.add(triple)

    # Save result
    final_graph.serialize(destination=output_file, format="xml")
    print(f"📦 Saved connected RDF graph with {len(final_graph)} triples to '{output_file}'")
