"""Home Assistant 网易云音乐统一播放器实体。"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_IDLE,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_interval

from .manifest import manifest

DOMAIN = manifest.domain
_LOGGER = logging.getLogger(__name__)

SUPPORT_FEATURES = (
    MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.BROWSE_MEDIA
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.CLEAR_PLAYLIST
    | MediaPlayerEntityFeature.SHUFFLE_SET
    | MediaPlayerEntityFeature.REPEAT_SET
    | MediaPlayerEntityFeature.SELECT_SOURCE
)

TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=1)
UNSUB_INTERVAL = None
UNIFIED_UNIQUE_ID = f"{DOMAIN}_unified_player"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """只创建一个云音乐入口，播放目标通过“播放源”动态选择。"""
    source_players = list(dict.fromkeys(entry.options.get("media_player", [])))
    registry = er.async_get(hass)
    for registry_entry in list(registry.entities.values()):
        if (
            registry_entry.config_entry_id == entry.entry_id
            and registry_entry.platform == DOMAIN
            and registry_entry.unique_id != UNIFIED_UNIQUE_ID
        ):
            registry.async_remove(registry_entry.entity_id)

    # 即使尚未选择目标设备也创建统一入口。这样用户仍可浏览歌单，
    # 并且在集成选项里添加播放器后不再出现“实体消失”的错觉。
    entities = [CloudMusicMediaPlayer(hass, source_players)]

    def media_player_interval(now: datetime.datetime) -> None:
        for player in entities:
            player.interval(now)

    global UNSUB_INTERVAL
    if UNSUB_INTERVAL is not None:
        UNSUB_INTERVAL()
    UNSUB_INTERVAL = async_track_time_interval(
        hass, media_player_interval, TIME_BETWEEN_UPDATES
    )
    async_add_entities(entities, True)


class CloudMusicMediaPlayer(MediaPlayerEntity):
    """一个网易云浏览入口，可把歌曲发往任意已选择的播放器。"""

    _attr_has_entity_name = False
    _attr_media_image_remotely_accessible = True
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_supported_features = SUPPORT_FEATURES
    _attr_unique_id = UNIFIED_UNIQUE_ID
    _attr_name = "网易云音乐"

    def __init__(self, hass: HomeAssistant, source_players: list[str]) -> None:
        self.hass = hass
        self.cloud_music = hass.data["cloud_music"]
        self._attributes = {"platform": DOMAIN}
        self._attr_state = STATE_ON
        self._attr_volume_level = 1.0
        self._attr_repeat = "all"
        self._attr_shuffle = False
        self.before_state: dict[str, Any] | None = None
        self.current_state: str | None = None

        self._source_to_entity: dict[str, str] = {}
        used_labels: set[str] = set()
        for entity_id in source_players:
            state = hass.states.get(entity_id)
            friendly_name = (
                state.attributes.get("friendly_name") if state is not None else None
            )
            base_label = str(friendly_name or entity_id)
            label = base_label
            if label in used_labels:
                label = f"{base_label}（{entity_id}）"
            used_labels.add(label)
            self._source_to_entity[label] = entity_id
        self._attr_source_list = list(self._source_to_entity)
        self._attr_source = (
            self._attr_source_list[0] if self._attr_source_list else None
        )
        self.source_media_player = (
            self._source_to_entity.get(self._attr_source)
            if self._attr_source is not None
            else None
        )

    def interval(self, now: datetime.datetime) -> None:
        """同步当前目标播放器状态并在结束时自动下一曲。"""
        if self._attr_state == STATE_PAUSED:
            return
        media_player = self.media_player
        if media_player is not None:
            attrs = media_player.attributes
            self._attr_media_position = attrs.get("media_position", 0) or 0
            self._attr_media_duration = attrs.get("media_duration", 0) or 0
            self._attr_media_position_updated_at = datetime.datetime.now(
                datetime.UTC
            )
            source_state = media_player.state
            if self.before_state is not None:
                previous_duration = self.before_state["media_duration"]
                previous_position = self.before_state["media_position"]
                near_end = (
                    previous_duration > 0
                    and previous_duration - previous_position <= 5
                )
                became_idle = (
                    self.before_state["state"] == STATE_PLAYING
                    and source_state == STATE_IDLE
                )
                empty_finished = (
                    previous_duration == 0
                    and previous_position == 0
                    and source_state == STATE_IDLE
                    and self._attr_media_duration == 0
                    and self._attr_media_position == 0
                    and self._attr_state == STATE_PLAYING
                )
                if (near_end and became_idle) or empty_finished:
                    self.hass.create_task(self.async_media_next_track())
                    self.before_state = None
                    return
            self.before_state = {
                "media_position": int(self._attr_media_position),
                "media_duration": int(self._attr_media_duration),
                "state": source_state,
            }
            self.current_state = source_state

        if hasattr(self, "playlist") and self.playlist:
            music_info = self.playlist[self.playindex]
            self._attr_app_name = music_info.singer
            self._attr_media_image_url = music_info.thumbnail
            self._attr_media_album_name = music_info.album
            self._attr_media_title = music_info.song
            self._attr_media_artist = music_info.singer
        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def media_player(self):
        if self.source_media_player is None:
            return None
        return self.hass.states.get(self.source_media_player)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "unified_player")},
            "name": "网易云音乐",
            "manufacturer": "shaonianzhentan / bilezhou",
            "model": "CloudMusic Unified Player",
            "sw_version": manifest.version,
            "configuration_url": manifest.documentation,
        }

    @property
    def extra_state_attributes(self):
        return {
            **self._attributes,
            "target_entity_id": self.source_media_player,
            "target_count": len(self._source_to_entity),
        }

    async def async_select_source(self, source: str) -> None:
        entity_id = self._source_to_entity.get(source)
        if entity_id is None:
            _LOGGER.warning("忽略未知播放源：%s", source)
            return
        self._attr_source = source
        self.source_media_player = entity_id
        self.before_state = None
        self.current_state = None
        self.async_write_ha_state()

    async def async_browse_media(
        self, media_content_type=None, media_content_id=None
    ):
        return await self.cloud_music.async_browse_media(
            self, media_content_type, media_content_id
        )

    async def async_volume_up(self) -> None:
        await self.async_call("volume_up")

    async def async_volume_down(self) -> None:
        await self.async_call("volume_down")

    async def async_mute_volume(self, mute: bool) -> None:
        self._attr_is_volume_muted = mute
        await self.async_call("volume_mute", {"is_volume_muted": mute})
        self.async_write_ha_state()

    async def async_set_volume_level(self, volume: float) -> None:
        self._attr_volume_level = volume
        await self.async_call("volume_set", {"volume_level": volume})
        self.async_write_ha_state()

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs
    ) -> None:
        if self.media_player is None:
            _LOGGER.warning("尚未选择可用的播放设备")
            return
        self._attr_state = STATE_PAUSED
        result = await self.cloud_music.async_play_media(
            self, self.cloud_music, media_id
        )
        media_content_id = media_id
        if result == "index":
            media_content_id = self.playlist[self.playindex].url
        elif isinstance(result, str) and result.startswith("http"):
            media_content_id = result
        elif result is not None:
            media_content_id = self.playlist[self.playindex].url
        self._attr_media_content_id = media_content_id
        await self.async_call(
            "play_media",
            {
                "media_content_id": media_content_id,
                "media_content_type": "music",
            },
        )
        self._attr_state = STATE_PLAYING
        self.before_state = None
        self.async_write_ha_state()

    async def async_media_play(self) -> None:
        self._attr_state = STATE_PLAYING
        await self.async_call("media_play")
        self.async_write_ha_state()

    async def async_media_pause(self) -> None:
        self._attr_state = STATE_PAUSED
        await self.async_call("media_pause")
        self.async_write_ha_state()

    async def async_set_repeat(self, repeat: str) -> None:
        self._attr_repeat = repeat
        self.async_write_ha_state()

    async def async_set_shuffle(self, shuffle: bool) -> None:
        self._attr_shuffle = shuffle
        self.async_write_ha_state()

    async def async_media_next_track(self) -> None:
        self._attr_state = STATE_PAUSED
        await self.cloud_music.async_media_next_track(self, self._attr_shuffle)

    async def async_media_previous_track(self) -> None:
        self._attr_state = STATE_PAUSED
        await self.cloud_music.async_media_previous_track(
            self, self._attr_shuffle
        )

    async def async_media_seek(self, position: float) -> None:
        await self.async_call("media_seek", {"seek_position": position})

    async def async_media_stop(self) -> None:
        await self.async_call("media_stop")

    async def async_update(self) -> None:
        return

    async def async_call(
        self, service: str, service_data: dict[str, Any] | None = None
    ) -> None:
        media_player = self.media_player
        if media_player is None:
            return
        payload = dict(service_data or {})
        payload["entity_id"] = media_player.entity_id
        await self.hass.services.async_call(
            "media_player", service, payload, blocking=True
        )

