"""One-time/refactoring aid: mark translated UI literals without touching data.

Requires the optional development packages in requirements-dev.txt.
Run after adding French phrases to locales/en.json. Review the changes.
"""

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eco.i18n import translate


def javascript():
    from tree_sitter import Language, Parser
    import tree_sitter_javascript

    parser = Parser(Language(tree_sitter_javascript.language()))
    for name in ("campagne-joueur.js", "campagne-hote.js", "intro.js", "visuels.js", "debrief.js"):
        path = ROOT / "web" / name
        raw = path.read_bytes()
        edits = []

        def visit(node, raw=raw, edits=edits):
            if (
                node.parent
                and node.parent.type == "arguments"
                and node.parent.parent.type == "call_expression"
                and raw[node.parent.parent.start_byte : node.parent.start_byte] == b"EcoI18n.t"
            ):
                return
            if node.type == "string":
                source = raw[node.start_byte : node.end_byte].decode("utf-8")
                try:
                    value = ast.literal_eval(source)
                except (ValueError, SyntaxError):
                    return
                if value == "fr-FR":
                    edits.append((node.start_byte, node.end_byte, b"EcoI18n.locale"))
                elif translate(value, "en") != value:
                    if node.parent.type == "pair" and node == node.parent.child_by_field_name(
                        "key"
                    ):
                        return
                    edits.append(
                        (node.start_byte, node.end_byte, ("EcoI18n.t(" + source + ")").encode())
                    )
                return
            if node.type == "string_fragment" and node.parent.type == "template_string":
                value = raw[node.start_byte : node.end_byte].decode("utf-8")
                if translate(value, "en") != value:
                    replacement = "${EcoI18n.t(" + json.dumps(value, ensure_ascii=False) + ")}"
                    edits.append((node.start_byte, node.end_byte, replacement.encode()))
                return
            for child in node.children:
                visit(child)

        visit(parser.parse(raw).root_node)
        for start, end, replacement in sorted(edits, reverse=True):
            raw = raw[:start] + replacement + raw[end:]
        if parser.parse(raw).root_node.has_error:
            raise ValueError("Translation introduced a syntax error: " + name)
        path.write_bytes(raw)
        print(name, len(edits), "presentation literals")


def desktop():
    path = ROOT / "eco" / "desktop.py"
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    tree = ast.parse(raw)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "DesktopApp")
    edits = []
    protected = {
        id(child)
        for node in ast.walk(cls)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_t"
        for child in ast.walk(node)
    }
    for node in ast.walk(cls):
        if (
            id(node) not in protected
            and isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and translate(node.value, "en") != node.value
        ):
            if node.value == "Automatique":
                continue
            start, end = (
                offsets[node.lineno - 1] + node.col_offset,
                offsets[node.end_lineno - 1] + node.end_col_offset,
            )
            edits.append((start, end, b"_t(" + raw[start:end] + b")"))
    for start, end, replacement in sorted(edits, reverse=True):
        raw = raw[:start] + replacement + raw[end:]
    ast.parse(raw)
    path.write_bytes(raw)
    print("desktop", len(edits), "presentation literals")


if __name__ == "__main__":
    javascript()
    # Desktop literals only need annotation once; do not nest _t calls.
    if "--desktop" in sys.argv:
        desktop()
