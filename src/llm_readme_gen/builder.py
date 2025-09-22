from pathlib import Path
from .analyzer import RepoMetadata
from .template_engine import TemplateEngine
from .llm_client import LLMClient, NoopLLMClient
from typing import Optional
from .config import Config


class ReadmeBuilder:
    def __init__(self, cfg: Config, llm: Optional[LLMClient] = None, template_dir: Path = Path("templates")):
        self.cfg = cfg
        self.llm = llm or NoopLLMClient()
        self.template_engine = TemplateEngine(template_dir)

    def build_context(self, metadata: RepoMetadata) -> dict:
        """
        Build context for README generation.
        Uses LLM to generate full README if enabled.
        """
        description = metadata.description or ""

        if self.cfg.use_llm:
            # Compose full README prompt instead of just short description
            prompt = self._compose_full_readme_prompt(metadata, self.cfg.repo_url)
            try:
                description = self.llm.generate(prompt, max_tokens=1500, temperature=0.2)
            except Exception:
                # fallback
                description = metadata.description or ""

        context = {
            "name": metadata.name,
            "description": description,
            "languages": metadata.languages,
            "top_files": metadata.top_files,
            "has_tests": metadata.has_tests,
            "dependencies": metadata.dependencies,
            "license": metadata.license or "Unspecified",
            "repo_url": self.cfg.repo_url or f"https://github.com/yourusername/{metadata.name}"
        }

        # Optionally keep heuristic usage if you want
        context.setdefault("usage", self._generate_usage_hint(metadata))

        return context

    def _compose_prompt_for_description(self, metadata: RepoMetadata) -> str:
        """
        Build a detailed prompt for the LLM so it writes an accurate README.
        """
        # Show top files (just 10) and include relative paths
        top_files = "\n".join(f"- {f}" for f in metadata.top_files[:10])

        # Show dependencies by language
        dependencies = "\n".join(
            f"- {lang}: {', '.join(pkgs)}" for lang, pkgs in (metadata.dependencies or {}).items()
        ) or "None"

        # Include first paragraph from existing README if exists
        readme_excerpt = ""
        readme_paths = [self.cfg.work_dir / "README.md", self.cfg.work_dir / "README.rst"]
        for p in readme_paths:
            if p.exists():
                readme_excerpt = "\n".join(p.read_text(errors="ignore").splitlines()[:10])
                break

        prompt = f"""
    You are a helpful assistant generating a README.md for a GitHub repository.
    Use ONLY the information provided. Do NOT make up commands, repo names, or URLs.

    Repository name: {metadata.name}
    Short description: {metadata.description or 'N/A'}
    Languages used: {', '.join(metadata.languages.keys()) or 'unknown'}
    Top files (from repo root):
    {top_files}
    Dependencies:
    {dependencies}
    First few lines of existing README (if any):
    {readme_excerpt or 'None'}

    Write a README that includes:

    1. Correct project title
    2. Description (summarize functionality based on files and description)
    3. Installation instructions (based on detected dependencies)
    4. Usage instructions (based on detected main files)
    5. Project structure (list top files)
    6. Tests (if detected)
    7. License (if available)

    Do not fabricate any information. Use proper Markdown formatting.
    """
        return prompt
    
    def _compose_full_readme_prompt(self, metadata: RepoMetadata, repo_url: str) -> str:
        """
        Generate a detailed prompt for the full README using repo metadata.
        """
        prompt = f"""
    You are a helpful assistant. Write a complete, factual README for the repository.

    Repository Name: {metadata.name}
    Repository URL: {repo_url}
    Short Description: {metadata.description or 'No description provided'}
    Languages: {', '.join(metadata.languages.keys()) or 'unknown'}
    Top Files: {', '.join(metadata.top_files[:10])}
    Dependencies: {metadata.dependencies or 'None detected'}
    Tests Included: {'Yes' if metadata.has_tests else 'No'}
    License: {metadata.license or 'Unspecified'}

    Include sections:
    - Project Overview
    - Installation Instructions (use detected dependencies)
    - Usage Guide (include example commands based on main files)
    - Project Structure (list top files/directories)
    - Testing Instructions
    - License Information

    Make the instructions accurate and specific to the repository. Avoid generic placeholders like 'repo' or 'python -m <package>'.
    """
        return prompt

    def _generate_usage_hint(self, metadata: RepoMetadata) -> str:
        # heuristic usage hints
        if "Python" in metadata.languages:
            if "requirements.txt" in (metadata.dependencies.get("python") or []):
                return "pip install -r requirements.txt\npython -m <package>"
            return "python -m <package> or python main.py"
        if "JavaScript" in metadata.languages or "TypeScript" in metadata.languages:
            return "npm install\nnpm start"
        return "See project files for usage instructions."

    def render(self, metadata: RepoMetadata, output_path: Path):
    # If LLM is enabled, generate the entire README
        if self.cfg.use_llm:
            prompt = self._compose_full_readme_prompt(metadata, repo_url=self.cfg.repo_address)
            content = self.llm.generate(prompt, max_tokens=1500)
        else:
            # Fallback: use template-based generation
            ctx = self.build_context(metadata)
            content = self.template_engine.render("readme.md.jinja", ctx)

        output_path.write_text(content, encoding="utf8")
        return content