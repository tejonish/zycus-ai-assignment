````markdown
# Zycus AI Support Ticket Triage

## Overview

This project implements an AI-assisted support ticket triage system for analyzing customer support tickets, retrieving relevant knowledge-base information, generating draft responses, and summarizing account health.

The system:

- Loads support knowledge-base documents
- Splits documents into searchable sections
- Uses TF-IDF vectorization for text representation
- Uses cosine similarity for knowledge-base retrieval
- Retrieves relevant knowledge-base content for support tickets
- Classifies tickets into support categories
- Assigns ticket urgency
- Generates ticket summaries
- Generates draft support replies
- Returns relevant knowledge-base sources
- Calculates retrieval confidence
- Evaluates the retrieval system against predefined test cases
- Generates account-level health summaries for TAM review

## Features

### 1. Knowledge Base Retrieval

The retrieval pipeline reads Markdown knowledge-base documents from the `data/knowledge-base/` directory.

Documents are:

1. Loaded from the knowledge base
2. Split into smaller searchable chunks
3. Converted into TF-IDF vectors
4. Compared against ticket text using cosine similarity
5. Ranked based on relevance

The system returns the most relevant knowledge-base sections for a given support ticket.

### 2. Ticket Triage

The ticket triage system analyzes support tickets and produces:

- Ticket ID
- Category
- Urgency
- Summary
- Draft reply
- Relevant KB sources
- Confidence score

The triage logic uses ticket information and retrieved knowledge-base content to determine an appropriate response.

### 3. Account Health Summarization

The account summarization component combines account information with available support ticket information.

It provides:

- Account summary
- Company information
- Plan tier
- ARR
- Licensed and active seats
- Products
- Health status
- Usage trend
- Open ticket count
- High-priority ticket count
- Churn risk indicators
- Escalation indicators
- Executive summary
- TAM talking points
- Recent ticket information

The account health output is intended to help a TAM quickly understand customer risk and prioritize follow-up actions.

## Technology

The current implementation uses:

- Python
- scikit-learn
- TF-IDF vectorization
- Cosine similarity
- pytest
- JSON
- Markdown knowledge-base documents

No external LLM or OpenAI API key is required for the current implementation.

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
│   └── test_cases.json
│
├── src/
│   ├── __init__.py
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── chunker.py
│   │   ├── retriever.py
│   │   └── test_ticket_retrieval.py
│   │
│   ├── summarizer/
│   │   ├── __init__.py
│   │   └── summarizer.py
│   │
│   └── triage/
│       ├── __init__.py
│       └── triage.py
│
├── tests/
│   ├── test_retrieval.py
│   └── test_summarizer.py
│
├── .env.example
├── .gitignore
├── inspect_data.py
├── inspect_tickets.py
├── requirements.txt
└── README.md
````

## Installation

Create a Python virtual environment:

```powershell
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```powershell
pip install -r requirements.txt
```

## Running Knowledge Base Retrieval

From the project root:

```powershell
python src\retrieval\retriever.py
```

The retrieval component loads the knowledge base and performs similarity-based search against support ticket text.

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

Example output structure:

```json
{
  "ticket_id": "TKT-10499",
  "category": "How-To",
  "urgency": "P4",
  "summary": "New team member onboarding to SecureVault",
  "draft_reply": "Thanks for reaching out about New team member onboarding to SecureVault...",
  "kb_sources": [
    "onboarding\\onboarding-guide.md",
    "products\\securevault.md"
  ],
  "confidence": 0.65
}
```

## Running Account Health Summarization

From the project root:

```powershell
python src\summarizer\summarizer.py
```

The summarizer loads account and ticket data and produces an account-level health summary.

A specific account can also be tested using:

```powershell
python -c "from src.summarizer.summarizer import build_account_health; import json; print(json.dumps(build_account_health('ACC-3336'), indent=2))"
```

The account health result includes:

* Account ID
* Account summary
* Executive summary
* Open risks
* Churn flags
* Escalation flags
* TAM talking points
* Recent tickets

## Running Tests

Run the complete test suite from the project root:

```powershell
python -m pytest
```

The current test suite covers:

* Knowledge-base retrieval
* Ticket retrieval
* Retrieval relevance
* Account health summarization

Current result:

```text
5 passed
```

## Running Evaluation

The evaluation suite contains predefined support-ticket test cases.

Run:

```powershell
python eval\evaluate.py
```

Current evaluation result:

```text
PASS: How do I enable SSO?
PASS: Users are unable to sync files
PASS: How much does the Business plan cost?
PASS: WorkflowEngine approval is stuck
PASS: DataBridge Pro ingestion is failing
PASS: CloudSync webhook is not reaching Snowflake

Passed: 6/6
```

## Evaluation Dataset

The evaluation cases are stored in:

```text
eval/test_cases.json
```

The evaluation covers representative support scenarios including:

* Authentication and SSO
* Product synchronization
* Billing and pricing
* Workflow approvals
* Data ingestion
* CloudSync integrations

The evaluation is intended to verify that the retrieval and triage pipeline identifies relevant knowledge-base content and produces appropriate results.

## Retrieval Approach

The retrieval pipeline uses a lightweight classical information-retrieval approach.

### Step 1: Document Loading

Markdown knowledge-base files are loaded from:

```text
data/knowledge-base/
```

### Step 2: Chunking

Documents are divided into smaller sections so that retrieval can return focused information instead of entire documents.

### Step 3: TF-IDF Vectorization

Each knowledge-base chunk is converted into a TF-IDF vector.

TF-IDF gives higher importance to terms that help distinguish relevant documents and sections.

### Step 4: Cosine Similarity

The ticket query is converted into the same vector space.

Cosine similarity is used to compare the ticket against the knowledge-base chunks.

Higher similarity indicates stronger lexical relevance.

### Step 5: Ranking

The retrieved chunks are ranked by similarity score and the most relevant sources are returned.

## Confidence

The confidence value is derived from the retrieval similarity results.

A higher score indicates that the retrieved knowledge-base content is more closely related to the ticket.

The confidence value should be interpreted as a retrieval relevance signal rather than a calibrated probability.

## Ticket Classification

The triage component assigns a support category using information available in the ticket and relevant context.

Example categories include:

* Billing
* Bug
* How-To
* Onboarding
* Data Loss
* Feature Request

## Urgency

Tickets are assigned an urgency level such as:

* P1
* P2
* P3
* P4

Urgency is determined from information available in the ticket, including explicit priority indicators and the severity of the reported issue.

## Draft Reply Generation

The system generates a concise draft response using the ticket information and retrieved knowledge-base content.

The draft response is designed to:

* Acknowledge the customer's issue
* Reference relevant knowledge-base guidance
* Provide an appropriate next step
* Avoid inventing unsupported troubleshooting information

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

## Data Handling

The project uses the supplied account and ticket datasets.

Account-level ticket counts and the tickets available in the ticket dataset may not always match.

The summarizer therefore distinguishes between:

* Ticket counts stored on the account record
* Tickets actually available for the account in the ticket dataset
* Recent tickets included in the configured time window

This prevents missing ticket records from automatically being interpreted as having no support activity.

## Limitations

The current implementation intentionally uses a lightweight retrieval and rule-based approach.

Known limitations include:

* TF-IDF primarily relies on lexical similarity
* Semantically similar phrases with different wording may not always retrieve the best result
* Confidence scores are retrieval scores and are not calibrated probabilities
* Ticket classification is rule-based rather than model-based
* Draft replies are template-driven
* Account and ticket datasets may contain inconsistent or incomplete relationships
* The current implementation does not require an external LLM

## Future Improvements

Potential improvements include:

* Semantic embeddings for retrieval
* Hybrid keyword and vector search
* LLM-based ticket classification
* LLM-based response generation
* Calibrated confidence scoring
* Improved product and entity matching
* More comprehensive evaluation metrics
* Automated escalation detection
* Historical account trend analysis
* Account-level risk scoring
* Integration with a production ticketing system

## Reproducibility

The project is designed to run locally using the supplied data and Python dependencies.

After installing the requirements, the main verification commands are:

```powershell
python -m pytest
```

and:

```powershell
python eval\evaluate.py
```

The current implementation can therefore be evaluated without requiring external services or API credentials.

## Verification

The current implementation has been verified with:

```text
5 passed
```

for the automated test suite and:

```text
Passed: 6/6
```

for the evaluation suite.

## Summary

This project provides a lightweight AI-assisted support workflow that combines:

* Knowledge-base retrieval
* Ticket triage
* Ticket summarization
* Draft response generation
* Retrieval confidence
* Evaluation
* Account health summarization
* TAM talking points

The implementation focuses on being:

* Simple
* Reproducible
* Explainable
* Testable
* Easy to extend

```
```
