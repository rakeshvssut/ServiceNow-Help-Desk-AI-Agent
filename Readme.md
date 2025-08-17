# ServiceNow ATOS Agent

An intelligent, AI-powered agent designed to automate the triage and routing of ServiceNow tickets. This agent uses Large Language Models (LLMs) and a dynamic knowledge base fetched directly from ServiceNow to understand incoming tickets and assign them to the correct specialist team, or escalate to a human service desk when uncertain.

---

## ✨ Features

-   **Automatic Triggering:** Activates automatically when a ticket is assigned to its designated group in ServiceNow.
-   **Multi-Ticket Support:** Intelligently identifies ticket types (`INC`, `RITM`, etc.) and queries the correct ServiceNow tables.
-   **Live Knowledge Base:** Builds its understanding of team responsibilities by fetching group data directly from the ServiceNow API at startup, ensuring it's always up-to-date.
-   **AI-Powered Decision Making:** Uses a local LLM (via Ollama) to analyze ticket content and make a confident routing decision.
-   **Safe Escalation Path:** Automatically assigns tickets to a human service desk if its confidence score is low, ensuring no ticket is lost.
-   **Scalable Architecture:** Built with FastAPI and designed to handle parallel requests in a production environment.

---

## 🏗️ Architecture Flowchart

```mermaid
graph TD
    A[Start: Ticket Assigned to ATOS Agent 🤖] --> B{Agent Triggered via Webhook};
    B --> C[1. Fetch Live Group Data <br/>(On Startup, from ServiceNow)];
    C --> D[2. Build In-Memory Knowledge Base <br/>(Vector Store)];
    B --> E[3. Fetch Ticket Details <br/>(From correct table: INC, RITM, etc.)];
    E --> F[4. Find Candidate Teams <br/>(Search In-Memory Knowledge Base)];
    F --> G[5. Analyze & Decide <br/>(Send data to LLM)];
    G --> H{6. Confidence Check};
    H -- High Confidence --> I[✅ Route to Specialist Team];
    H -- Low/Medium Confidence --> J[⚠️ Escalate to Human Desk];
    I --> K[End: Process Complete];
    J --> K;
```

---

## 🛠️ Technology Stack

-   **Orchestration:** LangGraph
-   **Backend:** Python, FastAPI, Uvicorn
-   **LLM Serving:** Ollama (running models like Llama 3)
-   **Vector Database:** ChromaDB
-   **Target Platform:** ServiceNow
-   **Containerization:** Docker

---

## 🚀 Setup and Installation

Follow these steps to set up the project locally.

### 1. Prerequisites
-   [Python 3.12](https://www.python.org/downloads/windows/)
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
-   [Git](https://git-scm.com/downloads/)
-   A [ServiceNow Personal Developer Instance (PDI)](https://developer.servicenow.com/).

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd atos_agent
```

### 3. Configure ServiceNow
-   Log into your PDI and create two user groups:
    1.  `ATOS Agent` (for the AI)
    2.  `ATOS Service Desk` (for human escalation)
-   Note the `sys_id` for each group.

### 4. Start Local AI Services
-   Ensure Docker Desktop is running.
-   Start the ChromaDB and Ollama containers:
    ```bash
    docker run -d -p 8000:8000 --name chromadb ghcr.io/chroma-core/chroma:latest
    docker run -d -p 11434:11434 --name ollama ollama/ollama
    ```
-   Pull the necessary models:
    ```bash
    docker exec ollama ollama pull llama3
    docker exec ollama ollama pull nomic-embed-text
    ```

### 5. Configure the Project
-   **Create `config.py`:** Create this file in the root directory.
-   **Fill `config.py`:** Add your ServiceNow instance ID, credentials, and the `sys_id` for the human service desk group.

### 6. Install Dependencies
-   Create and activate a Python virtual environment:
    ```bash
    # Use the Python 3.12 you installed
    py -3.12 -m venv snow_venv
    .\snow_venv\Scripts\activate
    ```
-   Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

---

## ▶️ Running the Agent

1.  **Start Docker Containers:** Make sure your `chromadb` and `ollama` containers are running.
2.  **Start the Agent Server:** From the `atos_agent` directory, run:
    ```bash
    uvicorn main:app --reload
    ```
    The server will be available at `http://127.0.0.1:8000`.

---

## 🧪 Testing

### Manual Test
-   Use a tool like PowerShell or Postman to send a `POST` request to the agent.
    ```powershell
    Invoke-RestMethod -Method Post -Uri [http://127.0.0.1:8000/process_ticket](http://127.0.0.1:8000/process_ticket) -ContentType "application/json" -Body '{"ticket_number": "INC0010001"}'
    ```

### End-to-End Test (with ServiceNow Trigger)
1.  **Expose Local Server:** Use `ngrok` to create a public URL for your local server.
    ```bash
    ngrok http 8000
    ```
2.  **Create Business Rule:** In ServiceNow, create a Business Rule that triggers when a ticket's `Assignment group` changes to `ATOS Agent`.
3.  **Configure Action:** In the rule's "Advanced" tab, add the script to send a request to your `ngrok` URL's `/process_ticket` endpoint.
4.  **Test:** Assign a ticket in ServiceNow to the `ATOS Agent` group and watch the logs in your server terminal.