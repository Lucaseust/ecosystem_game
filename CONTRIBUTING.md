# Working on ECOSYSTEM

The playable application uses Python's standard library and local HTML/CSS/JavaScript. Development tools are optional. Install `requirements-dev.txt` only when changing or testing code; no build step is required to play.

Run from the project folder:

```sh
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m unittest discover -s tests -p "test_*.py"
python tests/test_partie.py
python tests/simuler_campagne.py
python -m playwright install chromium
python tests/verifier_campagne.py
python tests/verifier_anglais.py
python tools/build_release.py
```

The GitHub presentation lives in `README.md` (English) and `README.fr.md`. User manuals are authored in `NOTICE.md` and `NOTICE.fr.md`; the launcher opens their offline HTML editions. After editing a manual, regenerate the HTML and PDF files with `python tools/build_guides.py --pdf`. Markdown is an optional development dependency, not a requirement for reading the generated guides. Regenerate the bilingual public documentation screenshots with `python tools/capture_readme.py`; it creates isolated sessions with fictional participants. Keep actual classroom images and saves outside `docs/screenshots`.

The browser checks create their own temporary server and data folder. Screenshots use fictional participants. Core checks exercise the real launcher-owned server, consent, transaction rollback, confidentiality, accounts, HTTP input validation and localisation. The simulation compares four policies under the same 80 seeds; it is a balance regression check, not evidence of universal game balance.

Python formatting and lint settings are in `pyproject.toml`. Keep new JavaScript readable, use explicit blocks, and syntax-check it in a browser. Avoid unrelated changes to the archived engine when changing the current campaign. GitHub Actions defines core checks for Windows, Linux and macOS on Python 3.10 and 3.14, plus browser checks; these jobs run after the repository is published.

`eco/campaign.py` owns rules and transactions. `serveur.py` handles HTTP and process lifecycle; `eco/http_security.py` owns bounded request validation. `eco/store.py` writes atomically. Campaign decisions and initial state are written synchronously while holding the game lock. The archived engine has a delayed saver that also holds the game lock through the write. Do not write older snapshots after releasing that lock.

Amounts in the engine and raw exports are integer hundredths of a credit. Revenue allocations and funding use integer hundredths of a credit. A fresh unanimous agreement is required each quarter; disagreement produces no quarter cash flows. Preserve the existing accounting identities, consent and idempotency checks. Validate the quote again at commitment. Paid investments remain paid; profiles contribute only while their original company supplies the relevant activity. Keep historical journal entries intact when fixing subsequent behaviour.

French is the authoring language. `locales/en.json` contains English presentation phrases. JavaScript calls `EcoI18n.t` on static author-written text before inserting player values; `eco/i18n.py` translates copied API views at the HTTP boundary. Protocol keys, enums, numeric amounts, identities and player messages stay unchanged. Offline reports embed the same runtime and catalogue. Do not translate an assembled HTML string containing user input. When adding copy, add a catalogue entry and the relevant `EcoI18n.t` or launcher `_t` call. `tools/extract_text.py` and `tools/annotate_i18n.py` are optional refactoring aids requiring the tree-sitter development packages; review their changes and run both browser checks.

Use the release builder's allowlist for distribution. It includes GPL-3.0-only licensing and a SHA-256 file manifest, and excludes local sessions, preferences, training exports and cloudflared. New runtime assets must be included in that allowlist. Test the extracted ZIP, rather than relying only on the working folder. Do not commit names, access credentials or real classroom exports.
