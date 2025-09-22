from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Config:
    repo_address: str                 # git URL or local path
    output_path: Path = Path("README.md")
    work_dir: Path = Path(".cache_repo")
    use_llm: bool = False
    llm_provider: Optional[str] = None   # "openai" or "deepseek"
    llm_model: Optional[str] = None      # e.g. "deepseek-chat" or "deepseek-reasoner"
    llm_base_url: Optional[str] = None   # optional override
