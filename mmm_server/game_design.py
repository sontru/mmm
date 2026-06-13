import math

from .design_settings import apply_tile_overrides, design_settings


TILE_SIZE = 48
ADMIN_SCALE = 0.5
MAP_WIDTH = 90
MAP_HEIGHT = 62
START_TILE = {"x": 46, "y": 14, "label": "Player Start"}

TILES = {
    "water": 0,
    "sand": 1,
    "grass": 2,
    "forest": 3,
    "rock": 4,
    "tallRock": 5,
    "beach": 6,
}

BUILDING_PLANS = [
    {"id": "black-abbey", "name": "Black Abbey", "kind": "monastery", "x": 30, "y": 25, "w": 30, "h": 12},
    {"id": "harbour-ship", "name": "Harbour Ship", "kind": "ship", "x": 45, "y": 10, "w": 4, "h": 4},
    {"id": "north-chapel", "name": "North Chapel", "kind": "house"},
    {"id": "west-manor", "name": "West Manor", "kind": "house"},
    {"id": "east-ruin", "name": "East Ruin", "kind": "house"},
    {"id": "south-lodge", "name": "Beach Lodge", "kind": "house"},
    {"id": "granary", "name": "Granary", "kind": "house", "x": 45, "y": 51, "w": 3, "h": 3},
    {"id": "old-parish-house", "name": "Old Parish House", "kind": "house"},
]

SHIP_BUILDING = {
    "id": "harbour-ship",
    "name": "Harbour Ship",
    "kind": "ship",
    "x": 45,
    "y": 10,
    "w": 4,
    "h": 4,
    "background": TILES["water"],
    "entrances": [
        {"id": "harbour-ship-boarding-plank", "name": "Boarding Plank", "areaId": "harbour-ship-deck", "x": 1, "y": 3, "w": 2, "h": 1}
    ],
    "pier": {"x": 46, "y": 14, "w": 2, "h": 2},
}

CAVE_ENTRANCES = [
    {"id": "north-cave-entrance", "name": "North Cave Entrance", "x": 67, "y": 41, "w": 1, "h": 2, "terrainKind": "cave"},
    {"id": "south-cave-entrance", "name": "South Cave Entrance", "x": 64, "y": 45, "w": 1, "h": 2, "terrainKind": "cave"},
]

LAKE_OF_TEARS = {"id": "lake-of-tears", "name": "Lake of Tears", "x1": 52, "y1": 13, "x2": 63, "y2": 22}
CLOISTER_LANDMARKS = [
    {"id": "west-fountain", "name": "West Fountain", "x": 39.3, "y": 29.35},
    {"id": "cloister-well", "name": "Well", "x": 45, "y": 31},
    {"id": "east-fountain", "name": "East Fountain", "x": 50.7, "y": 29.35},
]

HOUSE_BUILDING_PLANS = [
    {"id": "north-chapel", "name": "North Chapel", "areaId": "north-chapel-nave"},
    {"id": "west-manor", "name": "West Manor", "areaId": "west-manor-hall"},
    {"id": "east-ruin", "name": "East Ruin", "areaId": "east-ruin-vault"},
    {"id": "south-lodge", "name": "Beach Lodge", "areaId": "south-lodge-room"},
    {"id": "old-parish-house", "name": "Old Parish House", "areaId": "old-parish-house-room"},
]

GRANARY_BUILDING = {"id": "granary", "name": "Granary", "areaId": "granary-room", "x": 45, "y": 51, "w": 3, "h": 3}

HOUSE_CANDIDATES = [
    {"x": 43, "y": 8},
    {"x": 14, "y": 29},
    {"x": 73, "y": 33},
    {"x": 51, "y": 51},
    {"x": 25, "y": 18},
]

COLORS = {
    TILES["water"]: "#172c45",
    TILES["sand"]: "#6a6e70",
    TILES["grass"]: "#263925",
    TILES["forest"]: "#1d2d22",
    TILES["rock"]: "#2d2d34",
    TILES["tallRock"]: "#22232a",
    TILES["beach"]: "#746d57",
}

DESIGN_ZONES = [
    {
        "id": "orchard-garden",
        "name": "Fruit Orchard and Vegetable Garden",
        "x1": 27,
        "y1": 43,
        "x2": 43,
        "y2": 53,
        "splitX": 35,
        "parts": [
            {"name": "Fruit Orchard", "x1": 27, "y1": 43, "x2": 35, "y2": 53},
            {"name": "Vegetable Garden", "x1": 36, "y1": 43, "x2": 43, "y2": 53},
        ],
    },
    {
        "id": "barley-field",
        "name": "Barley Field",
        "x1": 44,
        "y1": 39,
        "x2": 51,
        "y2": 50,
        "pathX": 47,
        "pathY": 44,
        "parts": [
            {"name": "Barley Field", "x1": 44, "y1": 39, "x2": 51, "y2": 50},
            {"name": "Cross Paths", "x1": 47, "y1": 44, "x2": 47, "y2": 44},
        ],
    }
]

DESIGN_NOTES = [
    "Browser owns rendering and immediate movement.",
    "Python owns accounts, saves, events, and admin summaries.",
    "World constants are mirrored here so admin views can visualize design intent.",
]


def design_payload():
    """Build the complete design payload consumed by the browser and admin UI."""
    world = generate_world()
    settings = design_settings()
    base_grid = [row[:] for row in world["tiles"]]
    apply_tile_overrides(world["tiles"], settings["tileOverrides"])
    return {
        "title": "Abbey Island Mystery",
        "map": {
            "tileSize": TILE_SIZE,
            "adminScale": ADMIN_SCALE,
            "adminTileSize": int(TILE_SIZE * ADMIN_SCALE),
            "width": MAP_WIDTH,
            "height": MAP_HEIGHT,
            "pixelWidth": MAP_WIDTH * TILE_SIZE,
            "pixelHeight": MAP_HEIGHT * TILE_SIZE,
            "adminPixelWidth": int(MAP_WIDTH * TILE_SIZE * ADMIN_SCALE),
            "adminPixelHeight": int(MAP_HEIGHT * TILE_SIZE * ADMIN_SCALE),
        },
        "tiles": TILES,
        "tileColors": COLORS,
        "tileOverrides": settings["tileOverrides"],
        "blockingOverrides": settings["blockingOverrides"],
        "tileOptions": [
            {"id": TILES["water"], "name": "Water", "asset": "assets/graphics/tile-water.svg"},
            {"id": TILES["sand"], "name": "Sand", "asset": "assets/graphics/tile-sand.svg"},
            {"id": TILES["grass"], "name": "Grass", "asset": "assets/graphics/tile-grass.svg"},
            {"id": TILES["forest"], "name": "Forest", "asset": "assets/graphics/tile-forest.svg"},
            {"id": TILES["rock"], "name": "Rock", "asset": "assets/graphics/tile-rock.svg"},
            {"id": TILES["tallRock"], "name": "Tall Rock", "asset": "assets/graphics/tile-tall-rock.svg"},
            {"id": TILES["beach"], "name": "Beach", "asset": "assets/graphics/tile-beach.svg"},
        ],
        "start": {
            **START_TILE,
            "pixelX": START_TILE["x"] * TILE_SIZE + 13,
            "pixelY": START_TILE["y"] * TILE_SIZE + 8,
        },
        "baseGrid": base_grid,
        "grid": world["tiles"],
        "buildings": world["buildings"],
        "caveEntrances": CAVE_ENTRANCES,
        "landmarks": [*CLOISTER_LANDMARKS, LAKE_OF_TEARS],
        "zones": DESIGN_ZONES,
        "notes": DESIGN_NOTES,
    }


def generate_world():
    """Generate the map tiles and building layout for the island."""
    tiles = generate_island()
    buildings = place_buildings(tiles)
    patch_south_beach(tiles)
    return {"tiles": tiles, "buildings": buildings}


def generate_island():
    """Create the base island terrain grid before authored patches are applied."""
    rng = mulberry32(18)
    center_x = MAP_WIDTH / 2
    center_y = MAP_HEIGHT / 2
    max_distance = min(MAP_WIDTH, MAP_HEIGHT) * 0.48
    tiles = []

    for y in range(MAP_HEIGHT):
        row = []
        for x in range(MAP_WIDTH):
            dx = (x - center_x) / max_distance
            dy = (y - center_y) / (max_distance * 0.82)
            distance = math.sqrt(dx * dx + dy * dy)
            coast_wobble = (
                math.sin(x * 0.25) * 0.08
                + math.cos(y * 0.23) * 0.07
                + math.sin((x + y) * 0.17) * 0.05
                + (rng() * 0.11 - 0.055)
            )
            height = 1.0 - distance + coast_wobble

            if height < 0.03:
                tile = TILES["water"]
            elif height < 0.14:
                tile = TILES["sand"]
            elif height < 0.46:
                tile = TILES["grass"]
            elif height < 0.68:
                tile = TILES["forest"]
            else:
                tile = TILES["rock"]
            row.append(tile)
        tiles.append(row)

    carve_paths(tiles)
    tiles[7][36] = TILES["sand"]
    patch_harbour_ship_water(tiles)
    patch_lake_of_tears(tiles)
    patch_orchard_garden(tiles)
    patch_barley_field(tiles)
    patch_rock_double_line(tiles)
    patch_tall_rock_edges(tiles)
    patch_cave_entrances(tiles)
    return tiles


def patch_lake_of_tears(tiles):
    """Carve the oval Lake of Tears into the authored island terrain."""
    lake = LAKE_OF_TEARS
    center_x = (lake["x1"] + lake["x2"]) / 2
    center_y = (lake["y1"] + lake["y2"]) / 2
    radius_x = (lake["x2"] - lake["x1"] + 1) / 2
    radius_y = (lake["y2"] - lake["y1"] + 1) / 2
    for y in range(lake["y1"], lake["y2"] + 1):
        for x in range(lake["x1"], lake["x2"] + 1):
            dx = (x + 0.5 - center_x) / radius_x
            dy = (y + 0.5 - center_y) / radius_y
            if in_bounds(x, y) and dx * dx + dy * dy <= 1:
                tiles[y][x] = TILES["water"]


def patch_south_beach(tiles):
    """Paint the authored southern beach strip and its sand shoreline."""
    for x in range(53, 64):
        for y in range(51, MAP_HEIGHT):
            if not in_bounds(x, y):
                continue
            if tiles[y][x] == TILES["water"]:
                break
            if y <= 54 or tiles[y][x] in (TILES["sand"], TILES["beach"]):
                tiles[y][x] = TILES["beach"]


def patch_cave_entrances(tiles):
    """Shape cave entrance openings into the rock terrain."""
    for entrance in CAVE_ENTRANCES:
        bounds = cave_entrance_bounds(entrance)
        for y in range(bounds["y"], bounds["y"] + bounds["h"]):
            for x in range(bounds["x"], bounds["x"] + bounds["w"]):
                if in_bounds(x, y):
                    tiles[y][x] = TILES["tallRock"]


def cave_entrance_bounds(entrance):
    """Return the tile rectangle occupied by a cave entrance."""
    return {
        "x": entrance["x"] - (entrance.get("w", 1) // 2),
        "y": entrance["y"],
        "w": entrance.get("w", 1),
        "h": entrance.get("h", 1),
    }


def patch_tall_rock_edges(tiles):
    """Mark cliff-edge rock tiles that should render as tall rocks."""
    tall_rocks = []
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if tiles[y][x] == TILES["rock"] and is_outer_rock_tile(tiles, x, y):
                tall_rocks.append((x, y))
    for x, y in tall_rocks:
        tiles[y][x] = TILES["tallRock"]


def is_outer_rock_tile(tiles, tile_x, tile_y):
    """Return whether a rock tile borders non-rock terrain."""
    for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x = tile_x + offset_x
        y = tile_y + offset_y
        if not in_bounds(x, y) or tiles[y][x] != TILES["rock"]:
            return True
    return False


def patch_rock_double_line(tiles):
    """Add authored double rock-line features to the terrain grid."""
    start = {"x": 66, "y": 40}
    end = {"x": 63, "y": 50}
    steps = max(abs(end["x"] - start["x"]), abs(end["y"] - start["y"]))
    for index in range(steps + 1):
        progress = index / steps
        x = round(start["x"] + (end["x"] - start["x"]) * progress)
        y = round(start["y"] + (end["y"] - start["y"]) * progress)
        for offset_x in (0, 1):
            if in_bounds(x + offset_x, y):
                tiles[y][x + offset_x] = TILES["rock"]


def patch_harbour_ship_water(tiles):
    """Restore harbour water around the ship placement."""
    for y in range(SHIP_BUILDING["y"], SHIP_BUILDING["y"] + SHIP_BUILDING["h"]):
        for x in range(SHIP_BUILDING["x"], SHIP_BUILDING["x"] + SHIP_BUILDING["w"]):
            if in_bounds(x, y):
                tiles[y][x] = TILES["water"]
    pier = SHIP_BUILDING["pier"]
    for y in range(pier["y"], pier["y"] + pier["h"]):
        for x in range(pier["x"], pier["x"] + pier["w"]):
            if in_bounds(x, y):
                tiles[y][x] = TILES["sand"]


def patch_orchard_garden(tiles):
    """Apply the orchard garden terrain patch to the map grid."""
    zone = DESIGN_ZONES[0]
    for y in range(zone["y1"], zone["y2"] + 1):
        for x in range(zone["x1"], zone["x2"] + 1):
            if in_bounds(x, y):
                tiles[y][x] = TILES["sand"] if is_orchard_garden_path_tile(x, y) else TILES["grass"]


def patch_barley_field(tiles):
    """Apply the Barley Field terrain patch with cross paths."""
    zone = DESIGN_ZONES[1]
    for y in range(zone["y1"], zone["y2"] + 1):
        for x in range(zone["x1"], zone["x2"] + 1):
            if in_bounds(x, y):
                tiles[y][x] = TILES["sand"] if is_barley_field_path_tile(x, y) else TILES["grass"]


def barley_field_area_for_tile(tile_x, tile_y):
    """Return the Barley Field zone if a tile is inside it."""
    zone = DESIGN_ZONES[1]
    if zone["x1"] <= tile_x <= zone["x2"] and zone["y1"] <= tile_y <= zone["y2"]:
        return zone
    return None


def is_barley_field_path_tile(tile_x, tile_y):
    """Return whether a Barley Field tile belongs to the cross paths."""
    zone = barley_field_area_for_tile(tile_x, tile_y)
    return bool(zone) and (tile_x == zone["pathX"] or tile_y == zone["pathY"])


def orchard_garden_area_for_tile(tile_x, tile_y):
    """Return which orchard garden sub-area contains a tile."""
    zone = DESIGN_ZONES[0]
    if tile_y < zone["y1"] or tile_y > zone["y2"] or tile_x < zone["x1"] or tile_x > zone["x2"]:
        return None
    if tile_x <= zone["splitX"]:
        return {"x1": zone["x1"], "x2": zone["splitX"], "y1": zone["y1"], "y2": zone["y2"]}
    return {"x1": zone["splitX"] + 1, "x2": zone["x2"], "y1": zone["y1"], "y2": zone["y2"]}


def is_orchard_garden_path_tile(tile_x, tile_y):
    """Return whether a tile belongs to an orchard garden path."""
    area = orchard_garden_area_for_tile(tile_x, tile_y)
    if not area:
        return False
    path_x = (area["x1"] + area["x2"]) // 2
    path_y = (area["y1"] + area["y2"]) // 2
    return tile_x == path_x or tile_y == path_y


def carve_paths(tiles):
    """Carve authored paths through the generated island terrain."""
    center = {"x": MAP_WIDTH // 2, "y": MAP_HEIGHT // 2}
    targets = [
        {"x": MAP_WIDTH // 2, "y": 8},
        {"x": 14, "y": MAP_HEIGHT // 2},
        {"x": MAP_WIDTH - 15, "y": MAP_HEIGHT // 2 + 3},
        {"x": MAP_WIDTH // 2 + 8, "y": MAP_HEIGHT - 9},
    ]

    for target in targets:
        x = center["x"]
        y = center["y"]
        while x != target["x"] or y != target["y"]:
            if x < target["x"]:
                x += 1
            elif x > target["x"]:
                x -= 1
            if y < target["y"]:
                y += 1
            elif y > target["y"]:
                y -= 1

            for yy in range(y - 1, y + 2):
                for xx in range(x - 1, x + 2):
                    if in_bounds(xx, yy) and tiles[yy][xx] != TILES["water"]:
                        tiles[yy][xx] = TILES["sand"]


def place_buildings(tiles):
    """Place authored and generated buildings onto the map."""
    monastery = {
        "id": "black-abbey",
        "name": "Black Abbey",
        "kind": "monastery",
        "x": 30,
        "y": 25,
        "w": 30,
        "h": 12,
        "background": TILES["sand"],
        "entrances": [
            {"id": "black-abbey-gatehouse", "name": "West Tower", "areaId": "black-abbey-gatehouse", "x": 13, "y": 11},
            {"id": "black-abbey-north-cloister", "name": "North Cloister", "areaId": "black-abbey-north-cloister", "x": 10, "y": 2},
            {"id": "black-abbey-prior-room", "name": "Prior's Room", "areaId": "black-abbey-prior-room", "x": 22, "y": 2},
            {"id": "black-abbey-west-chapel", "name": "West Chapel", "areaId": "black-abbey-west-chapel", "x": 5, "y": 5},
            {"id": "black-abbey-crypt-stair", "name": "Crypt Stair", "areaId": "black-abbey-crypt-stair", "x": 0, "y": 5},
            {"id": "black-abbey-library", "name": "Library", "areaId": "black-abbey-library", "x": 29, "y": 8},
            {"id": "black-abbey-refectory", "name": "Refectory", "areaId": "black-abbey-refectory", "x": 4, "y": 11},
            {"id": "black-abbey-infirmary", "name": "Infirmary", "areaId": "black-abbey-infirmary", "x": 22, "y": 11},
            {"id": "black-abbey-east-tower", "name": "East Tower", "areaId": "black-abbey-east-tower", "x": 16, "y": 11},
        ],
    }
    ship = dict(SHIP_BUILDING)
    buildings = [monastery, ship]
    make_building_ground(tiles, monastery["x"], monastery["y"], monastery["w"], monastery["h"], monastery["background"])
    granary = {
        "id": GRANARY_BUILDING["id"],
        "name": GRANARY_BUILDING["name"],
        "kind": "house",
        "x": GRANARY_BUILDING["x"],
        "y": GRANARY_BUILDING["y"],
        "w": GRANARY_BUILDING["w"],
        "h": GRANARY_BUILDING["h"],
        "background": building_background(tiles, GRANARY_BUILDING["x"], GRANARY_BUILDING["y"], GRANARY_BUILDING["w"], GRANARY_BUILDING["h"]),
        "entrances": [{"id": "granary-entrance", "name": "Front Door", "areaId": GRANARY_BUILDING["areaId"], "x": 1, "y": 2}],
    }
    buildings.append(granary)
    make_building_ground(tiles, granary["x"], granary["y"], granary["w"], granary["h"], granary["background"])

    for index, candidate in enumerate(HOUSE_CANDIDATES):
        site = find_buildable_site(tiles, candidate["x"], candidate["y"], 3, 3, buildings)
        if not site:
            continue
        background = building_background(tiles, site["x"], site["y"], 3, 3)
        plan = HOUSE_BUILDING_PLANS[index]
        buildings.append(
            {
                "id": plan["id"],
                "name": plan["name"],
                "kind": "house",
                "x": site["x"],
                "y": site["y"],
                "w": 3,
                "h": 3,
                "background": background,
                "entrances": [{"id": f"{plan['id']}-entrance", "name": "Front Door", "areaId": plan["areaId"], "x": 1, "y": 2}],
            }
        )
        make_building_ground(tiles, site["x"], site["y"], 3, 3, background)

    return buildings


def find_buildable_site(tiles, tile_x, tile_y, width, height, buildings):
    """Find a nearby clear site for a generated building footprint."""
    for radius in range(9):
        for offset_y in range(-radius, radius + 1):
            for offset_x in range(-radius, radius + 1):
                if abs(offset_x) != radius and abs(offset_y) != radius:
                    continue
                x = tile_x + offset_x
                y = tile_y + offset_y
                if can_place_building(tiles, x, y, width, height, buildings):
                    return {"x": x, "y": y}
    return None


def can_place_building(tiles, tile_x, tile_y, width, height, buildings):
    """Return whether a building footprint can occupy the requested tiles."""
    for y in range(tile_y, tile_y + height):
        for x in range(tile_x, tile_x + width):
            if not in_bounds(x, y) or tiles[y][x] in (TILES["water"], TILES["rock"], TILES["tallRock"]):
                return False
    return not any(rects_overlap({"x": tile_x, "y": tile_y, "w": width, "h": height}, building) for building in buildings)


def building_background(tiles, tile_x, tile_y, width, height):
    """Choose the terrain background used under a building footprint."""
    counts = {TILES["sand"]: 0, TILES["grass"]: 0, TILES["forest"]: 0, TILES["beach"]: 0}
    for y in range(tile_y - 1, tile_y + height + 1):
        for x in range(tile_x - 1, tile_x + width + 1):
            if tile_x <= x < tile_x + width and tile_y <= y < tile_y + height:
                continue
            if in_bounds(x, y) and tiles[y][x] in counts:
                counts[tiles[y][x]] += 1
    return max(counts, key=counts.get)


def make_building_ground(tiles, tile_x, tile_y, width, height, background):
    """Create a rectangular terrain patch beneath a building."""
    for y in range(tile_y, tile_y + height):
        for x in range(tile_x, tile_x + width):
            tiles[y][x] = background


def rects_overlap(a, b):
    """Return whether two tile rectangles overlap."""
    return a["x"] < b["x"] + b["w"] and a["x"] + a["w"] > b["x"] and a["y"] < b["y"] + b["h"] and a["y"] + a["h"] > b["y"]


def in_bounds(tile_x, tile_y):
    """Return whether tile coordinates are inside the map."""
    return 0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT


def mulberry32(seed):
    """Create a deterministic pseudo-random number generator from a seed."""
    value = seed

    def random():
        """Return the next deterministic pseudo-random float."""
        nonlocal value
        value = uint32(value + 0x6D2B79F5)
        t = value
        t = uint32(math_imul(t ^ (t >> 15), t | 1))
        t ^= uint32(t + math_imul(t ^ (t >> 7), t | 61))
        return uint32(t ^ (t >> 14)) / 4294967296

    return random


def math_imul(a, b):
    """Emulate JavaScript signed 32-bit integer multiplication."""
    return ((a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)) & 0xFFFFFFFF


def uint32(value):
    """Coerce a value into an unsigned 32-bit integer."""
    return value & 0xFFFFFFFF
