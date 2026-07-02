"""Coordinator for China Unicom."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import UnicomAPI
from .const import DEFAULT_REFRESH_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class UnicomCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for China Unicom data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: UnicomAPI,
        refresh_interval: int = DEFAULT_REFRESH_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=refresh_interval),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            data = await self.api.fetch_all_data()
            # An empty dict {} is truthy in Python; check sub-values explicitly
            if not data or all(v == {} for v in data.values()):
                raise UpdateFailed("No data received from API")
            return data
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
