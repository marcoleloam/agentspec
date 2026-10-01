import json
import os
import subprocess
import sys


_DRIVER = r'''
import json, pathlib, shutil, subprocess, sys, tempfile
source = pathlib.Path.cwd()
payload = json.loads(sys.argv[1])
with tempfile.TemporaryDirectory(prefix='.df11-', dir=source) as temporary:
    work = pathlib.Path(temporary)
    root = work / 'repo'
    def ignore(directory, names):
        return [n for n in names if n in {'.git', '.venv', '__pycache__', 'node_modules', '.pytest_cache', 'acceptance'} or n.startswith('.df11-')]
    shutil.copytree(source, root, symlinks=True, ignore=ignore)
    kb = root / '.claude/kb'
    if kb.exists():
        shutil.rmtree(kb)
    kb.mkdir(parents=True)
    (work / 'outside.txt').write_text('outside', encoding='utf-8')
    for name, content in payload['files'].items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    for name in payload.get('dirs', []):
        (root / name).mkdir(parents=True, exist_ok=True)
    result = subprocess.run(['python3', 'scripts/lint_kb_links.py'], cwd=root, capture_output=True, text=True, timeout=45)
    print(json.dumps({'code': result.returncode, 'out': result.stdout, 'err': result.stderr}))
'''


def _case(files, dirs=()):
    result = subprocess.run([os.environ['FACTORY_CANDIDATE'], sys.executable, '-c', _DRIVER, json.dumps({'files': files, 'dirs': dirs})], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_resolution_encoding_fragments_and_repository_boundary():
    good = [
        '../../../docs/guide.md', '../ok.md', '#local',
        '../../../docs/guide.md#nonexistent-anchor',
        '../../../docs/space%20name.md?download=1#part',
        '../../../docs/question%3Fpart%23hash.md?download=1#part',
        '../../../docs/assets', '../../../docs/assets/',
        'https://example.invalid/missing.md', 'mailto:nobody@example.invalid',
        'custom+v2:opaque/path', '//example.invalid/missing.md',
    ]
    bad = [
        '../missing.md#section', './lost.md?q=2#fragment',
        '../../../docs/no-dir/', '/etc/passwd',
        '../../../../outside.txt',
        '%2e%2e/%2e%2e/%2e%2e/%2e%2e/outside.txt',
    ]
    files = {
        '.claude/kb/deep/source.md': ''.join(f'[link]({target})\n' for target in good + bad),
        '.claude/kb/ok.md': '',
        'docs/guide.md': '[not a source](missing.md)',
        'docs/space name.md': '',
        'docs/question?part#hash.md': '',
    }
    result = _case(files, dirs=['docs/assets'])
    assert result['code'] == 1, result
    assert result['out'] == ''.join(f'.claude/kb/deep/source.md:{len(good) + i}: {target}\n' for i, target in enumerate(bad, 1)), result
    assert result['err'] == '', result
    files['.claude/kb/deep/source.md'] = ''.join(f'[link]({target})\n' for target in good)
    assert _case(files, dirs=['docs/assets']) == {'code': 0, 'out': '', 'err': ''}
