# HyperRoute Master Blueprint & Agent Memory Store

> **CRITICAL DIRECTIVE FOR ALL AI AGENTS**:
> This document is the **single source of truth** and **persistent memory** for the HyperRoute codebase. 
> Whenever you (the AI assistant) introduce new microservices, refactor existing components, modify network ports, or change architectural patterns, **you are strictly required to update this file in the same turn**.
> Before responding to architectural inquiries, cross-verify this document against the physical workspace (`Makefile`, `build.gradle`, `contracts/`, `docker-compose.yml`) to ensure zero hallucinations.

---

## 1. System Design & Architecture Overview

HyperRoute is an enterprise-grade **3-Tier Polyglot Compound AI Financial Gateway and Forensic Compliance Mesh**. It unifies deterministic sub-microsecond state machine validation with high-throughput banking ledger persistence and asynchronous multi-agent forensic reasoning.

### High-Level System Topology

```
                               ┌────────────────────────────────────────────────────────┐
                               │   Frontend (React 19 + TypeScript + Vite)             │
                               │   • Port: :5173                                        │
                               │   • SpatialHUD 3D/2D Transaction Dashboard             │
                               │   • ReactFlow Live DAG Graph & Forensic Chat Drawer    │
                               └───────────────────────────┬────────────────────────────┘
                                                           │ HTTP / WebSocket (:8080 / :8000)
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │   Gateway (Spring Cloud Gateway WebFlux / Go Ingress)   │
                               │   • Port: :8080                                        │
                               │   • OTel Distributed Tracing, JWT/OAuth2 Auth          │
                               │   • Distributed Redis Rate Limiting & Resilience4j     │
                               └──────────────┬──────────────────────────┬──────────────┘
                                              │                          │
                         gRPC / Event Stream  │                          │ REST / HTTP/2 WebClient
                                              ▼                          ▼
 ┌────────────────────────────────────────────────────┐  ┌──────────────────────────────────────────────┐
 │ Banking Core Engine (:8080 / :8081)                │  │ Agent Runtime (:8000)                        │
 │ Java 21 + Spring Boot 3.3.3                        │  │ Python 3.14 + FastAPI + Google ADK           │
 │ • Polyglot Persistence:                           │  │ • Token Vault: AES-256-GCM PII Redaction     │
 │   - PostgreSQL: Double-entry immutable ledger      │  │ • Tier 1: Sub-millisecond statistical screener│
 │   - Redis (:6379): Distributed lock & idempotency  │  │ • Tier 2: Google ADK Multi-Agent DAG Mesh    │
 │   - Kafka (:9092): Event-driven transaction log    │  │ • 4-Tier Memory: Working, Short, Long, Episodic│
 └────────────────────────────────────────────────────┘  └──────────────────────┬───────────────────────┘
                                                                                │
                                                            POSIX Shared Memory │ gRPC (:50051)
                                                            Latency: 2.79 µs    ▼
                                                         ┌──────────────────────────────────────────────┐
                                                         │ Compliance FSM Engine (:50051)               │
                                                         │ C++20 + Embedded RocksDB + AVX-512 SIMD      │
                                                         │ • O(1) Bitmask state transition matrix       │
                                                         │ • Embedded RocksDB on local NVMe instance    │
                                                         │ • Mathematical guardrail: Zero GC pauses     │
                                                         └──────────────────────────────────────────────┘
```

---

## 2. Core Polyglot Component Map

| Component | Path | Language / Runtime | Primary Port | Core Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | `/frontend` | React 19, TypeScript, Vite, Tailwind CSS, Three.js, ReactFlow | `:5173` | Real-time transaction telemetry, 3D SpatialHUD visualization, interactive ReactFlow DAG investigation trees, and compliance officer Forensic Chat Drawer. |
| **API Gateway** | `/gateway` | Java 21 / Spring Cloud Gateway (Netty WebFlux) & Go ingress | `:8080` | Ingress traffic termination, non-blocking reverse proxying, distributed Redis rate limiting, JWT validation, and OpenTelemetry span propagation. |
| **Banking Core** | `/banking-core` | Java 21, Spring Boot 3.3.3, JPA, Redis, Kafka | `:8080` / `:8081` | Core banking accounting, ACID-compliant double-entry ledger, distributed idempotency via Redis, and transaction event publication to Kafka topics. |
| **Agent Runtime** | `/agent-runtime` | Python 3.14, FastAPI, Uvicorn, Google ADK | `:8000` | Dual-Tier AI Mesh: Token Vault PII redaction (AES-256-GCM), Tier 1 statistical fast-path (< 4ms), Tier 2 Google ADK multi-agent forensic DAG, 4-tier memory store. |
| **FSM Engine** | `/fsm-engine` | C++20, CMake, RocksDB, gRPC, AVX-512 | `:50051` | Deterministic compliance state machine. Evaluates transition requests against $O(1)$ bitmasks with hardware SIMD vectorization; commits state to local RocksDB in 2.79 µs. |
| **Contracts** | `/contracts` | Protocol Buffers (proto3), gRPC | N/A | Language-neutral type definitions (`fsm_engine.proto`, `fsm_service.proto`) defining binary wire formats across C++, Python, and Java. |
| **Infrastructure** | `/infrastructure` | Docker Compose, Terraform, Kubernetes Kustomize | Various | Backing services: Redis (:6379), Kafka (:9092), LocalStack/Moto AWS (:4566), OpenTelemetry Collector, Jaeger, Tempo, Loki, Prometheus, Grafana. |
| **Documentation** | `/docs` | Markdown, SVG | N/A | In-depth system design whitepaper, architectural diagrams, and comprehensive codebase & directory guide. |

---

## 3. End-to-End Transaction Lifecycle

1. **Ingress & Security**: An incoming payment payload arrives at the API Gateway (`:8080`). The gateway verifies HMAC/OAuth2 credentials and checks distributed Redis rate limits.
2. **Double-Entry Ledger Ingestion**: The Banking Core (`/banking-core`) records an uncommitted ledger entry and emits an event to the Apache Kafka transaction topic.
3. **PII Tokenization**: The Python Agent Runtime (`/agent-runtime`) intercepts the transaction. The `TokenVault` strips all sensitive PII (PAN, SSN, Account Numbers) using deterministic AES-256-GCM envelope encryption before processing.
4. **Dual-Tier AI Evaluation**:
   * **Tier 1 (Statistical Fast-Path)**: 90%+ of nominal transactions clear in **$< 4\text{ ms}$** via tabular statistical/ML classification without invoking Large Language Models.
   * **Tier 2 (Deep Forensic Investigation)**: Anomalies trigger the **Google ADK Multi-Agent DAG** (`ComplianceInvestigationGraph`):
     - *Evidence Parser Agent*: Extracts structured transaction metadata and narrative facts.
     - *Historical Forensic Correlator Agent*: Cross-references 4-tier memory (past SARs, historical typologies).
     - *Risk Decision Agent*: Compiles a cryptographic audit dossier with an attestation proof.
5. **Hard Mathematical Guardrail Validation**: The agent runtime dispatches a transition request (`VALIDATE_AND_TRANSITION`) to the C++20 FSM Compliance Engine over gRPC (`:50051`) or POSIX shared memory.
   * **Rule**: AI agents are **strictly prohibited** from clearing transactions or freezing accounts directly. They can only present attested findings to the FSM.
   * The C++ FSM validates the transition using bitwise $O(1)$ regulatory bitmasks and AVX-512 SIMD payload verification.
   * On approval, the state is committed to embedded RocksDB on local NVMe in **2.79 µs**.
6. **Telemetry & Live UI**: The FSM outcome is streamed via WebSocket to the React 19 Frontend (`:5173`), rendering state updates on the SpatialHUD and live ReactFlow node graph.

---

## 4. Architectural Decision Records (ADRs)

### ADR-001: Standardization on Google Agent Development Kit (ADK) over LangChain / CrewAI
* **Status**: Accepted & Enforced
* **Decision**: Migrate all multi-agent orchestration exclusively to the **Google Agent Development Kit (Google ADK)** on **Python 3.14**.
* **Decisive Engineering Rationale**:
  1. **Zero Framework Bloat & Abstraction Leakage**: LangChain and CrewAI introduce deeply nested wrapper classes, heavy third-party dependencies, and frequent breaking changes across minor releases. Google ADK provides clean, lightweight DAG orchestration (`GraphWorkflow`) with direct model invocation.
  2. **Deterministic Banking Compliance vs. "Chatty" Roleplay**: Frameworks like CrewAI encourage unconstrained conversational banter between agents. In financial compliance, conversational roleplay produces non-deterministic latency and regulatory hallucination risks. Google ADK enforces rigid step-by-step DAG transitions where every agent step produces a structured, auditable attestation artifact.
  3. **Native Tool Grounding & Structured Streaming**: Google ADK natively binds with Gemini reasoning interfaces using strict JSON schema validation, eliminating prompt-injection vulnerabilities inherent in manual text parsing.
  4. **Python 3.14 Native Concurrency**: Google ADK runs cleanly on Python 3.14 asynchronous event loops without legacy C-extension or threading incompatibilities common in older agent packages.
  5. **Direct C++20 Bridge Compatibility**: Google ADK output objects serialize cleanly into Protobuf stubs for instant IPC transmission to our C++ FSM engine.

### ADR-002: Native C++20 FSM with Embedded RocksDB over Remote SQL/PostgreSQL
* **Status**: Accepted & Enforced
* **Decision**: Implement regulatory state machine validation in **C++20** backed by **embedded RocksDB on local NVMe storage**, rather than PostgreSQL, MySQL, or DynamoDB.
* **Decisive Engineering Rationale**:
  1. **Microsecond SLA Budget**: Banking transaction rails enforce strict latency budgets. Remote database network roundtrips take $1.5\text{ ms} - 4.0\text{ ms}$, which completely exhausts the latency budget. Embedded RocksDB commits directly via PCIe Gen4 bus speed in **$2.79\ \mu\text{s}$**.
  2. **Zero Garbage Collection (GC) Jitter**: Java (even with ZGC) and Go runtimes experience GC pause spikes that create tail latency violations ($P_{99.9}$). C++20 guarantees deterministic sub-microsecond execution.
  3. **Hardware-Accelerated Bitmasking**: Regulatory rules are encoded as 64-bit integer bitmasks. Intel Sapphire Rapids AVX-512 SIMD vector instructions inspect 64 bytes per clock cycle, evaluating regulatory matrices in nanoseconds.

### ADR-003: Java 21 Spring Boot for Banking Core Ledger
* **Status**: Accepted & Enforced
* **Decision**: Retain **Java 21 Spring Boot 3.3.3** for the Banking Core accounting engine.
* **Decisive Engineering Rationale**:
  1. **Transactional Integrity**: Financial double-entry bookkeeping requires rock-solid ACID transactions, strict schema enforcement, and distributed locking (Redis Redlock).
  2. **Virtual Threads (Project Loom)**: Java 21 virtual threads enable high-throughput non-blocking concurrency without reactive callback complexity.
  3. **Enterprise Polyglot Persistence**: Seamlessly coordinates PostgreSQL (audited ledger balances), Redis (idempotency tokens and sliding-window rate limits), and Apache Kafka (immutable transaction change-data-capture).

### ADR-004: Dual-Tier Compound AI Mesh (Statistical Screener + Deep Forensic DAG)
* **Status**: Accepted & Enforced
* **Decision**: Do not route 100% of transactions through LLMs. Instead, route transactions through a **Dual-Tier AI mesh**.
* **Decisive Engineering Rationale**:
  1. **Cost & Throughput**: Running millions of nominal transactions through LLMs costs tens of thousands of dollars daily and introduces 1–3 second latency per swipe.
  2. **Tier 1 Fast-Path**: A lightweight statistical/ML tabular screener clears > 90% of nominal payments in $< 4\text{ ms}$.
  3. **Tier 2 Forensic Escalation**: Only transactions flagged as anomalous or high-risk trigger the Google ADK multi-agent DAG.

### ADR-005: 4-Tier Memory Hierarchy for Forensic Reasoning
* **Status**: Accepted & Enforced
* **Decision**: Structure the Agent Runtime memory into 4 decoupled persistence tiers (`/agent-runtime/src/memory/`):
  * **Working Memory**: In-flight scratchpad discarded after DAG completion.
  * **Short-Term Memory**: Transaction session context retained across sub-investigation steps.
  * **Long-Term Semantic Memory**: Vector-indexed regulatory policies, typologies, and compliance rules.
  * **Episodic Memory**: Auditable past investigation dossiers and suspicious activity reports (SARs) stored for historical pattern correlation.

---

## 5. Development & Automation Commands

* **Compile Protobuf / gRPC Stubs**: `make stubs`
* **Build Polyglot Services**: `make build` (builds C++ FSM, Java Gateway, and Frontend)
* **Start Complete Runtime**: `make start` (or `bash scripts/start_all.sh`)
* **Stop Complete Runtime**: `make stop` (or `bash scripts/stop_all.sh`)
* **Execute Test Suites**: `make test` (Python pytest + Gradle test)
* **Verify System Pipeline**: `make verify` (Full end-to-end automated smoke and regression checks)

---

## 6. Key Architectural References

* **Comprehensive Codebase & Directory Breakdown**: [`docs/CODEBASE_GUIDE.md`](docs/CODEBASE_GUIDE.md)
* **System Design & Architecture Whitepaper**: [`docs/SYSTEM_DESIGN_AND_ARCHITECTURE.md`](docs/SYSTEM_DESIGN_AND_ARCHITECTURE.md)
* **Production AWS Deployment Runbook**: [`AWS_DEPLOYMENT.md`](AWS_DEPLOYMENT.md)
