"""Render the bilingual user manuals as offline HTML and optionally PDF.

Markdown and Playwright are optional development tools; generated guides need
neither Python packages nor the game server to open.
"""

import argparse
import base64
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
CSS = """
:root { color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: #18313f; background: #eef2f4; }
* { box-sizing: border-box; }
body { margin: 0; line-height: 1.65; font-size: 16px; }
.masthead { background: #10232f; color: #f4f8fa; padding: 22px max(24px, calc((100vw - 980px)/2)); display: flex; gap: 24px; flex-wrap: wrap; align-items: center; justify-content: space-between; }
.brand { font-size: 25px; font-weight: 750; letter-spacing: -.8px; }
.brand span { color: #c7e89e; }
.masthead nav { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.masthead a { color: #d7edf5; }
button { cursor: pointer; background: #c7e89e; color: #162c24; border: 0; border-radius: 5px; font: inherit; font-size: 14px; font-weight: 650; padding: 9px 14px; }
main { max-width: 980px; margin: 32px auto; background: white; border: 1px solid #dbe3e8; border-radius: 8px; padding: 42px 48px; }
h1, h2, h3 { color: #102b3a; line-height: 1.25; scroll-margin-top: 20px; }
h1 { font-size: 36px; letter-spacing: -1px; margin: 0 0 22px; }
h2 { font-size: 25px; margin: 42px 0 18px; padding-top: 22px; border-top: 1px solid #dbe3e8; }
h3 { font-size: 20px; margin-top: 28px; }
p { margin: 14px 0; }
a { color: #11627e; text-decoration-thickness: 1px; text-underline-offset: 3px; }
a:focus-visible, button:focus-visible { outline: 3px solid #1886ad; outline-offset: 4px; }
li { margin: 8px 0; }
table { width: 100%; border-collapse: collapse; font-size: 14px; line-height: 1.55; margin: 22px 0; }
th, td { border: 1px solid #d7e1e6; padding: 11px 13px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { background: #eaf2f5; color: #102b3a; }
tbody tr:nth-child(even) { background: #f8fafb; }
td:first-child { min-width: 135px; }
pre { background: #10232f; color: #eff8fb; padding: 18px; border-radius: 5px; overflow-x: auto; font-size: 13px; line-height: 1.6; }
code { font-family: Consolas, "Liberation Mono", monospace; font-size: .88em; background: #edf3f5; padding: .12em .3em; border-radius: 3px; overflow-wrap: anywhere; }
pre code { background: transparent; padding: 0; color: inherit; }
img { max-width: 100%; height: auto; border: 1px solid #c7d5dc; border-radius: 5px; display: block; margin: 22px 0; }
.toc { background: #eff5f7; padding: 18px 24px; border-left: 4px solid #377e96; margin: 26px 0; }
.toc > ul { columns: 2; padding-left: 20px; margin: 0; }
.toc li { break-inside: avoid; margin: 5px 0; font-size: 14px; }
.toc a { text-decoration: none; }
footer { max-width: 980px; margin: 0 auto 32px; padding: 0 24px; font-size: 13px; color: #526c7a; }
@media (max-width: 650px) { main { margin: 0; padding: 28px 20px; border: 0; border-radius: 0; } h1 { font-size: 30px; } table { font-size: 12px; } th,td { padding: 8px; } td:first-child { min-width: 95px; } .toc > ul { columns: 1; } .masthead { padding: 18px 20px; } }
@page { size: A4; margin: 16mm 15mm 18mm; }
@media print {
  :root, body { background: white; color: #172f3c; font-size: 10pt; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .screen-only, .masthead nav { display: none; }
  .masthead { background: white; color: #10232f; padding: 0 0 12px; border-bottom: 2px solid #10232f; }
  .brand { font-size: 19pt; } .brand span { color: #3e7637; }
  main { max-width: none; border: 0; margin: 0; padding: 20px 0 0; }
  h1 { font-size: 23pt; } h2 { font-size: 16pt; margin-top: 23px; padding-top: 15px; break-after: avoid; } h3 { break-after: avoid; }
  p { orphans: 3; widows: 3; }
  table { font-size: 8.5pt; } th,td { padding: 7px; } thead { display: table-header-group; } tr { break-inside: avoid; }
  pre { white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid; font-size: 8pt; }
  img { max-height: 125mm; width: auto; max-width: 100%; break-inside: avoid; }
  .toc { break-inside: avoid; } .toc > ul { columns: 2; } .toc li { font-size: 9pt; }
  footer { margin: 18px 0 0; padding: 0; font-size: 8pt; }
}
"""


def render(language):
    stem = "NOTICE" if language == "en" else "NOTICE.fr"
    source = (ROOT / (stem + ".md")).read_text(encoding="utf-8")
    renderer = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc"],
        extension_configs={"toc": {"toc_depth": "2-2"}},
    )
    content = renderer.convert(source)
    content = content.replace("<h2", renderer.toc + "\n<h2", 1)
    # The offline manual's language selector should keep users in rendered HTML.
    content = content.replace('href="NOTICE.md"', 'href="NOTICE.html"').replace(
        'href="NOTICE.fr.md"', 'href="NOTICE.fr.html"'
    )

    def embed_image(match):
        path = (ROOT / match[1]).resolve()
        if not path.is_relative_to(ROOT.resolve()) or path.suffix != ".png":
            raise ValueError("Manual images must be local PNG files inside the project")
        return (
            'src="data:image/png;base64,'
            + base64.b64encode(path.read_bytes()).decode("ascii")
            + '"'
        )

    content = re.sub(r'src="([^"]+)"', embed_image, content)
    title = "ECOSYSTEM — user guide" if language == "en" else "ECOSYSTEM — notice d’utilisation"
    print_label = "Print / Save as PDF" if language == "en" else "Imprimer / Enregistrer en PDF"
    nav_label = "Language and printing" if language == "en" else "Langue et impression"
    footer = (
        "Offline user guide · Current narrative campaign · GPL-3.0-only · Demo images use fictional participants."
        if language == "en"
        else "Notice hors connexion · Campagne narrative courante · GPL-3.0-only · Les captures utilisent des participants fictifs."
    )
    page = f'''<!doctype html>
<html lang="{language}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head>
<body>
<header class="masthead"><div class="brand">ecosystem<span>.</span></div>
<nav aria-label="{nav_label}"><a href="NOTICE.html" lang="en">English</a><a href="NOTICE.fr.html" lang="fr">Français</a><button type="button" onclick="window.print()">{print_label}</button></nav></header>
<main>{content}</main><footer>{footer}</footer>
</body></html>
'''
    path = ROOT / (stem + ".html")
    path.write_text(page, encoding="utf-8")
    return path


def build(pdf=False):
    pages = [render(language) for language in ("en", "fr")]
    if pdf:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for path in pages:
                page = browser.new_page()
                page.goto(path.as_uri(), wait_until="networkidle")
                # Printed local links would disclose the build machine's path
                # and would not work on another computer. Keep web references
                # and internal section navigation; HTML retains relative links.
                page.evaluate("""() => document.querySelectorAll('a[href]').forEach(a => {
                  const href = a.getAttribute('href');
                  if (!href.startsWith('#') && !/^https?:/.test(href)) a.removeAttribute('href');
                })""")
                page.pdf(
                    path=str(path.with_suffix(".pdf")),
                    print_background=True,
                    prefer_css_page_size=True,
                )
                page.close()
            browser.close()
    return pages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf", action="store_true", help="also render PDFs with Playwright Chromium"
    )
    args = parser.parse_args()
    for path in build(args.pdf):
        print(path.name + (" + PDF" if args.pdf else ""))
