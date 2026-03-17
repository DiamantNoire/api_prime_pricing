import os
from dataclasses import dataclass
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / "dev_build_models").exists():
            return parent
    raise FileNotFoundError("Impossible de trouver le dossier dev_build_models")


@dataclass(frozen=True)
class Settings:
    app_name: str = "Prime Pricing API"
    app_version: str = "1.0.0"
    api_prefix: str = "/v1"

    @property
    def repo_root(self) -> Path:
        configured = os.getenv("REPO_ROOT")
        if configured:
            return Path(configured).resolve()
        return _find_repo_root(Path(__file__).resolve())

    @property
    def models_root(self) -> Path:
        configured = os.getenv("MODELS_ROOT")
        if configured:
            return Path(configured).resolve()
        return self.repo_root / "dev_build_models" / "sorties"


settings = Settings()
