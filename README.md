# SupportDesk-RAG — Principal+ Production RAG Architecture

A production-oriented reference architecture for an **IT support troubleshooting RAG platform**. It demonstrates LangChain/LCEL, LlamaIndex, FAISS and Chroma integration points, five indexing strategies, hybrid/two-layer retrieval, grounded generation, retrieval + generation evaluation, and an agentic multi-turn extension.

> **Architectural invariant:** an LLM is not a knowledge authority. Retrieved enterprise content is evidence, not executable instruction. Every answer must be attributable to authorized evidence or explicitly abstain.

## 1. Why this is more than a chatbot

SupportDesk-RAG sits in the operational path between employees/customers and IT knowledge. Wrong advice can extend outages, cause data loss, bypass security controls, or amplify a malicious document. The architecture therefore optimizes not only relevance but **groundedness, provenance, authorization, freshness, blast-radius control, reproducibility, and graceful abstention**.

## 2. Repository map

```text
app/
  main.py             FastAPI serving plane
  models.py           stable API contracts
  indexing.py         five indexing strategies
  retrieval.py        first-stage retrieval + second-stage reranking
  guardrails.py       grounding/abstention + prompt-injection boundary
  evaluation.py       retrieval and generation evaluation
  memory.py           bounded conversation memory abstraction
  agent.py            agentic troubleshooting loop
  lcel_pipeline.py    complete LCEL composition example
  vector_adapters.py  FAISS / Chroma / LlamaIndex integration points
java/                  Java 21 Spring Boot ticket-context gateway
Dockerfile / compose   local deployment
.github/workflows      CI
```

## 3. System context

```text
 Employee / Support Engineer
          |
      API Gateway
          |
  Ticket/RAG API  <----> Java Ticket Context Gateway ----> ITSM / CRM
          |
  AuthZ + Tenant Filter
          |
 Conversation Orchestrator
     |       |       |
 query   memory   policy/guardrails
 rewrite             |
     |                v
     +------> Retrieval Plane -------------------------+
              |                                       |
       lexical/vector                           metadata/ACL filter
              |                                       |
        FAISS / Chroma / BM25 <---- Index Catalog ----+
              |
        candidate fusion
              |
       cross-encoder reranker       (Layer 2)
              |
       evidence sufficiency gate
          /             \
      abstain          grounded prompt
                           |
                     LLM / LCEL chain
                           |
                citation/claim verifier
                           |
                    Answer + sources
                           |
                 traces / eval events

 Offline Knowledge Plane:
 Connectors -> normalize -> classify -> redact -> chunk -> embed
 -> index version -> shadow evaluation -> promote -> serving aliases
```

### Control plane vs data plane

**Serving/data plane** owns low-latency query processing: identity, query normalization, retrieval, reranking, generation, citations and response policy. **Knowledge/control plane** owns connectors, parsing, ACL propagation, embedding/index builds, index promotion/rollback, evaluation datasets, model/prompt policy and configuration. Separating them prevents ingestion spikes or a broken re-index from destabilizing ticket serving.

## 4. Request lifecycle

1. Authenticate caller and derive tenant, user, groups and data entitlements.
2. Fetch ticket metadata through a narrow service contract; do not expose the entire ITSM record to the model.
3. Normalize the question and resolve bounded conversation references.
4. Apply **pre-retrieval authorization filters**. Security trimming after retrieval is too late because unauthorized content may already influence ranking or generation.
5. Layer 1 retrieves a broad candidate set using vector + lexical signals.
6. Fuse/deduplicate candidates (RRF is a strong default).
7. Layer 2 reranks candidates with a cross-encoder or task-specific reranker.
8. Evidence gate checks relevance, source trust, freshness, ACL state and evidence diversity.
9. If insufficient, abstain or ask a diagnostic question rather than guessing.
10. Generator receives a constrained evidence envelope. Retrieved documents are delimited as untrusted data.
11. Post-generation checks validate citations, prohibited actions, unsupported claims and output schema.
12. Emit response plus trace/evaluation metadata. Production traces should contain IDs/hashes rather than unrestricted sensitive document text.

## 5. Five indexing approaches

### A. Fixed-token/window chunks
Simple and fast; useful baseline and stable benchmark. Weakness: cuts semantic units and procedures.

### B. Recursive structure-aware chunks
Split by document/section/paragraph boundaries, then enforce token budgets. Recommended general-purpose default for runbooks and KB articles.

### C. Semantic chunks
Detect topic boundaries and group semantically cohesive passages. Better context quality, but higher ingestion cost and harder reproducibility when embedding models change.

### D. Parent-child retrieval
Embed compact child passages for precise recall but return larger parent sections for generation. Particularly useful for troubleshooting procedures where the matching symptom is small but remediation requires surrounding prerequisites/warnings.

### E. Summary + detail / multi-vector representation
Index generated/curated summaries alongside canonical detail. Summaries improve discovery for verbose documents; generation must still cite canonical content. Never let an unverified generated summary become the source of truth.

Each strategy should be evaluated against the **same frozen ticket/query set** before promotion. Do not select chunking by intuition alone.

## 6. FAISS, Chroma, LangChain and LlamaIndex

**FAISS** is excellent for local/high-performance ANN experiments and embedded deployments. It is an index library, not a complete multi-tenant knowledge service; persistence, metadata, ACLs, replication and lifecycle remain your responsibility.

**Chroma** provides a convenient persistent vector-store abstraction and metadata filtering for development/smaller deployments. At larger enterprise scale the vector store is an interchangeable infrastructure choice behind `Retriever` contracts.

**LangChain LCEL** composes the online execution graph: retrieval -> evidence formatting -> constrained prompt -> model -> parser. `app/lcel_pipeline.py` demonstrates the composition while keeping provider choice outside business logic.

**LlamaIndex** is useful in the knowledge/index layer for document/node abstractions and index composition. `vector_adapters.py` demonstrates a Chroma-backed LlamaIndex boundary.

The principal-level decision is **not to make any framework the architecture**. Frameworks are adapters. Domain contracts, policy, observability and evaluation remain owned by the platform.

## 7. Two-layer retrieval

Layer 1 optimizes **recall**: BM25/lexical + dense ANN + metadata filters produce perhaps 50–200 candidates. Layer 2 optimizes **precision**: a cross-encoder reranks the shortlist to perhaps 5–10 evidence passages. Reciprocal Rank Fusion avoids assuming incomparable lexical/vector scores share a calibrated scale.

A production score can include semantic relevance, lexical match, source authority, freshness and ticket/product affinity. ACL is a hard predicate, never merely a score penalty.

## 8. Anti-hallucination architecture

Safeguards are layered rather than a single prompt:

- authorization before retrieval;
- trusted-source allowlists and document lifecycle state;
- prompt-injection classification on ingested/query content;
- explicit separation of system instructions and retrieved data;
- evidence sufficiency threshold and abstention;
- temperature appropriate for support tasks;
- structured response schema;
- citation requirement at claim granularity for consequential advice;
- post-generation entailment/claim verification where warranted;
- risky remediation actions require deterministic policy or human approval;
- no secrets, privileged commands or credentials from the model;
- adversarial evaluation in CI and before index/model promotion.

## 9. Evaluation: two independent layers

### Retrieval evaluation
Measure Recall@K, Precision@K, MRR, nDCG, coverage, latency and ACL leakage rate. Segment by product, language, ticket type, document age and head/tail query frequency. An aggregate metric can hide a catastrophic tail segment.

### Generation evaluation
Measure groundedness/faithfulness, answer relevance, citation correctness/completeness, instruction-following, abstention precision/recall, harmful-remediation rate, latency and token cost. Use deterministic checks where possible, model-as-judge only with calibrated rubrics and periodic human agreement studies.

**Promotion gate example:** no ACL leaks; no regression beyond agreed confidence bounds on critical slices; groundedness and citation metrics above floor; p95 latency/cost inside budget; red-team suite passes.

## 10. Agentic RAG and conversation memory

The agent extension follows a bounded state machine rather than giving a free-form model arbitrary control:

```text
UNDERSTAND_TICKET -> RETRIEVE -> RERANK -> ASSESS_EVIDENCE
       ^                                      |
       |                          insufficient+--> ASK_DIAGNOSTIC
       |                                      |
       +------------------- new observation <-+
                                              |
                                   sufficient v
                                        PROPOSE_FIX
                                              |
                                   VERIFY / ESCALATE
```

Memory has three tiers: short-lived turn buffer, structured ticket state (symptoms, attempted steps, observed errors), and durable ticket events in the ITSM system. Summaries are versioned derived data, not canonical facts. Tenant/user ACL context is never inferred from conversational memory.

## 11. Multi-tenancy

Tenant ID is derived from authenticated identity, never trusted from request JSON in production. Namespace index collections or enforce mandatory tenant predicates at the storage abstraction. Encryption keys, quotas, evaluation dashboards and retention can be tenant-specific. High-compliance tenants may require physical index isolation.

## 12. Reliability and SLO design

Illustrative targets (choose from measured business requirements): API availability 99.9–99.95%; p95 retrieval <300 ms; p95 end-to-end <3 s for normal answers; zero tolerated cross-tenant leakage. Apply deadlines per stage so a slow reranker cannot consume the entire request budget.

Graceful degradation order: preferred LLM -> smaller approved model -> extractive evidence response -> search-only citations -> explicit temporary failure. Never degrade by dropping ACL or grounding controls.

Use bulkheads for model providers/vector stores, bounded retries with jitter only for retryable failures, circuit breakers, request idempotency where ticket actions exist, and load shedding before resource exhaustion.

## 13. Capacity and cost model

For `Q` peak queries/s, candidate count `C`, rerank count `R`, average prompt tokens `P` and output `O`, model throughput and dollar cost are driven mainly by `Q*(P+O)`. Retrieval cost scales with corpus/vector dimensions and ANN parameters; reranking scales roughly with `Q*R` model inferences. Cache safe artifacts: embeddings for identical normalized content, retrieval results where ACL/freshness permit, and immutable parsed documents. Avoid blindly caching generated answers because ticket context and KB freshness change.

## 14. Index lifecycle and zero-downtime migration

Never rebuild the serving index in place. Build `index-vN+1`, validate document counts/checksums/ACLs, run offline eval, shadow traffic, compare metrics, then atomically move a serving alias. Retain `vN` for immediate rollback. Embedding-model migrations create a new index version; do not mix incompatible vector spaces.

## 15. Security threat model

Threats include indirect prompt injection in KB pages, poisoned documents, cross-tenant leakage, malicious ticket text, PII/secret exfiltration, over-privileged connectors, unsafe shell/admin remediation, and trace/log leakage. Controls include least-privilege connector identities, immutable provenance, content signing/checksums where appropriate, malware/content scanning, ACL propagation, policy enforcement outside the LLM, output DLP, secret redaction, audit logs and restricted action tools.

**Key rule:** retrieved content cannot redefine system policy or tool permissions.

## 16. Observability

Trace each request with correlation IDs across gateway, retriever, vector store, reranker and model. Record model/prompt/index versions, candidate IDs and scores, evidence IDs, token usage, latency by stage, abstention reason and policy outcome. Dashboards: QPS/error rate/latency, retrieval empty rate, reranker score distribution, groundedness, citation failures, abstentions, token spend, index freshness and connector lag. Do not log raw sensitive prompts by default.

## 17. Disaster recovery

Canonical documents remain in durable object/source systems; vector indexes are reproducible derived state. Back up manifests, normalized documents, metadata/ACL snapshots, evaluation sets and configuration. Rebuild vector indexes from versioned manifests. Define RPO/RTO independently for serving, ingestion and analytics. A secondary region can serve the last promoted immutable index if ingestion is unavailable.

## 18. Deployment topology

Small deployment: FastAPI replicas + Chroma + external LLM + ITSM gateway. Enterprise deployment: global/API gateway -> regional RAG services -> Redis/cache -> hybrid search/vector cluster -> reranker pool -> model gateway; separate Kafka/queue-driven ingestion workers and object store; OpenTelemetry into metrics/log/trace backends. Kubernetes HPA should consider concurrency/queue depth, not CPU alone for I/O/model-bound workloads.

## 19. API

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
curl -X POST http://localhost:8080/v1/support/answer \
  -H 'content-type: application/json' \
  -d '{"ticket_id":"INC-42","question":"VPN error 809: what should I check?","top_k":5}'
```

The included deterministic generator makes the baseline runnable without an external API key. Configure an approved LLM and use `build_lcel()` for model-backed generation.

## 20. Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
make run
# or
docker compose up --build
```

## 21. CI/CD and evaluation gates

PR: unit tests -> contract tests -> retrieval golden set -> hallucination/adversarial suite -> dependency/SAST scan. Build immutable image and index manifest. Staging runs shadow queries. Production uses canary model/prompt/index configuration with automated rollback on safety/SLO regression. Model, prompt, embedding, reranker and index versions are independently observable configuration dimensions.

## 22. Architecture decision records worth discussing

1. **RAG over fine-tuning for mutable support knowledge:** facts change frequently and require provenance/deletion; fine-tuning can improve behavior but is not the primary mutable knowledge store.
2. **Hybrid retrieval:** exact error codes/product names favor lexical retrieval while paraphrased symptoms favor dense retrieval.
3. **Two-stage ranking:** expensive semantic reranking is applied only to a recall-optimized shortlist.
4. **Explicit abstention:** expected safe behavior, not a failure.
5. **Framework isolation:** LangChain/LlamaIndex are replaceable adapters.
6. **Immutable versioned indexes:** reproducibility and rollback outweigh in-place simplicity.
7. **Policy outside the model:** authorization and consequential actions must be deterministic.

## 23. Principal+ interview discussion

A Principal Engineer should be able to explain not just *how* RAG works but organizational boundaries and tradeoffs: Who owns KB quality? How are ACL changes propagated within minutes? How do you prove a deleted document cannot be retrieved? What happens when an embedding provider changes? How do you measure support-ticket resolution rather than only RAGAS-style proxy scores? Which fixes may be automated? How do you prevent a malicious wiki page from acquiring tool authority? How does a 10x corpus or traffic increase change index topology and reranking economics? How do you roll back a bad index independently of application code?

## 24. Evolution roadmap

**Phase 1:** read-only RAG with citations and abstention. **Phase 2:** hybrid retrieval, reranking, automated eval, index aliases. **Phase 3:** structured ticket memory and diagnostic agent. **Phase 4:** constrained read-only tools (service health, asset inventory). **Phase 5:** human-approved remediation actions. **Phase 6:** selected low-risk closed-loop automation with policy-as-code, idempotency, compensating actions and complete audit trails.

## 25. Production gaps intentionally left as adapters

This repository is a complete architectural reference and runnable baseline, but real deployment requires organization-specific identity/ACL integration, document connectors, secrets/KMS, chosen embedding/reranker/model endpoints, durable memory, production vector/search infrastructure, PII policy, observability backend and ITSM action authorization. Those concerns should be injected through interfaces rather than hard-coded into the demo.
