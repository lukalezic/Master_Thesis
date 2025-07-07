from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, TURTLE

# Configuration
sparql_endpoint = "https://data-interop.era.europa.eu/api/sparql"
sparql_files = ["Inf_Data.sparql", "Track_Data_1.sparql", "Track_Data_2.sparql", "Others.sparql"]
output_file = "merged_output.ttl"
import sys
country_code = sys.argv[1] if len(sys.argv) > 1 else "NONE"

def load_query(file_path, country):
    with open(file_path, "r", encoding="utf-8") as file:
        query = file.read()
    return query.replace("@@COUNTRY@@", country)

def execute_sparql_query(endpoint, query):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(TURTLE)
    sparql.setMethod("POST")
    sparql.setTimeout(180)  # <-- Increase timeout (in seconds)
    results = sparql.query().convert()

    graph = Graph()
    graph.parse(data=results, format="turtle")
    return graph

def main():
    merged_graph = Graph()

    for file in sparql_files:
        print(f"Executing query from {file} for country {country_code}...")
        query = load_query(file, country_code)
        result_graph = execute_sparql_query(sparql_endpoint, query)
        merged_graph += result_graph

    print(f"Saving merged data to {output_file}...")
    merged_graph.serialize(destination=output_file, format="turtle")
    print("Done.")

if __name__ == "__main__":
    main()
