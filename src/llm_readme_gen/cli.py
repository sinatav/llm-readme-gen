import argparse
from pathlib import Path
from .config import Config
from .repo_fetcher import RepoFetcher
from .analyzer import RepoAnalyzer
from .builder import ReadmeBuilder
from .llm_client import NoopLLMClient, OpenAIClient, DeepSeekClient
import os


def main(argv=None):
    parser = argparse.ArgumentParser(prog="llm-readme-gen")
    parser.add_argument("repo", help="git URL or local path to repository")
    parser.add_argument("--out", "-o", default="GENERATED_README.md", help="output README path")
    parser.add_argument("--work-dir", default=".cache_repo")
    parser.add_argument("--use-llm", action="store_true", help="use configured LLM to enhance text")
    parser.add_argument("--provider", choices=["openai", "deepseek"], default=None)
    parser.add_argument("--model", default=None, help="LLM model to use (e.g., deepseek-chat or OpenAI model)")
    args = parser.parse_args(argv)

    cfg = Config(repo_address=args.repo, output_path=Path(args.out), work_dir=Path(args.work_dir), use_llm=args.use_llm, llm_provider=args.provider, llm_model=args.model,)

    fetcher = RepoFetcher(cfg)
    repo_root = fetcher.fetch()

    analyzer = RepoAnalyzer(repo_root)
    metadata = analyzer.analyze()

    llm = None
    if cfg.use_llm:
        if cfg.llm_provider == "deepseek":
            key = os.getenv("DEEPSEEK_API_KEY")
            if not key:
                raise RuntimeError("DEEPSEEK_API_KEY not set in environment")
            model = cfg.llm_model or "deepseek-chat"
            base_url = cfg.llm_base_url or "https://api.deepseek.com"
            llm = DeepSeekClient(api_key=key, model=model, base_url=base_url)
        elif cfg.llm_provider == "openai":
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise RuntimeError("OPENAI_API_KEY not set in environment")
            llm = OpenAIClient(api_key=key)
        else:
            llm = NoopLLMClient()
    else:
        llm = NoopLLMClient()


    builder = ReadmeBuilder(cfg, llm=llm, template_dir=Path(__file__).parent.parent.parent / "templates")
    content = builder.render(metadata, cfg.output_path)
    print(f"Wrote README to {cfg.output_path}")
    print("---\nPreview:\n")
    print(content[:1000])  # small preview


if __name__ == "__main__":
    main()
