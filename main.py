import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global driver
    try:
        driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        yield
    finally:
        if driver:
            await driver.close()

app = FastAPI(title="Placement Intelligence Platform API", lifespan=lifespan)

# Allow the Next.js frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/companies/{name}")
async def get_company_intelligence(name: str):
    """Get hiring stats, roles, and historical interview questions for a company."""
    query = '''
    MATCH (c:Company)
    WHERE toLower(c.name) = toLower($name)
    OPTIONAL MATCH (c)-[:HIRES_FOR]->(j:JobRole)
    OPTIONAL MATCH (c)-[:ASKED_QUESTION]->(q:InterviewQuestion)
    OPTIONAL MATCH (q)-[:TESTS_KNOWLEDGE]->(k:KnowledgeTopic)
    RETURN c { .name, .tier, .average_ctc } AS company,
           collect(DISTINCT j { .title, .expected_salary }) AS roles,
           collect(DISTINCT q { .text, .difficulty, .phase }) AS questions,
           collect(DISTINCT k.subdomain) AS skills_tested
    '''
    async with driver.session() as session:
        result = await session.run(query, name=name)
        record = await result.single()
        if not record or not record["company"]:
            raise HTTPException(status_code=404, detail="Company not found")
        return {
            "company": record["company"],
            "roles": record["roles"],
            "questions": record["questions"],
            "skills_tested": record["skills_tested"]
        }

@app.get("/api/skills/{domain}")
async def get_skills_by_domain(domain: str):
    """Explore skills within a specific domain and see which companies demand them."""
    query = '''
    MATCH (k:KnowledgeTopic)
    WHERE toLower(k.domain) = toLower($domain)
    OPTIONAL MATCH (j:JobRole)-[:DEMANDS_SKILL]->(k)
    OPTIONAL MATCH (c:Company)-[:HIRES_FOR]->(j)
    RETURN k.subdomain AS skill,
           collect(DISTINCT c.name) AS requested_by_companies
    '''
    async with driver.session() as session:
        result = await session.run(query, domain=domain)
        skills = [record.data() async for record in result]
        if not skills:
            raise HTTPException(status_code=404, detail="Domain not found or no skills present")
        return {"domain": domain, "skills": skills}

@app.get("/api/graph/top-skills")
async def get_top_skills():
    """Rank skills mathematically based on how frequently companies ask questions about them."""
    query = '''
    MATCH (c:Company)-[:ASKED_QUESTION]->(q:InterviewQuestion)-[:TESTS_KNOWLEDGE]->(k:KnowledgeTopic)
    RETURN k.subdomain AS skill, k.domain AS domain, count(DISTINCT c) AS company_demand_score
    ORDER BY company_demand_score DESC
    LIMIT 10
    '''
    async with driver.session() as session:
        result = await session.run(query)
        top_skills = [record.data() async for record in result]
        return {"top_skills": top_skills}

@app.get("/")
async def root():
    return {"message": "Welcome to the Placement Intelligence Platform API. Access /docs for the API Swagger UI."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
