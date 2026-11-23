"""Build an allowlisted source ZIP; local sessions and binaries cannot enter it."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = {
    "serveur.py",
    "interface.pyw",
    "launcher.py",
    "lancer.bat",
    "lancer-tunnel.bat",
    "ouvrir-interface.bat",
    "README.md",
    "README.en.md",
    "README.fr.md",
    "NOTICE.md",
    "NOTICE.fr.md",
    "NOTICE.html",
    "NOTICE.fr.html",
    "NOTICE.pdf",
    "NOTICE.fr.pdf",
    "README-manches.md",
    "concept.md",
    "architecture-narrative.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "pyproject.toml",
    "requirements-dev.txt",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
}
DIRECTORIES = {
    "eco": {".py"},
    "web": {".js", ".html", ".css", ".svg"},
    "locales": {".json"},
    "tests": {".py"},
    "tools": {".py"},
    "docs": {".md", ".mmd"},
    "docs/screenshots": {".md", ".png"},
    ".github/workflows": {".yml"},
}
# Only screenshots generated with fictional participants by the browser checks.
SCREENSHOTS = {
    "intro-objectif-mobile.png",
    "gestion-etudiants.png",
    "accueil-mobile.png",
    "intro-contexte-mobile.png",
    "intro-roles-mobile.png",
    "negociation-mobile.png",
    "dossier-mobile.png",
    "table-mobile.png",
    "tableau-enseignant.png",
    "trajectoires-enseignant.png",
    "english-company-mobile.png",
    "english-debrief.png",
}


def source_files(root=ROOT):
    files = [root / name for name in sorted(TOP_LEVEL) if (root / name).is_file()]
    for directory, suffixes in DIRECTORIES.items():
        folder = root / directory
        files.extend(p for p in sorted(folder.glob("*")) if p.is_file() and p.suffix in suffixes)
    files.extend(
        root / "docs" / name for name in sorted(SCREENSHOTS) if (root / "docs" / name).is_file()
    )
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(
                "Release sources must be regular files inside the project: " + str(path)
            )
    return files


def build(destination=None, root=ROOT):
    destination = Path(destination) if destination else root / "dist" / "ecosystem-source.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = source_files(root)
    manifest = {
        str(p.relative_to(root).as_posix()): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files
    }
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, "ecosystem/" + path.relative_to(root).as_posix())
        archive.writestr("ecosystem/SHA256SUMS.json", json.dumps(manifest, indent=2) + "\n")
    return destination, manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    path, manifest = build(args.output)
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_name(path.name + ".sha256").write_text(
        f"{checksum}  {path.name}\n", encoding="utf-8", newline="\n"
    )
    print(
        "Created %s (%d files). No local games, preferences, reports or tunnel executables included."
        % (path, len(manifest))
    )
