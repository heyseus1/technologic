# src/hue_async/clients/hue_client.py
from __future__ import annotations

"""
HueClient: thin HTTP wrapper around the Hue v2 local API.

This is intentionally "dumb":
- It knows how to build URLs and headers.
- It performs GET/PUT.
- It does NOT contain business logic like "room selection" or "scene filtering".
  That belongs in the service layer.

We keep it sync (requests) for now because you're prototyping locally and
want curl-like behavior. Later we can swap to async httpx with minimal changes.
"""

from typing import Any

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HueClient:
    def __init__(self, bridge_ip: str, app_key: str) -> None:
        self.bridge_ip = bridge_ip
        self.app_key = app_key

    def _url(self, path: str) -> str:
        # All Hue v2 endpoints are under https://<bridge>/clip/v2/resource/...
        return f"https://{self.bridge_ip}{path}"

    def _headers(self, json: bool = False) -> dict[str, str]:
        headers = {
            "hue-application-key": self.app_key,
            "Accept": "application/json",
        }
        if json:
            headers["Content-Type"] = "application/json"
        return headers

    def get(self, path: str) -> dict[str, Any]:
        r = requests.get(self._url(path), headers=self._headers(), verify=False, timeout=10)
        r.raise_for_status()
        return r.json()

    def put(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        r = requests.put(self._url(path), headers=self._headers(json=True), json=body, verify=False, timeout=10)
        r.raise_for_status()
        return r.json() if r.content else {}
