"""China Unicom sensor platform."""
import logging
import aiohttp

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_OPENID, CONF_REFRESH_INTERVAL
from .coordinator import UnicomCoordinator
from .api import UnicomAPI

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up the China Unicom sensor."""
    openid = entry.data[CONF_OPENID]
    refresh_interval = entry.data.get(CONF_REFRESH_INTERVAL, 15)

    # Create a persistent session for this entry
    session = aiohttp.ClientSession()

    # Create API and coordinator
    api = UnicomAPI(session, openid)
    coordinator = UnicomCoordinator(hass, api, refresh_interval)

    # Store data keyed by entry_id (multi-instance isolation)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "openid": openid,
        "session": session,
    }

    # Create sensor entity
    entity = UnicomSensor(coordinator, openid, entry.unique_id, entry.entry_id)
    async_add_entities([entity])


class UnicomSensor(CoordinatorEntity):
    """Single entity for all Unicom data."""

    def __init__(self, coordinator, openid: str, unique_id: str, entry_id: str):
        super().__init__(coordinator)
        self.openid = openid
        self._unique_id = unique_id
        self._entry_id = entry_id

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        if self.coordinator.data:
            return self.coordinator.data.get("balance_detail", {}).get("curntbalancecust")
        return None

    @property
    def unit_of_measurement(self):
        return "元"

    @property
    def icon(self):
        return "mdi:sim"

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data
        usage = d.get("usage_details", {})
        balance = d.get("balance_detail", {})

        return {
            "openid": self.openid,
            "voice_usage": usage.get("voice", {}).get("use"),
            "voice_total": usage.get("voice", {}).get("total"),
            "voice_balance": usage.get("voice", {}).get("remain"),
            "voice_percent": usage.get("voice", {}).get("usedPercent"),
            "sms_usage": usage.get("sms", {}).get("use"),
            "sms_total": usage.get("sms", {}).get("total"),
            "sms_balance": usage.get("sms", {}).get("remain"),
            "sms_percent": usage.get("sms", {}).get("usedPercent"),
            "balance": balance.get("curntbalancecust"),
            "available_balance": balance.get(
                "canusefeecustNew", balance.get("canusefeecust")
            ),
            "real_time_fee": balance.get(
                "totalrealfee", balance.get("realfeecustnew")
            ),
            "total_owed": balance.get("allbowefeecust"),
            "credit_limit": balance.get("canuselimitcust"),
            "data_items": usage.get("data_items", []),
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": f"中国联通 {self.openid[:3]}****{self.openid[-4:]}",
            "manufacturer": "中国联通",
            "entry_type": DeviceEntryType.SERVICE,
            "model": "CU 中国联通",
        }

    async def async_added_to_hass(self):
        # HA-recommended: properly handles first fetch errors (won't crash entity)
        await self.coordinator.async_config_entry_first_refresh()

        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )