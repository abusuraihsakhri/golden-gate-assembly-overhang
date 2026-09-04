# Golden Gate Assembly Overhang

> **Domain:** Computational Biology, AI Drug Discovery & Synthetic Biology  
> **Standards:** `wwPDB, IUPAC, NEB Golden Gate Assembly Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Golden Gate Assembly Overhang is an enterprise-grade multi-agent evaluation platform that processes biological/analytical task payloads through specialized worker agents. It performs:

- **Deterministic boundary evaluation** against configurable thresholds
- **Multi-tier urgency classification** (ROUTINE, ELEVATED, CRITICAL_STAT)
- **HMAC-SHA256 tamper-evident audit logging** with chained signatures
- **Zero-PHI outbound guard** blocking sensitive data leakage
- **FastAPI REST API** with Prometheus-compatible metrics

---

## ⚙️ Architecture

The project contains two parallel agent systems:

| Module | Purpose | Standard |
|--------|---------|----------|
| `agents/` | Enterprise multi-agent supervisor with PHI guard, audit trail, and FastAPI server | wwPDB / IUPAC / OpenSMILES |
| `golden_gate_agent/` | Frontier domain engine for Golden Gate assembly overhang fidelity | NEB Golden Gate Assembly |

### Key Components

- **`agents/supervisor.py`** — Master orchestrator dispatching tasks to specialized workers
- **`agents/workers.py`** — InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
- **`agents/base.py`** — PHI guard, HMAC-SHA256 audit trail, security validators
- **`agents/api.py`** — FastAPI REST endpoints
- **`golden_gate_agent/engine.py`** — Core algorithmic evaluation engine
- **`golden_gate_agent/agents.py`** — Specialized sub-agents (OverhangFidelityMatrix, InternalSiteExclusion, LigationJunctionValidator)
- **`enrichment.py`** — 8 enrichment feature engines (fidelity scoring, enzyme selection, codon optimization, etc.)

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/golden-gate-assembly-overhang.git
cd golden-gate-assembly-overhang

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## 💻 CLI Usage

### 1. Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Supervisory Chat
```bash
python cli.py chat "What standard is applied?"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameters
| Flag | Description | Default |
|------|-------------|---------|
| `--task-id` | Unique task identifier | TASK-2026-001 |
| `--target` | Target/sample identifier | KEY-TARGET-01 |
| `--primary` | Primary measurement value | 28.5 |
| `--secondary` | Secondary metric value | 14.2 |
| `--critical` | Flag as critical priority | False |
| `--status` | Status descriptor | DISCORDANT |

---

## 🛡️ Security Architecture

* **Zero-PHI Outbound Interceptor:** AST and regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs with signature verification
* **Path Traversal Protection:** All file I/O operations validate paths stay within the working directory
* **Input Validation:** NaN, Infinity, and out-of-bounds metric values are rejected
* **Secure Secret Management:** `AUDIT_SECRET_KEY` loaded from environment; random key generated if unset (see `.env.example`)

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env and set a strong AUDIT_SECRET_KEY:
#   python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🧪 Testing

```bash
# Run full test suite
pytest -v

# Run with coverage
pip install pytest-cov
pytest -v --cov=agents --cov=golden_gate_agent --cov-report=term-missing
```

### Test Coverage
- PHI guard enforcement
- Path traversal protection
- Input validation (NaN/Infinity rejection)
- HMAC signature verification
- Audit chain integrity
- Worker agent evaluation logic
- Supervisor consensus and audit
- CLI commands (audit, chat, verify-audit)
- Enrichment suite execution

---

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
docker-compose up --build

# Or manual Docker
docker build -t golden-gate-assembly-overhang .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") golden-gate-assembly-overhang
```

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check and system metadata |
| GET | `/metrics` | Operational metrics (dossier count, audit blocks) |
| POST | `/api/audit` | Submit task payload for evaluation |
| POST | `/api/chat` | Supervisory conversational query |
| GET | `/api/audit/logs` | Retrieve and verify HMAC audit trail |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
