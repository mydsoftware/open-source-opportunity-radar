import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('scan', Path(__file__).parents[1] / 'scripts' / 'scan.py')
scan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scan)


def test_license_scores_are_ordered():
    repo={'stargazers_count':10000,'forks_count':500,'open_issues_count':20,'pushed_at':'2026-09-01T00:00:00Z','name':'ai-agent','description':'AI agent'}
    mit=scan.score(repo,'AI',100)[0]
    agpl=scan.score(repo,'AI',45)[0]
    assert mit > agpl


def test_score_is_bounded():
    repo={'stargazers_count':10_000_000,'forks_count':1_000_000,'open_issues_count':0,'pushed_at':'x','name':'x','description':'x'}
    assert 0 <= scan.score(repo,'AI',100)[0] <= 100
