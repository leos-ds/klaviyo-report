"""Flow performance audit per client.

Usage:
    python scripts/audit.py --client krekry_cz
    python scripts/audit.py --all
    python scripts/audit.py --client krekry_cz --timeframe last_30_days

Output: outputs/{slug}/audit_YYYY-MM-DD.md

Notes on Klaviyo API:
- flow-values-reports always returns per-message rows (flow_message_id required in group_by)
- There is no flow-level aggregation endpoint — we aggregate from messages ourselves
- revenue stats (conversion_value, revenue_per_recipient) live in statistics, not value_statistics
"""
from __future__ import annotations

import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.accounts import Account, load_registry
from lib.benchmarks import benchmark_open, flow_category, grade
from lib.klaviyo import KlaviyoClient

console = Console()
ROOT = Path(__file__).resolve().parent.parent


def strip_leading_emoji(s: str) -> str:
    """Remove leading emoji characters from a string (Klaviyo flow names often have them)."""
    import re
    return re.sub(r'^[\U00010000-\U0010ffff\U00002600-\U000027FF\U0001F300-\U0001FAFF\s]+', '', s).strip()


def fmt_pct(v: float | None) -> str:
    return "—" if v is None else f"{v * 100:.1f} %"


def fmt_num(v: float | None) -> str:
    return "—" if v is None else f"{round(v):,}".replace(",", " ")


def fmt_money(v: float | None) -> str:
    return "—" if v is None else f"{round(v):,}".replace(",", " ")


def aggregate_flow(messages: list[dict]) -> dict:
    """Aggregate per-message stats into a single flow-level stat dict.

    Uses delivered-weighted averages for rates and sums for totals.
    """
    total_delivered = sum(m["statistics"].get("delivered") or 0 for m in messages)
    total_recipients = sum(m["statistics"].get("recipients") or 0 for m in messages)
    total_conv_value = sum(m["statistics"].get("conversion_value") or 0 for m in messages)

    def wavg(key: str) -> float | None:
        if not total_delivered:
            return None
        return sum((m["statistics"].get(key) or 0) * (m["statistics"].get("delivered") or 0)
                   for m in messages) / total_delivered

    rpr = total_conv_value / total_recipients if total_recipients else None

    return {
        "recipients": total_recipients,
        "delivered": total_delivered,
        "open_rate": wavg("open_rate"),
        "click_rate": wavg("click_rate"),
        "conversion_rate": wavg("conversion_rate"),
        "unsubscribe_rate": wavg("unsubscribe_rate"),
        "bounce_rate": wavg("bounce_rate"),
        "conversion_value": total_conv_value,
        "revenue_per_recipient": rpr,
    }


def audit_client(acc: Account, timeframe: str) -> str:
    """Run audit and return the markdown report."""
    with KlaviyoClient(acc.api_key) as kl:
        account = kl.get_account()
        account_name = account.get("contact_information", {}).get("organization_name", acc.display_name)
        currency = account.get("preferred_currency", "")

        # Find conversion metric
        metric_id = kl.placed_order_metric_id()
        if not metric_id:
            return (
                f"# {account_name} — Audit failed\n\n"
                "No 'Placed Order' metric found. Cannot grade conversion rates.\n"
            )

        # Pull all flows
        flows = list(kl.list_flows())
        live = [f for f in flows if f.get("attributes", {}).get("status") == "live"]
        if not live:
            return (
                f"# {account_name} — Audit failed\n\n"
                f"No live flows found (saw {len(flows)} total).\n"
            )

        # Build id → name map
        flow_name_map: dict[str, str] = {
            f["id"]: f.get("attributes", {}).get("name", f["id"])
            for f in flows
        }
        live_id_set = {f["id"] for f in live}

        # Single API call — returns per-message rows
        messages = kl.flow_report(
            conversion_metric_id=metric_id,
            timeframe_key=timeframe,
        )

        # Group messages by flow_id (only live flows)
        msgs_by_flow: dict[str, list[dict]] = defaultdict(list)
        for m in messages:
            fid = m.get("groupings", {}).get("flow_id", "")
            if fid in live_id_set:
                msgs_by_flow[fid].append(m)

    # Aggregate to flow level
    flow_agg: list[dict] = []
    for fid, msgs in msgs_by_flow.items():
        flow_agg.append({
            "flow_id": fid,
            "flow_name": flow_name_map.get(fid, fid),
            "statistics": aggregate_flow(msgs),
            "messages": msgs,
        })

    # Also include live flows with zero data in the report
    for f in live:
        if f["id"] not in msgs_by_flow:
            flow_agg.append({
                "flow_id": f["id"],
                "flow_name": flow_name_map.get(f["id"], f["id"]),
                "statistics": {},
                "messages": [],
            })

    return render_report(
        account_name=account_name,
        currency=currency,
        slug=acc.slug,
        industry=acc.industry,
        timeframe=timeframe,
        flows_total=len(flows),
        flow_agg=flow_agg,
    )


def render_report(
    account_name: str,
    currency: str,
    slug: str,
    industry: str,
    timeframe: str,
    flows_total: int,
    flow_agg: list[dict],
) -> str:
    today = dt.date.today().isoformat()
    lines: list[str] = []
    lines.append(f"# {account_name} — Klaviyo Flow Audit")
    lines.append(
        f"> Date: {today} · Industry: `{industry}` · Currency: {currency} · Timeframe: `{timeframe}`  "
        f"\n> Live flows: {len(flow_agg)} of {flows_total} total"
    )
    lines.append("")

    # Red flags
    bads: list[dict] = []
    for f in flow_agg:
        name = f["flow_name"]
        cat = flow_category(name)
        s = f["statistics"]
        g_open = grade("open", s.get("open_rate"), cat, industry)
        g_conv = grade("conv", s.get("conversion_rate"), cat, industry)
        if g_open == "bad" or (g_conv == "bad" and cat != "sunset"):
            bads.append(f)

    if bads:
        lines.append("## 🔴 Red flags")
        for f in bads:
            name = strip_leading_emoji(f["flow_name"])
            s = f["statistics"]
            cat = flow_category(name)
            bench = benchmark_open(cat, industry)
            actual = s.get("open_rate") or 0
            gap = round((1 - actual / bench) * 100) if bench else 0
            lines.append(
                f"- **{name}** — open {fmt_pct(s.get('open_rate'))} "
                f"vs benchmark {bench*100:.0f}% (−{gap}%). "
                f"Conv: {fmt_pct(s.get('conversion_rate'))}."
            )
        lines.append("")
    else:
        lines.append("## ✅ All live flows meet benchmark thresholds\n")

    # Flow summary table
    lines.append("## Flow performance")
    lines.append("")
    lines.append(f"| Flow | Recipients | Open rate | CTR | Conv rate | RPR ({currency}) | Revenue ({currency}) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for f in sorted(flow_agg, key=lambda x: -(x["statistics"].get("conversion_value") or 0)):
        name = strip_leading_emoji(f["flow_name"])
        s = f["statistics"]
        cat = flow_category(name)
        bench = benchmark_open(cat, industry)
        g = grade("open", s.get("open_rate"), cat, industry)
        emoji = {"good": "🟢", "warn": "🟡", "bad": "🔴", "neutral": "⚪"}[g]
        lines.append(
            f"| {emoji} {name} "
            f"| {fmt_num(s.get('recipients'))} "
            f"| {fmt_pct(s.get('open_rate'))} *(>{bench*100:.0f}%)* "
            f"| {fmt_pct(s.get('click_rate'))} "
            f"| {fmt_pct(s.get('conversion_rate'))} "
            f"| {fmt_money(s.get('revenue_per_recipient'))} "
            f"| {fmt_money(s.get('conversion_value'))} |"
        )
    lines.append("")

    # Per-message drilldown for red-flagged flows
    if bads:
        lines.append("## Per-message drilldown (red-flagged flows only)")
        lines.append("")
        for f in bads:
            name = strip_leading_emoji(f["flow_name"])
            msgs = sorted(f["messages"], key=lambda x: -(x["statistics"].get("conversion_value") or 0))
            lines.append(f"### {name}")
            lines.append("")
            lines.append(f"| # | Message ID | Recipients | Open | CTR | Conv | RPR | Revenue |")
            lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
            for i, m in enumerate(msgs, 1):
                g = m.get("groupings", {})
                s = m.get("statistics", {})
                mid = g.get("flow_message_id", "?")
                lines.append(
                    f"| {i} | `{mid}` "
                    f"| {fmt_num(s.get('recipients'))} "
                    f"| {fmt_pct(s.get('open_rate'))} "
                    f"| {fmt_pct(s.get('click_rate'))} "
                    f"| {fmt_pct(s.get('conversion_rate'))} "
                    f"| {fmt_money(s.get('revenue_per_recipient'))} "
                    f"| {fmt_money(s.get('conversion_value'))} |"
                )
            lines.append("")

    lines.append("---")
    lines.append(f"_Generated by `audit.py` for account `{slug}`._")
    return "\n".join(lines)


@click.command()
@click.option("--client", default=None, help="Audit single client by slug")
@click.option("--all", "run_all", is_flag=True, help="Audit all clients")
@click.option("--timeframe", default="last_90_days", help="last_30_days | last_90_days | last_365_days")
def main(client: str | None, run_all: bool, timeframe: str) -> None:
    if not client and not run_all:
        console.print("[red]Specify --client <slug> or --all[/red]")
        sys.exit(1)

    reg = load_registry()
    targets = reg.accounts if run_all else [reg.by_slug(client)]
    output_root = ROOT / "outputs"

    with Progress(console=console) as bar:
        task = bar.add_task("Auditing", total=len(targets))
        for acc in targets:
            try:
                md = audit_client(acc, timeframe)
                out_dir = output_root / acc.slug
                out_dir.mkdir(parents=True, exist_ok=True)
                fname = f"audit_{dt.date.today().isoformat()}.md"
                (out_dir / fname).write_text(md, encoding="utf-8")
                console.print(f"[green]✓[/green] {acc.slug}: {out_dir / fname}")
            except Exception as e:
                console.print(f"[red]✗[/red] {acc.slug}: {type(e).__name__}: {e}")
            bar.advance(task)


if __name__ == "__main__":
    main()
