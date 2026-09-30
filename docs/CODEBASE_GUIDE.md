# HyperRoute Enterprise Codebase Architecture & Directory Guide

This guide provides an exhaustive breakdown of the **HyperRoute** repository structure. It explains the engineering rationale behind every directory and file, demonstrating how real-world enterprise repositories organize complex, polyglot microservice systems.

---

## 1. Enterprise Architectural Pattern: The Polyglot Monorepo

In modern tier-1 tech companies and fintech institutions, large platforms often adopt a **Polyglot Monorepo** pattern:
* **Polyglot**: Different microservices are built in the language best suited for their specific SLA (Service Level Agreement):
  * **C++20** for sub-microsecond deterministic state machines and SIMD hardware acceleration.
  * **Java 21 (Spring Boot / Netty)** for ACID double-entry accounting ledgers and high-throughput non-blocking gateways.
  * **Python 3.14** for AI/ML pipelines, LLM agent graphs (Google ADK), and statistical screening.
  * **TypeScript / React 19** for real-time compliance UI, 3D visualization, and streaming investigation drawers.
* **Monorepo**: All services live in a single Git repository sharing unified versioning, contract definitions (Protobuf), infrastructure configurations (Terraform, Docker Compose, Kubernetes), and end-to-end integration test suites.

```
HyperRoute Root
├── Root Config & Governance    (AGENTS.md, README.md, Makefile, build.gradle)
├── contracts/                  (API & Binary Protobuf Schemas)
├── gateway/                    (Spring Cloud Gateway Edge Ingress :8080)
├── banking-core/               (Java 21 Double-Entry Accounting Engine :8081 / :8090)
├── agent-runtime/              (Python 3.14 Compound AI & Google ADK Mesh :8000)
├── fsm-engine/                 (C++20 AVX-512 Compliance State Machine :50051)
├── frontend/                   (React 19 + TypeScript + Vite SpatialHUD :5173)
├── infrastructure/             (Docker Compose, Observability, Terraform AWS)
├── deploy/                     (Kubernetes Pod Co-location & Kustomize)
├── scripts/                    (Orchestration & Verification Automation)
└── tests/ & load-tests/        (E2E Integration & Stress Testing)
```

---

## 2. Directory-by-Directory & File-by-File Breakdown

### Root Directory: Governance, Build Orchestration & Standards

| File | Purpose & Company Practice |
| :--- | :--- |
| [`AGENTS.md`](../AGENTS.md) | **Master Blueprint & Agent Memory Store**: Contains system topology, ports, Architectural Decision Records (ADRs), and strict rules for AI assistants to prevent code drift and hallucinations. |
| [`README.md`](../README.md) | **Developer Landing Page**: Executive overview, benchmark metrics (P99 latencies), ASCII architecture diagrams, and quickstart commands for onboarding engineers. |
| [`Makefile`](../Makefile) | **Monorepo Task Runner**: Standardizes developer commands across C++, Java, Python, and Node (`make stubs`, `make build`, `make start`, `make stop`, `make test`, `make verify`). |
| [`build.gradle`](../build.gradle) & [`settings.gradle`](../settings.gradle) | **Root Gradle Configuration**: Coordinates multi-module Java builds (`gateway` and `banking-core`), shared plugins, and Java 21 toolchains. |
| [`AWS_DEPLOYMENT.md`](../AWS_DEPLOYMENT.md) | **Production Cloud Runbook**: Step-by-step instructions for deploying to AWS EKS, RDS PostgreSQL, ElastiCache Redis, and MSK Kafka. |
| [`pytest.ini`](../pytest.ini) | **Python Test Configuration**: Configures test discovery paths, log levels, and asyncio test modes. |

---

### 1. `contracts/`: API & Binary Wire Protocol Boundary

In enterprise architectures, independent teams cannot hard-code endpoints or ad-hoc JSON payloads. They practice **Contract-First Development** using Protocol Buffers (gRPC).

```
contracts/
├── proto/
│   ├── fsm_service.proto
│   └── hyperroute/v1/
│       └── fsm_engine.proto
├── compile_stubs.sh
└── generate_stubs.sh
```

* [`contracts/proto/hyperroute/v1/fsm_engine.proto`](../contracts/proto/hyperroute/v1/fsm_engine.proto): The core wire protocol defining `TransactionTransitionRequest`, `ValidationState`, bitmask flags, and `TransitionAuditRecord`.
* [`contracts/proto/fsm_service.proto`](../contracts/proto/fsm_service.proto): The gRPC service contract defining RPC methods: `ValidateAndTransition()` and `GetTransactionState()`.
* [`contracts/generate_stubs.sh`](../contracts/generate_stubs.sh) & [`contracts/compile_stubs.sh`](../contracts/compile_stubs.sh): Shell scripts invoking `protoc` and `grpc_tools` to compile Protobuf definitions into native C++ headers (`.pb.h`) and Python modules (`_pb2.py`).

---

### 2. `fsm-engine/`: Tier-0 Compliance State Machine (C++20)

Handles high-frequency regulatory checks where latency must be deterministic (sub-microsecond) without Java or Python garbage-collection (GC) pause spikes.

```
fsm-engine/
├── CMakeLists.txt
├── Dockerfile
└── src/
    ├── main.cpp
    ├── fsm_engine.hpp
    ├── fsm_service_impl.hpp
    ├── rocksdb_storage.hpp
    └── rocksdb_storage.cpp
```

* [`CMakeLists.txt`](../fsm-engine/CMakeLists.txt): CMake build script enabling `-std=c++20`, AVX-512 SIMD vector instructions, and linking gRPC, Protobuf, and RocksDB libraries.
* [`src/main.cpp`](../fsm-engine/src/main.cpp): Server daemon bootstrap listening on gRPC port `:50051` or shared POSIX memory.
* [`src/fsm_engine.hpp`](../fsm-engine/src/fsm_engine.hpp): Mathematical state machine. Holds the bitwise state transition matrix (`ALLOWED_TRANSITIONS`), evaluates sanction masks in $O(1)$ time, and performs hardware SIMD payload verification.
* [`src/fsm_service_impl.hpp`](../fsm-engine/src/fsm_service_impl.hpp): gRPC service implementation mapping network RPC calls directly into `FSMEngine` executions.
* [`src/rocksdb_storage.hpp`](../fsm-engine/src/rocksdb_storage.hpp) & [`src/rocksdb_storage.cpp`](../fsm-engine/src/rocksdb_storage.cpp): Local NVMe storage abstraction using embedded RocksDB (LSM-tree), achieving persistence in $2.79\ \mu\text{s}$ without remote database network hops.

---

### 3. `banking-core/`: Tier-1 Core Ledger & Accounting (Java 21 / Spring Boot)

Maintains the immutable financial truth using the double-entry accounting principle (every debit must equal a credit).

```
banking-core/
├── Dockerfile
└── src/
    ├── main/
    │   ├── java/com/hyperroute/banking/
    │   │   ├── BankingCoreApplication.java
    │   │   ├── domain/
    │   │   │   ├── Account.java
    │   │   │   ├── LedgerEntry.java
    │   │   │   ├── Money.java
    │   │   │   ├── PaymentTransaction.java
    │   │   │   ├── OutboxEvent.java
    │   │   │   └── PaymentState.java
    │   │   ├── repository/
    │   │   │   ├── AccountRepository.java
    │   │   │   ├── LedgerEntryRepository.java
    │   │   │   ├── PaymentTransactionRepository.java
    │   │   │   └── OutboxEventRepository.java
    │   │   ├── service/
    │   │   │   ├── TransferService.java
    │   │   │   ├── IdempotencyService.java
    │   │   │   ├── OutboxEventPublisher.java
    │   │   │   └── HyperRouteClient.java
    │   │   └── controller/
    │   │       ├── TransferController.java
    │   │       └── SimulationController.java
    │   └── resources/
    │       └── application.yml
    └── test/
```

* [`BankingCoreApplication.java`](../banking-core/src/main/java/com/hyperroute/banking/BankingCoreApplication.java): Spring Boot application entrypoint running on port `:8081` (or `:8090`).
* **Domain Layer (`domain/`)**:
  * [`Account.java`](../banking-core/src/main/java/com/hyperroute/banking/domain/Account.java): Customer balance entity with optimistic locking (`@Version`) to prevent balance corruption.
  * [`LedgerEntry.java`](../banking-core/src/main/java/com/hyperroute/banking/domain/LedgerEntry.java): Immutable double-entry debit/credit line item.
  * [`Money.java`](../banking-core/src/main/java/com/hyperroute/banking/domain/Money.java): Value object wrapping `BigDecimal` and `Currency` to prevent IEEE floating-point rounding errors.
  * [`PaymentTransaction.java`](../banking-core/src/main/java/com/hyperroute/banking/domain/PaymentTransaction.java): Master transaction record holding reference IDs and states.
  * [`OutboxEvent.java`](../banking-core/src/main/java/com/hyperroute/banking/domain/OutboxEvent.java): Implements the **Transactional Outbox Pattern** to guarantee Kafka delivery without dual-write race conditions.
* **Service Layer (`service/`)**:
  * [`TransferService.java`](../banking-core/src/main/java/com/hyperroute/banking/service/TransferService.java): Coordinates `@Transactional` balance checks, debit/credit ledger writes, and outbox creation.
  * [`IdempotencyService.java`](../banking-core/src/main/java/com/hyperroute/banking/service/IdempotencyService.java): Uses Redis atomic keys (`SETNX`) to ensure duplicate payment requests return identical cached responses without double-charging.
  * [`OutboxEventPublisher.java`](../banking-core/src/main/java/com/hyperroute/banking/service/OutboxEventPublisher.java): Background worker reading uncommitted events from PostgreSQL and streaming them to Apache Kafka.
  * [`HyperRouteClient.java`](../banking-core/src/main/java/com/hyperroute/banking/service/HyperRouteClient.java): Non-blocking HTTP/gRPC client communicating with the Agent Runtime and Compliance FSM.
* **Controller Layer (`controller/`)**:
  * [`TransferController.java`](../banking-core/src/main/java/com/hyperroute/banking/controller/TransferController.java): REST endpoints (`POST /api/v1/transfers`) handling transfer requests.

---

### 4. `gateway/`: Edge Ingress & Reverse Proxy (Spring Cloud Gateway / WebFlux)

The perimeter of the banking mesh. Exposes port `:8080` to the internet, terminating TLS, enforcing rate limits, authenticating JWTs, and tracing every request.

```
gateway/
├── Dockerfile
└── src/
    └── main/
        ├── java/com/hyperroute/
        │   ├── GatewayApplication.java
        │   ├── config/
        │   │   ├── CorsConfig.java
        │   │   └── RateLimiterConfig.java
        │   ├── controller/
        │   │   ├── GatewayIngressController.java
        │   │   └── FallbackController.java
        │   ├── observability/
        │   │   ├── ObservabilityFilter.java
        │   │   └── ObservabilityMetrics.java
        │   └── service/
        │       └── AgentInvestigationService.java
        └── resources/
            ├── application.yml
            └── logback-spring.xml
```

* [`GatewayApplication.java`](../gateway/src/main/java/com/hyperroute/GatewayApplication.java): Netty-based non-blocking reactive gateway entrypoint.
* [`config/RateLimiterConfig.java`](../gateway/src/main/java/com/hyperroute/config/RateLimiterConfig.java): Distributed sliding-window token bucket algorithm powered by Redis (`KeyResolver`), defending against DDoS and credential stuffing.
* [`controller/GatewayIngressController.java`](../gateway/src/main/java/com/hyperroute/controller/GatewayIngressController.java): High-throughput ingestion controller for incoming alerts and transactions.
* [`controller/FallbackController.java`](../gateway/src/main/java/com/hyperroute/controller/FallbackController.java): Resilience4j Circuit Breaker fallback endpoints returning graceful degradation messages if downstream services are saturated.
* [`observability/ObservabilityFilter.java`](../gateway/src/main/java/com/hyperroute/observability/ObservabilityFilter.java): Injects W3C distributed trace headers (`traceparent`, `tracestate`) across all downstream calls.
* [`resources/application.yml`](../gateway/src/main/resources/application.yml): Route definitions routing `/api/v1/agent/**` to port `:8000`, `/api/v1/banking/**` to port `:8081`, and static assets.

---

### 5. `agent-runtime/`: Tier-2 Compound AI & Forensic Reasoning (Python 3.14 + Google ADK)

Implements a **Dual-Tier Compound AI** system:
1. **Tier 1 Fast-Path**: Rapid statistical/tabular screening in $< 4\text{ ms}$ for > 90% of payments.
2. **Tier 2 Deep Forensics**: Google Agent Development Kit (ADK) multi-agent DAG that analyzes high-risk anomalies, queries 4-tier memory, and produces cryptographic audit dossiers.

```
agent-runtime/
├── requirements.txt
├── Dockerfile
└── src/
    ├── main.py
    ├── classifier.py & features.py
    ├── fsm_client.py
    ├── security/token_vault.py
    ├── google_adk/
    │   ├── workflows/graph.py
    │   ├── agents.py
    │   ├── tools.py
    │   ├── planner.py
    │   └── reasoning.py
    ├── memory/memory_store.py
    ├── cache/semantic_cache.py
    ├── a2a/
    │   ├── protocol.py
    │   └── supervisor.py
    ├── mcp/
    │   ├── server.py
    │   └── graph_rag.py
    ├── compiler/
    │   ├── agentscript.py
    │   └── router.py
    ├── evals/
    │   ├── benchmarks.py
    │   └── evaluator.py
    └── audit/tracer.py
```

* [`src/main.py`](../agent-runtime/src/main.py): FastAPI web server listening on port `:8000`. Exposes `/api/v1/screener`, `/api/v1/investigate`, and WebSocket feeds for real-time telemetry.
* [`src/security/token_vault.py`](../agent-runtime/src/security/token_vault.py): **Data Privacy Boundary**: Strips credit card PANs, SSNs, and bank account numbers using AES-256-GCM envelope encryption *before* sending transaction context to LLMs.
* [`src/classifier.py`](../agent-runtime/src/classifier.py) & [`src/features.py`](../agent-runtime/src/features.py): Tier-1 statistical model evaluating transaction risk instantly.
* **Google ADK Multi-Agent Mesh (`src/google_adk/`)**:
  * [`workflows/graph.py`](../agent-runtime/src/google_adk/workflows/graph.py): Multi-agent DAG orchestrator (`ComplianceInvestigationGraph`).
  * [`agents.py`](../agent-runtime/src/google_adk/agents.py): Defines specialized autonomous agents:
    * `EvidenceParserAgent`: Extracts structured transaction metadata and narrative facts.
    * `HistoricalForensicCorrelatorAgent`: Cross-references historical case typologies.
    * `RiskDecisionAgent`: Synthesizes final risk scoring and generates an attested finding.
  * [`tools.py`](../agent-runtime/src/google_adk/tools.py): Bound tools (sanctions list lookup, velocity calculators, FX anomaly detectors).
* [`src/memory/memory_store.py`](../agent-runtime/src/memory/memory_store.py): Implements the **4-Tier Memory Hierarchy**:
  * *Working Memory*: Transient in-flight scratchpad.
  * *Short-Term Memory*: Multi-turn investigation session context.
  * *Long-Term Semantic Memory*: Vector-indexed regulatory policies and FATF guidelines.
  * *Episodic Memory*: SQLite database (`case_history.db`) storing past Suspicious Activity Reports (SARs).
* [`src/cache/semantic_cache.py`](../agent-runtime/src/cache/semantic_cache.py): Embedding cache that returns cached investigations for identical transaction typologies, reducing LLM costs to zero.
* [`src/fsm_client.py`](../agent-runtime/src/fsm_client.py): High-performance gRPC client dispatching transitions to the C++ FSM on `:50051`.
* [`src/audit/tracer.py`](../agent-runtime/src/audit/tracer.py): Cryptographic audit tracer generating SHA-256 attestation proofs for compliance audits.

---

### 6. `frontend/`: Real-Time Compliance SpatialHUD (React 19 + TypeScript + Vite)

The user-facing control plane for compliance officers, fraud investigators, and executives.

```
frontend/
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── types.ts
    ├── index.css
    └── components/
        └── ForensicChatDrawer.tsx
```

* [`package.json`](../frontend/package.json): Defines modern dependencies: React 19, Lucide icons, Tailwind CSS, ReactFlow (for DAG rendering), and Zustand (state management).
* [`src/main.tsx`](../frontend/src/main.tsx): Application mounting point.
* [`src/App.tsx`](../frontend/src/App.tsx): Main dashboard rendering:
  * **SpatialHUD**: 2D/3D visual transaction flow metrics.
  * **Live Ingestion Feed**: Real-time transaction telemetry with latency indicators.
  * **State Machine Monitor**: C++ FSM transition status and bitmask breakdown.
* [`src/components/ForensicChatDrawer.tsx`](../frontend/src/components/ForensicChatDrawer.tsx): Interactive slide-over drawer enabling officers to interrogate the Google ADK agents regarding why a specific transaction was flagged or held.
* [`src/types.ts`](../frontend/src/types.ts): Shared TypeScript interfaces ensuring type-safety across telemetry events and agent states.

---

### 7. `infrastructure/`: Local Backing Services & Observability Stack

Provides containerized infrastructure for local development and Terraform templates for AWS cloud deployment.

```
infrastructure/
├── docker-compose.yml
├── prometheus.yaml
├── loki.yaml
├── tempo.yaml
├── otel-collector-config.yaml
├── grafana/
│   └── provisioning/datasources/datasources.yaml
└── terraform/
    ├── versions.tf
    ├── variables.tf
    ├── vpc.tf
    ├── eks.tf
    ├── rds.tf
    ├── messaging.tf
    ├── data_stores.tf
    └── irsa.tf
```

* [`docker-compose.yml`](../infrastructure/docker-compose.yml): Spawns the entire local ecosystem in seconds:
  * `redis:7-alpine` (`:6379`) - Idempotency & Rate Limiting.
  * `kafka:latest` (`:9092`) - Event Streaming.
  * `postgres:16-alpine` (`:5432`) - Immutable Banking Ledger.
  * `otel-collector` (`:4317`) - Trace and Metric aggregation.
  * `prometheus` (`:9090`) - Metrics database.
  * `grafana` (`:3000`) - Dashboards.
  * `loki` (`:3100`) & `tempo` (`:3200`) - Log aggregation & distributed trace visualization.
* **`terraform/` (Infrastructure-as-Code)**:
  * [`vpc.tf`](../infrastructure/terraform/vpc.tf): Multi-AZ secure banking Virtual Private Cloud.
  * [`eks.tf`](../infrastructure/terraform/eks.tf): AWS Elastic Kubernetes Service cluster definition.
  * [`rds.tf`](../infrastructure/terraform/rds.tf): Multi-AZ PostgreSQL RDS database with automated backups and encryption.
  * [`messaging.tf`](../infrastructure/terraform/messaging.tf): AWS MSK (Managed Streaming for Apache Kafka).
  * [`data_stores.tf`](../infrastructure/terraform/data_stores.tf): AWS ElastiCache Redis cluster.
  * [`irsa.tf`](../infrastructure/terraform/irsa.tf): IAM Roles for Service Accounts (least privilege cloud security).

---

### 8. `deploy/`: Production Kubernetes (K8s) Orchestration

Contains Kubernetes manifests demonstrating advanced low-latency deployment strategies.

```
deploy/k8s/
├── namespace.yaml
├── kustomization.yaml
├── gateway-deployment.yaml
├── gateway-service.yaml
└── agent-fsm-colocated-pod.yaml
```

* [`agent-fsm-colocated-pod.yaml`](../deploy/k8s/agent-fsm-colocated-pod.yaml): **Colocated Pod Pattern**: Packages the Python Agent Runtime and the C++ FSM Engine inside the *same* Kubernetes Pod. Both containers share a POSIX shared-memory volume (`/dev/shm`), reducing IPC latency between Python and C++ to **$2.79\ \mu\text{s}$**, eliminating network overhead entirely!
* [`gateway-deployment.yaml`](../deploy/k8s/gateway-deployment.yaml) & [`gateway-service.yaml`](../deploy/k8s/gateway-service.yaml): Scalable gateway replica deployment with health probes and LoadBalancer service.

---

### 9. `scripts/`, `tests/`, & `load-tests/`: Automation & Quality Engineering

```
scripts/
├── start_all.sh
├── stop_all.sh
└── verify_all.sh

tests/
├── e2e_hyperroute_suite.py
├── test_enterprise_ai_platform.py
├── test_enhanced_agent_suite.py
└── mock_upstream_services.py

load-tests/
└── stress_test.py
```

* [`scripts/start_all.sh`](../scripts/start_all.sh) & [`scripts/stop_all.sh`](../scripts/stop_all.sh): Shell scripts orchestrating service startups in order of dependency (Infra -> FSM -> Banking -> Agent -> Gateway -> Frontend) with process tracking.
* [`scripts/verify_all.sh`](../scripts/verify_all.sh): Automated health check script testing all listening ports.
* [`tests/e2e_hyperroute_suite.py`](../tests/e2e_hyperroute_suite.py): Comprehensive end-to-end integration test pushing a live transaction through the entire pipeline: Ingress -> Redaction -> Screener -> Agent Investigation -> C++ FSM Bitmask -> State Commit.
* [`load-tests/stress_test.py`](../load-tests/stress_test.py): Concurrent load-testing harness simulating 1,000+ TPS to benchmark P99 latency and throughput.

---

## 3. End-to-End Request Lifecycle Through the Files

To visualize how these files execute together in production:

```
[1. User/Card Swipe]
        │
        ▼ (HTTP POST /api/v1/transfers)
[gateway/src/main/java/.../GatewayIngressController.java]
        │  * Rate check: RateLimiterConfig.java (Redis)
        │  * Trace injection: ObservabilityFilter.java (OTel)
        ▼
[banking-core/src/main/java/.../TransferController.java]
        │  * Idempotency check: IdempotencyService.java
        │  * Balance check & ledger write: TransferService.java & LedgerEntry.java
        │  * Kafka event write: OutboxEventPublisher.java
        ▼
[agent-runtime/src/main.py]
        │  * PII stripping: security/token_vault.py (AES-256-GCM)
        │  * Tier 1 Fast Path (< 4ms): classifier.py
        │       ├─ If Nominal (> 90%): Bypass LLM
        │       └─ If Anomaly: Trigger Tier 2 ADK Graph
        │  * Tier 2 ADK DAG: google_adk/workflows/graph.py
        │       ├─ Evidence Parser Agent
        │       ├─ Historical Forensic Correlator Agent (memory/memory_store.py)
        │       └─ Risk Decision Agent -> Cryptographic Audit Proof (audit/tracer.py)
        ▼ (gRPC :50051 / Shared Memory IPC)
[fsm-engine/src/main.cpp & fsm_service_impl.hpp]
        │  * Bitmask Matrix Check: fsm_engine.hpp (AVX-512 SIMD)
        │  * Commit to Local NVMe (2.79 µs): rocksdb_storage.cpp
        ▼ (WebSocket / SSE)
[frontend/src/App.tsx & ForensicChatDrawer.tsx]
        │  * SpatialHUD updates state indicators
        │  * Compliance officer inspects agent decision in real-time
```
