from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, TURTLE

# Configuration
sparql_endpoint = "https://data-interop.era.europa.eu/api/sparql"  # Replace with your actual endpoint
sparql_files = ["Inf_Data.sparql", "Track_Data_1.sparql", "Track_Data_2.sparql"]
output_file = "merged_output.ttl"

def load_query(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def execute_sparql_query(endpoint, query):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(TURTLE)
    sparql.setMethod("POST")  # <-- Add this line to use POST method
    results = sparql.query().convert()

    graph = Graph()
    graph.parse(data=results, format="turtle")
    return graph

def main():
    merged_graph = Graph()

    for file in sparql_files:
        print(f"Executing query from {file}...")
        query = load_query(file)
        result_graph = execute_sparql_query(sparql_endpoint, query)
        merged_graph += result_graph

    print(f"Saving merged data to {output_file}...")
    merged_graph.serialize(destination=output_file, format="turtle")
    print("Done.")

if __name__ == "__main__":
    main()
