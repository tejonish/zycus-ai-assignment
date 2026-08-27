\# Zycus AI Support Ticket Triage



\## Overview



This project implements an AI-assisted support ticket triage system.



The system:

\- Loads support knowledge-base documents

\- Splits documents into searchable sections

\- Uses TF-IDF and cosine similarity for retrieval

\- Retrieves relevant knowledge-base content for support tickets

\- Classifies tickets into support categories

\- Assigns ticket urgency

\- Generates a draft support reply

\- Returns relevant KB sources and confidence



\## Current Implementation



The retrieval system uses:

\- Python

\- scikit-learn

\- TF-IDF vectorization

\- Cosine similarity



No external LLM or OpenAI API key is required for the current implementation.



\## Project Structure



```text

zycus-ai-assignment/

├── data/

│   ├── knowledge-base/

│   └── tickets/

├── docs/

├── eval/

├── src/

│   ├── retrieval/

│   │   ├── chunker.py

│   │   ├── retriever.py

│   │   └── test\_ticket\_retrieval.py

│   └── triage/

│       └── triage.py

├── tests/

├── requirements.txt

└── .env.example





Running Retrieval



From the project root:



python src\\retrieval\\retriever.py

Running Tests

python -m pytest



Expected result:



3 passed

Running Ticket Triage

python src\\triage\\triage.py



The output contains:



Ticket ID

Category

Urgency

Summary

Draft reply

KB sources

Confidence

