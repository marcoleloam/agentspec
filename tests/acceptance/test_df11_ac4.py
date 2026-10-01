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
    result = subprocess.run([os.environ['FACTORY_CANDIDATE'], sys.executable, '-c', code], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    workflow = yaml.safe_load(data['workflow'])
    events = workflow.get('on', workflow.get(True))
    assert isinstance(events, dict), events
    changed_tests = [path for path, digest in data['tests'].items() if _BASE_TESTS.get(path) != digest]
    assert changed_tests, 'No new or modified executable test module under tests/'
    required = ['.claude/kb/index.md', '.claude/kb/deep/topic/page.MD', '.claude/kb/_templates/example.md.template', 'scripts/lint_kb_links.py', '.github/workflows/quality-checks.yml', *changed_tests]
    for event in ('push', 'pull_request'):
        assert event in events, events
        config = events[event]
        assert isinstance(config, dict) and isinstance(config.get('paths'), list), (event, config)
        assert 'paths-ignore' not in config, (event, config)
        for path in required:
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
