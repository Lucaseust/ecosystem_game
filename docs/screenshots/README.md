# Documentation screenshots

These are real application captures from isolated demo sessions with fictional participants (`Demo 01` to `Demo 10`). The script never reads classroom saves or launcher preferences, and never opens a public tunnel. Its temporary instructor credentials are not shown in the images. Displayed outcomes illustrate one session and are not a recommended strategy.

Regenerate from the project root after installing the optional development tools and Playwright Chromium:

```sh
python tools/capture_readme.py
```

The script captures the briefing, private company view, negotiation table, instructor dashboard, enlarged join QR and debrief in English and French. It stops its demo server and discards the temporary saves when finished.
