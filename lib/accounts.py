"""Load and validate the client registry from accounts.yml + .env."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class Account(BaseModel):
    slug: str
    display_name: str
    env_var: str
    locale: str = "cs"
    industry: str = "default"
    status: str = "active"   # active | setup | progress
    clickup_folder_name: Optional[str] = None
    notes: str = ""

    @property
    def api_key(self) -> str:
        """Read the Klaviyo Private API key from environment.

        Never log or print the return value. Use mask() if you need to show it.
        """
        key = os.environ.get(self.env_var)
        if not key:
            raise RuntimeError(
                f"Missing env var {self.env_var} for client {self.slug}. "
                f"Set it in .env (see .env.example)."
            )
        return key

    def mask(self) -> str:
        """Return a redacted form of the key for logging."""
        try:
            k = self.api_key
        except RuntimeError:
            return "<unset>"
        if len(k) < 10:
            return "<short>"
        return f"{k[:6]}…{k[-4:]}"


class ClickUpConfig(BaseModel):
    shared_list_id: str
    space_name: str
    campaign_field_cz: str
    campaign_field_sk: str


class ReportingConfig(BaseModel):
    default_timeframe: str = "last_90_days"
    short_timeframe: str = "last_30_days"
    output_dir: str = "outputs/"


class Registry(BaseModel):
    accounts: list[Account]
    clickup: ClickUpConfig
    reporting: ReportingConfig

    def by_slug(self, slug: str) -> Account:
        for a in self.accounts:
            if a.slug == slug:
                return a
        raise KeyError(f"No account with slug={slug}. Known: {[a.slug for a in self.accounts]}")

    def all_slugs(self) -> list[str]:
        return [a.slug for a in self.accounts]


_registry: Registry | None = None


def load_registry() -> Registry:
    """Load accounts.yml from repo root."""
    global _registry
    if _registry is not None:
        return _registry
    path = ROOT / "accounts.yml"
    if not path.exists():
        raise FileNotFoundError(f"accounts.yml not found at {path}")
    with path.open() as f:
        raw = yaml.safe_load(f)
    _registry = Registry(**raw)
    return _registry


if __name__ == "__main__":
    reg = load_registry()
    print(f"Loaded {len(reg.accounts)} accounts:")
    for a in reg.accounts:
        print(f"  {a.slug:20s}  {a.display_name:25s}  {a.locale}/{a.industry}  key={a.mask()}")
