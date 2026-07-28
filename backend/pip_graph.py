import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# ==========================================
# 1. Define Pydantic Schema for Graph Extractor
# ==========================================
class Company(BaseModel):
    name: str = Field(..., description="Name of the company (e.g., Google, TCS)")
    tier: Optional[str] = Field(None, description="Company tier, e.g., Tier 1, Tier 2, Startup, MNC")
    average_ctc: Optional[str] = Field(None, description="Average CTC or salary offered by the company")

class JobRole(BaseModel):
    title: str = Field(..., description="Job role title, e.g., Software Engineer, Data Scientist")
    expected_salary: Optional[str] = Field(None, description="Expected salary for this role if mentioned")
    branch_restrictions: Optional[List[str]] = Field(None, description="Restricted branches like CS, IT, ECE")

class KnowledgeTopic(BaseModel):
    domain: str = Field(..., description="Broad domain, e.g., Core CS, HR, Programming, System Design")
    subdomain: str = Field(..., description="Specific skill or topic, e.g., Dynamic Programming, React, OS Concepts")

class InterviewQuestion(BaseModel):
    text: str = Field(..., description="The actual question or problem statement asked")
    difficulty: Optional[str] = Field(None, description="Difficulty of the question: Easy, Medium, Hard")
    phase: Optional[str] = Field(None, description="Interview phase, e.g., Online Assessment, Technical Round 1, HR Round")

# Edges
class HiresForEdge(BaseModel):
    company_name: str
    job_role_title: str

class DemandsSkillEdge(BaseModel):
    job_role_title: str
    knowledge_subdomain: str

class AskedQuestionEdge(BaseModel):
    company_name: str
    question_text: str

class TestsKnowledgeEdge(BaseModel):
    question_text: str
    knowledge_subdomain: str

class PlacementGraphData(BaseModel):
    """The full graph structure extracted from a placement experience document."""
    companies: List[Company] = Field(default_factory=list)
    job_roles: List[JobRole] = Field(default_factory=list)
    knowledge_topics: List[KnowledgeTopic] = Field(default_factory=list)
    interview_questions: List[InterviewQuestion] = Field(default_factory=list)
    
    hires_for: List[HiresForEdge] = Field(default_factory=list)
    demands_skill: List[DemandsSkillEdge] = Field(default_factory=list)
    asked_question: List[AskedQuestionEdge] = Field(default_factory=list)
    tests_knowledge: List[TestsKnowledgeEdge] = Field(default_factory=list)


# ==========================================
# 2. LLM Extraction Pipeline
# ==========================================
def extract_graph_from_text(text: str) -> PlacementGraphData:
    """Extracts structured graph entities and relationships from raw text."""
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    structured_llm = llm.with_structured_output(PlacementGraphData)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert data extraction algorithm for a Placement Intelligence Platform.
        Your task is to extract structured entities and their relationships from unstructured interview experiences.
        Ensure you only extract information present in the text.
        If a property is unknown, leave it null. Do not hallucinate.
        Match relationships precisely using the exact names, titles, and text you extracted for nodes."""),
        ("human", "{text}")
    ])
    
    chain = prompt | structured_llm
    result = chain.invoke({"text": text})
    return result


# ==========================================
# 3. Neo4j Graph Ingestion
# ==========================================
class GraphIngestor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
        
    def setup_constraints(self):
        """Create constraints to ensure uniqueness and fast lookup."""
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (j:JobRole) REQUIRE j.title IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (k:KnowledgeTopic) REQUIRE k.subdomain IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (q:InterviewQuestion) REQUIRE q.text IS UNIQUE",
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)

    def ingest_data(self, data: PlacementGraphData):
        with self.driver.session() as session:
            # 1. Ingest Nodes
            for company in data.companies:
                session.run(
                    """
                    MERGE (c:Company {name: $name})
                    SET c.tier = COALESCE($tier, c.tier), c.average_ctc = COALESCE($ctc, c.average_ctc)
                    """,
                    name=company.name, tier=company.tier, ctc=company.average_ctc
                )
                
            for role in data.job_roles:
                session.run(
                    """
                    MERGE (j:JobRole {title: $title})
                    SET j.expected_salary = COALESCE($salary, j.expected_salary),
                        j.branch_restrictions = COALESCE($branches, j.branch_restrictions)
                    """,
                    title=role.title, salary=role.expected_salary, branches=role.branch_restrictions
                )
                
            for topic in data.knowledge_topics:
                session.run(
                    """
                    MERGE (k:KnowledgeTopic {subdomain: $subdomain})
                    SET k.domain = COALESCE($domain, k.domain)
                    """,
                    subdomain=topic.subdomain, domain=topic.domain
                )
                
            for question in data.interview_questions:
                session.run(
                    """
                    MERGE (q:InterviewQuestion {text: $text})
                    SET q.difficulty = COALESCE($difficulty, q.difficulty),
                        q.phase = COALESCE($phase, q.phase)
                    """,
                    text=question.text, difficulty=question.difficulty, phase=question.phase
                )
                
            # 2. Ingest Relationships
            for edge in data.hires_for:
                session.run(
                    """
                    MATCH (c:Company {name: $c_name}), (j:JobRole {title: $j_title})
                    MERGE (c)-[:HIRES_FOR]->(j)
                    """,
                    c_name=edge.company_name, j_title=edge.job_role_title
                )
                
            for edge in data.demands_skill:
                session.run(
                    """
                    MATCH (j:JobRole {title: $j_title}), (k:KnowledgeTopic {subdomain: $k_sub})
                    MERGE (j)-[:DEMANDS_SKILL]->(k)
                    """,
                    j_title=edge.job_role_title, k_sub=edge.knowledge_subdomain
                )
                
            for edge in data.asked_question:
                session.run(
                    """
                    MATCH (c:Company {name: $c_name}), (q:InterviewQuestion {text: $q_text})
                    MERGE (c)-[:ASKED_QUESTION]->(q)
                    """,
                    c_name=edge.company_name, q_text=edge.question_text
                )
                
            for edge in data.tests_knowledge:
                session.run(
                    """
                    MATCH (q:InterviewQuestion {text: $q_text}), (k:KnowledgeTopic {subdomain: $k_sub})
                    MERGE (q)-[:TESTS_KNOWLEDGE]->(k)
                    """,
                    q_text=edge.question_text, k_sub=edge.knowledge_subdomain
                )

# Example usage (for testing)
if __name__ == "__main__":
    sample_text = """
    I recently interviewed for the Software Engineer role at Google. The CTC was 30 LPA.
    In the first technical round, they asked me to reverse a linked list and also asked 
    about the differences between processes and threads in Operating Systems.
    """
    print("Extracting graph data...")
    graph_data = extract_graph_from_text(sample_text)
    import json
    print(json.dumps(graph_data.model_dump(), indent=2))
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
    
    print("\\nConnecting to Neo4j to save the graph...")
    try:
        ingestor = GraphIngestor(neo4j_uri, neo4j_user, neo4j_pass)
        ingestor.setup_constraints()
        ingestor.ingest_data(graph_data)
        print("Successfully ingested into Neo4j!")
        ingestor.close()
    except Exception as e:
        print(f"Failed to ingest into Neo4j: {e}")
