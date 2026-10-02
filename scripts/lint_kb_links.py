#!/usr/bin/env python3
"""Check local Markdown destinations in .claude/kb, without network access.

Run from the repository root: python3 scripts/lint_kb_links.py
Exit codes: 0 = clean, 1 = broken links, 2 = invocation or operational error.
The parser deliberately covers Markdown links, not HTML or wiki syntax.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import dataclass
import errno
import html
import os
from pathlib import Path
import re
import stat
import string
import sys
from urllib.parse import unquote


_ESCAPE = re.compile(r"\\([" + re.escape(string.punctuation) + r"])")
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


@dataclass(frozen=True)
class Link:
    position: int
    target: str


def _unescape(text: str) -> str:
    return html.unescape(_ESCAPE.sub(r"\1", text))


def _label(text: str) -> str:
    return " ".join(_unescape(text).split()).casefold()


def _hide(text: str) -> str:
    """Mask ignored syntax while preserving offsets and newline positions."""
    return "".join("\n" if char == "\n" else "\0" for char in text)


def _blocks(text: str) -> str:
    lines = []
    fence = None
    comment = False
    offset = 0
    code_until = 0
    list_indents = []
    previous_quote_depth = 0
    for line in text.splitlines(keepends=True):
        # Remove container syntax for block recognition, retaining its width
        # below so every link still points to its original source position.
        content = line
        quote_depth = 0
        while prefix := re.match(r" {0,3}>[ \t]?", content):
            quote_depth += 1
            content = content[prefix.end():]
        if quote_depth != previous_quote_depth:
            list_indents.clear()
        previous_quote_depth = quote_depth
        indentation = len(content) - len(content.lstrip(" "))
        if content.strip():
            while list_indents and indentation < list_indents[-1]:
                list_indents.pop()
        list_indent = list_indents[-1] if list_indents else 0
        content = content[min(indentation, list_indent):]
        if fence and (quote_depth < fence[2] or
                      (line.strip() and list_indent < fence[3])):
            fence = None
        if fence:
            if quote_depth == fence[2] and re.fullmatch(
                    r" {0,3}" + re.escape(fence[0]) +
                    r"{" + str(fence[1]) + r",}[ \t]*\n?", content):
                fence = None
            lines.append(_hide(line))
            offset += len(line)
            continue
        if not comment and code_until <= offset:
            # A list item's first line can open a fence or a definition;
            # continuation lines use the indentation established by its marker.
            while marker := re.match(r" {0,3}(?:[-+*]|[0-9]{1,9}[.)])([ \t]{1,4})(?=\S)", content):
                list_indent += marker.end()
                list_indents.append(list_indent)
                content = content[marker.end():]
            opening = re.match(r" {0,3}(`{3,}|~{3,})(.*)", content)
            if opening and not (opening[1][0] == "`" and "`" in opening[2]):
                fence = (opening[1][0], len(opening[1]), quote_depth, list_indent)
                lines.append(_hide(line))
                offset += len(line)
                continue
            if content.startswith(("    ", "\t")):
                lines.append(_hide(line))
                offset += len(line)
                continue
        # Spaces neutralize quote/list markers in definitions and multiline
        # labels without changing offsets. Indented code was masked above.
        line = " " * (len(line) - len(content)) + content
        # Comments can span lines and can share a line with real links.
        result = ""
        index = 0
        while index < len(line):
            if code_until > offset + index:
                end = min(len(line), code_until - offset)
                result += line[index:end]
                index = end
                continue
            if comment:
                end = line.find("-->", index)
                end = len(line) if end < 0 else end + 3
                result += _hide(line[index:end])
                comment = not line[index:end].endswith("-->")
            else:
                token = re.search(r"<!--|`+|\\[" + re.escape(string.punctuation) + "]", line[index:])
                if token is None:
                    result += line[index:]
                    break
                end = index + token.start()
                result += line[index:end]
                if token[0] == "<!--":
                    comment = True
                else:
                    if token[0].startswith("`"):
                        code_until = _code_end(text, offset + end) or 0
                    result += token[0]
                    end += len(token[0])
            index = end
        lines.append(result)
        offset += len(line)
    return "".join(lines)


def _spaces(text: str, index: int) -> int:
    while index < len(text) and text[index] in " \t\n":
        index += 1
    return index


def _destination(text: str, index: int) -> tuple[str, int] | None:
    start = index
    if index < len(text) and text[index] == "<":
        index += 1
        start = index
        while index < len(text):
            char = text[index]
            if char == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
                index += 2
                continue
            if char == ">":
                return text[start:index], index + 1
            if char in "<\n\0":
                return None
            index += 1
        return None
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
            index += 2
            continue
        if char.isspace() or char == "\0":
            break
        if char == "(":
            depth += 1
        elif char == ")":
            if not depth:
                break
            depth -= 1
        elif char == "<":
            return None
        index += 1
    if depth:
        return None
    return text[start:index], index


def _title(text: str, index: int) -> int | None:
    if index >= len(text) or text[index] not in "\"'(":
        return None
    closing = ")" if text[index] == "(" else text[index]
    index += 1
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
            index += 2
            continue
        if text[index] == closing:
            return index + 1
        if text[index] == "\0" or (closing == ")" and text[index] == "("):
            return None
        index += 1
    return None


def _definitions(text: str) -> tuple[str, dict[str, str]]:
    definitions = {}
    spans = []
    code_spans = []
    index = 0
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
            index += 2
        elif text[index] == "`":
            end = _code_end(text, index)
            if end is not None:
                code_spans.append((index, end))
            index = end if end is not None else index + len(re.match(r"`+", text[index:])[0])
        else:
            index += 1
    pattern = re.compile(r"^[ \t]*\[((?:\\.|[^\[\]\\\0])+)\]:[ \t]*", re.M)
    for match in pattern.finditer(text):
        # Reference labels may span lines, but cannot cross a blank line.
        if re.search(r"\n[ \t]*\n", match[1]):
            continue
        if spans and match.start() < spans[-1][1]:
            continue
        if any(start <= match.start() < end for start, end in code_spans):
            continue
        start = _spaces(text, match.end())
        parsed = _destination(text, start)
        if parsed is None:
            continue
        target, end = parsed
        if end == start:
            continue
        after = _spaces(text, end)
        title = _title(text, after) if after > end else None
        if title is not None:
            end = title
        # A definition must occupy the remainder of its line.
        line_end = text.find("\n", end)
        if line_end < 0:
            line_end = len(text)
        if text[end:line_end].strip(" \t"):
            continue
        label = _label(match[1])
        if label:
            definitions.setdefault(label, target)
            spans.append((match.start(), line_end))
    masked = list(text)
    for start, end in spans:
        masked[start:end] = _hide(text[start:end])
    return "".join(masked), definitions


def _code_end(text: str, index: int) -> int | None:
    run = re.match(r"`+", text[index:])[0]
    # Only a delimiter with the exact same number of backticks closes a span.
    closing = re.search(r"(?<!`)" + run + r"(?!`)", text[index + len(run):])
    return index + len(run) + closing.end() if closing else None


def _bracket_end(text: str, index: int) -> int | None:
    depth = 1
    index += 1
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
            index += 2
            continue
        if char == "`":
            end = _code_end(text, index)
            if end is not None:
                index = end
                continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if not depth:
                return index
        elif char == "\0":
            return None
        index += 1
    return None


def _inline(text: str, index: int) -> tuple[str, int] | None:
    start = _spaces(text, index + 1)
    parsed = _destination(text, start)
    if parsed is None:
        return None
    target, end = parsed
    after = _spaces(text, end)
    if after > end and after < len(text) and text[after] in "\"'(":
        title = _title(text, after)
        if title is None:
            return None
        after = _spaces(text, title)
    if after < len(text) and text[after] == ")":
        return target, after + 1
    return None


def _links(text: str, definitions: dict[str, str], offset: int = 0) -> list[Link]:
    links = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
            index += 2
            continue
        if char == "`":
            end = _code_end(text, index)
            index = end if end is not None else index + len(re.match(r"`+", text[index:])[0])
            continue
        if char == "<":
            # HTML tags (including quoted attributes) and autolinks are opaque.
            tag = re.match(r'''<(?:[^<>"']|"[^"]*"|'[^']*')*>''', text[index:])
            if tag:
                index += tag.end()
                continue
        if text.startswith("[[", index):
            end = text.find("]]", index + 2)
            if end >= 0:
                index = end + 2
                continue
        bracket = index + 1 if text.startswith("![", index) else index
        if text[bracket:bracket + 1] != "[":
            index += 1
            continue
        close = _bracket_end(text, bracket)
        if close is None:
            index += 1
            continue
        label = text[bracket + 1:close]
        end = close + 1
        parsed = _inline(text, end) if text[end:end + 1] == "(" else None
        if parsed is None:
            reference = label
            if text[end:end + 1] == "[":
                ref_end = _bracket_end(text, end)
                if ref_end is not None:
                    reference = text[end + 1:ref_end] or label
                    end = ref_end + 1
            target = definitions.get(_label(reference))
            if target is not None:
                parsed = target, end
        if parsed is not None:
            target, end = parsed
            links.append(Link(offset + index, target))
            # Images in a link's label are occurrences in their own right.
            links.extend(_links(label, definitions, offset + bracket + 1))
            index = end
        else:
            index += 1
    return links


def markdown_links(text: str) -> list[Link]:
    """Return destinations per use, keeping the original spelling and offset."""
    text, definitions = _definitions(_blocks(text))
    return sorted(_links(text, definitions), key=lambda link: link.position)


def broken_target(root: Path, source: Path, target: str) -> bool:
    destination = _unescape(target)
    if destination.startswith(("#", "//")) or _SCHEME.match(destination):
        return False
    path = unquote(re.split(r"[?#]", destination, maxsplit=1)[0])
    if "\0" in path:
        return True
    candidate = Path(path)
    if candidate.is_absolute():
        return True
    try:
        resolved = (source.parent / candidate).resolve()
        if not resolved.is_relative_to(root):
            return True
        mode = resolved.stat().st_mode
        return not (stat.S_ISREG(mode) or stat.S_ISDIR(mode))
    except (FileNotFoundError, NotADirectoryError, RuntimeError):
        # RuntimeError is raised for symlink loops on Python <= 3.12.
        return True
    except OSError as error:
        if error.errno == errno.ELOOP:
            return True
        raise


def sources(root: Path) -> list[Path]:
    kb = root / ".claude/kb"
    if kb.is_symlink() or not kb.is_dir():
        raise OSError(".claude/kb must be an existing, regular directory")

    def fail(error: OSError) -> None:
        raise error

    found = []
    for directory, dirs, files in os.walk(kb, followlinks=False, onerror=fail):
        dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
        for name in files:
            path = Path(directory) / name
            if path.suffix in {".md", ".MD"} and stat.S_ISREG(path.lstat().st_mode):
                found.append(path)
    return sorted(found, key=lambda path: path.relative_to(root).as_posix())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    diagnostics = []
    try:
        root = Path.cwd().resolve()
        for source in sources(root):
            text = source.read_text(encoding="utf-8")
            newlines = [match.start() for match in re.finditer("\n", text)]
            for link in markdown_links(text):
                if broken_target(root, source, link.target):
                    line = bisect_right(newlines, link.position) + 1
                    diagnostics.append(f"{source.relative_to(root).as_posix()}:{line}: {link.target}")
    except (OSError, UnicodeError) as error:
        print(f"lint_kb_links: {error}", file=sys.stderr)
        return 2
    for diagnostic in diagnostics:
        print(diagnostic)
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
