from rdflib import Graph, RDF, RDFS, OWL, URIRef, Literal
from rdflib.namespace import Namespace
import sys
from rdflib.namespace import SKOS

# --- CONFIG ---
DATA_FILE = "merged_output.ttl"
ONTOLOGY_FILE = "sub_ontology.ttl"
ERA = Namespace("http://data.europa.eu/949/")
# --------------

# Load graphs
data_graph = Graph()
data_graph.parse(DATA_FILE, format="turtle")

ontology_graph = Graph()
ontology_graph.parse(ONTOLOGY_FILE, format="turtle")

# Helper: get declared domain and range for a property
def get_domain_range(predicate):
    domain = None
    range_ = None
    for o in ontology_graph.objects(predicate, RDFS.domain):
        domain = o
    for o in ontology_graph.objects(predicate, RDFS.range):
        range_ = o
    return domain, range_

# Helper: get rdf:type(s) of a resource
def get_types(resource, graph):
    return set(graph.objects(resource, RDF.type))

# Check triples
missing_properties = set()
domain_violations = []
range_violations = []

print("🔍 Checking triples for property declarations and type compliance...\n")

for s, p, o in data_graph:
    if isinstance(p, URIRef) and str(p).startswith(str(ERA)):

        # 1. Is predicate defined in ontology?
        if (p, None, None) not in ontology_graph:
            missing_properties.add(p)

        # 2. Check domain
        domain, range_ = get_domain_range(p)
        if domain:
            subj_types = get_types(s, data_graph)
            if domain not in subj_types:
                domain_violations.append((s, p, domain, subj_types))

        # 3. Check range
        if range_:
            if isinstance(o, URIRef):
                obj_types = get_types(o, data_graph)
                if range_ not in obj_types:
                    if range_ == SKOS.Concept:
                        continue
                    range_violations.append((o, p, range_, obj_types))
            elif isinstance(o, Literal):
                # Optional: could validate xsd types
                pass

# --- RESULTS ---
print(f"🚫 Properties not found in ontology: {len(missing_properties)}")
for p in missing_properties:
    print(f"  ❌ {p}")

print(f"\n🚨 Domain violations: {len(domain_violations)}")
for s, p, expected, found in domain_violations:
    print(f"  ❌ Subject {s} used with {p} but is not typed as {expected} (found: {found})")

print(f"\n🚨 Range violations: {len(range_violations)}")
for o, p, expected, found in range_violations:
    print(f"  ❌ Object {o} used with {p} but is not typed as {expected} (found: {found})")
