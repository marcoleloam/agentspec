import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

import yaml


_BASE_TESTS = {
    'tests/test_eval_runner.py': 'dcdd8edf5d2fb0ee87e30cfb0b4cf10e4b7de4263383e2c7a1066b08ed196a4b',
    'tests/test_generate_agent_router.py': '24f0d6a4b59da6de0f75ddc5228174283dcb697af14722578f8b73228320be3b',
    'tests/test_generate_codex_plugin.py': '4807e0855339c7b243c3da3e175ff77f0eb00d0cd029a47ea668a969ed6c7f5f',
    'tests/test_generate_grok_plugin.py': '841da0443d15be1b63371bdfc0e92f70a88604867ae54ec4eb29597bf93f696d',
    'tests/test_jev_client.py': '4bc362bcc3f6dc05684bb6c8cbebceb1460055c332660ef3927d275c0ab26960',
    'tests/test_judge.py': '8b8632c9b53bac7f618914ddee7c1e3b4b1b25173a41f40b87d25dce1fcb2c4b',
}


# Relevant event filters and jobs from the supplied base workflow.
_BASE_CI = r'''
on:
  push:
    branches: [main]
    paths: &base_paths
      - 'scripts/**'
      - 'tests/**'
      - '**/*.sh'
      - '.claude/agents/**'
      - '.claude/commands/**'
      - 'plugin-grok/**'
      - '.grok/**'
      - 'tools/spec-linter/**'
      - 'tools/spec-judge/**'
      - '.github/workflows/quality-checks.yml'
  pull_request:
    branches: [main]
    paths: *base_paths
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python3 -m pip install -r requirements-dev.txt
      - run: python3 -m pytest tests/ -v
  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get update && sudo apt-get install -y shellcheck
      - run: >-
          shellcheck -S warning
          build-plugin.sh
          .claude/skills/visual-explainer/scripts/share.sh
          plugin-extras/scripts/init-workspace.sh
  spec-linter:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python3 -m pip install -e 'tools/spec-linter[dev]'
      - run: python3 -m pytest tools/spec-linter/tests -v
  spec-judge:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python3 -m pip install -e tools/spec-linter -e 'tools/spec-judge[dev]'
      - run: python3 -m pytest tools/spec-judge/tests -v
      - run: tools/spec-judge/spec-judge --selfcheck
'''


def _matches(path, pattern):
    parts = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if pattern[index:index + 3] == '**/':
            parts.append('(?:.*/)?')
            index += 3
        elif pattern[index:index + 2] == '**':
            parts.append('.*')
            index += 2
        elif char == '*':
            parts.append('[^/]*')
            index += 1
        elif char == '?':
            parts.append('[^/]')
            index += 1
        else:
            parts.append(re.escape(char))
            index += 1
    return re.fullmatch(''.join(parts), path) is not None


def _included(path, patterns):
    included = False
    for pattern in patterns:
        negative = pattern.startswith('!')
        if _matches(path, pattern[1:] if negative else pattern):
            included = not negative
    return included


def test_ci_events_filters_and_explicit_root_command():
    code = 'import hashlib,json,pathlib; root=pathlib.Path.cwd(); print(json.dumps({"workflow":(root/".github/workflows/quality-checks.yml").read_text(), "tests":{p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path("tests").rglob("test_*.py") if "acceptance" not in p.parts}}))'
    result = subprocess.run(([os.environ['FACTORY_CANDIDATE']] if os.environ.get('FACTORY_CANDIDATE') else []) + [sys.executable, '-c', code], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    workflow = yaml.safe_load(data['workflow'])
    events = workflow.get('on', workflow.get(True))
    assert isinstance(events, dict), events
    changed_tests = [path for path, digest in data['tests'].items() if _BASE_TESTS.get(path) != digest]
    assert changed_tests, 'No new or modified executable test module under tests/'
    required = ['.claude/kb/index.md', '.claude/kb/deep/topic/page.MD', '.claude/kb/_templates/example.md.template', 'scripts/lint_kb_links.py', '.github/workflows/quality-checks.yml', *changed_tests]
    base = yaml.safe_load(_BASE_CI)
    base_events = base.get('on', base.get(True))
    for event in ('push', 'pull_request'):
        assert event in events, events
        config = events[event]
        assert isinstance(config, dict) and isinstance(config.get('paths'), list), (event, config)
        assert 'paths-ignore' not in config, (event, config)
        base_config = base_events[event]
        for branch in base_config['branches']:
            assert _included(branch, config.get('branches', ['**'])), (event, config)
            assert not _included(branch, config.get('branches-ignore', [])), (event, config)
        old_paths = [
            pattern.replace('**/', depth).replace('**', depth + name).replace('*', 'df11-probe')
            for pattern in base_config['paths']
            for depth in ('', 'nested/')
            for name in ('df11-probe.py', 'df11-probe.md', 'df11-probe.sh')
        ]
        for path in [*required, *old_paths]:
            assert _included(path, config['paths']), (event, path, config['paths'])
    found = []
    for job_name, job in workflow['jobs'].items():
        steps = job.get('steps', [])
        for index, step in enumerate(steps):
            tokens = shlex.split(step.get('run', ''), comments=True)
            if any(tokens[i:i + 2] == ['python3', 'scripts/lint_kb_links.py'] for i in range(len(tokens) - 1)):
                found.append((job_name, job, step))
                assert job.get('continue-on-error', False) is False, job
                assert step.get('continue-on-error', False) is False, step
                directory = step.get('working-directory', job.get('defaults', {}).get('run', {}).get('working-directory', workflow.get('defaults', {}).get('run', {}).get('working-directory', '.')))
                assert directory in ('.', './', '${{ github.workspace }}', '${{github.workspace}}'), directory
                runner = str(job.get('runs-on', ''))
                assert 'ubuntu' in runner or 'macos' in runner or any(str(previous.get('uses', '')).startswith('actions/setup-python@') for previous in steps[:index]), job
    assert found, 'No job explicitly invokes python3 scripts/lint_kb_links.py'


_CI_AUDIT = r'''
import ast, json, os, pathlib, re, shlex, subprocess, sys, tempfile
import yaml

source = pathlib.Path.cwd()
real = subprocess.run(['python3', 'scripts/lint_kb_links.py'], cwd=source, capture_output=True, text=True, timeout=90)
assert real.returncode == 0, ('Lint failed on the real candidate KB', real.returncode, real.stdout, real.stderr)
workflow = yaml.safe_load((source / '.github/workflows/quality-checks.yml').read_text())

def enabled(condition, event):
    if condition is None or condition is True:
        return True
    if condition is False:
        return False
    text = str(condition).strip()
    if text.startswith('${{') and text.endswith('}}'):
        text = text[3:-2].strip()
    text = text.replace('github.event_name', repr(event))
    text = text.replace('success()', 'True').replace('always()', 'True')
    text = text.replace('failure()', 'False').replace('cancelled()', 'False')
    text = re.sub(r'\btrue\b', 'True', text, flags=re.I)
    text = re.sub(r'\bfalse\b', 'False', text, flags=re.I)
    text = text.replace('&&', ' and ').replace('||', ' or ')
    text = re.sub(r'!(?!=)', ' not ', text)
    tree = ast.parse(text.strip(), mode='eval')
    allowed = (ast.Expression, ast.Constant, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.Compare, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Tuple, ast.List, ast.Load)
    assert all(isinstance(node, allowed) for node in ast.walk(tree)), ('Cannot establish that drift check is enabled', condition)
    return bool(eval(compile(tree, '<workflow condition>', 'eval'), {'__builtins__': {}}, {}))

# Compare execution with the supplied base using isolated command stand-ins.
base = yaml.safe_load(sys.argv[1])
preserved_stub = r"""
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
if name == 'python':
    name = 'python3'
args = sys.argv[1:]
if name == 'python3' and args[:2] == ['-m', 'pytest']:
    args = [arg for arg in args if arg != '-v']
row = [name, args, os.path.relpath(os.getcwd(), os.environ['GITHUB_WORKSPACE'])]
with open(os.environ['DF11_PRESERVE_LOG'], 'a', encoding='utf-8') as stream:
    stream.write(json.dumps(row) + '\n')
target = json.loads(os.environ['DF11_PRESERVE_FAIL'])
if target and name == target[0]:
    remaining = iter(args)
    if all(any(value == wanted for value in remaining) for wanted in target[1]):
        raise SystemExit(1)
"""

def preserved_call(row, expected):
    if row[0] != expected[0] or row[2] != expected[2]:
        return False
    remaining = iter(row[1])
    return all(any(value == wanted for value in remaining) for wanted in expected[1])

def probe_preserved_step(document, job, step, event, target=None):
    with tempfile.TemporaryDirectory(prefix='.df11-', dir=source) as temporary:
        root = pathlib.Path(temporary)
        for name in ('build-plugin.sh', 'bin/git', 'bin/sudo', 'bin/apt-get', 'bin/shellcheck', 'bin/python', 'bin/python3', '.venv/bin/python', '.venv/bin/python3', 'tools/spec-judge/spec-judge'):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('#!' + sys.executable + '\n' + preserved_stub, encoding='utf-8')
            path.chmod(0o755)
        script = root / 'step.sh'
        script.write_text(step['run'], encoding='utf-8')
        defaults = dict(document.get('defaults', {}).get('run', {}))
        defaults.update(job.get('defaults', {}).get('run', {}))
        shell = step.get('shell', defaults.get('shell'))
        if shell is None:
            command = ['bash', '-e', str(script)]
        elif shell == 'bash':
            command = ['bash', '--noprofile', '--norc', '-e', '-o', 'pipefail', str(script)]
        elif shell == 'sh':
            command = ['sh', '-e', str(script)]
        else:
            command = [part.replace('{0}', str(script)) for part in shlex.split(shell)]
        def expand(value):
            return str(value).replace('${{ github.workspace }}', str(root)).replace('${{github.workspace}}', str(root))
        directory = pathlib.Path(expand(step.get('working-directory', defaults.get('working-directory', '.'))))
        if not directory.is_absolute():
            directory = root / directory
        env = os.environ.copy()
        for layer in (document, job, step):
            env.update({key: expand(value) for key, value in layer.get('env', {}).items()})
        env['PATH'] = str(root / 'bin') + os.pathsep + env.get('PATH', '')
        env['GITHUB_WORKSPACE'] = str(root)
        env['GITHUB_EVENT_NAME'] = event
        log = root / 'calls.jsonl'
        env['DF11_PRESERVE_LOG'] = str(log)
        env['DF11_PRESERVE_FAIL'] = json.dumps(target)
        result = subprocess.run(command, cwd=directory, env=env, capture_output=True, text=True, timeout=60)
        records = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        return result, records

for job_name, base_job in base['jobs'].items():
    assert job_name in workflow.get('jobs', {}), ('Missing base job', job_name)
    job = workflow['jobs'][job_name]
    assert job.get('runs-on'), job
    assert job.get('continue-on-error', False) is False, job
    expected_calls = []
    for step in base_job['steps']:
        if 'run' in step:
            result, records = probe_preserved_step(base, base_job, step, 'push')
            assert result.returncode == 0 and records, (job_name, result.stdout, result.stderr)
            expected_calls.extend(records)
    for event in ('push', 'pull_request'):
        assert enabled(job.get('if'), event), (job_name, event, job.get('if'))
        for base_step in base_job['steps']:
            if 'uses' in base_step:
                action = base_step['uses'].split('@')[0]
                assert any(
                    str(step.get('uses', '')).split('@')[0] == action
                    and enabled(step.get('if'), event)
                    and step.get('continue-on-error', False) is False
                    for step in job.get('steps', [])
                ), ('Missing mandatory base action', job_name, event, action)
        observed = []
        for step in job.get('steps', []):
            if 'run' not in step or not enabled(step.get('if'), event):
                continue
            result, records = probe_preserved_step(workflow, job, step, event)
            assert result.returncode == 0, (job_name, event, step, result.stdout, result.stderr)
            observed.extend((row, step) for row in records)
        for expected in expected_calls:
            matches = [(row, step) for row, step in observed if preserved_call(row, expected)]
            assert matches, ('Base command did not execute', job_name, event, expected, observed)
            mandatory = [step for row, step in matches if step.get('continue-on-error', False) is False]
            assert mandatory, ('Base command is optional', job_name, event, expected)
            failures = []
            for step in mandatory:
                result, records = probe_preserved_step(workflow, job, step, event, expected)
                failures.append(result.returncode != 0 and any(preserved_call(row, expected) for row in records))
            assert any(failures), ('Masked base command failure', job_name, event, expected)

# Execute only isolated stand-ins; never rebuild or commit the candidate.
stub = r"""
import json, os, pathlib, sys
name = sys.argv[1]
args = sys.argv[2:]
with open(os.environ['DF11_DRIFT_LOG'], 'a', encoding='utf-8') as stream:
    stream.write(json.dumps([name, args, os.getcwd()]) + '\n')
if name == 'git':
    if 'status' in args and '--porcelain' in args and os.environ['DF11_DIRTY'] == '1':
        print(' M plugin/df11-drift.md')
    raise SystemExit(0)
raise SystemExit(int(os.environ['DF11_DRIFT_STATUS']) if name == os.environ['DF11_DRIFT_TARGET'] else 0)
"""
targets = ('generate-agent-router.py', 'generate-codex-plugin.py', 'generate-grok-plugin.py', 'build-plugin.sh')
for target in targets:
    selected = []
    for job in workflow.get('jobs', {}).values():
        for step in job.get('steps', []):
            tokens = shlex.split(step.get('run', ''), comments=True)
            command = tokens[1:2] if tokens[:1] in (['python'], ['python3']) else tokens[:1]
            if any(pathlib.PurePosixPath(token.rstrip(';')).name == target for token in command):
                selected.append((job, step))
    assert selected, ('Missing mandatory drift check', target)
    for job, step in selected:
        assert job.get('continue-on-error', False) is False, job
        assert step.get('continue-on-error', False) is False, step
        defaults = dict(workflow.get('defaults', {}).get('run', {}))
        defaults.update(job.get('defaults', {}).get('run', {}))
        environment = dict(workflow.get('env', {}))
        environment.update(job.get('env', {}))
        environment.update(step.get('env', {}))
        for event in ('push', 'pull_request'):
            assert enabled(job.get('if'), event), (target, event, job.get('if'))
            assert enabled(step.get('if'), event), (target, event, step.get('if'))
            with tempfile.TemporaryDirectory(prefix='.df11-', dir=source) as temporary:
                root = pathlib.Path(temporary)
                (root / 'scripts').mkdir()
                (root / 'bin').mkdir()
                (root / 'plugin').mkdir()
                (root / '.venv/bin').mkdir(parents=True)
                for interpreter in ('python', 'python3'):
                    (root / '.venv/bin' / interpreter).symlink_to(sys.executable)
                for name in (*targets[:3], 'lint_kb_links.py'):
                    (root / 'scripts' / name).write_text('import sys\nsys.argv.insert(1, ' + repr(name) + ')\n' + stub, encoding='utf-8')
                (root / 'scripts/df11_probe.py').write_text(stub, encoding='utf-8')
                build = root / 'build-plugin.sh'
                build.write_text('#!/bin/sh\nexec python3 scripts/df11_probe.py build-plugin.sh "$@"\n', encoding='utf-8')
                build.chmod(0o755)
                git = root / 'bin/git'
                git.write_text('#!/usr/bin/env python3\nimport sys\nsys.argv.insert(1, "git")\n' + stub, encoding='utf-8')
                git.chmod(0o755)
                script = root / 'step.sh'
                script.write_text(step['run'], encoding='utf-8')
                shell = step.get('shell', defaults.get('shell'))
                if shell is None:
                    command = ['bash', '-e', str(script)]
                elif shell == 'bash':
                    command = ['bash', '--noprofile', '--norc', '-e', '-o', 'pipefail', str(script)]
                elif shell == 'sh':
                    command = ['sh', '-e', str(script)]
                else:
                    command = [part.replace('{0}', str(script)) for part in shlex.split(shell)]
                def expand(value):
                    return str(value).replace('${{ github.workspace }}', str(root)).replace('${{github.workspace}}', str(root))
                directory = pathlib.Path(expand(step.get('working-directory', defaults.get('working-directory', '.'))))
                if not directory.is_absolute():
                    directory = root / directory
                env = os.environ.copy()
                env.update({key: expand(value) for key, value in environment.items()})
                env['PATH'] = str(root / 'bin') + os.pathsep + env.get('PATH', '')
                env['GITHUB_WORKSPACE'] = str(root)
                env['GITHUB_EVENT_NAME'] = event
                env['DF11_DRIFT_TARGET'] = target
                cases = [(0, False), (1, False)]
                if target == 'build-plugin.sh':
                    cases.append((0, True))
                for status, dirty in cases:
                    log = root / ('probe-' + str(status) + '-' + str(dirty) + '.jsonl')
                    env['DF11_DRIFT_LOG'] = str(log)
                    env['DF11_DRIFT_STATUS'] = str(status)
                    env['DF11_DIRTY'] = '1' if dirty else '0'
                    result = subprocess.run(command, cwd=directory, env=env, capture_output=True, text=True, timeout=60)
                    records = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
                    evidence = (target, event, status, dirty, result.returncode, records, result.stdout, result.stderr)
                    calls = [row for row in records if row[0] == target]
                    assert calls, evidence
                    assert all(pathlib.Path(row[2]).resolve() == root.resolve() for row in calls), evidence
                    if target.endswith('.py'):
                        assert all('--check' in row[1] for row in calls), evidence
                    if status:
                        assert result.returncode != 0, ('Masked drift-check failure', evidence)
                    elif dirty:
                        assert result.returncode == 1, ('Plugin drift must exit 1', evidence)
                    else:
                        assert result.returncode == 0, ('Clean drift check must pass', evidence)
                    if target == 'build-plugin.sh' and not status:
                        assert any(row[0] == 'git' and 'status' in row[1] and '--porcelain' in row[1] for row in records), ('Missing git status --porcelain check', evidence)
print('ok')
'''


def test_real_candidate_kb_and_mandatory_drift_checks():
    command = ([os.environ['FACTORY_CANDIDATE']] if os.environ.get('FACTORY_CANDIDATE') else []) + [sys.executable, '-c', _CI_AUDIT, _BASE_CI]
    result = subprocess.run(command, capture_output=True, text=True, timeout=1800)
    assert result.returncode == 0, result.stdout + result.stderr
