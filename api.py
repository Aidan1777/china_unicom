"""API client for China Unicom."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import aiohttp
from aiohttp import ClientSession

from .const import (
    API_BALANCE_DETAIL,
    API_GET_TICKET,
    API_QUERY_GOODS_LIST,
    API_SERVICE_ENTRANCE,
    API_SSPBIGBALL,
    API_USAGE_DETAIL,
    HEADERS_FORM,
    HEADERS_JSON,
)

_LOGGER = logging.getLogger(__name__)


def _safe_float(value: str | float | None) -> float:
    """Safely convert a value to float."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


class UnicomAPI:
    """China Unicom API client."""

    def __init__(self, session: ClientSession, openid: str) -> None:
        self.session = session
        self.openid = openid
        self._ticket = ""
        self._ticket_phone = ""
        self._micro_hall_user = ""
        self._micro_hall_access_token = ""
        self._auth_lock = asyncio.Lock()
        self._api_lock = asyncio.Lock()

    async def _auto_get_auth(self) -> None:
        """Auto-fetch authentication ticket and cookies."""
        async with self._auth_lock:
            try:
                payload = {"openId": self.openid, "channel": "wxmini"}
                async with self.session.post(
                    API_GET_TICKET, json=payload, headers=HEADERS_JSON
                ) as resp:
                    text = await resp.text()
                    data = json.loads(text)
                    if data.get("code") != "0000":
                        _LOGGER.warning("getTicket failed: %s", data.get("code"))
                        return
                    self._ticket = data.get("data", "")
                    self._ticket_phone = f"wx{int(time.time() * 1000)}"
            except Exception as err:
                _LOGGER.warning("Auto-auth failed: %s", err)
                return

            try:
                entrance_url = (
                    f"{API_SERVICE_ENTRANCE}"
                    f"?ticket={self._ticket}"
                    f"&servicecode=YH10007"
                    f"&ticketChannel=XCXSYHF"
                )
                async with self.session.get(entrance_url) as entrance_resp:
                    for cookie_str in entrance_resp.headers.getall("Set-Cookie", []):
                        if "microHallUser=" in cookie_str:
                            self._micro_hall_user = (
                                cookie_str.split("microHallUser=", 1)[1]
                                .split(";")[0]
                                .strip()
                            )
                        if "microHallAccessToken=" in cookie_str:
                            self._micro_hall_access_token = (
                                cookie_str.split("microHallAccessToken=", 1)[1]
                                .split(";")[0]
                                .strip()
                            )
            except Exception:
                pass

    async def get_overview(self) -> dict[str, Any]:
        """Get overview from sspbigball API."""
        payload = {"openid": self.openid, "channel": "wxmini"}
        async with self.session.post(
            API_SSPBIGBALL, json=payload, headers=HEADERS_JSON
        ) as resp:
            text = await resp.text()
            data = json.loads(text)
            if data.get("code") == "0000":
                return data.get("data", {})
            return {}

    async def get_phone_number(self) -> str | None:
        """Extract phone number from queryGoodsList API."""
        payload = {"openid": self.openid, "channel": "wxmini"}
        async with self.session.post(
            API_QUERY_GOODS_LIST, json=payload, headers=HEADERS_JSON
        ) as resp:
            text = await resp.text()
            data = json.loads(text)
            if data.get("code") == "0000" and data.get("data", {}).get("res"):
                for item in data["data"]["res"]:
                    num = item.get("mainNumber", "")
                    if num and len(num) == 11 and num.startswith("1"):
                        return num
        return None

    async def get_balance_detail(self) -> dict[str, Any]:
        """Get balance detail."""
        form_data = {
            "duanlianjieabc": "",
            "channelCode": "",
            "serviceType": "",
            "saleChannel": "",
            "externalSources": "",
            "contactCode": "",
            "ticket": self._ticket,
            "ticketPhone": self._ticket_phone,
            "ticketChannel": "XCXSYHF",
            "language": "chinese",
            "channel": "client",
            "openid": self.openid,
        }
        headers = HEADERS_FORM.copy()
        cookies = []
        if self._micro_hall_user:
            cookies.append(f"microHallUser={self._micro_hall_user}")
        if self._micro_hall_access_token:
            cookies.append(f"microHallAccessToken={self._micro_hall_access_token}")
        if cookies:
            headers["Cookie"] = "; ".join(cookies)

        async with self.session.post(
            API_BALANCE_DETAIL, data=form_data, headers=headers
        ) as resp:
            text = await resp.text()
            data = json.loads(text)
            if data.get("code") == "0000":
                return data.get("data", data)
            _LOGGER.warning("Balance API error: code=%s", data.get("code"))
            return {}

    async def get_usage_detail(self) -> dict[str, Any]:
        """Get usage detail (flow/voice/SMS)."""
        form_data = {
            "duanlianjieabc": "",
            "channelCode": "",
            "serviceType": "",
            "saleChannel": "",
            "externalSources": "",
            "contactCode": "",
            "ticket": self._ticket,
            "ticketPhone": self._ticket_phone,
            "ticketChannel": "XCXYLCXYY",
            "language": "chinese",
            "openid": self.openid,
        }
        headers = HEADERS_FORM.copy()
        cookies = []
        if self._micro_hall_user:
            cookies.append(f"microHallUser={self._micro_hall_user}")
        if self._micro_hall_access_token:
            cookies.append(f"microHallAccessToken={self._micro_hall_access_token}")
        if cookies:
            headers["Cookie"] = "; ".join(cookies)

        async with self.session.post(
            API_USAGE_DETAIL, data=form_data, headers=headers
        ) as resp:
            text = await resp.text()
            data = json.loads(text)
            parsed: dict[str, Any] = {"data_items": []}

            # Parse data items (elemType=3: flow)
            if data.get("shareData") and data["shareData"].get("details"):
                for item in data["shareData"]["details"]:
                    if isinstance(item, dict) and item.get("elemType") == "3":
                        parsed["data_items"].append({
                            "addUpItemName": item.get("addUpItemName"),
                            "use": item.get("use"),
                            "total": item.get("total"),
                            "remain": item.get("remain"),
                            "xexceedvalue": item.get("xexceedvalue"),
                            "usedPercent": item.get("usedPercent"),
                            "endDate": item.get("endDate"),
                            "beforeTotal": item.get("beforeTotal"),
                            "flowType": item.get("flowType"),
                        })

            # Parse voice (elemType=1) and SMS (elemType=2)
            resources = data.get("resources", [])
            voice_items = []
            sms_items = []

            if isinstance(resources, list):
                for group in resources:
                    if not isinstance(group, dict):
                        continue
                    details = group.get("details", [])
                    if not isinstance(details, list):
                        continue
                    for item in details:
                        if not isinstance(item, dict):
                            continue
                        etype = item.get("elemType")
                        if etype == "1":
                            voice_items.append(item)
                        elif etype == "2":
                            sms_items.append(item)

            if voice_items:
                total_use = sum(_safe_float(i.get("use")) for i in voice_items)
                total_total = sum(_safe_float(i.get("total")) for i in voice_items)
                total_remain = sum(_safe_float(i.get("remain")) for i in voice_items)
                used_pct = round(total_use / total_total * 100) if total_total > 0 else 0
                parsed["voice"] = {
                    "use": str(int(total_use)) if total_use == int(total_use) else str(total_use),
                    "total": str(int(total_total)) if total_total == int(total_total) else str(total_total),
                    "remain": str(int(total_remain)) if total_remain == int(total_remain) else str(total_remain),
                    "usedPercent": str(used_pct),
                }

            if sms_items:
                total_use = sum(_safe_float(i.get("use")) for i in sms_items)
                total_total = sum(_safe_float(i.get("total")) for i in sms_items)
                total_remain = sum(_safe_float(i.get("remain")) for i in sms_items)
                used_pct = round(total_use / total_total * 100) if total_total > 0 else 0
                parsed["sms"] = {
                    "use": str(int(total_use)) if total_use == int(total_use) else str(total_use),
                    "total": str(int(total_total)) if total_total == int(total_total) else str(total_total),
                    "remain": str(int(total_remain)) if total_remain == int(total_remain) else str(total_remain),
                    "usedPercent": str(used_pct),
                }

            return parsed

    async def fetch_all_data(self) -> dict[str, Any]:
        """Fetch all Unicom data APIs.

        Uses instance lock to prevent concurrent refresh cycles of the same entry.
        Different phone numbers (different instances) operate independently.
        """
        async with self._api_lock:
            result: dict[str, Any] = {
                "overview": {},
                "usage_details": {},
                "balance_detail": {},
            }

            await self._auto_get_auth()
            result["overview"] = await self.get_overview()
            result["balance_detail"] = await self.get_balance_detail()
            result["usage_details"] = await self.get_usage_detail()

            return result