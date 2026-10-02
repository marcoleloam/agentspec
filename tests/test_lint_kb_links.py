"""Exercise the public KB lint command in small, isolated repositories."""

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/lint_kb_links.py"


@pytest.fixture
def repo():
    # Explicitly use TMPDIR, including when pytest's --basetemp is elsewhere.
    with tempfile.TemporaryDirectory(prefix="kb-links-", dir=os.environ.get("TMPDIR")) as temporary:
        root = Path(temporary) / "repo"
        (root / ".claude/kb").mkdir(parents=True)
        (root / "scripts").mkdir()
        shutil.copyfile(SCRIPT, root / "scripts/lint_kb_links.py")
        yield root


def write(repo, path, content=""):
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content.encode("utf-8"))
    return target


def run(repo, *args):
    return subprocess.run(
        [sys.executable, "scripts/lint_kb_links.py", *args],
        cwd=repo, capture_output=True, text=True, timeout=20,
    )


def test_relative_paths_encoding_queries_and_directories(repo):
    write(repo, "docs/guide.md")
    write(repo, "docs/space name.md")
    write(repo, "docs/question?hash#.md")
    write(repo, "docs/literal%20name.md")
    (repo / "docs/assets").mkdir()
    valid = [
        "../../../docs/guide.md", "../../../docs/guide.md#not-an-anchor",
        "../../../docs/space%20name.md?download#section",
        "../../../docs/question%3Fhash%23.md?q#fragment",
        "../../../docs/literal%2520name.md", "../../../docs/assets",
        "../../../docs/assets/", "#local", "?query", "",
    ]
    invalid = ["./missing.md?q#section", "missing.md#section", "lost/",
               "../../../docs/literal%20name.md", "../../../../outside.md",
               "%2e%2e/%2e%2e/%2e%2e/%2e%2e/outside.md", "/etc/passwd"]
    source = ".claude/kb/deep/source.md"
    write(repo, source, "".join(f"[link]({path})\n" for path in valid + invalid))
    result = run(repo)
    assert result.returncode == 1
    assert result.stdout == "".join(f"{source}:{i}: {path}\n" for i, path in enumerate(invalid, len(valid) + 1))
    assert result.stderr == ""
    write(repo, source, "".join(f"[link]({path})\n" for path in valid))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_syntax_titles_escapes_references_and_crlf(repo):
    write(repo, ".claude/kb/present(v2).md")
    source = ".claude/kb/source.md"
    write(repo, source, "\r\n".join([
        '[inline](./lost.md?q=1#part "title") ![image](<space name.png> \'title\')',
        '[balanced](absent(v2).md (title)) [escaped](present\\(v2\\).md)',
        '[full][ Foo   BAR ] [collapsed][] [shortcut] ![image ref][foo bar]',
        '[multiline', 'label](multi.md)',
        '[foo bar]: <refs/lost.md> "title"',
        '[collapsed]: collapsed.md', '[shortcut]: shortcut.md',
        '[unused]: unused.md', '[undefined] [x][undefined]',
        '[FOO BAR]: ignored-duplicate.md',
        '[full again][foo\tbar]',
        '[Straße]: unicode.md', '[label][STRASSE]', '',
    ]))
    result = run(repo)
    expected = [(1, "./lost.md?q=1#part"), (1, "space name.png"),
                (2, "absent(v2).md"), (3, "refs/lost.md"), (3, "collapsed.md"),
                (3, "shortcut.md"), (3, "refs/lost.md"), (4, "multi.md"),
                (12, "refs/lost.md"), (14, "unicode.md")]
    assert result.returncode == 1
    assert result.stdout == "".join(f"{source}:{line}: {target}\n" for line, target in expected)
    assert result.stderr == ""


def test_ignored_constructs_and_network_destinations(repo):
    write(repo, ".claude/kb/ignored.md", "\n".join([
        '`[code](lost.md)` ``[tick ` code](lost.md)``',
        '```markdown', '[fenced](lost.md)', '````',
        '~~~', '![fenced](lost.png)', '~~~',
        '', '    [indent](lost.md)', '\t[indent](lost.md)', '',
        '<!-- [comment](lost.md)', '[comment](lost.md) -->',
        '<a href="lost.md" title="[text](lost.md)">text</a><img src="lost.png">',
        '[[wiki]] [[wiki|label]] <https://example.invalid>',
        r'\[escaped](lost.md)', r'\![escaped image](#local)',
        '[web](https://example.invalid/lost.md)', '[mail](mailto:x@example.invalid)',
        '[scheme](custom+v2:opaque) [host](//example.invalid/lost.md)',
        '[fragment](#whatever)', '[undefined][unknown]', '[unknown]',
        '[unused]: missing.md', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_sources_order_duplicates_and_nested_images(repo):
    write(repo, ".claude/kb/z.MD", "[one](lost.md) [two](lost.md)\n")
    write(repo, ".claude/kb/a/deep.md", "[![nested](lost.png)](lost.md)\n")
    for path in ("docs/outside.md", ".claude/kb/x.Md", ".claude/kb/a.md.template", ".claude/kb/x.txt"):
        write(repo, path, "[ignored](lost.md)")
    (repo / ".claude/kb/directory.md").mkdir()
    result = run(repo)
    assert result.returncode == 1
    assert result.stdout == (
        ".claude/kb/a/deep.md:1: lost.md\n.claude/kb/a/deep.md:1: lost.png\n"
        ".claude/kb/z.MD:1: lost.md\n.claude/kb/z.MD:1: lost.md\n"
    )


@pytest.mark.parametrize("prefix", ["> ", "> > ", "  > > "])
@pytest.mark.parametrize("fence", ["~~~", "```"])
def test_code_fences_in_quotes_preserve_surrounding_links(repo, prefix, fence):
    write(repo, ".claude/kb/source.md", "\r\n".join([
        '[before](before.md)',
        prefix + fence + 'markdown',
        prefix + '[example](missing.md)',
        prefix + '![image](missing.png)',
        prefix + '[hidden]: hidden.md',
        prefix + fence[0] * 4,
        prefix + '[after](after.md)',
        '[hidden]', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:1: before.md\n.claude/kb/source.md:7: after.md\n', '',
    )


def test_unclosed_quote_fence_ends_with_quote_container(repo):
    write(repo, ".claude/kb/source.md", '\n'.join([
        '> > ~~~', '> > [hidden](hidden.md)',
        '> [outer](outer.md)', '[outside](outside.md)',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:3: outer.md\n.claude/kb/source.md:4: outside.md\n', '',
    )


@pytest.mark.parametrize("opening,continuation", [
    ("- > ", "  > "), ("12) > ", "    > "),
    ("> - > ", ">   > "), ("- > - > ", "  >   > "),
])
@pytest.mark.parametrize("fence", ["~~~", "```"])
@pytest.mark.parametrize("closed", [False, True])
def test_fences_in_alternating_list_and_quote_containers(repo, opening, continuation, fence, closed):
    lines = [
        opening + fence,
        continuation + '[code](missing.md)',
        continuation + '![code](missing.png)',
        continuation + '[hidden]: hidden.md',
    ]
    if closed:
        lines += [continuation + fence, continuation + '[inside](inside.md)']
    lines += ['[outside](outside.md)', '[hidden]']
    write(repo, '.claude/kb/source.md', '\r\n'.join(lines) + '\r\n')
    result = run(repo)
    expected = '.claude/kb/source.md:6: inside.md\n' if closed else ''
    expected += f'.claude/kb/source.md:{7 if closed else 5}: outside.md\n'
    assert (result.returncode, result.stdout, result.stderr) == (1, expected, '')


@pytest.mark.parametrize("prefix", ['', '> ', '- > '])
@pytest.mark.parametrize("blank", ['', '  ', '\t'])
@pytest.mark.parametrize("delimiter", ['`', '``'])
def test_inline_code_cannot_cross_blank_paragraph_boundaries(repo, prefix, blank, delimiter):
    continuation = '  > ' if prefix == '- > ' else prefix
    write(repo, '.claude/kb/source.md', '\r\n'.join([
        prefix + delimiter + 'unmatched', continuation + blank,
        continuation + '[x](missing.md)', continuation + blank,
        continuation + delimiter, '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:3: missing.md\n', '',
    )


def test_inline_code_still_spans_soft_line_breaks(repo):
    write(repo, '.claude/kb/source.md',
          '`code\n[x](missing.md)\n` [real](real.md)\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:3: real.md\n', '',
    )


@pytest.mark.parametrize("prefix", ["> ", "> > ", "  > > "])
def test_reference_definitions_inside_quotes(repo, prefix):
    write(repo, ".claude/kb/source.md", "\r\n".join([
        prefix + '[texto][ref]', prefix.rstrip(),
        prefix + '[ref]: <./ausente.md?q=1#part> "title"',
        prefix + '![REF][] [ref]',
        '[outside][ref]',
        prefix + '[unused]: unused.md',
        prefix + '[multi', prefix + 'line]: other.md',
        prefix + '[multi', prefix + 'line]',
    ]))
    result = run(repo)
    expected = [(1, './ausente.md?q=1#part'), (4, './ausente.md?q=1#part'),
                (4, './ausente.md?q=1#part'), (5, './ausente.md?q=1#part'),
                (9, 'other.md')]
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ''.join(f'.claude/kb/source.md:{line}: {target}\n'
                   for line, target in expected), '',
    )


@pytest.mark.parametrize("quote", ["", "> ", "> > "])
@pytest.mark.parametrize("marker", ["- ", "+ ", "* ", "1. ", "12) ", "- - "])
@pytest.mark.parametrize("fence", ["~~~", "```"])
def test_list_fences_ignore_examples_and_preserve_following_links(repo, quote, marker, fence):
    continuation = quote + ' ' * len(marker)
    write(repo, ".claude/kb/source.md", '\r\n'.join([
        quote + marker + fence + 'markdown',
        continuation + '[exemplo](ausente.md)',
        continuation + '![example](missing.png)',
        continuation + '[hidden]: hidden.md',
        continuation + fence, '',
        '[real](real-ausente.md)', '[hidden]',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:7: real-ausente.md\n', '',
    )


@pytest.mark.parametrize("closing", ['  ~~~\n', ''])
def test_list_continuation_fence_ends_at_container_boundary(repo, closing):
    write(repo, ".claude/kb/source.md",
          '- item\n\n  ~~~markdown\n  [example](missing.md)\n' + closing +
          '\n- [sibling](sibling.md)\n\n[real](real.md)\n')
    result = run(repo)
    shift = bool(closing)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, f'.claude/kb/source.md:{6 + shift}: sibling.md\n'
           f'.claude/kb/source.md:{8 + shift}: real.md\n', '',
    )


def test_reference_definitions_in_list_items(repo):
    write(repo, ".claude/kb/source.md", '\n'.join([
        '- [ref]: missing.md',
        '  [ref]',
        '  - [nested]: nested.md',
        '    [nested]',
        '    ~~~', '    [hidden]: hidden.md', '    ~~~',
        '[hidden]', '[ref] [nested]',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:2: missing.md\n'
           '.claude/kb/source.md:4: nested.md\n'
           '.claude/kb/source.md:9: missing.md\n'
           '.claude/kb/source.md:9: nested.md\n', '',
    )


def test_multiline_reference_definitions_normalize_labels_per_use(repo):
    write(repo, '.claude/kb/source.md', '\r\n'.join([
        '[hello', 'world]: <./missing.md?q=1#part> "title"', '',
        '[hello world]', '[full][ HELLO\tWORLD ]', '![hello world][]',
        '[hello', 'world]',
        '[unused', 'label]: unused.md',
        '[hello world]: duplicate.md', '',
        '[invalid', '', 'label]: invalid.md', '[invalid label]',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ''.join(f'.claude/kb/source.md:{line}: ./missing.md?q=1#part\n'
                   for line in (4, 5, 6, 7)), '',
    )


def test_code_spans_do_not_define_references_or_start_comments(repo):
    write(repo, ".claude/kb/source.md", "\n".join([
        '`<!--` [broken](lost.md)',
        '`multiline code', '[hidden]: hidden.md', '`',
        '[hidden]', '[label with `code [text]` inside](other.md)',
        '[actual]: actual.md', '[actual]',
    ]))
    result = run(repo)
    assert result.returncode == 1
    assert result.stdout == (
        ".claude/kb/source.md:1: lost.md\n.claude/kb/source.md:6: other.md\n"
        ".claude/kb/source.md:8: actual.md\n"
    )
    assert result.stderr == ""


@pytest.mark.parametrize("title", ['"<!--"', "'<!--'", '(<!--)', '"first\n<!-- last"'])
@pytest.mark.parametrize("image", ["", "!"])
@pytest.mark.parametrize("reference", [False, True])
def test_comment_markers_in_titles_are_literal(repo, title, image, reference):
    if reference:
        source = f'{image}[x][ref]\n\n[ref]: missing.md {title}\n'
    else:
        source = f'{image}[x](missing.md {title})\n'
    following_line = source.count('\n') + 1
    source += '[y](other.md) <!-- [hidden](hidden.md) --> [z](last.md)\n'
    write(repo, '.claude/kb/source.md', source.replace('\n', '\r\n'))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:1: missing.md\n'
           f'.claude/kb/source.md:{following_line}: other.md\n'
           f'.claude/kb/source.md:{following_line}: last.md\n', '',
    )


@pytest.mark.parametrize("indent", ['    ', '\t', '        ', ' \t', '  \t', '   \t'])
@pytest.mark.parametrize("prefix", ['', '> ', '- '])
def test_indented_paragraph_continuation_is_not_code(repo, indent, prefix):
    continuation = '  ' if prefix == '- ' else prefix
    write(repo, '.claude/kb/source.md', '\r\n'.join([
        prefix + 'paragraph',
        continuation + indent + '[x](missing.md)',
        continuation + indent + '![y](missing.png)',
        continuation.rstrip(),
        continuation + indent + '[code](ignored.md)',
        continuation + indent + '![code](ignored.png)',
        '', '[after](other.md)', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:2: missing.md\n'
           '.claude/kb/source.md:3: missing.png\n'
           '.claude/kb/source.md:8: other.md\n', '',
    )


@pytest.mark.parametrize("block", ['', '# Heading\n', '---\n', 'Heading\n===\n',
                                   '[ref]: target.md\n', '```\ncode\n```\n'])
@pytest.mark.parametrize("indent", ['    ', ' \t', '  \t', '   \t'])
def test_indented_code_after_complete_block_is_ignored(repo, block, indent):
    write(repo, '.claude/kb/source.md', block + indent + '[code](ignored.md)\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')


@pytest.mark.parametrize("start", ['===\n', 'paragraph\n    # still paragraph\n',
                                   'paragraph\n    ---\n'])
def test_heading_like_paragraph_text_does_not_start_indented_code(repo, start):
    write(repo, '.claude/kb/source.md', start + '    [x](missing.md)\n')
    result = run(repo)
    line = start.count('\n') + 1
    assert (result.returncode, result.stdout, result.stderr) == (
        1, f'.claude/kb/source.md:{line}: missing.md\n', '',
    )


@pytest.mark.parametrize("image", ['', '!'])
@pytest.mark.parametrize("suffix", ['(./missing.md?q=1#part "<!-- literal -->")', '[ref]'])
@pytest.mark.parametrize("comment", [
    '<!-- ignored -->',
    '<!-- [hidden](hidden.md) ] ` -->',
    '<!-- multiline\n[hidden](hidden.md) [ -->',
])
def test_comments_in_link_labels_preserve_occurrences(repo, image, suffix, comment):
    source = (f'{image}[text {comment}]{suffix}\n'
              '[after](after.md)\n\n'
              '[ref]: ./missing.md?q=1#part\n')
    write(repo, '.claude/kb/source.md', source.replace('\n', '\r\n'))
    result = run(repo)
    after_line = comment.count('\n') + 2
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:1: ./missing.md?q=1#part\n'
           f'.claude/kb/source.md:{after_line}: after.md\n', '',
    )


def test_symlinks_resolve_inside_repo_but_never_expand_scan(repo):
    write(repo, "docs/real.md", "[not scanned](absent.md)")
    outside = repo.parent / "outside.md"
    outside.write_text("[outside](absent.md)")
    kb = repo / ".claude/kb"
    (kb / "alias.md").symlink_to(repo / "docs/real.md")
    (kb / "alias-dir").symlink_to(repo / "docs", target_is_directory=True)
    (kb / "outside.md").symlink_to(outside)
    (kb / "outside-dir").symlink_to(repo.parent, target_is_directory=True)
    (kb / "dangling.md").symlink_to(kb / "nonexistent")
    (kb / "cycle.md").symlink_to(kb / "cycle.md")
    write(repo, ".claude/kb/source.md", "\n".join([
        '[valid](alias.md) [valid](alias-dir/) [valid](alias-dir/real.md)',
        '[bad](outside.md) [bad](outside-dir/outside.md)',
        '[bad](dangling.md) [bad](cycle.md)',
    ]))
    result = run(repo)
    assert result.returncode == 1
    assert result.stdout == (
        ".claude/kb/source.md:2: outside.md\n.claude/kb/source.md:2: outside-dir/outside.md\n"
        ".claude/kb/source.md:3: dangling.md\n.claude/kb/source.md:3: cycle.md\n"
    )
    assert result.stderr == ""


@pytest.mark.parametrize("args", [("somewhere",), ("--unknown",), ("--root", ".")])
def test_invalid_invocations(repo, args):
    result = run(repo, *args)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip()


@pytest.mark.parametrize("failure", ["missing-kb", "invalid-utf8"])
def test_operational_errors(repo, failure):
    if failure == "missing-kb":
        (repo / ".claude/kb").rmdir()
    else:
        (repo / ".claude/kb/source.md").write_bytes(b"\xff")
    result = run(repo)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "lint_kb_links:" in result.stderr


def test_empty_kb_is_clean(repo):
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
