import os
import requests
from dotenv import load_dotenv

# Import our Pydantic models and ingestion logic from the existing pipeline
from pip_graph import (
    Company,
    JobRole,
    HiresForEdge,
    PlacementGraphData,
    GraphIngestor
)

load_dotenv()

API_URL = "https://placements25-26.vercel.app/api/placements"

def fetch_and_map_data():
    print(f"Fetching data from {API_URL}...")
    response = requests.get(API_URL)
    response.raise_for_status()
    
    data = response.json()
    if not data.get("ok"):
        raise ValueError("API responded with not OK.")
        
    placements = data.get("placements", [])
    print(f"Found {len(placements)} placement records.")
    
    graph_data = PlacementGraphData()
    
    for placement in placements:
        company_name = placement.get("companyName")
        if not company_name:
            continue
            
        # Create Company Node
        company = Company(name=company_name)
        graph_data.companies.append(company)
        
        offers = placement.get("offers", [])
        for offer in offers:
            role_title = offer.get("jobRole")
            if not role_title:
                continue
                
            # Ensure branch_restrictions is a list of strings
            raw_branches = offer.get("branchesAllowed")
            branches = raw_branches if isinstance(raw_branches, list) else []
            
            # Create JobRole Node
            job_role = JobRole(
                title=role_title,
                expected_salary=offer.get("ctc") or None,
                branch_restrictions=branches
            )
            graph_data.job_roles.append(job_role)
            
            # Create HiresForEdge Relationship
            edge = HiresForEdge(
                company_name=company_name,
                job_role_title=role_title
            )
            graph_data.hires_for.append(edge)
            
    return graph_data

if __name__ == "__main__":
    try:
        graph_data = fetch_and_map_data()
        print(f"Mapped {len(graph_data.companies)} companies and {len(graph_data.job_roles)} roles.")
        
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
        
        print("\\nConnecting to Neo4j to ingest the live data...")
        ingestor = GraphIngestor(neo4j_uri, neo4j_user, neo4j_pass)
        ingestor.setup_constraints()
        ingestor.ingest_data(graph_data)
        ingestor.close()
        
        print("Successfully ingested the live placements data into Neo4j!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
