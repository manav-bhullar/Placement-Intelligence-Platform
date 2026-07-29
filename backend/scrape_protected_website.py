import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import json

# Import the existing LLM Graph Extractor and Neo4j Ingestor
from pip_graph import extract_graph_from_text, GraphIngestor

load_dotenv()

COOKIE_STRING = os.getenv("TIETPREP_COOKIE")
LOGIN_URL = "https://tietprep.humblesolutions.in"

async def scrape_and_ingest():
    if not COOKIE_STRING:
        print("Error: TIETPREP_COOKIE not found in .env")
        return

    print(f"Launching Playwright to navigate to {LOGIN_URL} with Cookie bypass...")
    
    async with async_playwright() as p:
        # Launch Chromium headless
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Inject the cookie header directly to bypass login
        await context.set_extra_http_headers({'Cookie': COOKIE_STRING})
        page = await context.new_page()
        
        print("Loading dashboard page...")
        try:
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            print("Waiting for SPA to load content...")
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"Failed during page load: {e}")
            await browser.close()
            return
            
        print("Extracting interview experiences from the page...")
        # Get all text from the body to capture the experiences
        raw_text = await page.evaluate("document.body.innerText")
        
        if not raw_text or len(raw_text.strip()) < 50:
            print("Failed to extract meaningful text from the page. Might be blocked or empty.")
            await browser.close()
            return
            
        print(f"Extracted {len(raw_text)} characters of text. \\nTEXT:\\n{raw_text}")
        await browser.close()

    # Pass the text to our LLM Graph Extractor pipeline
    # Note: If the text is massive, we might need to chunk it, but we'll try the whole thing first.
    try:
        # We might need to truncate if it exceeds Groq context length, keeping the first 15,000 chars as a safe buffer
        safe_text = raw_text[:15000]
        
        graph_data = extract_graph_from_text(safe_text)
        print(f"LLM Extraction Complete! Found {len(graph_data.companies)} Companies, {len(graph_data.interview_questions)} Questions, and {len(graph_data.tests_knowledge)} Knowledge edges.")
        
        # Ingest into Neo4j
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
        
        print("\\nConnecting to Neo4j to save the interview graph...")
        ingestor = GraphIngestor(neo4j_uri, neo4j_user, neo4j_pass)
        ingestor.setup_constraints()
        ingestor.ingest_data(graph_data)
        ingestor.close()
        
        print("Successfully ingested the interview experiences into Neo4j!")
        
    except Exception as e:
        print(f"An error occurred during extraction or ingestion: {e}")

if __name__ == "__main__":
    asyncio.run(scrape_and_ingest())
