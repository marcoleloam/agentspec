import json
import os
import subprocess
import sys


_DRIVER = r'''
import ast, json, os, pathlib, shutil, subprocess, tempfile
source = pathlib.Path.cwd()
with tempfile.TemporaryDirectory(prefix='.df11-', dir=source) as temporary:
    work = pathlib.Path(temporary)
    root = work / 'repo'
    def ignore(directory, names):
        return [n for n in names if n in {'.git', '.venv', '__pycache__', 'node_modules', '.pytest_cache', 'acceptance'} or n.startswith('.df11-')]
    shutil.copytree(source, root, symlinks=True, ignore=ignore)
    if (source / '.venv').is_dir():
        (root / '.venv').symlink_to(source / '.venv', target_is_directory=True)
    plugin = work / 'df11_observer.py'
    plugin.write_text('import json, os\ndef pytest_runtest_logreport(report):\n    if report.when == "call":\n        with open(os.environ["DF11_REPORT"], "a", encoding="utf-8") as stream:\n            stream.write(json.dumps({"node": report.nodeid, "outcome": report.outcome, "detail": str(report.longrepr)}) + "\\n")\n', encoding='utf-8')
    env = os.environ.copy()
    env['PYTHONPATH'] = str(work) + os.pathsep + env.get('PYTHONPATH', '')
    env['PYTEST_ADDOPTS'] = '-p df11_observer --ignore=tests/acceptance'
    def run(label):
        report = work / (label + '.jsonl')
        env['DF11_REPORT'] = str(report)
        result = subprocess.run(['make', 'test'], cwd=root, env=env, capture_output=True, text=True, timeout=240)
        events = [json.loads(line) for line in report.read_text(encoding='utf-8').splitlines()] if report.exists() else []
        return {'code': result.returncode, 'events': events, 'output': (result.stdout + result.stderr)[-18000:]}
    healthy = run('healthy')
    script = root / 'scripts/lint_kb_links.py'
    tree = ast.parse(script.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'main':
            node.body = [ast.Return(value=ast.Constant(value=0))]
    position = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        position = 1
    while position < len(tree.body) and isinstance(tree.body[position], ast.ImportFrom) and tree.body[position].module == '__future__':
        position += 1
    tree.body[position:position] = ast.parse('if __name__ == "__main__":\n    raise SystemExit(0)\n').body
    ast.fix_missing_locations(tree)
    script.write_text(ast.unparse(tree) + '\n', encoding='utf-8')
    for cache in (root / 'scripts').rglob('__pycache__'):
        shutil.rmtree(cache)
    mutant = run('always_zero')
    print(json.dumps({'healthy': healthy, 'mutant': mutant}))
'''


def test_make_test_passes_and_detects_an_always_successful_linter():
    result = subprocess.run([os.environ['FACTORY_CANDIDATE'], sys.executable, '-c', _DRIVER], capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data['healthy']['code'] == 0, data['healthy']['output']
    assert any(event['outcome'] == 'passed' and event['node'].startswith('tests/') for event in data['healthy']['events']), data
    assert data['mutant']['code'] != 0, 'make test accepted a public linter that always exits 0'
    failures = [event for event in data['mutant']['events'] if event['outcome'] == 'failed' and event['node'].startswith('tests/')]
    assert any('AssertionError' in event['detail'] or '\nE   assert ' in event['detail'] for event in failures), data['mutant']['output']
