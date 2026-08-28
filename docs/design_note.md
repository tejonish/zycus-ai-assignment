# Production Design Note

## 1. Production Failure Modes

A production version of the support ticket triage system can fail in several realistic ways. The first major failure mode is **poor knowledge-base retrieval**. A ticket may contain terminology that does not closely match the wording used in the knowledge base, causing the correct document to rank below irrelevant results. This can be detected using retrieval similarity scores and evaluation metrics such as top-1 and top-3 accuracy. If confidence is low, the system should avoid presenting an unsupported answer and instead route the ticket for human review. Retrieval quality should also be monitored continuously using a representative evaluation set.

The second failure mode is **incorrect classification or urgency assignment**. A rule-based classifier can misinterpret ambiguous tickets, especially when a request contains multiple issues. For example, a ticket may contain both a billing question and a technical problem. This can be detected by monitoring classification accuracy and comparing predictions against manually reviewed tickets. Low-confidence or ambiguous tickets should be flagged for human review instead of being automatically resolved.

The third failure mode is **stale or incomplete knowledge-base information**. Even if retrieval works correctly, the retrieved guidance may no longer reflect the current product behavior. This can lead to incorrect support responses. Knowledge-base documents should therefore have ownership, version information, and review dates. When a document is changed, retrieval evaluation should be rerun to ensure that important queries still return the expected sources.

## 2. Latency vs Quality

The current implementation uses local TF-IDF vectorization and cosine similarity for retrieval. This approach is lightweight, deterministic, and does not require an external LLM or API call. As a result, retrieval can be performed quickly without network latency or API availability concerns.

There is a natural trade-off between latency and answer quality. More sophisticated retrieval methods, such as semantic embeddings followed by reranking, can improve matching when the user's wording differs significantly from the knowledge-base wording. However, embedding generation, vector-database access, and reranking introduce additional processing and infrastructure.

If latency became the highest priority, the system could keep the current TF-IDF index in memory, reduce the number of retrieved candidates, cache frequent queries, and avoid unnecessary processing. If answer quality became the higher priority, the retrieval layer could be upgraded to hybrid lexical and semantic retrieval, followed by a reranker. A production system should measure both retrieval quality and response latency before making this trade-off.

## 3. Data Sensitivity

Support tickets and account records may contain sensitive business information and personally identifiable information. The current implementation processes the supplied data locally and does not send ticket or account information to an external LLM API. This reduces the risk of unintentionally exposing customer data to a third-party service.

In production, access to ticket and account data should follow least-privilege principles. Users should only be able to access information required for their role. Sensitive fields should be redacted before sending data to external AI services when external processing is required. API credentials and other secrets should be stored in environment variables or a secrets manager rather than source code.

Production systems should also maintain audit logs for access to customer information, define data-retention policies, encrypt data in transit and at rest, and ensure that generated support responses do not expose information from unrelated customers. Any external AI provider should be reviewed for appropriate data-processing, retention, and security controls before customer data is sent to it.

## 4. Scaling

At 10x the current ticket volume, the first scaling concern would be data loading and retrieval-index construction. Rebuilding the complete TF-IDF index every time the application starts would become increasingly expensive as the knowledge base grows. The index should therefore be persisted and updated incrementally when documents are added or changed.

The retrieval layer can be scaled by keeping the search index in memory for fast access or moving to a dedicated search or vector database when the corpus becomes large. Ticket processing can also be made asynchronous so that multiple tickets can be triaged concurrently rather than processing every request sequentially.

Account-health generation can similarly be separated from the request path and calculated periodically for accounts whose data has changed. Frequently requested account summaries can be cached to reduce repeated computation.

At larger scale, the architecture should separate ingestion, indexing, retrieval, classification, and response generation into independent components. Monitoring should track retrieval latency, classification accuracy, error rates, queue depth, and resource utilization. This allows individual components to scale independently without requiring the entire application to scale together.

## Conclusion

The current implementation provides a simple and deterministic baseline for ticket retrieval, triage, and account-health analysis. A production deployment would add stronger monitoring, human-review paths for low-confidence cases, secure handling of customer data, persistent indexing, caching, and independently scalable processing components. These changes would improve reliability and maintainability while preserving the explainability of the current system.