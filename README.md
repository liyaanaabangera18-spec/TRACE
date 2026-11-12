# TRACE · Python investigation room

Preserves TRACE's navy/blue palette, original SVG logo, Petal & Crumb and Harbour Bakes. Python performs the review logic; your browser displays the interface. No external packages, accounts or internet connection are required once Python is installed.

## Run in VS Code

**Windows shortcut:** after extracting the ZIP, double-click `Start_TRACE.bat`. It finds a working Python installation and opens the website in your browser. Keep the launcher window open while using TRACE. If port 8000 is occupied, TRACE chooses another free port automatically.

1. Extract the ZIP. Open the extracted **TRACE_Python** folder in VS Code.
2. Install Python 3.10 or newer if needed. Choose its interpreter in VS Code.
3. Open Terminal → New Terminal. Run `python app.py` (on Windows, `py app.py` also works if the Python launcher is installed).
4. Open **http://127.0.0.1:8000** in your browser. Keep the terminal running. Stop with Ctrl+C.

Do not double-click `trace.html`: the interface uses the Python API. If `python` opens the Microsoft Store or is unavailable, install Python and reopen the terminal. If port 8000 is occupied, TRACE chooses another free port automatically.

## Try the investigation

- Each bakery has a separate 60-minute analyst budget. Eight checks cost 110 minutes in total, so choose the combination that resolves the most important uncertainties.
- Evidence checks cover payment patterns, fulfilled orders, complaints, checkout routes, shared device/account links, online activity, settlement destinations and merchant responses.
- The payment-pattern view uses 1,000 reproducible synthetic processor records. It shows time, amount and payer distributions, overlaps between signals, and 12 priority TX references with order and settlement fields. Thresholds are prompts, not fraud scores.
- Each checked finding names its synthetic source, what that source can establish and what it cannot. The decision stage gives a working conclusion and specific next steps; the case report retains the transaction reference, source register, pattern breakdown and open questions.
- Select a response on the five-level ladder: monitor quietly, ask the merchant, verify operations, limit a suspicious flow, or send the case to an analyst. Stronger actions require more evidence; verified checkout evidence can directly unlock analyst review.
- Choose a response, read its case-specific consequence, then record it. The report retains the selected response, inspected evidence, recommendation, open questions and analyst effort.
- Open Scenario lab. Give Petal a verified prohibited checkout, apply the scenario and run checkout verification. Its recommendation changes. Set Harbour's fulfilled orders to 95% and remove complaint/checkout evidence; inspect payments and verify orders. Its recommendation changes too.
- Restart review resets checks for that bakery; it keeps scenario inputs. Restore original scenario resets both. Decision history stays until cleared. Download the JSON case report before clearing browser storage.

##  The reference

The reference contributes a staged investigation, scarce review time, linked payment references, multiple evidence sources and a response ladder with consequences. This  avoids hard-coded fraud probabilities and claimed money saved. Recommendations depend on inspected evidence, not merchant names. The scenario lab changes the underlying synthetic facts, without granting that knowledge automatically to the reviewer. No onward bank-transfer visibility is assumed.

## Limits and assumptions

This is a transparent teaching prototype, not a trained detection model or production integration. One thousand reproducible fictional payment records are generated per scenario. Only 12 are displayed; payment metrics use all 1,000. Percentage controls construct a simplified dataset, not an empirically representative distribution. Fulfilment records, complaints and checkout findings are simulated evidence registers. An actual implementation would need authorised sources and verified evidence provenance.

The 80% fulfilment rule and payment-pattern thresholds are illustrative design choices, not validated policy. Payment patterns prompt questions; they never independently establish prohibited activity. Verified checkout evidence takes priority over a legitimate-order explanation because mixed activity can occur. An unchecked source is unknown, not absent. There are no financial loss forecasts, confidence percentages, real account restrictions or automatic referrals.

Decision consequences describe workflow effects, not measured future outcomes. A human must authorise any real-world intervention. Browser history is local to this browser and machine; this app has no multi-user authentication, central audit store or deployment hardening. It binds only to localhost.

## Files and checks

- `app.py`: local HTTP server and API.
- `engine.py`: synthetic records, evidence selection, recommendation rules and input checks.
- `trace.html`: six-stage responsive investigation, response ladder and scenario controls.
- `logo.svg`: unchanged TRACE logo from the previous project.
- `test_trace.py`: behaviour and HTTP integration tests. Run `python -m unittest -v`.


