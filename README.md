# Golden Gate Assembly Overhang

Static four-base overhang sequence screening for Golden Gate DNA assembly, plus the repository's existing threshold-based Python APIs and CLIs.

## Browser application

The site at the repository root operates completely client-side: it generates 2–16 four-nucleotide overhang candidates, screens custom sets of up to 64 sequences for duplicates, reverse-complement collisions, palindromes and invalid bases, flags extreme GC content and three-base homopolymers, reports nearest Hamming distances, and exports results to CSV.

**Interpretation:** These are heuristic sequence checks, **not** empirical ligation-fidelity measurements or assembly-efficiency predictions. Restriction-site content, enzyme-specific biases, junction orientation and fragment context are not evaluated. Validate designs experimentally and with appropriate enzyme-specific data.

**Privacy:** The browser application runs entirely locally. It does not upload sequences, load analytics, or call any third-party API.

Open `index.html` in a current browser, or serve the repository root:

```bash
python -m http.server 8000
# Visit http://localhost:8000/
```

## Python workflows

The pre-existing `agents/` and `golden_gate_agent/` packages evaluate **numeric threshold payloads**. They are preserved for compatibility; their alert classifications do not establish sequence-level overhang fidelity.

```bash
python -m pip install -e '.[server,test]'
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
python -m pytest -q
node --test tests/overhang.test.cjs
```

The existing `golden-gate-assembly-overhang` console entry point invokes `golden_gate_agent.cli`; the additional `golden-gate-operations` entry point invokes the root `cli.py` workflow. Both remain available. Python 3.9+ is declared, with CI covering 3.10–3.12.

### REST API

The optional FastAPI server exposes `GET /health`, `GET /metrics`, `POST /api/audit`, `POST /api/chat`, and `GET /api/audit/logs`. The audit logs endpoint requires a configured `AUDIT_READ_TOKEN` and a matching `X-Audit-Token` request header; without configuration it returns 403.

Only use synthetic or non-sensitive identifiers. The regex-based guard is not comprehensive PHI de-identification, the supervisory chat is a deterministic mock, and the HMAC audit ledger resides in volatile process memory. Persistent deployments must configure a strong `AUDIT_SECRET_KEY` (see `.env.example`). Do not place secrets in client-side Pages assets.

## Hosting

The static app requires no backend, no Pyodide and no build system. GitHub Pages can host the root `index.html`, `overhang.js` and `app.js` through the included deployment workflow when Pages is set to **GitHub Actions** as its publishing source. A live link will be listed here once the deployed site has been verified.

Modern Firefox, Safari, Chromium and Chromium-based browsers support the client-side app. Docker Compose runs the separate Python API server and requires `AUDIT_SECRET_KEY`.

## License

MIT — see [LICENSE](LICENSE).
