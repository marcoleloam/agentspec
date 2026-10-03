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
        '',
        '[foo bar]: <refs/lost.md> "title"',
        '[collapsed]: collapsed.md', '[shortcut]: shortcut.md',
        '[unused]: unused.md', '[undefined] [x][undefined]',
        '',
        '[FOO BAR]: ignored-duplicate.md',
        '[full again][foo\tbar]',
        '',
        '[Straße]: unicode.md', '[label][STRASSE]', '',
    ]))
    result = run(repo)
    expected = [(1, "./lost.md?q=1#part"), (1, "space name.png"),
                (2, "absent(v2).md"), (3, "refs/lost.md"), (3, "collapsed.md"),
                (3, "shortcut.md"), (3, "refs/lost.md"), (4, "multi.md"),
                (14, "refs/lost.md"), (17, "unicode.md")]
    assert result.returncode == 1
    assert result.stdout == "".join(f"{source}:{line}: {target}\n" for line, target in expected)
    assert result.stderr == ""


@pytest.mark.parametrize("distinct,plain", [(r"a\*", "a*"), ("a&amp;", "a&")])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("form", ["full", "collapsed", "shortcut"])
def test_reference_labels_preserve_escapes_and_entities(repo, distinct, plain, reverse, form):
    write(repo, ".claude/kb/present.md")
    source = ".claude/kb/source.md"

    def reference(label):
        label = " " + label.upper() + "\t "
        if form == "full":
            return f"[text][{label}]"
        return f"[{label}]" + ("[]" if form == "collapsed" else "")

    # Either definition order must keep the two labels distinct. Check both
    # clean uses and broken uses so collisions cannot hide behind exit 1.
    for used, target in ((plain, "present.md"), (distinct, "missing.md")):
        definitions = [f"[{distinct}]: missing.md", f"[{plain}]: present.md"]
        if reverse:
            definitions.reverse()
        usage = reference(used)
        write(repo, source, "\r\n".join([usage, "!" + usage, "", *definitions, ""]))
        result = run(repo)
        expected = (0, "", "") if target == "present.md" else (
            1, f"{source}:1: missing.md\n{source}:2: missing.md\n", "",
        )
        assert (result.returncode, result.stdout, result.stderr) == expected


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("form", ["inline", "reference"])
@pytest.mark.parametrize("target,existing,broken", [
    (r"a\&amp;b.md", "a&amp;b.md", False),
    (r"a\&amp;b.md", "a&b.md", True),
    ("a&amp;b.md", "a&b.md", False),
    ("a&amp;b.md", "a&amp;b.md", True),
    (r"a\&copy;b.md", "a&copy;b.md", False),
    (r"a&amp\;b.md", "a&amp;b.md", False),
    (r"a&amp\;b.md", "a&b.md", True),
    (r"a&copy\;b.md", "a&copy;b.md", False),
    ("a&copyb.md", "a&copyb.md", False),
    ("a&notarealname;b.md", "a&notarealname;b.md", False),
])
def test_escaped_ampersand_does_not_start_destination_entity(repo, newline, form,
                                                              target, existing, broken):
    write(repo, ".claude/kb/" + existing)
    source = "[x](" + target + ")" if form == "inline" else "[x][ref]\n\n[ref]: " + target
    write(repo, ".claude/kb/source.md", source.replace("\n", newline) + newline)
    result = run(repo)
    expected = (1, f".claude/kb/source.md:1: {target}\n", "") if broken else (0, "", "")
    assert (result.returncode, result.stdout, result.stderr) == expected


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


@pytest.mark.parametrize("source", [
    '2 < 3 and [broken](missing.md) > 1',
    '2 < 3 and ![broken](missing.md) > 1',
    '2 < 3 and [broken][ref] > 1\n\n[ref]: missing.md',
    '2 < 3 and [ref][] > 1\n\n[ref]: missing.md',
    '2 < 3 and [ref] > 1\n\n[ref]: missing.md',
    'text <word [broken](missing.md) > text',
    'text </word [broken](missing.md)> text',
    'text <https://example.invalid/ [broken](missing.md)> text',
    'text <user@example.invalid [broken](missing.md)> text',
])
def test_angle_bracket_prose_preserves_markdown_links(repo, source):
    write(repo, '.claude/kb/source.md', source + '\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:1: missing.md\n', '',
    )


@pytest.mark.parametrize("opaque", [
    '<a href="missing.md" title="[hidden](hidden.md) >">',
    "<img src='missing.png' title='[hidden](hidden.md) <' />",
    '<custom-element data-label="[hidden](hidden.md)" disabled>',
    '<a title="<!--">',
    "<a title='<!--'>",
    '<!DOCTYPE [hidden](hidden.md)>',
    '<?pi [hidden](hidden.md)?>',
    '<![CDATA[[hidden](hidden.md)]]>',
    '<https://example.invalid/[hidden](hidden.md)>',
    '<custom+v2:opaque[hidden](hidden.md)>',
    '<user@example.invalid>',
    '</a >',
])
def test_html_tags_and_autolinks_preserve_surrounding_links(repo, opaque):
    write(repo, '.claude/kb/source.md',
          f'[before](before.md) {opaque} [after](after.md)\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:1: before.md\n'
           '.claude/kb/source.md:1: after.md\n', '',
    )


@pytest.mark.parametrize("tag", [
    '<a title="<!--">text</a>',
    "<a title='<!--'>text</a>",
    '<a title="first line\n<!-- [hidden](hidden.md)">text</a>',
    '<custom-element data-label="<!-- > [hidden](hidden.md)" />',
])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("comment", [False, True])
def test_comment_markers_in_html_attributes_preserve_later_links(repo, tag, newline, comment):
    lines = [tag, '', '[real](missing.md)']
    if comment:
        lines.append('<!-- [ignored](ignored.md) --> [after](after.md)')
    write(repo, '.claude/kb/source.md', '\n'.join(lines).replace('\n', newline))
    result = run(repo)
    line = tag.count('\n') + 3
    expected = f'.claude/kb/source.md:{line}: missing.md\n'
    if comment:
        expected += f'.claude/kb/source.md:{line + 1}: after.md\n'
    assert (result.returncode, result.stdout, result.stderr) == (
        1, expected, '',
    )


def test_html_attributes_are_literal_in_labels_and_definition_discovery(repo):
    write(repo, '.claude/kb/source.md', '\n'.join([
        '[<a title="<!-- ] ` [hidden](hidden.md)">text</a>](missing.md)',
        '<span title="`">[ref]</span>',
        '', '[ref]: reference.md', '', '<span title="`"></span>',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:1: missing.md\n'
           '.claude/kb/source.md:2: reference.md\n', '',
    )


def test_backticks_in_html_attributes_do_not_hide_reference_definitions(repo):
    write(repo, '.claude/kb/source.md', '\n'.join([
        '<span title="`">text</span>',
        '',
        '[ref]: missing.md',
        '<span title="`">text</span>',
        '', '[ref]',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:6: missing.md\n', '',
    )


@pytest.mark.parametrize('source,targets', [
    ('[a [b](b.md)](a.md)', ['b.md']),
    ('[![b](b.png)](a.md)', ['a.md', 'b.png']),
    ('![a [b](b.md)](a.png)', ['a.png']),
    ('![![b](b.png)](a.png)', ['a.png']),
    ('[a [![b](b.png)](c.md)](a.md)', ['c.md', 'b.png']),
    ('[a [b](b.md)]([c](c.md))', ['b.md', 'c.md']),
])
def test_nested_links_follow_commonmark_precedence(repo, source, targets):
    write(repo, '.claude/kb/source.md', source + '\n')
    result = run(repo)
    expected = ''.join(f'.claude/kb/source.md:1: {target}\n' for target in targets)
    assert (result.returncode, result.stdout, result.stderr) == (1, expected, '')


@pytest.mark.parametrize('source', [
    '> paragraph\n>\n> \t[link](missing.md)\n',
    '- paragraph\n\n  \t[link](missing.md)\n',
])
def test_tab_after_container_prefix_is_visible(repo, source):
    write(repo, '.claude/kb/source.md', source)
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:3: missing.md\n', '',
    )


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


@pytest.mark.parametrize("opening,continuation", [
    ("", ""), ("> ", "> "), ("- ", "  "), ("- > ", "  > "),
])
@pytest.mark.parametrize("fence,closing", [
    ("~~~", "~~~"), ("```", "```"), ("   ~~~~python", "~~~~"),
])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_unclosed_inline_code_cannot_close_inside_following_fence(
        repo, opening, continuation, fence, closing, newline):
    write(repo, '.claude/kb/source.md', newline.join([
        opening + '`open', continuation + fence, continuation + '`',
        continuation + closing, continuation + '[x](missing.md)', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:5: missing.md\n', '',
    )


@pytest.mark.parametrize("line", ["~~", "```invalid`info", "    ~~~", r"\~~~"])
def test_non_fences_do_not_interrupt_multiline_inline_code(repo, line):
    write(repo, '.claude/kb/source.md',
          f'``open\n{line}\n[hidden](hidden.md)\n`` [real](missing.md)\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:4: missing.md\n', '',
    )


@pytest.mark.parametrize('opening,continuation', [
    ('> ', '> '), ('- ', '  '), ('- > ', '  > '),
])
@pytest.mark.parametrize('fence', ['~~~', '```'])
def test_fence_in_new_container_interrupts_inline_code(repo, opening, continuation, fence):
    write(repo, '.claude/kb/source.md', '\n'.join([
        '`open', opening + fence, continuation + '`',
        continuation + fence, '[real](missing.md)', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:5: missing.md\n', '',
    )


@pytest.mark.parametrize('marker', ['0. ', '2. ', '02. ', '3) ', '9) '])
def test_ordered_list_above_one_does_not_interrupt_inline_code(repo, marker):
    write(repo, '.claude/kb/source.md', '\n'.join([
        '`open', marker + '~~~', '[hidden](missing.md)', '`', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')


@pytest.mark.parametrize('marker', ['1. ', '01. ', '001) ', '> 2. ', '- 2. '])
def test_fence_after_interrupting_list_is_visible(repo, marker):
    write(repo, '.claude/kb/source.md', '\n'.join([
        '`open', marker + '~~~', '[real](missing.md)', '`', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:3: missing.md\n', '',
    )


def test_fence_hides_link_after_provisional_inline_code(repo):
    write(repo, '.claude/kb/source.md', '\n'.join([
        '`open', '~~~python', '` [hidden](hidden.md)', '~~~',
        '[real](missing.md)', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:5: missing.md\n', '',
    )


@pytest.mark.parametrize('literal', [
    '<a title="open\n~~~\nclose">',
    '[valid](#ok "open\n~~~\nclose")',
])
@pytest.mark.parametrize('closed', [False, True])
def test_fence_line_interrupts_multiline_literal_syntax(repo, literal, closed):
    write(repo, '.claude/kb/source.md', literal + '\n' + ('~~~\n' if closed else '')
          + '[real](missing.md)\n')
    result = run(repo)
    expected = (1, '.claude/kb/source.md:5: missing.md\n', '') if closed else (0, '', '')
    assert (result.returncode, result.stdout, result.stderr) == expected


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


@pytest.mark.parametrize("prefix", ["", "> "])
@pytest.mark.parametrize("marker", ["-", "12)"])
@pytest.mark.parametrize("spacing", [1, 4, 5, 6])
def test_list_opening_padding_distinguishes_paragraphs_from_code(repo, prefix, marker, spacing):
    padding = ' ' * spacing
    width = len(marker) + (spacing if spacing <= 4 else 1)
    continuation = prefix + ' ' * width
    write(repo, '.claude/kb/source.md', '\r\n'.join([
        prefix + marker + padding + '[code](missing-code.md)',
        continuation + (padding[1:] if spacing > 4 else '') + '![image](missing.png)',
        '', '[after](after.md)', '',
    ]))
    result = run(repo)
    expected = '' if spacing > 4 else (
        '.claude/kb/source.md:1: missing-code.md\n'
        '.claude/kb/source.md:2: missing.png\n'
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        1, expected + '.claude/kb/source.md:4: after.md\n', '',
    )


@pytest.mark.parametrize('prefix,visible', [
    ('-\t  ', False), ('- \t  ', False), ('  - \t  ', False),
    ('-\t ', True), ('- \t ', True), ('> -\t  ', True),
    ('- -\t  ', True), ('12)\t  ', True),
])
def test_tab_padding_after_list_marker_uses_visual_columns(repo, prefix, visible):
    write(repo, '.claude/kb/source.md', prefix + '[link](missing.md)\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1 if visible else 0,
        '.claude/kb/source.md:1: missing.md\n' if visible else '',
        '',
    )


@pytest.mark.parametrize("opening,continuation,visible", [
    ('-', '      ', False), ('+', '      ', False), ('*', '      ', False),
    ('- ', '      ', False), ('-\t', '      ', False),
    ('-', '    ', True),
    ('1.', '       ', False), ('2.', '       ', False),
    ('1.', '      ', True),
    ('> -', '>       ', False),
    ('- -', '      ', True), ('1. -', '        ', True),
    ('- > -', '      ', False),
])
@pytest.mark.parametrize("newline", ['\n', '\r\n'])
def test_empty_list_item_distinguishes_indented_code(
        repo, opening, continuation, visible, newline):
    write(repo, '.claude/kb/source.md', newline.join([
        opening, continuation + '[link](missing.md)', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1 if visible else 0,
        '.claude/kb/source.md:2: missing.md\n' if visible else '',
        '',
    )


@pytest.mark.parametrize("opening,continuation", [
    ('-', '    '), ('- -', '      '), ('1. -', '        '),
    ('> -', '>       '),
])
def test_blank_after_empty_list_item_closes_item(
        repo, opening, continuation):
    write(repo, '.claude/kb/source.md',
          opening + '\n\n' + continuation + '[code](missing.md)\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')


@pytest.mark.parametrize("opening,visible", [
    ('-', False), ('- ', False), ('+', True), ('1.', True),
])
def test_empty_list_marker_after_paragraph_preserves_interruption_rules(
        repo, opening, visible):
    write(repo, '.claude/kb/source.md',
          'paragraph\n' + opening + '\n      [link](missing.md)\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1 if visible else 0,
        '.claude/kb/source.md:3: missing.md\n' if visible else '',
        '',
    )


@pytest.mark.parametrize("literal,target", [
    ('a`b.md', 'a`b.md'), ('<a`b.md>', 'a`b.md'),
    ('a.md "literal ` title"', 'a.md'),
])
@pytest.mark.parametrize("definition", [True, False])
def test_literal_backticks_do_not_hide_intervening_reference_definitions(repo, literal, target, definition):
    first = f'[a]: {literal}' if definition else f'# [a]({literal})'
    last = '[c]: c`d.md' if definition else '# [c](c`d.md)'
    write(repo, '.claude/kb/source.md', '\r\n'.join([
        first, '[b]: missing.md', '', last, '',
        '[b] ![b][] [full][b]', '[a] [c]', '',
        '`real code', '[hidden]: hidden.md', '`', '[hidden]', '',
    ]))
    result = run(repo)
    expected = '' if definition else (
        f'.claude/kb/source.md:1: {target}\n'
        '.claude/kb/source.md:4: c`d.md\n'
    )
    expected += '.claude/kb/source.md:6: missing.md\n' * 3
    if definition:
        expected += f'.claude/kb/source.md:7: {target}\n.claude/kb/source.md:7: c`d.md\n'
    assert (result.returncode, result.stdout, result.stderr) == (1, expected, '')


@pytest.mark.parametrize("definition,valid", [
    ('[ref]: missing.md\n"title" extra', True),
    ('[ref]: missing.md\n"valid title"', True),
    ('[ref]: missing.md\n"unclosed title', True),
    ('[ref]: missing.md "title" extra', False),
    ('[ref]: missing.md "valid title"', True),
    ('[ref]: missing.md "unclosed title', False),
    ('[ref]:\n missing.md\n"title" extra', True),
    ('[ref]:\n\nmissing.md', False),
])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_reference_title_failure_only_invalidates_same_line(
        repo, definition, valid, newline):
    source = definition + "\n\n[ref]\n"
    write(repo, ".claude/kb/source.md", source.replace("\n", newline))
    result = run(repo)
    line = definition.count("\n") + 3
    assert (result.returncode, result.stdout, result.stderr) == (
        1 if valid else 0,
        f".claude/kb/source.md:{line}: missing.md\n" if valid else "",
        "",
    )


def test_invalid_next_line_title_is_scanned_as_paragraph(repo):
    write(repo, ".claude/kb/source.md",
          '[ref]: missing.md\n"title" [other](other.md)\n\n[ref]\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:2: other.md\n"
           ".claude/kb/source.md:4: missing.md\n", "",
    )


def test_blank_line_separates_reference_title_candidate(repo):
    write(repo, ".claude/kb/source.md",
          '[ref]: missing.md\n\n"[other](other.md)"\n\n[ref]\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:3: other.md\n"
           ".claude/kb/source.md:5: missing.md\n", "",
    )


def test_multiline_reference_definitions_normalize_labels_per_use(repo):
    write(repo, '.claude/kb/source.md', '\r\n'.join([
        '[hello', 'world]: <./missing.md?q=1#part> "title"', '',
        '[hello world]', '[full][ HELLO\tWORLD ]', '![hello world][]',
        '[hello', 'world]',
        '',
        '[unused', 'label]: unused.md',
        '[hello world]: duplicate.md', '',
        '[invalid', '', 'label]: invalid.md', '[invalid label]',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ''.join(f'.claude/kb/source.md:{line}: ./missing.md?q=1#part\n'
                   for line in (4, 5, 6, 7)), '',
    )


@pytest.mark.parametrize('invalid', ['[]', '[ ]', '[\t]', '[a[b]]', '[[a]]'])
@pytest.mark.parametrize('newline', ['\n', '\r\n'])
def test_invalid_reference_label_keeps_following_definition_in_paragraph(repo, invalid, newline):
    write(repo, '.claude/kb/source.md', newline.join([
        f'{invalid}: unused.md', '[ref]: missing.md', '', '[ref]', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')


@pytest.mark.parametrize("source,expected", [
    ('paragraph\n[ref]: missing.md\n\n[ref]', []),
    ('paragraph\n[ref]: missing.md\n[ref]', []),
    ('paragraph\n[hello\nworld]: missing.md\n\n[hello world]', []),
    ('> paragraph\n> [ref]: missing.md\n>\n> [ref]', []),
    ('- paragraph\n  [ref]: missing.md\n\n[ref]', []),
    ('paragraph\n[ref]: [x](missing.md)', [(2, 'missing.md')]),
    ('paragraph\n\n[ref]: missing.md\n\n[ref]', [(5, 'missing.md')]),
    ('# heading\n[ref]: missing.md\n\n[ref]', [(4, 'missing.md')]),
    ('> paragraph\n>\n> [ref]: missing.md\n>\n> [ref]', [(5, 'missing.md')]),
    ('[ref]: existing.md\n\nparagraph\n[ref]: missing.md\n\n[ref]',
     [(4, 'existing.md'), (6, 'existing.md')]),
])
@pytest.mark.parametrize("newline", ['\n', '\r\n'])
def test_reference_definition_does_not_interrupt_paragraph(repo, source, expected, newline):
    write(repo, '.claude/kb/source.md', source.replace('\n', newline) + newline)
    result = run(repo)
    output = ''.join(f'.claude/kb/source.md:{line}: {target}\n' for line, target in expected)
    assert (result.returncode, result.stdout, result.stderr) == (
        1 if expected else 0, output, '',
    )


@pytest.mark.parametrize("source", [
    '[label\n\n](missing.md)',
    '[label\n \t\n](missing.md)',
    '> [label\n>\n>](missing.md)',
    '- [label\n  \n  ](missing.md)',
    '[label <!-- comment\n\nstill comment -->](missing.md)',
    '[label <span title="first\n\nlast">](missing.md)',
    '[label `code\n\n end`](missing.md)',
    '[lab\n\nel]: missing.md\n\n[label]',
])
@pytest.mark.parametrize("newline", ['\n', '\r\n'])
def test_link_label_cannot_cross_empty_paragraph(source, newline, repo):
    source = source.replace('\n', newline)
    write(repo, '.claude/kb/source.md', source + newline)
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')


@pytest.mark.parametrize("source,target", [
    ('[label\ncontinued](missing.md)', 'missing.md'),
    ('![alt\ntext](missing.png)', 'missing.png'),
    (r'[escaped \]' + '\ncontinued](missing.md)', 'missing.md'),
    ('[label <!-- comment\ncontinued -->](missing.md)', 'missing.md'),
    ('[foo\nbar][ref]\n\n[ref]: missing.md', 'missing.md'),
    ('[[inner](inner.md)\nouter](outer.md)', 'inner.md'),
])
@pytest.mark.parametrize("newline", ['\n', '\r\n'])
def test_link_label_can_cross_soft_line_break(source, target, newline, repo):
    write(repo, '.claude/kb/source.md', source.replace('\n', newline) + newline)
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, f'.claude/kb/source.md:1: {target}\n', '',
    )


@pytest.mark.parametrize('source', [
    '[x](missing.md\n\n)',
    '[x](\n\nmissing.md)',
    '[x](missing.md\n\n"title")',
    '[x](missing.md "title\n\ncontinued")',
    '- [x](missing.md\n  \n  )',
])
@pytest.mark.parametrize('newline', ['\n', '\r\n'])
def test_inline_link_cannot_cross_blank_paragraph(source, newline, repo):
    write(repo, '.claude/kb/source.md', source.replace('\n', newline) + newline)
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')


@pytest.mark.parametrize('source', [
    '[x](missing.md\n)',
    '[x](\nmissing.md)',
    '[x](missing.md\n"title")',
    '[x](missing.md "first\nsecond")',
])
@pytest.mark.parametrize('newline', ['\n', '\r\n'])
def test_inline_link_accepts_one_soft_line_break(source, newline, repo):
    write(repo, '.claude/kb/source.md', source.replace('\n', newline) + newline)
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:1: missing.md\n', '',
    )


def test_code_spans_do_not_define_references_or_start_comments(repo):
    write(repo, ".claude/kb/source.md", "\n".join([
        '`<!--` [broken](lost.md)',
        '`multiline code', '[hidden]: hidden.md', '`',
        '[hidden]', '# [label with `code [text]` inside](other.md)',
        '[actual]: actual.md', '[actual]',
    ]))
    result = run(repo)
    assert result.returncode == 1
    assert result.stdout == (
        ".claude/kb/source.md:1: lost.md\n.claude/kb/source.md:6: other.md\n"
        ".claude/kb/source.md:8: actual.md\n"
    )
    assert result.stderr == ""


@pytest.mark.parametrize("prefix", ["# ", "   ## ", "######\t", "> # ", "> > ## ", "- # ", "- - ### "])
@pytest.mark.parametrize("ticks", ["`", "``"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_unclosed_heading_code_does_not_hide_following_links(repo, prefix, ticks, newline):
    write(repo, ".claude/kb/source.md", newline.join([
        prefix + ticks + "heading", "[x](missing.md)", ticks, "",
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:2: missing.md\n", "",
    )


@pytest.mark.parametrize("prefix", ["# ", "   ## ", "######\t", "> # ",
                                    "- # ", "1. # ", "> - # ", "- - # "])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_atx_heading_interrupts_provisional_inline_code(repo, prefix, newline):
    write(repo, ".claude/kb/source.md", newline.join([
        "text `", prefix + "[broken](missing.md) `", "",
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:2: missing.md\n", "",
    )


@pytest.mark.parametrize("prefix", ["#notheading ", "####### ", "    # ",
                                    "2. # ", r"\# "])
def test_non_atx_line_keeps_provisional_inline_code(repo, prefix):
    write(repo, ".claude/kb/source.md",
          "text `\n" + prefix + "[hidden](missing.md) `\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_atx_heading_interrupts_code_inside_existing_list(repo):
    write(repo, ".claude/kb/source.md",
          "- `open\n  # [broken](missing.md) `\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:2: missing.md\n", "",
    )


def test_atx_heading_keeps_its_own_code_span(repo):
    write(repo, ".claude/kb/source.md",
          "`open\n# `[hidden](hidden.md)` [broken](missing.md) `\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:2: missing.md\n", "",
    )


def test_ordered_list_after_blank_line_can_start_atx_heading(repo):
    write(repo, ".claude/kb/source.md",
          "text `\n\n2. # [broken](missing.md) `\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:3: missing.md\n", "",
    )


@pytest.mark.parametrize("source", [
    '<a title="\n# [broken](missing.md) `\n">\n',
    '[label](target.md "literal\n# [broken](missing.md) `")\n',
])
def test_atx_heading_interrupts_multiline_literal_syntax(repo, source):
    write(repo, ".claude/kb/source.md", source)
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:2: missing.md\n", "",
    )


@pytest.mark.parametrize("marker", ["***", "* * *", "___", "_ _ _", "- - -",
                                     "> ***", "- ***", "1. ***", "> * * *",
                                     "> - - -", "- * * *", "1. * * *"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_thematic_break_interrupts_provisional_inline_code(repo, marker, newline):
    write(repo, ".claude/kb/source.md", newline.join([
        "text `", marker, "[broken](missing.md)", "`", "",
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:3: missing.md\n", "",
    )


def test_thematic_break_inside_existing_list_interrupts_inline_code(repo):
    write(repo, ".claude/kb/source.md",
          "- `open\n  ***\n  [broken](missing.md)\n  `\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:3: missing.md\n", "",
    )


@pytest.mark.parametrize("marker", ["    ***", "2. ***", "***text", "*bold*"])
def test_non_thematic_line_keeps_provisional_inline_code(repo, marker):
    write(repo, ".claude/kb/source.md",
          "text `\n" + marker + "\n[hidden](missing.md)\n`\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


@pytest.mark.parametrize("opening,marker", [
    ("text `", "> [broken](missing.md) `"),
    ("text `", "- [broken](missing.md) `"),
    ("text `", "+ [broken](missing.md) `"),
    ("text `", "* [broken](missing.md) `"),
    ("text `", "1. [broken](missing.md) `"),
    ("- `open", "  - [broken](missing.md) `"),
    ("- `open", "  > [broken](missing.md) `"),
    ("- `open", "> [broken](missing.md) `"),
])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_new_quote_or_list_interrupts_provisional_inline_code(
        repo, opening, marker, newline):
    write(repo, ".claude/kb/source.md", newline.join([opening, marker, ""]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:2: missing.md\n", "",
    )


@pytest.mark.parametrize("opening,marker", [
    ("text `", "0. [hidden](missing.md) `"),
    ("text `", "2. [hidden](missing.md) `"),
    ("text `", "    - [hidden](missing.md) `"),
    ("- `open", "  [hidden](missing.md) `"),
    ("> `open", "> [hidden](missing.md) `"),
])
def test_non_interrupting_container_lines_keep_inline_code(repo, opening, marker):
    write(repo, ".claude/kb/source.md", opening + "\n" + marker + "\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_new_list_interrupts_code_before_following_link(repo):
    write(repo, ".claude/kb/source.md",
          "text `\n- item\n[broken](missing.md)\n`\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:3: missing.md\n", "",
    )


def test_new_list_keeps_its_own_inline_code(repo):
    write(repo, ".claude/kb/source.md",
          "text `\n- `[hidden](hidden.md)` [broken](missing.md) `\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:2: missing.md\n", "",
    )


@pytest.mark.parametrize("marker", ["*", "+", "1.", "1)"])
@pytest.mark.parametrize("padding", ["     ", "       "])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_empty_list_marker_does_not_interrupt_paragraph_code(
        repo, marker, padding, newline):
    write(repo, ".claude/kb/source.md", newline.join([
        "`open", marker + padding, "[hidden](missing.md) `", "",
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_hyphen_underline_still_ends_setext_heading(repo):
    write(repo, ".claude/kb/source.md",
          "`open\n-     \n[broken](missing.md) `\n")
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:3: missing.md\n", "",
    )


@pytest.mark.parametrize("source,line", [
    ("- item\n\t[broken](missing.md)\n", 2),
    ("1. item\n\t[broken](missing.md)\n", 2),
    ("- - nested\n\t[broken](missing.md)\n", 2),
    ("- item\n\n\t[broken](missing.md)\n", 3),
    ("- item\n\t\t[broken](missing.md)\n", 2),
    ("- item\n    [broken](missing.md)\n", 2),
    ("- item\n      [broken](missing.md)\n", 2),
])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_list_continuation_uses_tab_columns(repo, source, line, newline):
    write(repo, ".claude/kb/source.md", source.replace("\n", newline))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, f".claude/kb/source.md:{line}: missing.md\n", "",
    )


@pytest.mark.parametrize("source", [
    "- item\n\n\t\t[hidden](missing.md)\n",
    "- item\n\n\t  [hidden](missing.md)\n",
    "- - nested\n\n\t\t[hidden](missing.md)\n",
    "- item\n\n      [hidden](missing.md)\n",
])
def test_list_continuation_overflow_stays_code_after_blank(repo, source):
    write(repo, ".claude/kb/source.md", source)
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


@pytest.mark.parametrize("source,visible", [
    ('> paragraph\n    [link](missing.md)', True),
    ('> paragraph\n\t[link](missing.md)', True),
    ('> paragraph\n    text [link](missing.md)', True),
    ('> paragraph\n    plain text\n    [link](missing.md)', True),
    ('> - item\n    [link](missing.md)', True),
    ('> > paragraph\n    [link](missing.md)', True),
    ('> paragraph\n    ![image](missing.md)', True),
    ('> paragraph\n\n    [link](missing.md)', False),
    ('> paragraph\n\n    text [link](missing.md)', False),
    ('> > paragraph\n    # [link](missing.md)', False),
    ('> > paragraph\n    - [link](missing.md)', False),
    ('> > paragraph\n    <div>[link](missing.md)</div>', False),
    ('> > paragraph\n    > <div>[link](missing.md)</div>', False),
    ('> paragraph\n    > <div>[link](missing.md)</div>', False),
    ('> > paragraph\n    ```[link](missing.md)', False),
    ('> > paragraph\n      ~~~[link](missing.md)', False),
])
@pytest.mark.parametrize("newline", ['\n', '\r\n'])
def test_lazy_quote_link_continuation_is_not_indented_code(
        repo, source, visible, newline):
    write(repo, '.claude/kb/source.md', source.replace('\n', newline) + newline)
    result = run(repo)
    line = source.count('\n') + 1
    assert (result.returncode, result.stdout, result.stderr) == (
        1 if visible else 0,
        f'.claude/kb/source.md:{line}: missing.md\n' if visible else '',
        '',
    )


@pytest.mark.parametrize("underline", ["=======", "---", "=", "-", "   ===\t"])
@pytest.mark.parametrize("prefix,continuation", [("", ""), ("> ", "> "), ("- ", "  "),
                                                  ("- > ", "  > ")])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_unclosed_setext_code_does_not_hide_following_links(
        repo, underline, prefix, continuation, newline):
    write(repo, ".claude/kb/source.md", newline.join([
        prefix + "`titulo", continuation + underline,
        continuation + "[x](missing.md)", continuation + "`", "",
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:3: missing.md\n", "",
    )


def test_setext_boundary_preserves_heading_links_and_following_definitions(repo):
    write(repo, ".claude/kb/source.md", "\n".join([
        '`[hidden](hidden.md)` [heading](heading.md) ``open',
        'second heading line', '===',
        '[ref]: reference.md', '[ref] ![image][ref]', '``', '',
        '`soft break', '[hidden](also-hidden.md)', '` [after](after.md)', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:1: heading.md\n"
           ".claude/kb/source.md:5: reference.md\n"
           ".claude/kb/source.md:5: reference.md\n"
           ".claude/kb/source.md:10: after.md\n", "",
    )


@pytest.mark.parametrize("line", ["==== text", "== ==", "    ===", r"\===", "-- -- text"])
def test_non_setext_lines_preserve_multiline_inline_code(repo, line):
    write(repo, ".claude/kb/source.md",
          f'`code\n{line}\n[x](hidden.md)\n` [after](after.md)\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:4: after.md\n", "",
    )


@pytest.mark.parametrize("prefix", ["# ", "> > ## ", "- - ### "])
def test_heading_code_keeps_inline_syntax_and_following_definitions(repo, prefix):
    write(repo, ".claude/kb/source.md", "\r\n".join([
        prefix + '`[hidden](hidden.md)` [x](first.md "literal ` title") `open',
        '[ref]: second.md', '[ref]', '`', '',
        '`multiline', '[hidden](also-hidden.md)', '`',
        '[after](last.md)', '',
    ]))
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, ".claude/kb/source.md:1: first.md\n"
           ".claude/kb/source.md:3: second.md\n"
           ".claude/kb/source.md:9: last.md\n", "",
    )


@pytest.mark.parametrize('underline', ['===', '---'])
@pytest.mark.parametrize('opening,continuation', [
    ('', ''), ('> ', '> '), ('- ', '  '), ('> - ', '>   '),
])
def test_unclosed_code_span_in_setext_heading_ends_at_line_break(
        repo, opening, continuation, underline):
    write(repo, '.claude/kb/source.md',
          opening + '`heading\n' + continuation + underline + '\n'
          + continuation + '[x](missing.md)\n' + continuation + '`\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:3: missing.md\n', '',
    )


def test_indented_paragraph_continuation_is_not_setext_heading(repo):
    write(repo, '.claude/kb/source.md',
          'foo\n    `heading\n    ===\n[x](missing.md)\n`\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')


def test_setext_heading_in_nested_list_continuation(repo):
    write(repo, '.claude/kb/source.md',
          '- - intro\n    `heading\n    ===\n'
          '    [x](missing.md)\n    `\n')
    result = run(repo)
    assert (result.returncode, result.stdout, result.stderr) == (
        1, '.claude/kb/source.md:4: missing.md\n', '',
    )


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
    expected = ('.claude/kb/source.md:2: missing.md\n'
                '.claude/kb/source.md:3: missing.png\n')
    # A tab after a quote/list marker starts at the marker's original column.
    # One tab, or one space then a tab, may add fewer than four columns.
    if prefix and indent in ('\t', ' \t'):
        expected += ('.claude/kb/source.md:5: ignored.md\n'
                     '.claude/kb/source.md:6: ignored.png\n')
    expected += '.claude/kb/source.md:8: other.md\n'
    assert (result.returncode, result.stdout, result.stderr) == (
        1, expected, '',
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
