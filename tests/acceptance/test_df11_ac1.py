import json
import os
import subprocess
import sys


_DRIVER = r'''
import json, os, pathlib, shutil, subprocess, sys, tempfile
source = pathlib.Path.cwd()
payload = json.loads(sys.argv[1])
with tempfile.TemporaryDirectory(prefix='.df11-', dir=source) as temporary:
    work = pathlib.Path(temporary)
    root = work / 'repo'
    def ignore(directory, names):
        ignored = [n for n in names if n in {'.git', '.venv', '__pycache__', 'node_modules', '.pytest_cache', 'acceptance'} or n.startswith('.df11-')]
        if pathlib.Path(directory) == source / '.claude':
            ignored.extend(n for n in ('agents', 'commands') if n in names)
        return ignored
    shutil.copytree(source, root, symlinks=True, ignore=ignore)
    for name in ('agents', 'commands'):
        original = source / '.claude' / name
        if original.exists():
            (root / '.claude' / name).symlink_to(original, target_is_directory=True)
    kb = root / '.claude/kb'
    if kb.exists():
        shutil.rmtree(kb)
    kb.mkdir(parents=True)
    for name, content in payload['files'].items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode('utf-8'))
    for name in payload.get('dirs', []):
        (root / name).mkdir(parents=True, exist_ok=True)
    result = subprocess.run(['python3', 'scripts/lint_kb_links.py', *payload.get('args', [])], cwd=root, capture_output=True, text=True, timeout=45)
    print(json.dumps({'code': result.returncode, 'out': result.stdout, 'err': result.stderr}))
'''


def _case(files, dirs=(), args=()):
    result = subprocess.run(([os.environ['FACTORY_CANDIDATE']] if os.environ.get('FACTORY_CANDIDATE') else []) + [sys.executable, '-c', _DRIVER, json.dumps({'files': files, 'dirs': dirs, 'args': args})], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_inline_reference_images_and_occurrence_positions():
    source = '\n'.join([
        '# Links',
        '[good](present.md "a title")',
        '[bad](./absent.md?q=1#frag "title") ![image](images/absent.png)',
        '[one](dup.md) [two](dup.md)',
        '[angle](<space name.md> \'caption\')',
        '[balanced](missing(v2).md (caption))',
        '[full][broken] [collapsed][] [shortcut]',
        '',
        '[broken]: refs/lost.md "title"',
        '[collapsed]: other.md',
        '[shortcut]: shortcut.md',
        '[escaped](present\\(v2\\).md)',
        '[multiline',
        'label](multiline-missing.md)',
        '',
    ])
    result = _case({'.claude/kb/a.md': source, '.claude/kb/present.md': '', '.claude/kb/present(v2).md': ''})
    expected = [
        (3, './absent.md?q=1#frag'), (3, 'images/absent.png'),
        (4, 'dup.md'), (4, 'dup.md'), (5, 'space name.md'),
        (6, 'missing(v2).md'), (7, 'refs/lost.md'),
        (7, 'other.md'), (7, 'shortcut.md'), (13, 'multiline-missing.md'),
    ]
    assert result['code'] == 1, result
    assert result['out'] == ''.join(f'.claude/kb/a.md:{line}: {target}\n' for line, target in expected), result
    assert result['err'] == '', result


def test_ignored_syntax_and_source_extensions():
    ignored = '\n'.join([
        '`[code](inline-missing.md)`',
        '``[code with ` tick](also-missing.md)``',
        '```markdown', '[fenced](fenced-missing.md)', '```',
        '~~~', '![fenced](image-missing.png)', '~~~',
        '', '    [indented](indented-missing.md)', '',
        '<!-- [comment](comment-missing.md)', '![comment](other-missing.md) -->',
        '<a href="html-missing.md">HTML</a><img src="html-missing.png">',
        '[[wiki-missing]] <https://example.invalid/no-network>',
        '\\[escaped](escaped-missing.md)',
        '[fragment](#anything)', '',
    ])
    files = {
        '.claude/kb/ignored.md': ignored,
        '.claude/kb/deep/upper.MD': '[broken](missing-upper.md)\n',
        '.claude/kb/_templates/a.md.template': '[template](missing-template.md)',
        '.claude/kb/plain.txt': '[text](missing-text.md)',
        'docs/outside.md': '[outside](missing-outside.md)',
    }
    result = _case(files, dirs=['.claude/kb/directory.md'])
    assert result == {'code': 1, 'out': '.claude/kb/deep/upper.MD:1: missing-upper.md\n', 'err': ''}
    files['.claude/kb/deep/upper.MD'] = '[good](../ignored.md#not-checked)\n'
    assert _case(files, dirs=['.claude/kb/directory.md']) == {'code': 0, 'out': '', 'err': ''}


def test_invalid_invocation_is_operational_error():
    result = _case({'.claude/kb/ok.md': ''}, args=['--df11-unknown-option'])
    assert result['code'] == 2, result
    assert result['out'] == '', result
    assert result['err'].strip(), result
