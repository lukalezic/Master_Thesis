#!/usr/bin/env python3
from pathlib import Path
from rdflib import Graph

# --- Configuration ---
root_dir = Path("./")   # change this to your top-level folder
output_path = Path("output.rdf")     # where merged RDF will be saved
# ----------------------

# Create an empty RDF graph
merged_graph = Graph()

# Find and merge all matching RDF files
rdf_files = list(root_dir.rglob("connected_sections.rdf"))
print(f"Found {len(rdf_files)} connected_sections.rdf files")

for rdf_file in rdf_files:
    print(f"Loading: {rdf_file}")
    g = Graph()
    g.parse(str(rdf_file))  # rdflib auto-detects format
    merged_graph += g       # merge triples

# Save the merged RDF graph
merged_graph.serialize(destination=str(output_path), format="xml")
print(f"Merged RDF saved to {output_path} with {len(merged_graph)} triples")
