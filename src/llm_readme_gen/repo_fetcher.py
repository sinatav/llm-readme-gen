import shutil
import subprocess
from pathlib import Path
from typing import Tuple
from config import Config


class RepoFetcher:
    """
    Clone a git repository to a working directory or validate a local path.
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.work_dir = Path(cfg.work_dir).absolute()

    def prepare(self) -> Path:
        """Ensure work_dir exists and is empty."""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        return self.work_dir

    def fetch(self) -> Path:
        """
        If repo_address is a git URL -> clone into work_dir/repo
        If it's a local path -> validate and copy (or use in place)
        Returns path to checked out repository root.
        """
        addr = self.cfg.repo_address
        repo_root = self.prepare() / "repo"
        if addr.startswith(("http://", "https://", "git@")):
            cmd = ["git", "clone", "--depth", "1", addr, str(repo_root)]
            subprocess.run(cmd, check=True)
            return repo_root
        else:
            local = Path(addr).expanduser()
            if not local.exists():
                raise FileNotFoundError(f"Local path {local} does not exist")
            # copy contents to repo_root to avoid changing user files
            shutil.copytree(local, repo_root)
            return repo_root
