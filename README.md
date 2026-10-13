# Post Cardiac Arrest Agent

A browser-based **adult post–return-of-spontaneous-circulation (ROSC) observation checklist**, alongside legacy Python synthetic-rule demonstration modules.

**Use for education and software testing only.** The application is not validated clinical decision support. It does not diagnose disease, prescribe treatment, interpret EEG or biomarkers, forecast neurologic outcome, or communicate with clinical systems.

## Browser checklist

The static application is in [`web/index.html`](web/index.html). For local use, run:

```bash
python -m http.server 8080 --directory web
```

Then visit `http://localhost:8080/`. The browser application needs no backend, accounts, API keys, Python runtime, or external JavaScript dependencies.

It accepts four non-identifying observations: whether an adult is unresponsive to verbal commands after ROSC, a recorded temperature, accumulated hours of temperature control, and MAP. It flags values for review against a **limited** selection of the 2025 AHA post-cardiac-arrest recommendations:

- Maintain deliberate temperature control at 32–37.5 °C for adults unresponsive to commands after ROSC.
- Maintaining temperature control for at least 36 hours in those who remain unresponsive is reasonable.
- Avoid hypotension after ROSC; guideline minimum MAP is 65 mm Hg.
- Neurologic prognostication is delayed and multimodal. Sedative, temperature, and other confounders must be considered.

**Source:** [2025 AHA Guidelines, Part 11: Post-Cardiac Arrest Care](https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/post-cardiac-arrest-care).

The checklist reviews observations, not overall care quality. A result with no flagged values is **not** clearance, prognosis, or evidence of safety. It exports a local JSON summary, containing no identifier field.

## Privacy and limitations

The static page computes locally; it does not send inputs to a server, use browser storage, or embed remote analytics. **Do not submit real patient information.**

The remaining Python routes are **legacy synthetic demonstrations**, not implementations of the post-ROSC guidelines above. Their generic metrics, fixed thresholds, alert labels, and enrichment engines are not clinically validated. Existing command/API shapes are retained for compatibility with supplied test fixtures. Other modules (`post_arrest_sentinel.py`, `post_cardiac_arrest_agent/`, `agents/`) expose distinct legacy interfaces.

The optional Python service keeps task/audit metadata in process memory. Its pattern-based identifier check does **not** guarantee de-identification, HIPAA Safe Harbor compliance, or suitability for PHI. The audit HMAC verifies record integrity while the process/key is available; it is not a durable compliance archive. The `mock` inference adapter is not a real clinical or language-model reasoning system; other providers are not implemented.

## Python development and tests

Python 3.10–3.12 and Node.js (for browser-rule tests) are used in CI.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[server,test]"
pytest -q
node --test tests/web_audit.test.mjs
python cli.py audit --task-id TASK-DEMO-01 --primary 20 --secondary 5
python cli.py serve
```

The Python API is available locally at `http://127.0.0.1:8000/health`; it is **not** required by the static browser checklist. The PyPI-style console entry point is `post-cardiac-arrest-engine`.

For a Docker demonstration, set an independently generated high-entropy `AUDIT_SECRET_KEY` in your environment, then run `docker compose up --build`. Compose binds the API to loopback by default. Do not commit secrets to source control.

## Architecture

- `web/` — dependency-free browser checklist, observation rules, and JSON export
- `agents/` and `cli.py` — legacy synthetic orchestration, FastAPI interface, and in-memory HMAC audit
- `post_cardiac_arrest_agent/`, `post_arrest_sentinel.py` — additional legacy CLI/API numerical examples
- `enrichment.py` — synthetic placeholder threshold modules; not clinical models
- `tests/` — Python and browser regression checks
- `.github/workflows/` — test matrix and static Pages publishing workflow

Modern browsers with ES modules are supported; the browser workflow uses no WebAssembly, Pyodide, or server-side Python.

## License

[MIT](LICENSE).
