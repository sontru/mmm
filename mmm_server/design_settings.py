import json

from .config import ROOT_DIR


SETTINGS_PATH = ROOT_DIR / "mmm_design_settings.json"
VALID_TILE_IDS = {0, 1, 2, 3, 4, 5, 6}
MAP_WIDTH = 90
MAP_HEIGHT = 62


def design_settings():
    """Load and validate persisted map design overrides."""
    settings = {"tileOverrides": {}, "blockingOverrides": {}, "roomOverrides": {}}
    try:
        raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return settings

    overrides = raw.get("tileOverrides", {})
    if isinstance(overrides, dict):
        for key, tile in overrides.items():
            if _valid_override(key, tile):
                settings["tileOverrides"][key] = int(tile)
    blocking = raw.get("blockingOverrides", {})
    if isinstance(blocking, dict):
        for key, blocked in blocking.items():
            if _valid_blocking_override(key, blocked):
                settings["blockingOverrides"][key] = bool(blocked)
    rooms = raw.get("roomOverrides", {})
    if isinstance(rooms, dict):
        for room_id, override in rooms.items():
            if isinstance(room_id, str) and isinstance(override, dict):
                settings["roomOverrides"][room_id] = override
    return settings


def save_map_overrides(overrides, blocking_overrides=None):
    """Validate and persist map tile and blocking overrides."""
    settings = design_settings()
    if not isinstance(overrides, dict):
        raise ValueError("tileOverrides must be an object")
    if blocking_overrides is None:
        blocking_overrides = settings["blockingOverrides"]
    if not isinstance(blocking_overrides, dict):
        raise ValueError("blockingOverrides must be an object")

    clean_tiles = {}
    for key, tile in overrides.items():
        if not _valid_override(key, tile):
            raise ValueError(f"Invalid tile override: {key}={tile}")
        clean_tiles[str(key)] = int(tile)

    clean_blocking = {}
    for key, blocked in blocking_overrides.items():
        if not _valid_blocking_override(key, blocked):
            raise ValueError(f"Invalid blocking override: {key}={blocked}")
        clean_blocking[str(key)] = bool(blocked)

    payload = {
        "tileOverrides": dict(sorted(clean_tiles.items(), key=lambda item: _sort_key(item[0]))),
        "blockingOverrides": dict(sorted(clean_blocking.items(), key=lambda item: _sort_key(item[0]))),
        "roomOverrides": settings["roomOverrides"],
    }
    SETTINGS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return design_settings()


def save_room_overrides(room_overrides):
    """Validate and persist room design overrides."""
    settings = design_settings()
    if not isinstance(room_overrides, dict):
        raise ValueError("roomOverrides must be an object")

    clean_rooms = dict(settings["roomOverrides"])
    for room_id, override in room_overrides.items():
        if not isinstance(room_id, str):
            raise ValueError("Invalid room override key")
        if not isinstance(override, dict):
            raise ValueError("Room override must be an object")
        clean_rooms[room_id] = override

    payload = {
        "tileOverrides": settings["tileOverrides"],
        "blockingOverrides": settings["blockingOverrides"],
        "roomOverrides": clean_rooms,
    }
    SETTINGS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return design_settings()


def apply_room_overrides(rooms, overrides):
    """Apply persisted room field overrides to generated room definitions."""
    if not isinstance(overrides, dict):
        return
    for room in rooms:
        room_id = room.get("id")
        if room_id in overrides and isinstance(overrides[room_id], dict):
            _merge_room_fields(room, overrides[room_id])


def _merge_room_fields(room, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(room.get(key), dict):
            _merge_room_fields(room[key], value)
        else:
            room[key] = value


def apply_tile_overrides(tiles, overrides):
    """Apply saved tile overrides to a generated tile grid."""
    for key, tile in overrides.items():
        x, y = _parse_key(key)
        tiles[y][x] = int(tile)


def _valid_override(key, tile):
    """Return whether a tile override targets a valid map tile and tile kind."""
    try:
        x, y = _parse_key(key)
        tile = int(tile)
    except (TypeError, ValueError):
        return False
    return 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and tile in VALID_TILE_IDS


def _valid_blocking_override(key, blocked):
    """Return whether a blocking override targets a valid map tile."""
    try:
        x, y = _parse_key(key)
    except (TypeError, ValueError):
        return False
    return 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and isinstance(blocked, bool)


def _parse_key(key):
    """Parse a tile coordinate key into x and y integers."""
    x, y = str(key).split(",", 1)
    return int(x), int(y)


def _sort_key(key):
    """Return a stable row-major sort key for tile coordinate strings."""
    x, y = _parse_key(key)
    return y, x
