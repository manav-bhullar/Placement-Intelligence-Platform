import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from neo4j import GraphDatabase

from pip_graph import extract_graph_from_text, GraphIngestor

load_dotenv()

app = FastAPI(title="Placement Intelligence Platform API")

# Setup CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def get_neo4j_driver():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        yield driver
    finally:
        driver.close()

# Request Models
class IngestRequest(BaseModel):
    raw_text: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "PIP API is running"}

@app.post("/api/ingest")
def ingest_data(request: IngestRequest):
    try:
        # Extract graph data using LLM
        graph_data = extract_graph_from_text(request.raw_text)
        
        # Save to Neo4j
        ingestor = GraphIngestor(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        ingestor.setup_constraints()
        ingestor.ingest_data(graph_data)
        ingestor.close()
        
        return {
            "status": "success", 
            "message": "Data successfully ingested and graphed",
            "entities_extracted": {
                "companies": len(graph_data.companies),
                "job_roles": len(graph_data.job_roles),
                "knowledge_topics": len(graph_data.knowledge_topics),
                "questions": len(graph_data.interview_questions)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills/top")
def get_top_skills(limit: int = 10, driver = Depends(get_neo4j_driver)):
    """Calculate and return Degree Centrality for top required skills."""
    query = """
    MATCH (k:KnowledgeTopic)<-[r:DEMANDS_SKILL|TESTS_KNOWLEDGE]-(source)
    RETURN k.subdomain as skill, k.domain as domain, count(r) as importance_score
    ORDER BY importance_score DESC 
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, limit=limit)
        skills = [{"skill": record["skill"], "domain": record["domain"], "score": record["importance_score"]} for record in result]
    return skills

@app.get("/api/companies")
def get_companies(driver = Depends(get_neo4j_driver)):
    query = """
    MATCH (c:Company)
    RETURN c.name as name, c.tier as tier, c.average_ctc as average_ctc
    ORDER BY c.name
    """
    with driver.session() as session:
        result = session.run(query)
        companies = [{"name": r["name"], "tier": r["tier"], "average_ctc": r["average_ctc"]} for r in result]
    return companies

@app.get("/api/companies/{name}")
def get_company_details(name: str, driver = Depends(get_neo4j_driver)):
    query_stats = "MATCH (c:Company {name: $name}) RETURN c.tier as tier, c.average_ctc as average_ctc"
    query_questions = "MATCH (c:Company {name: $name})-[:ASKED_QUESTION]->(q:InterviewQuestion) RETURN q.text as text, q.difficulty as difficulty"
    query_skills = "MATCH (c:Company {name: $name})-[:HIRES_FOR]->(j)-[:DEMANDS_SKILL]->(k:KnowledgeTopic) RETURN DISTINCT k.subdomain as skill"
    
    with driver.session() as session:
        stats = session.run(query_stats, name=name).single()
        if not stats:
            raise HTTPException(status_code=404, detail="Company not found")
            
        questions_result = session.run(query_questions, name=name)
        questions = [{"text": r["text"], "difficulty": r["difficulty"]} for r in questions_result]
        
        skills_result = session.run(query_skills, name=name)
        skills = [r["skill"] for r in skills_result]
        
    return {
        "name": name,
        "tier": stats["tier"],
        "average_ctc": stats["average_ctc"],
        "top_skills": skills,
        "questions": questions
    }
