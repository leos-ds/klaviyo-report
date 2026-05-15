"""Verify every account in accounts.yml is reachable.

Usage:
    python scripts/smoke_test.py            # test all
    python scripts/smoke_test.py --client krekry_cz  # one client
"""
from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.accounts import load_registry
from lib.klaviyo import KlaviyoClient

console = Console()


@click.command()
@click.option("--client", default=None, help="Test only this slug")
def main(client: str | None) -> None:
    reg = load_registry()
    targets = [reg.by_slug(client)] if client else reg.accounts

    tbl = Table(title="Klaviyo connection smoke test")
    tbl.add_column("Slug", style="cyan")
    tbl.add_column("Account", style="white")
    tbl.add_column("Currency", justify="center")
    tbl.add_column("Timezone")
    tbl.add_column("Status", justify="center")

    fails = 0
    for acc in targets:
        try:
            with KlaviyoClient(acc.api_key) as kl:
                a = kl.get_account()
                name = a.get("contact_information", {}).get("organization_name", "?")
                cur = a.get("preferred_currency", "?")
                tz = a.get("timezone", "?")
                tbl.add_row(acc.slug, name, cur, tz, "[green]✓[/green]")
        except Exception as e:
            tbl.add_row(acc.slug, "—", "—", "—", f"[red]✗ {type(e).__name__}[/red]")
            fails += 1

    console.print(tbl)
    if fails:
        console.print(f"\n[red]{fails} client(s) failed.[/red] Check .env values.")
        sys.exit(1)
    console.print(f"\n[green]All {len(targets)} client(s) connected.[/green]")


if __name__ == "__main__":
    main()
