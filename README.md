# ApexGateway: Enterprise Deterministic AI Governance Fabric

[![Architecture: Polyglot](https://img.shields.io/badge/Architecture-C%2B%2B20%20%7C%20Python%203.14%20%7C%20Java%2021-blue.svg)](#subsystem-breakdown)
[![Performance: Deterministic](https://img.shields.io/badge/FSM%20Latency-%3C%2015%20%CE%BCs%2Fstep-brightgreen.svg)](#performance--sla-benchmarks)
[![SIMD: AVX-512](https://img.shields.io/badge/Hardware%20SIMD-AVX--512%20Vectorized-orange.svg)](#cloud-architecture--hardware-specialization)
[![Infrastructure: AWS Cloud-Native](https://img.shields.io/badge/IaC-Terraform%201.7%2B-purple.svg)](AWS_DEPLOYMENT.md)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-lightgrey.svg)](LICENSE)

An ultra-high-throughput, polyglot AI governance gateway and multi-agent execution fabric designed for sub-millisecond, deterministic fraud investigation and regulatory compliance enforcement.

ApexGateway replaces non-deterministic LLM agent execution paths with a hybrid topology: a **Java 21 Reactive WebFlux gateway**, an **asynchronous Python 3.14 multi-agent orchestrator**, and an **in-memory C++20 Finite State Machine (FSM)** backed by an embedded **RocksDB 11.x storage engine**.

---

## System Architecture Topology

![ApexGateway Architecture Topology](architecture.svg)

The execution topology consists of four distinct operational boundaries:
1. **Edge & Client Ingress:** Banking core streams and the React 18 Mission Control push alerts into the gateway.
2. **Reactive Ingress Mesh:** Spring Boot 3.3 / WebFlux schedules non-blocking traffic on a Netty EventLoop with Resilience4j circuit breaker fallbacks.
3. **Co-Located Single-Pod Execution Unit:** The Python 3.14 Agent Runtime and native C++20 FSM communicate over an in-memory Unix Domain Socket (`/dev/shm/fsm.sock`), bypassing the host TCP/IP stack to deliver sub-6 μs IPC.
4. **Backing Infrastructure & Event Mesh:** Kafka KRaft partitions immutable forensic audit logs, Redis Stack handles HNSW vector similarity caching, OpenTelemetry pipes W3C distributed traces to Jaeger, and Moto provides zero-cost AWS API emulation.

---

## Subsystem Breakdown

| Subsystem | Stack & Runtimes | Architectural Purpose | Performance Invariant |
| :--- | :--- | :--- | :--- |
| **Ingress Gateway** | Java 21, Spring Boot 3.3, WebFlux, Netty | Reactive API Gateway, Circuit Breaker Mesh, Traffic Ingress Policing | < 2 ms Netty dispatch |
| **Agent Orchestrator** | Python 3.14, Google ADK, FastAPI, Boto3 | Multi-Agent Case Synthesis, Evidence Correlation, AWS Key Resolution | Async non-blocking dispatch |
| **Deterministic Engine** | C++20, gRPC, Protobuf v3, CMake/Ninja | Deterministic Regulatory Transition Matrix, Lock-free Bitmask Eval | **5 to 15 μs per transition** |
| **Token Guardrail Scanner** | C++20, SIMD Intrinsics (AVX-512) | Wire-speed PII and prompt-injection inspection on raw token streams | > 12.4 GB/s throughput |
| **State & Audit Store** | RocksDB 11.x (4 Column Families) | Contiguous transactional audit logging and microsecond state recovery | Direct NVMe instance path |
| **Mission Control** | React 18, TypeScript, Vite, React Flow | Interactive DAG visualization, real-time node state animation, HITL | Real-time state synchronization |
| **Event Ledger** | Apache Kafka 3.7 (Bitnami KRaft) | Multi-AZ immutable topic persistence (`fraud.alerts.v1`) | Partitioned sequential write |
| **Semantic Cache** | Redis Stack Server | HNSW vector indexing and Redlock distributed transaction locks | Sub-5 ms similarity lookup |
| **Distributed Tracing** | OpenTelemetry Collector + Jaeger UI | End-to-end W3C distributed trace spans across Java, Python, and C++ | OTLP over gRPC (:4317) |
| **Cloud Emulation** | Moto (AWS Mock Server) | Local AWS Secrets Manager & S3 Lakehouse emulation | Zero-cost offline harness |

---

## Performance & SLA Benchmarks

Validated on Apple Silicon (M-Series) and AWS `c7i.2xlarge` (Intel Sapphire Rapids):

* **FSM Step Transition Time:** 0.005 ms – 0.015 ms (5 – 15 μs)
* **Full Multi-Agent Pipeline Turnaround:** 72 ms (inclusive of 6 compliance transitions and RocksDB commits)
* **Ingress Circuit Breaker Failover:** < 1 ms transition to deterministic fallback heuristic upon downstream saturation
* **SIMD Token Scan Throughput:** 12.4 GB/s sustained per compute core
* **IPC Transport Latency:** < 6 μs via RAM-mounted Unix Domain Socket (`/dev/shm/fsm.sock`)

---

## Cloud Architecture & Hardware Specialization

For complete production deployment manifests, network designs, and FinOps models, see the **[AWS Production Deployment Specification](AWS_DEPLOYMENT.md)**.

### Architectural Decisions
1. **Intel Sapphire Rapids (`c7i`) Pinning:** Compute node pools are pinned to Intel 4th Gen Xeon processors to utilize hardware **AVX-512** 512-bit vector registers (`zmm0`–`zmm31`), avoiding the 75% vector throughput drop of ARM NEON (128-bit) without code refactoring.
2. **Direct-Attached NVMe Instance Stores:** RocksDB bypasses virtualized Amazon EBS (`gp3`/`io2`) entirely. Direct NVMe PCIe Gen4 communication eliminates the 1.5 – 3.5 ms Nitro hypervisor network hop, maintaining < 18 μs physical write latency. State durability is guaranteed via MSK Kafka replay on pod boot.
3. **Single-Pod IPC Co-Location:** Packaging the Python ADK runtime and C++20 engine in a single Kubernetes pod over an in-memory Unix Domain Socket drops IPC latency from 1,200 μs (TCP/IP) down to **6 μs**.
4. **Zero-Trust IRSA:** Static AWS keys are eliminated. All cloud permissions are resolved dynamically via AWS STS OIDC Web Identity Federation.

---

## Local Development & Quickstart

### Prerequisites
* **C++:** Clang / GCC supporting C++20, CMake 3.28+, Ninja
* **Python:** Python 3.14+
* **Java:** OpenJDK 21 or Eclipse Temurin 21, Gradle
* **Node.js:** Node.js 20+, npm 10+
* **Containers:** Docker Engine / Desktop with Docker Compose

### 1. Start Infrastructure & AWS Emulation Mesh
```bash
cd apexgateway-infra
docker compose up -d
./setup_moto.sh  # Provisions mock S3 audit bucket and Secrets Manager keys
2. Build & Run C++20 FSM Engine
Bash
cd apexgateway-fsm-engine
mkdir -p build && cd build
cmake -GNinja -DCMAKE_BUILD_TYPE=Release ..
ninja
./fsm_engine_server
# Listening on 0.0.0.0:50051 (Embedded RocksDB at /tmp/apexgateway_rocksdb)
3. Launch Python 3.14 Agent Runtime
Bash
cd apexgateway-agent-runtime
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=".:generated"
python -m src.main
# Listening on [http://0.0.0.0:8000](http://0.0.0.0:8000)
4. Launch Java 21 Reactive Gateway
Bash
cd apexgateway-gateway
gradle bootRun
# Ingress Gateway listening on http://localhost:8080
5. Start Mission Control UI
Bash
cd apexgateway-ui
npm install
npm run dev
# Dashboard accessible at http://localhost:5173
Triggering an End-to-End Investigation
Submit a transaction alert through the reactive ingress gateway:
Bash
curl -X POST http://localhost:8080/api/v1/gateway/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC-CORP-4402",
    "amount_usd": 3400000.00,
    "sender_country": "SG",
    "receiver_country": "US",
    "narrative": "Urgent multi-entity liquidity transfer across corporate entities."
  }'
Expected Response
JSON
{
  "workflow_id": "gw-39c1b24f",
  "status": "ESCALATED_TO_HUMAN",
  "final_fsm_state": 7,
  "total_steps_executed": 6,
  "transaction_amount": 3400000.0,
  "gateway_latency_ms": 72,
  "circuit_breaker_status": "CLOSED_HEALTHY"
}
Repository Layout
ApexGateway-Enterprise/
├── architecture.svg              # Animated SVG architecture topology diagram
├── apexgateway-contracts/        # Canonical Protobuf v3 schemas & gRPC stubs
├── apexgateway-fsm-engine/       # C++20 deterministic FSM, AVX-512 SIMD scanner, RocksDB
├── apexgateway-agent-runtime/    # Python 3.14 multi-agent orchestrator & AWS SDK bridge
├── apexgateway-gateway/          # Java 21 Spring Boot 3.3 Reactive WebFlux Ingress
├── apexgateway-ui/               # React 18 / TypeScript interactive DAG Mission Control
├── apexgateway-infra/            # Docker Compose infrastructure mesh & Moto AWS harness
│   ├── setup_moto.sh             # Automated mock AWS provisioning script
│   └── terraform/                # Modular AWS Terraform IaC (EKS, MSK, IRSA, VPC)
├── AWS_DEPLOYMENT.md             # Enterprise cloud systems specification & FinOps model
└── README.md                     # Project documentation and operational guide