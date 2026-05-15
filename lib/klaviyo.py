"""Minimal Klaviyo API client.

Only implements endpoints we actually use. Adds rate-limit handling and
key masking. Never logs or returns raw API keys.
"""
from __future__ import annotations

import time
from typing import Any, Iterator

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


BASE = "https://a.klaviyo.com/api"
REVISION = "2024-10-15"  # bump cautiously; new fields appear in newer revisions


class KlaviyoClient:
    """Thin Klaviyo wrapper.

    Usage:
        from lib.accounts import load_registry
        reg = load_registry()
        krekry = reg.by_slug("krekry_cz")
        with KlaviyoClient(krekry.api_key) as kl:
            acc = kl.get_account()
            flows = list(kl.list_flows())
    """

    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        if not api_key or not api_key.startswith("pk_"):
            raise ValueError("Invalid Klaviyo API key (expected pk_...)")
        self._key = api_key
        self._http = httpx.Client(
            base_url=BASE,
            timeout=timeout,
            headers={
                "Authorization": f"Klaviyo-API-Key {api_key}",
                "Accept": "application/json",
                "revision": REVISION,
            },
        )

    def __repr__(self) -> str:
        return f"KlaviyoClient(key={self._key[:6]}…{self._key[-4:]})"

    def __enter__(self) -> "KlaviyoClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self._http.close()

    # ---- low-level ----

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get(self, path: str, **params: Any) -> dict:
        r = self._http.get(path, params=params)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", "2")))
            r.raise_for_status()  # triggers retry
        r.raise_for_status()
        return r.json()

    def _paginate(self, path: str, **params: Any) -> Iterator[dict]:
        url: str | None = path
        first = True
        while url:
            if first:
                resp = self._get(path, **params)
                first = False
            else:
                # Klaviyo returns full next-page URLs in links.next
                full = httpx.URL(url)
                resp = self._get(str(full.copy_with(host="", scheme="").path or path),
                                 **dict(full.params))
            for row in resp.get("data", []):
                yield row
            url = resp.get("links", {}).get("next")

    # ---- endpoints ----

    def get_account(self) -> dict:
        """Return account.attributes for the connected key."""
        resp = self._get("/accounts/")
        data = resp.get("data", [])
        if not data:
            raise RuntimeError("Empty accounts response")
        return data[0]["attributes"]

    def list_flows(self, page_size: int = 50) -> Iterator[dict]:
        """Yield flow dicts with attributes name/status/triggerType."""
        yield from self._paginate(
            "/flows/",
            **{
                "page[size]": page_size,
                "fields[flow]": "name,status,trigger_type,created,updated",
            },
        )

    def list_metrics(self, integration_name: str | None = None) -> Iterator[dict]:
        """Yield metric dicts."""
        params: dict[str, Any] = {"fields[metric]": "name,integration"}
        if integration_name:
            params["filter"] = f'equals(integration.name,"{integration_name}")'
        yield from self._paginate("/metrics/", **params)

    def placed_order_metric_id(self) -> str | None:
        """Helper: find the Shopify (or fallback) Placed Order metric ID."""
        for m in self.list_metrics(integration_name="Shopify"):
            if m["attributes"]["name"] == "Placed Order":
                return m["id"]
        # Fallback: any integration
        for m in self.list_metrics():
            if m["attributes"]["name"] == "Placed Order":
                return m["id"]
        return None

    def flow_report(
        self,
        conversion_metric_id: str,
        timeframe_key: str = "last_90_days",
        statistics: list[str] | None = None,
    ) -> list[dict]:
        """POST to /flow-values-reports/.

        Returns list of per-message result dicts, each with:
          - groupings: {flow_id, flow_message_id, send_channel}
          - statistics: {open_rate, click_rate, conversion_value, ...}

        Note: Klaviyo requires flow_message_id in group_by and does not support
        flow-level aggregation in a single call — aggregate per flow_id yourself.
        The `value_statistics` field is not supported; revenue stats are in statistics.
        """
        stats = statistics or [
            "recipients", "delivered", "open_rate", "click_rate",
            "conversion_rate", "conversion_value", "revenue_per_recipient",
            "unsubscribe_rate", "bounce_rate",
        ]
        body = {
            "data": {
                "type": "flow-values-report",
                "attributes": {
                    "statistics": stats,
                    "conversion_metric_id": conversion_metric_id,
                    "timeframe": {"key": timeframe_key},
                    "filter": 'equals(send_channel,"email")',
                    "group_by": ["flow_id", "flow_message_id", "send_channel"],
                }
            }
        }
        r = self._http.post("/flow-values-reports/", json=body)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", "2")))
            r = self._http.post("/flow-values-reports/", json=body)
        r.raise_for_status()
        return r.json().get("data", {}).get("attributes", {}).get("results", [])

    def query_metric_aggregate(
        self,
        metric_id: str,
        measurements: list[str],
        start_iso: str,
        end_iso: str,
        group_by: list[str] | None = None,
        interval: str = "month",
        timezone: str = "Europe/Prague",
    ) -> dict:
        """POST to /metric-aggregates/. Returns response.data.attributes."""
        body = {
            "data": {
                "type": "metric-aggregate",
                "attributes": {
                    "metric_id": metric_id,
                    "measurements": measurements,
                    "interval": interval,
                    "page_size": 500,
                    "timezone": timezone,
                    "filter": [
                        f"greater-or-equal(datetime,{start_iso})",
                        f"less-than(datetime,{end_iso})",
                    ],
                },
            }
        }
        if group_by:
            body["data"]["attributes"]["by"] = group_by
        r = self._http.post("/metric-aggregates/", json=body)
        r.raise_for_status()
        return r.json().get("data", {}).get("attributes", {})
