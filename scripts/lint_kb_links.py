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
# Recognize Markdown's raw HTML tag grammar, including quoted attributes.
# Arbitrary angle-bracket prose (e.g. "2 < 3 and [x](y) > 1") is not HTML.
_HTML_TAG = re.compile(
    r"</[A-Za-z][A-Za-z0-9-]*[ \t\n]*>"
    r"|<[A-Za-z][A-Za-z0-9-]*"
    r"(?:[ \t\n]+[A-Za-z_:][A-Za-z0-9_.:-]*"
    r'''(?:[ \t\n]*=[ \t\n]*(?:[^ \t\n\"'=<>`]+|"[^"]*"|'[^']*'))?)*'''
    r"[ \t\n]*/?>"
)
_AUTOLINK = re.compile(
    r"<[A-Za-z][A-Za-z0-9+.-]{1,31}:[^\x00-\x20<>]*>"
    r"|<[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*>"
)


@dataclass(frozen=True)
class Link:
    position: int
    target: str


def _unescape(text: str) -> str:
    return html.unescape(_ESCAPE.sub(r"\1", text))


def _label(text: str) -> str:
    # Escapes and entities are literal label content, unlike destinations.
    return " ".join(text.split()).casefold()


def _hide(text: str, marker: str = "\0") -> str:
    """Mask ignored syntax while preserving offsets and newline positions."""
    return "".join("\n" if char == "\n" else marker for char in text)


def _blocks(text: str) -> str:
    lines = []
    fence = None
    comment = False
    offset = 0
    code_until = 0
    literal_suffixes = {}
    paragraph = False
    containers = []
    for line in text.splitlines(keepends=True):
        # Remove container syntax for block recognition, retaining its width
        # below so every link still points to its original source position.
        content = line
        # Match existing containers in nesting order: a quote may contain a
        # list, and a list may contain a quote (and so on).
        matched = 0
        for kind, width in containers:
            if kind == "quote":
                prefix = re.match(r" {0,3}>[ \t]?", content)
                if prefix is None:
                    break
                content = content[prefix.end():]
            else:
                indentation = len(content) - len(content.lstrip(" "))
                if content.strip() and indentation < width:
                    break
                content = content[min(indentation, width):]
            matched += 1
        if matched < len(containers):
            del containers[matched:]
            paragraph = False
        if fence and matched < fence[2]:
            fence = None
        if fence:
            if re.fullmatch(
                    r" {0,3}" + re.escape(fence[0]) +
                    r"{" + str(fence[1]) + r",}[ \t]*\n?", content):
                fence = None
            lines.append(_hide(line))
            paragraph = False
            offset += len(line)
            continue
        if not comment and code_until <= offset:
            # Discover new containers only outside code/comments. A list's
            # continuation indentation is relative to its enclosing container.
            while True:
                quote = re.match(r" {0,3}>[ \t]?", content)
                # With more than four padding spaces, only the first belongs
                # to the marker; the remainder introduces indented code.
                marker = quote or re.match(
                    r" {0,3}(?:[-+*]|[0-9]{1,9}[.)])"
                    r"(?:[ \t]{1,4}(?=\S)| (?= {4}))", content)
                if marker is None:
                    break
                paragraph = False
                containers.append(("quote" if quote else "list", marker.end()))
                content = content[marker.end():]
            opening = re.match(r" {0,3}(`{3,}|~{3,})(.*)", content)
            if opening and not (opening[1][0] == "`" and "`" in opening[2]):
                fence = (opening[1][0], len(opening[1]), len(containers))
                lines.append(_hide(line))
                paragraph = False
                offset += len(line)
                continue
            # Indented code cannot interrupt an open paragraph.
            if not paragraph and content.expandtabs(4).startswith("    "):
                lines.append(_hide(line))
                offset += len(line)
                continue
        # A Setext underline closes the preceding paragraph as a heading.
        # Keep that boundary for every later inline/definition pass, including
        # inside containers whose prefixes will otherwise become spaces.
        if not comment and paragraph and re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*\n?", content):
            lines.append(_hide(line))
            paragraph = False
            offset += len(line)
            continue
        # ATX headings end on this line, including inside quotes/lists. Bound
        # inline parsing before container prefixes are neutralized below.
        heading = not comment and re.match(r" {0,3}#{1,6}(?:[ \t]|$)", content) is not None
        inline_source = text[:offset + len(line)] if heading else text
        # Spaces neutralize quote/list markers in definitions and multiline
        # labels without changing offsets. Indented code was masked above.
        line = " " * (len(line) - len(content)) + content
        # Comments can span lines and can share a line with real links.
        result = ""
        index = 0
        while index < len(line):
            if not comment and offset + index in literal_suffixes:
                code_until = literal_suffixes.pop(offset + index)
            if code_until > offset + index:
                end = min(len(line), code_until - offset)
                result += line[index:end]
                index = end
                continue
            if comment:
                end = line.find("-->", index)
                end = len(line) if end < 0 else end + 3
                # Comments are inline content, so a surrounding link label
                # may cross them. Keep block boundaries (NUL) distinct.
                result += _hide(line[index:end], "\x01")
                comment = not line[index:end].endswith("-->")
            else:
                # Destinations and titles are literal syntax: comment markers
                # and backticks there must not affect later Markdown. Keep
                # scanning the label itself so its code/comments still work.
                position = offset + index
                # A complete HTML tag is opaque even when a quoted attribute
                # contains comment markers or backticks. Preserve it for the
                # inline passes, including when it spans multiple lines.
                if line[index] == "<":
                    tag = _HTML_TAG.match(inline_source, position)
                    if tag:
                        code_until = tag.end()
                        continue
                if line[index] == "[":
                    close = _bracket_end(inline_source, position, containers)
                    if close is not None:
                        suffix = close + 1
                        if text[suffix:suffix + 1] == "(":
                            parsed = _inline(inline_source, suffix)
                            if parsed is not None:
                                literal_suffixes[suffix] = parsed[1]
                        elif text[suffix:suffix + 1] == ":" and not line[:index].strip():
                            parsed = _definition_value(text, suffix + 1)
                            if parsed is not None:
                                literal_suffixes[suffix] = parsed[1]
                end = index
                if line.startswith("<!--", index):
                    comment = True
                else:
                    end += 1
                    if line[index] == "`":
                        code_until = _code_end(inline_source, position, containers) or 0
                        end = index + len(re.match(r"`+", line[index:])[0])
                    elif line[index] == "\\" and end < len(line) and line[end] in string.punctuation:
                        end += 1
                    result += line[index:end]
            index = end
        # Retain the heading boundary in subsequent inline/definition passes.
        # Replacing its newline preserves offsets; reported line numbers are
        # calculated from the untouched source, not this parser-only mask.
        lines.append(result[:-1] + "\0" if heading and result.endswith("\n") else result)
        visible = result.replace("\0", "").replace("\x01", "").strip()
        # These complete blocks do not leave a paragraph open for the next
        # indented line. Container prefixes have already been neutralized.
        complete_block = not content.expandtabs(4).startswith("    ") and (
            re.match(r"#{1,6}(?:\s|$)", visible)
            or re.fullmatch(r"(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,}", visible)
            or (paragraph and re.fullmatch(r"=+|-+", visible))
            or _definitions(result)[1]
        )
        paragraph = bool(visible) and not complete_block
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
            if char in "<\n\0\x01":
                return None
            index += 1
        return None
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
            index += 2
            continue
        if char.isspace() or char in "\0\x01":
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
        if text[index] in "\0\x01" or (closing == ")" and text[index] == "("):
            return None
        index += 1
    return None


def _definition_value(text: str, index: int) -> tuple[str, int] | None:
    start = _spaces(text, index)
    parsed = _destination(text, start)
    if parsed is None:
        return None
    target, end = parsed
    if end == start:
        return None
    after = _spaces(text, end)
    title = _title(text, after) if after > end else None
    if title is not None:
        end = title
    line_end = text.find("\n", end)
    if line_end < 0:
        line_end = len(text)
    if text[end:line_end].strip(" \t"):
        return None
    return target, line_end


def _definitions(text: str) -> tuple[str, dict[str, str]]:
    definitions = {}
    spans = []
    pattern = re.compile(r"(?:^|(?<=\0))[ \t]*\[((?:\\.|[^\[\]\\\0\x01])+)\]:[ \t]*", re.M)
    index = 0
    while index < len(text):
        if text[index] == "<":
            tag = _HTML_TAG.match(text, index) or _AUTOLINK.match(text, index)
            if tag:
                index = tag.end()
                continue
        # Definitions are block syntax. Consume their literal destinations and
        # titles before looking for inline code, so backticks cannot conceal a
        # subsequent definition. Real code spans are skipped as a whole below.
        match = pattern.match(text, index)
        if match and not re.search(r"\n[ \t]*\n", match[1]):
            parsed = _definition_value(text, match.end())
            label = _label(match[1])
            if parsed is not None and label:
                target, line_end = parsed
                definitions.setdefault(label, target)
                spans.append((index, line_end))
                index = line_end
                continue
        if text[index] == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
            index += 2
        elif text[index] == "`":
            end = _code_end(text, index)
            index = end if end is not None else index + len(re.match(r"`+", text[index:])[0])
        else:
            # Inline links have literal destinations/titles too. Their labels
            # are consumed here only for definition discovery; _links handles
            # the occurrences (including nested images) in the later pass.
            if text[index] == "[":
                close = _bracket_end(text, index)
                if close is not None and text[close + 1:close + 2] == "(":
                    parsed = _inline(text, close + 1)
                    if parsed is not None:
                        index = parsed[1]
                        continue
            index += 1
    masked = list(text)
    for start, end in spans:
        masked[start:end] = _hide(text[start:end])
    return "".join(masked), definitions


def _code_end(text: str, index: int, containers=()) -> int | None:
    run = re.match(r"`+", text[index:])[0]
    start = index + len(run)
    # _blocks calls this before fences have been masked. A fence interrupts
    # a paragraph even if a preceding code delimiter is still unmatched; a
    # backtick inside that block must never close the preceding inline span.
    # Include container prefixes and reject backtick fences with backticks in
    # their info string, just as _blocks does when recognizing the opening.
    # Continuation indentation belongs to its list container, so a fence may
    # be more than three columns from the physical start of the source line.
    prefixes = [""]
    for kind, width in containers:
        prefixes.append(prefixes[-1] + (r" {0,3}>[ \t]?" if kind == "quote" else " " * width))
    prefix = "(?:" + "|".join(prefixes) + ")"
    fence = (r"\n" + prefix + r" {0,3}(?:(?:>[ \t]?|(?:[-+*]|[0-9]{1,9}[.)])"
             r"[ \t]{1,4}) {0,3})*(?:`{3,}[^`\n]*|~{3,}[^\n]*)(?=\n|$)")
    # Block syntax takes precedence over code spans: an unmatched backtick
    # in a Setext heading cannot close in the paragraph after its underline.
    setext = r"\n" + prefix + r" {0,3}(?:=+|-+)[ \t]*(?=\n|$)"
    # Inline code may otherwise span soft line breaks, but not separate
    # paragraphs or masked blocks (including quote-only blank lines).
    boundary = re.search(r"\n[ \t]*(?:>[ \t]*)*\n|[\0\x01]|" + fence + "|" + setext, text[start:])
    limit = start + boundary.start() if boundary else len(text)
    # Only a delimiter with the exact same number of backticks closes a span.
    closing = re.search(r"(?<!`)" + run + r"(?!`)", text[start:limit])
    return start + closing.end() if closing else None


def _bracket_end(text: str, index: int, containers=()) -> int | None:
    depth = 1
    index += 1
    while index < len(text):
        char = text[index]
        if char == "<":
            tag = _HTML_TAG.match(text, index) or _AUTOLINK.match(text, index)
            if tag:
                index = tag.end()
                continue
        # _blocks also calls this on raw source to locate literal destinations
        # and titles. Brackets/backticks inside comments cannot close a label.
        if text.startswith("<!--", index):
            end = text.find("-->", index + 4)
            if end < 0:
                return None
            index = end + 3
            continue
        if char == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
            index += 2
            continue
        if char == "`":
            end = _code_end(text, index, containers)
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
            tag = _HTML_TAG.match(text, index) or _AUTOLINK.match(text, index)
            if tag:
                index = tag.end()
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
