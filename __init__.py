"""China Unicom integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up via configuration.yaml."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up China Unicom from a config entry."""
    # Clean stale data for this entry before setting up
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        old = hass.data[DOMAIN].pop(entry.entry_id)
        old_session = old.get("session")
        if old_session and not old_session.closed:
            await old_session.close()

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception as err:
        _LOGGER.error("async_setup_entry failed: %s", err)
        return False
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok and DOMAIN in hass.data:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if entry_data:
            session = entry_data.get("session")
            if session and not session.closed:
                await session.close()
    return ok