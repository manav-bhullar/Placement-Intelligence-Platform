# Placement Intelligence Platform (PIP)

The Placement Intelligence Platform (PIP) is a comprehensive system designed to turn unstructured placement data (interview experiences, company profiles) into actionable intelligence for students.

## Architecture

PIP utilizes the following stack:
- **Backend Graph Extraction**: Python (LangChain + Groq) to parse unstructured data into structured JSON.
- **Graph Database**: Neo4j, used to build a knowledge graph of Companies, Job Roles, Knowledge Topics, and Interview Questions.
- **Relational Database**: PostgreSQL, used for standard application data.

## Getting Started

### Prerequisites
- Docker and docker-compose
- Python 3.14+

### Setup
1. Clone the repository.
2. Ensure you have a `.env` file with your `GROQ_API_KEY`.
3. Start the databases:
   ```bash
   docker-compose up -d
   ```
4. Run the data extraction pipeline:
   ```bash
   source venv/bin/activate
   python pip_graph.py
   ```
