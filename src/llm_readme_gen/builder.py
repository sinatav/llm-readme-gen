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
        # Basic context created from metadata; LLM can expand description + usage
        description = metadata.description or ""
        # If LLM is enabled, ask it to write a polished project summary
        if self.cfg.use_llm:
            prompt = self._compose_prompt_for_description(metadata)
            try:
                description = self.llm.generate(prompt, max_tokens=400, temperature=0.2)
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
        }
        # Add a basic usage example generated heuristically or via LLM
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
    
    def _compose_full_readme_prompt(self, metadata: RepoMetadata) -> str:
        prompt = f"""
        Write a detailed and structured README for a GitHub repository with the following details:
        - **Name**: {metadata.name}
        - **Description**: {metadata.description or 'N/A'}
        - **Languages**: {', '.join(metadata.languages.keys()) or 'unknown'}
        - **Top Files**: {', '.join(metadata.top_files[:5])}
        - **Dependencies**: {', '.join(metadata.dependencies.get('python', [])) or 'None'}
        - **License**: {metadata.license or 'Unspecified'}

        The README should include:
        1. **Project Overview**: A brief introduction to the project.
        2. **Installation Instructions**: Steps to install and set up the project.
        3. **Usage Guide**: How to use the project, including code examples.
        4. **Project Structure**: Explanation of the project's directory and file structure.
        5. **Testing**: Information on how to run tests, if applicable.
        6. **License Information**: Details about the project's license.

        Ensure the content is clear, concise, and suitable for a GitHub repository.
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
            prompt = self._compose_full_readme_prompt(metadata)
            content = self.llm.generate(prompt, max_tokens=1500)
        else:
            # Fallback: use template-based generation
            ctx = self.build_context(metadata)
            content = self.template_engine.render("readme.md.jinja", ctx)

        output_path.write_text(content, encoding="utf8")
        return content