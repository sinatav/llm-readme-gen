from pathlib import Path
from llm_readme_gen.analyzer import RepoAnalyzer

def test_analyzer_on_simple_repo(tmp_path):
    # create dummy files
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hi')")
    (repo / "requirements.txt").write_text("requests")
    (repo / "LICENSE").write_text("MIT License")
    analyzer = RepoAnalyzer(repo)
    meta = analyzer.analyze()
    assert meta.name == "repo"
    assert "Python" in meta.languages
    assert meta.license == "MIT"
    assert "requirements.txt" in meta.dependencies.get("python", [])
