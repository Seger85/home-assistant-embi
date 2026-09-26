"""Validate UI language and sensor naming against Home Assistant's translation loader."""

from pathlib import Path

import pytest
from homeassistant import loader
from homeassistant.helpers.translation import async_get_translations

from custom_components.emby.options_flow import EmbyOptionsFlow
from custom_components.emby.sensor import SENSOR_DESCRIPTIONS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "language,expected", [("de", "Aktive Emby-Player"), ("en", "Emby active players")]
)
async def test_sensor_names_load_from_actual_language_files(hass, entry, language, expected):
    (Path(hass.config.config_dir) / "custom_components").symlink_to(
        Path(__file__).parents[1] / "custom_components", target_is_directory=True
    )
    loader.async_setup(hass)
    translations = await async_get_translations(hass, language, "entity", {"emby"})
    assert translations["component.emby.entity.sensor.active_players.name"] == expected
    assert all(
        f"component.emby.entity.sensor.{item.key}.name" in translations
        for item in SENSOR_DESCRIPTIONS
    )
    flow = EmbyOptionsFlow(entry)
    flow.hass = hass
    flow.context = {"language": language}
    assert flow._is_de() is (language == "de")
    form = await flow.async_step_sensors()
    assert form["description_placeholders"]["total"] == "7"
    assert "active_players" in form["data_schema"]({})["enabled_sensors"]


@pytest.mark.asyncio
async def test_upgrade_preserves_existing_sensor_selection_and_language_fallback(
    hass, entry_factory
):
    entry = entry_factory(options={"enabled_sensors": ["movie_count", "users_watching"]})
    flow = EmbyOptionsFlow(entry)
    flow.hass = hass
    flow.context = {}
    assert flow._is_de()
    assert flow._draft_options["enabled_sensors"] == ["movie_count", "users_watching"]
    flow._draft_options["enabled_sensors"].append("active_players")
    lines, count = await flow._review_lines()
    assert count == 1
    assert "Aktive Player" in lines[0]
    assert entry.options["enabled_sensors"] == ["movie_count", "users_watching"]
