from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Config:
    def __init__(
        self,
        repo_address: str,
        output_path: Path,
        work_dir: Path,
        use_llm: bool,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_base_url: Optional[str] = None,   # <- Add this
    ):
        self.repo_address = repo_address
        self.output_path = output_path
        self.work_dir = work_dir
        self.use_llm = use_llm
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_base_url = llm_base_url or "https://openrouter.ai/api/v1"  # default

        # Optional: detect repo URL automatically
        self.repo_url = repo_address if repo_address.startswith("http") else None
