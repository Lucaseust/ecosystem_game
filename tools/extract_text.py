"""Developer aid: list presentation literals using the JavaScript syntax tree.

Requires optional tree-sitter and tree-sitter-javascript development packages.
Never needed to run the game.
"""

import ast
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ["campagne-joueur.js", "campagne-hote.js", "intro.js", "visuels.js", "debrief.js"]


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

    def handle_starttag(self, tag, attrs):
        self.parts.extend(
            v for k, v in attrs if v and k in {"title", "aria-label", "placeholder", "alt"}
        )


def fragments():
    from tree_sitter import Language, Parser
    import tree_sitter_javascript

    parser = Parser(Language(tree_sitter_javascript.language()))
    found = {}
    for filename in FILES:
        raw = (ROOT / "web" / filename).read_bytes()
        tree = parser.parse(raw)
        if tree.root_node.has_error:
            raise ValueError("JavaScript parse error: " + filename)

        def visit(node, raw=raw, filename=filename):
            if node.type in {"string", "string_fragment"} and (
                node.type == "string" or node.parent.type == "template_string"
            ):
                text = raw[node.start_byte : node.end_byte].decode("utf-8")
                if node.type == "string":
                    try:
                        text = ast.literal_eval(text)
                    except (ValueError, SyntaxError):
                        text = text[1:-1]
                else:
                    text = text.replace("\\`", "`").replace("\\n", "\n")
                parts = Text()
                if "<" in text and ">" in text:
                    try:
                        parts.feed(text)
                    except Exception:
                        parts.parts = [text]
                else:
                    parts.parts = [text.strip()]
                for part in parts.parts:
                    if re.search(r"[A-Za-zÀ-ÿ]{2}", part) and not re.fullmatch(
                        r"[\w#./:=;(),\-\s]+", part, flags=re.ASCII
                    ):
                        found.setdefault(part, []).append(filename)
                    elif re.search(r"\s|[À-ÿ]", part) and re.search(r"[A-Za-zÀ-ÿ]{2}", part):
                        found.setdefault(part, []).append(filename)
            if node.type != "string":
                for child in node.children:
                    visit(child)

        visit(tree.root_node)
    return found


if __name__ == "__main__":
    print(json.dumps(list(fragments()), ensure_ascii=False, indent=2))
