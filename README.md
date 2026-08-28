````markdown
# Zycus AI Support Ticket Triage
## Overview
This project implements an AI-assisted support ticket triage system for analyzing customer support tickets, retrieving relevant knowledge-base information, generating grounded draft responses, and summarizing account health.
The system combines deterministic logic with a local LLM running through Ollama.
### Main capabilities
- Knowledge-base document loading
- Document chunking
- TF-IDF based retrieval
- Cosine similarity ranking
- Retrieval confidence scoring
- Ticket category classification
- Ticket urgency classification
- Ticket summarization
- Grounded draft response generation
- Local LLM integration using Ollama
- Deterministic fallback when the LLM is unavailable
- Account health analysis
- Churn and escalation risk detection
- TAM talking points
- Automated tests
- End-to-end evaluation
---
## Architecture
```text
                    Support Ticket
                          |
                          v
                +-------------------+
                |  KB Retrieval     |
                | TF-IDF + Cosine   |
                +---------+---------+
                          |
                          v
                Relevant KB Context
                          |
             +------------+------------+
             |                         |
             v                         v
     Deterministic Logic        Local LLM (Ollama)
     Category + Urgency         Draft Response
             |                   Generation
             |                         |
             +------------+------------+
                          |
                          v
                   Final Triage
                     Result
             Account Health Workflow
 Account Data + Ticket History
              |
              v
      Account Health Logic
              |
              +--> Open Risks
              +--> Churn Flags
              +--> Escalation Flags
              +--> Executive Summary
              +--> TAM Talking Points
````
---
## Features
### 1. Knowledge Base Retrieval
The retrieval pipeline reads Markdown knowledge-base documents from:
```text
data/knowledge-base/
```
Documents are:
1. Loaded from the knowledge base
2. Split into searchable sections
3. Converted into TF-IDF vectors
4. Compared against the query using cosine similarity
5. Ranked according to relevance
The system returns the most relevant knowledge-base sections and their source files.
---
### 2. Ticket Triage
The ticket triage system produces:
* Ticket ID
* Category
* Urgency
* Summary
* Draft reply
* Relevant KB sources
* Confidence score
Example:
```json
{
  "ticket_id": "TKT-10499",
  "category": "How-To",
  "urgency": "P4",
  "summary": "New team member onboarding to SecureVault",
  "draft_reply": "Thanks for reaching out...",
  "kb_sources": [
    "onboarding\\onboarding-guide.md",
    "products\\securevault.md"
  ],
  "confidence": 0.65
}
```
---
### 3. Local LLM Integration
The project uses **Ollama** for local language-model generation.
Current model:
```text
llama3.2:3b
```
The LLM is used primarily for natural-language response generation while deterministic logic continues to provide stable ticket classification and urgency assignment.
This design provides:
* Local execution
* No external API dependency for normal operation
* Reproducible classification
* Grounded response generation
* Graceful fallback when Ollama is unavailable
The LLM receives ticket information and retrieved knowledge-base context so that generated replies remain grounded in the supplied documentation.
---
### 4. LLM Fallback
If the Ollama model is unavailable, the system falls back to deterministic response generation.
This means the application can still operate without the local LLM service.
The fallback also prevents an LLM failure from breaking the overall ticket-triage workflow.
---
### 5. Account Health Summarization
The account health component combines account information with available support-ticket history.
It provides:
* Account ID
* Company information
* Plan tier
* ARR
* Licensed seats
* Active seats
* Products
* Health status
* Usage trend
* Open ticket count
* High-priority ticket count
* Churn indicators
* Escalation indicators
* Executive summary
* TAM talking points
* Recent tickets
The account health output is designed to help a TAM quickly understand customer risk and prioritize follow-up actions.
---
## Technology
The project uses:
* Python
* Streamlit
* scikit-learn
* TF-IDF
* Cosine similarity
* Ollama
* Llama 3.2 3B
* pytest
* JSON
* Markdown
---
## Project Structure
```text
zycus-ai-assignment/
│
├── data/
│   ├── accounts.json
│   ├── tickets.json
│   └── knowledge-base/
│       ├── billing/
│       │   └── billing-and-plans.md
│       ├── onboarding/
│       │   └── onboarding-guide.md
│       ├── products/
│       │   ├── analyticshub.md
│       │   ├── cloudsync.md
│       │   ├── databridge-pro.md
│       │   ├── securevault.md
│       │   └── workflowengine.md
│       └── troubleshooting/
│           ├── authentication-sso.md
│           └── performance-and-integrations.md
│
├── docs/
│   ├── README.md
│   └── evaluation.md
│
├── eval/
│   ├── evaluate.py
│   ├── test_cases.json
│   └── triage_test_cases.json
│
├── src/
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── chunker.py
│   │   └── retriever.py
│   │
│   ├── triage/
│   │   ├── __init__.py
│   │   └── triage.py
│   │
│   ├── summarizer/
│   │   ├── __init__.py
│   │   └── summarizer.py
│   │
│   └── llm/
│       └── llm_client.py
│
├── tests/
│   ├── test_retrieval.py
│   └── test_summarizer.py
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
---
## Installation
Create a virtual environment:
```powershell
python -m venv .venv
```
Activate it:
```powershell
.venv\Scripts\Activate.ps1
```
Install dependencies:
```powershell
pip install -r requirements.txt
```
---
## Ollama Setup
Install Ollama and verify that it is available:
```powershell
ollama --version
```
Check installed models:
```powershell
ollama list
```
The project uses:
```text
llama3.2:3b
```
If the model is not installed:
```powershell
ollama pull llama3.2:3b
```
Verify the model:
```powershell
ollama list
```
Test the model:
```powershell
python -c "import ollama; r=ollama.chat(model='llama3.2:3b', messages=[{'role':'user','content':'Reply with exactly: hello'}]); print(r['message']['content'])"
```
Expected output:
```text
hello
```
If Ollama is already running as a background service, there is no need to run `ollama serve` again.
---
## Running the Application
Start the Streamlit application:
```powershell
streamlit run app.py
```
The application provides the following workflows:
### Account Health
Look up an account and generate:
* Account overview
* Executive summary
* Open risks
* Churn flags
* Escalation flags
* TAM talking points
* Recent tickets
### AI Support Ticket Triage
Enter a support ticket to generate:
* Category
* Urgency
* Confidence
* Summary
* Grounded draft response
* KB sources
### Knowledge Base Search
Search the local documentation and inspect the most relevant retrieved sections.
---
## Running Knowledge Base Retrieval
From the project root:
```powershell
python src\retrieval\retriever.py
```
---
## Running Ticket Triage
From the project root:
```powershell
python src\triage\triage.py
```
The output contains:
* Ticket ID
* Category
* Urgency
* Summary
* Draft reply
* KB sources
* Confidence
---
## Running Account Health
From the project root:
```powershell
python src\summarizer\summarizer.py
```
A specific account can also be tested:
```powershell
python -c "from src.summarizer.summarizer import build_account_health; import json; print(json.dumps(build_account_health('ACC-3336'), indent=2))"
```
---
## Running Tests
Run the complete automated test suite:
```powershell
python -m pytest
```
Current result:
```text
5 passed
```
The tests cover:
* Knowledge-base retrieval
* Ticket retrieval
* Retrieval relevance
* Account health summarization
---
## Running Evaluation
Run:
```powershell
python eval\evaluate.py
```
The evaluation covers both retrieval and application-level behavior.
Current verified result:
```text
=== Retrieval Evaluation ===
PASS: How do I enable SSO?
PASS: Users are unable to sync files
PASS: How much does the Business plan cost?
PASS: WorkflowEngine approval is stuck
PASS: DataBridge Pro ingestion is failing
PASS: CloudSync webhook is not reaching Snowflake
=== Task 1: Ticket Triage ===
PASS: SSO setup
PASS: CloudSync file sync failure
PASS: Business plan pricing
PASS: Workflow approval stuck
PASS: DataBridge ingestion failure
PASS: Ambiguous support request
=== Task 2: Account Health ===
PASS: At-risk business account
PASS: Account with recent ticket
PASS: Account with recent support history
PASS: Account with ticket history
PASS: Valid account health lookup
PASS: Adversarial unknown account
=== Overall ===
Passed: 18/18
Failed: 0/18
Pass rate: 1.00
Quality score: 1.00
```
---
## Retrieval Approach
### Step 1: Document Loading
Markdown knowledge-base files are loaded from:
```text
data/knowledge-base/
```
### Step 2: Chunking
Documents are divided into smaller sections so retrieval can return focused information.
### Step 3: TF-IDF Vectorization
Each knowledge-base chunk is converted into a TF-IDF vector.
### Step 4: Cosine Similarity
The query is converted into the same vector space.
Cosine similarity compares the query with knowledge-base chunks.
### Step 5: Ranking
Chunks are ranked by similarity and the most relevant sources are returned.
---
## Confidence
The confidence value is derived from retrieval similarity results.
It represents retrieval relevance rather than a calibrated probability.
A higher value indicates stronger lexical similarity between the query and retrieved knowledge-base content.
---
## Ticket Classification
The triage component assigns a support category based on ticket information and relevant context.
Example categories include:
* Billing
* Technical
* How-To
* Onboarding
* Data Loss
* Feature Request
---
## Urgency
Tickets are assigned one of:
```text
P1
P2
P3
P4
```
Urgency is determined using information available in the ticket, including severity and explicit priority indicators.
---
## Grounded Draft Response Generation
The response-generation pipeline uses retrieved knowledge-base content as context for the local LLM.
The generated response is designed to:
* Acknowledge the customer's issue
* Use relevant KB information
* Provide an appropriate next step
* Avoid unsupported troubleshooting claims
* Avoid relying on information outside the available support context
If Ollama is unavailable, deterministic fallback generation is used.
---
## Account Health Logic
The account health summarizer combines:
1. Account-level information from `data/accounts.json`
2. Available support-ticket information from `data/tickets.json`
The summarizer identifies:
* Current account health
* Usage trend
* Open ticket volume
* High-priority support issues
* Churn indicators
* Escalation indicators
* Recent support activity
It then generates an executive summary and TAM talking points.
---
## Data Handling
The project uses the supplied account and ticket datasets.
Account-level ticket counts and tickets available in the ticket dataset may not always match.
The summarizer therefore distinguishes between:
* Ticket counts stored on the account record
* Tickets available in the ticket dataset
* Recent tickets included in the configured time window
This prevents missing ticket records from automatically being interpreted as having no support activity.
---
## Design Decisions
### Deterministic Classification
Category and urgency classification remain deterministic so that the evaluation remains reproducible.
### LLM-Assisted Generation
The local LLM is used where natural-language generation provides value, particularly for customer-facing draft responses.
### Retrieval-Grounded Generation
The LLM receives relevant retrieved KB content rather than being asked to answer from unrestricted external knowledge.
### Local Execution
Ollama allows the LLM component to run locally without requiring an external API key.
### Fallback Behavior
If the LLM is unavailable, the system continues using deterministic generation.
---
## Limitations
Known limitations include:
* TF-IDF primarily relies on lexical similarity
* Semantically similar phrases with very different wording may not always retrieve the best result
* Confidence scores are retrieval signals rather than calibrated probabilities
* Classification remains deterministic
* Local LLM quality depends on the selected Ollama model
* Account and ticket datasets may contain inconsistent or incomplete relationships
* The local 3B model may produce less sophisticated responses than larger hosted models
---
## Future Improvements
Potential improvements include:
* Semantic embeddings
* Hybrid keyword and vector retrieval
* Larger local LLM models
* LLM-assisted ticket classification
* Calibrated confidence scoring
* Improved product/entity matching
* More comprehensive evaluation metrics
* Automated escalation detection
* Historical account trend analysis
* Account-level risk scoring
* Integration with a production ticketing system
---
## Reproducibility
The project is designed to run locally using the supplied data, Python dependencies, and Ollama.
Main verification commands:
```powershell
python -m pytest
```
and:
```powershell
python eval\evaluate.py
```
The retrieval and deterministic components do not require an external API.
The LLM response-generation component requires a locally running Ollama installation with the configured model available.
---
## Verification
The current implementation has been verified with:
```text
pytest:
5 passed
```
and:
```text
evaluation:
18/18 passed
Pass rate: 1.00
Quality score: 1.00
```
---
## Summary
This project provides a lightweight AI-assisted support workflow combining:
* Knowledge-base retrieval
* TF-IDF search
* Ticket triage
* Category classification
* Urgency classification
* Ticket summarization
* Retrieval confidence
* Grounded LLM response generation
* Ollama local inference
* Deterministic fallback
* Account health analysis
* Churn and escalation detection
* TAM talking points
* Automated testing
* End-to-end evaluation
The implementation focuses on being:
* Simple
* Reproducible
* Explainable
* Testable
* Locally runnable
* Easy to extend
````
### Then save it
In Notepad:
**Ctrl + A → paste → Ctrl + S → close.**
Then **don't change anything else yet**.
Run:
```powershell
python -m pytest
````
and:
```powershell
python eval\evaluate.py
```

<!-- CI verification -->
