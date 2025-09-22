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
        Compose a richer prompt for the LLM so it generates:
        - Project purpose
        - Installation
        - How to run
        - Key files/folders explanation
        - Testing notes
        - License info
        """
        files_list = ', '.join(metadata.top_files[:20])  # first 20 files for context
        languages = ', '.join(metadata.languages.keys()) or 'unknown'

        prompt = f"""
    You are an expert software engineer and documentation writer.

    Generate a detailed README for the repository "{metadata.name}".
    Include:

    1. Purpose of the project: what it does and who it's for.
    2. Main technologies and languages: {languages}.
    3. Installation instructions.
    4. How to run the code (examples if possible).
    5. Explanation of important files/folders: {files_list}.
    6. Notes about testing or environment setup if present.
    7. License information: {metadata.license or 'Unspecified'}.

    Write the README in clear Markdown format. Make it concise, practical, and friendly.
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
        ctx = self.build_context(metadata)
        content = self.template_engine.render("readme.md.jinja", ctx)
        output_path.write_text(content, encoding="utf8")
        return content
