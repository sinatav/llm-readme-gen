from dataclasses import dataclass
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional
import re

EXT_LANG_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".java": "Java", ".go": "Go", ".rs": "Rust", ".cpp": "C++", ".c": "C",
    ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift"
}


@dataclass
class RepoMetadata:
    name: str
    description: Optional[str]
    languages: Dict[str, int]
    top_files: List[str]
    has_tests: bool
    dependencies: Dict[str, List[str]]  # e.g., {"python": ["requirements.txt"], "node": ["package.json"]}
    license: Optional[str]
    readme_exists: bool


class RepoAnalyzer:
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).absolute()

    def analyze(self) -> RepoMetadata:
        name = self.repo_path.name
        description = self._extract_description()
        languages = self._detect_languages()
        top_files = self._top_files()
        has_tests = self._detect_tests()
        dependencies = self._detect_dependencies()
        license_name = self._detect_license()
        readme_exists = (self.repo_path / "README.md").exists() or (self.repo_path / "README.rst").exists()
        return RepoMetadata(
            name=name,
            description=description,
            languages=languages,
            top_files=top_files,
            has_tests=has_tests,
            dependencies=dependencies,
            license=license_name,
            readme_exists=readme_exists
        )

    def _all_files(self):
        for p in self.repo_path.rglob("*"):
            if p.is_file():
                yield p

    def _detect_languages(self) -> Dict[str, int]:
        counter = Counter()
        for p in self._all_files():
            ext = p.suffix.lower()
            if ext in EXT_LANG_MAP:
                counter[EXT_LANG_MAP[ext]] += 1
        return dict(counter.most_common())

    def _top_files(self, n=10) -> List[str]:
        files = [p for p in self._all_files()]
        files.sort(key=lambda p: p.stat().st_size, reverse=True)
        return [str(p.relative_to(self.repo_path)) for p in files[:n]]

    def _detect_tests(self) -> bool:
        # Simple heuristics: presence of tests/ directory or files named test_*.py or *_test.go etc.
        for p in self.repo_path.rglob("*"):
            if p.is_dir() and p.name.lower().startswith("test"):
                return True
            if p.is_file() and re.search(r"(?:^test_|_test\.)", p.name):
                return True
        return False

    def _detect_dependencies(self) -> Dict[str, List[str]]:
        deps = {}
        py_req = self.repo_path / "requirements.txt"
        py_proj = self.repo_path / "pyproject.toml"
        pkg_json = self.repo_path / "package.json"
        if py_req.exists():
            deps.setdefault("python", []).append("requirements.txt")
        if py_proj.exists():
            deps.setdefault("python", []).append("pyproject.toml")
        if pkg_json.exists():
            deps.setdefault("node", []).append("package.json")
        return deps

    def _detect_license(self) -> Optional[str]:
        # read top level LICENSE or LICENSE.* first 1KB to try find type
        for lic in self.repo_path.glob("LICENSE*"):
            try:
                text = lic.read_text(encoding="utf8", errors="ignore")[:2000].lower()
                if "mit license" in text or "mit" in text:
                    return "MIT"
                if "apache" in text:
                    return "Apache"
                if "gpl" in text:
                    return "GPL"
                return lic.name
            except Exception:
                return lic.name
        return None

    def _extract_description(self) -> Optional[str]:
        # heuristics: read existing README short first paragraph or pyproject description
        readme_paths = [self.repo_path / "README.md", self.repo_path / "README.rst"]
        for p in readme_paths:
            if p.exists():
                text = p.read_text(errors="ignore")
                # first non-empty paragraph
                for part in text.split("\n\n"):
                    s = part.strip()
                    if s:
                        # return first line or trimmed paragraph
                        return s.splitlines()[0].strip()
        # fallback: pyproject.toml description
        pyproj = self.repo_path / "pyproject.toml"
        if pyproj.exists():
            content = pyproj.read_text(errors="ignore")
            m = re.search(r'description\s*=\s*"(.*?)"', content)
            if m:
                return m.group(1)
        return None

