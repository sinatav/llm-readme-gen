import argparse
from pathlib import Path
from config import Config
from repo_fetcher import RepoFetcher
from analyzer import RepoAnalyzer
from builder import ReadmeBuilder
from llm_client import NoopLLMClient, OpenAIClient
import os


def main(argv=None):
    parser = argparse.ArgumentParser(prog="llm-readme-gen")
    parser.add_argument("repo", help="git URL or local path to repository")
    parser.add_argument("--out", "-o", default="GENERATED_README.md", help="output README path")
    parser.add_argument("--work-dir", default=".cache_repo")
    parser.add_argument("--use-llm", action="store_true", help="use configured LLM to enhance text")
    parser.add_argument("--provider", choices=["openai"], default=None)
    args = parser.parse_args(argv)

    cfg = Config(repo_address=args.repo, output_path=Path(args.out), work_dir=Path(args.work_dir), use_llm=args.use_llm, llm_provider=args.provider)

    fetcher = RepoFetcher(cfg)
    repo_root = fetcher.fetch()

    analyzer = RepoAnalyzer(repo_root)
    metadata = analyzer.analyze()

    llm = None
    if cfg.use_llm and cfg.llm_provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        llm = OpenAIClient(api_key=key)
    else:
        llm = NoopLLMClient()

    builder = ReadmeBuilder(cfg, llm=llm, template_dir=Path(__file__).parent.parent.parent / "templates")
    content = builder.render(metadata, cfg.output_path)
    print(f"Wrote README to {cfg.output_path}")
    print("---\nPreview:\n")
    print(content[:1000])  # small preview
