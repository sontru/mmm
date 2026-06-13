import math
import os
import random
import struct
import sys
import wave

import pygame


SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60

TILE_SIZE = 48
MAP_WIDTH = 90
MAP_HEIGHT = 62

MUSIC_PATH = os.path.join("assets", "mmm_theme.wav")
PLAYER_NAME = "Player"

WATER = 0
SAND = 1
GRASS = 2
FOREST = 3
ROCK = 4
TALL_ROCK = 5
BEACH = 6

BUILDING_SITES = (
    {"x": 41, "y": 37, "id": "north-chapel", "name": "North Chapel", "area_id": "north-chapel-nave"},
    {"x": 59, "y": 33, "id": "west-manor", "name": "West Manor", "area_id": "west-manor-hall"},
    {"x": 30, "y": 33, "id": "east-ruin", "name": "East Ruin", "area_id": "east-ruin-vault"},
    {"x": 52, "y": 39, "id": "south-lodge", "name": "Beach Lodge", "area_id": "south-lodge-room"},
    {"x": 45, "y": 51, "id": "granary", "name": "Granary", "area_id": "granary-room"},
    {"x": 25, "y": 27, "id": "old-parish-house", "name": "Old Parish House", "area_id": "old-parish-house-room"},
)

SHIP_BUILDING = {
    "id": "harbour-ship",
    "name": "Harbour Ship",
    "kind": "ship",
    "x": 45,
    "y": 10,
    "w": 4,
    "h": 4,
    "background": WATER,
    "entrances": [
        {"id": "harbour-ship-boarding-plank", "name": "Boarding Plank", "area_id": "harbour-ship-deck", "x": 1, "y": 3, "w": 2, "h": 1}
    ],
    "pier": {"x": 46, "y": 14, "w": 2, "h": 2},
}

COLORS = {
    WATER: (23, 44, 69),
    SAND: (106, 110, 112),
    GRASS: (38, 57, 37),
    FOREST: (29, 45, 34),
    ROCK: (45, 45, 52),
    TALL_ROCK: (34, 35, 42),
    BEACH: (116, 109, 87),
}

DESIGN_ZONES = {
    "orchard_garden": {
        "x1": 27,
        "y1": 43,
        "x2": 43,
        "y2": 53,
        "split_x": 35,
    },
    "barley_field": {
        "x1": 44,
        "y1": 39,
        "x2": 51,
        "y2": 50,
        "path_x": 47,
        "path_y": 44,
    },
    "wheat_field": {
        "x1": 55,
        "y1": 39,
        "x2": 62,
        "y2": 50,
        "path_x": 58,
        "path_y": 44,
    },
}

CAVE_ENTRANCES = (
    {"id": "north-cave-entrance", "name": "North Cave Entrance", "x": 67, "y": 41, "w": 1, "h": 2, "terrain_kind": "cave"},
    {"id": "south-cave-entrance", "name": "South Cave Entrance", "x": 64, "y": 45, "w": 1, "h": 2, "terrain_kind": "cave"},
)

LAKE_OF_TEARS = {"id": "lake-of-tears", "name": "Lake of Tears", "x1": 52, "y1": 13, "x2": 63, "y2": 22}
CLOISTER_LANDMARKS = (
    {"id": "west-fountain", "name": "West Fountain", "x": 39.3, "y": 29.35},
    {"id": "cloister-well", "name": "Well", "x": 45, "y": 31},
    {"id": "east-fountain", "name": "East Fountain", "x": 50.7, "y": 29.35},
)


class World:
    def __init__(self):
        """Initialize the generated world tiles, buildings, and locations."""
        self.tiles = self._generate_island()
        self.buildings = self._place_buildings()
        self._patch_south_beach(self.tiles)
        self.land_positions = [
            (x, y)
            for y, row in enumerate(self.tiles)
            for x, tile in enumerate(row)
            if (
                tile not in (WATER, ROCK, TALL_ROCK)
                and not self.is_building_tile(x, y)
                and not (self._orchard_garden_area_for_tile(x, y) and not self._is_orchard_garden_path_tile(x, y))
                and not (self._barley_field_area_for_tile(x, y) and not self._is_barley_field_path_tile(x, y))
                and not (self._wheat_field_area_for_tile(x, y) and not self._is_wheat_field_path_tile(x, y))
            )
        ]

    def _generate_island(self):
        """Generate the desktop game island terrain grid."""
        rng = random.Random(18)
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
                    + rng.uniform(-0.055, 0.055)
                )
                height = 1.0 - distance + coast_wobble

                if height < 0.03:
                    tile = WATER
                elif height < 0.14:
                    tile = SAND
                elif height < 0.46:
                    tile = GRASS
                elif height < 0.68:
                    tile = FOREST
                else:
                    tile = ROCK

                row.append(tile)
            tiles.append(row)

        self._carve_paths(tiles)
        self._patch_harbour_ship_water(tiles)
        self._patch_lake_of_tears(tiles)
        self._patch_orchard_garden(tiles)
        self._patch_barley_field(tiles)
        self._patch_wheat_field(tiles)
        self._patch_rock_double_line(tiles)
        self._patch_tall_rock_edges(tiles)
        self._patch_cave_entrances(tiles)
        return tiles

    def _patch_lake_of_tears(self, tiles):
        """Carve the oval Lake of Tears into the desktop terrain."""
        lake = LAKE_OF_TEARS
        center_x = (lake["x1"] + lake["x2"]) / 2
        center_y = (lake["y1"] + lake["y2"]) / 2
        radius_x = (lake["x2"] - lake["x1"] + 1) / 2
        radius_y = (lake["y2"] - lake["y1"] + 1) / 2
        for y in range(lake["y1"], lake["y2"] + 1):
            for x in range(lake["x1"], lake["x2"] + 1):
                dx = (x + 0.5 - center_x) / radius_x
                dy = (y + 0.5 - center_y) / radius_y
                if self.in_bounds(x, y) and dx * dx + dy * dy <= 1:
                    tiles[y][x] = WATER

    def _patch_south_beach(self, tiles):
        """Paint the authored southern beach strip and its sand shoreline."""
        for x in range(53, 64):
            for y in range(51, MAP_HEIGHT):
                if not self.in_bounds(x, y):
                    continue
                if tiles[y][x] == WATER:
                    break
                if y <= 54 or tiles[y][x] in (SAND, BEACH):
                    tiles[y][x] = BEACH

    def _patch_harbour_ship_water(self, tiles):
        """Restore harbour water around the desktop ship placement."""
        for y in range(SHIP_BUILDING["y"], SHIP_BUILDING["y"] + SHIP_BUILDING["h"]):
            for x in range(SHIP_BUILDING["x"], SHIP_BUILDING["x"] + SHIP_BUILDING["w"]):
                if self.in_bounds(x, y):
                    tiles[y][x] = WATER
        pier = SHIP_BUILDING["pier"]
        for y in range(pier["y"], pier["y"] + pier["h"]):
            for x in range(pier["x"], pier["x"] + pier["w"]):
                if self.in_bounds(x, y):
                    tiles[y][x] = SAND

    def _carve_paths(self, tiles):
        """Carve authored walking paths through the desktop island terrain."""
        center = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        targets = [
            (MAP_WIDTH // 2, 8),
            (14, MAP_HEIGHT // 2),
            (MAP_WIDTH - 15, MAP_HEIGHT // 2 + 3),
            (MAP_WIDTH // 2 + 8, MAP_HEIGHT - 9),
        ]

        for target in targets:
            x, y = center
            while (x, y) != target:
                if x < target[0]:
                    x += 1
                elif x > target[0]:
                    x -= 1
                if y < target[1]:
                    y += 1
                elif y > target[1]:
                    y -= 1

                for yy in range(y - 1, y + 2):
                    for xx in range(x - 1, x + 2):
                        if self.in_bounds(xx, yy) and tiles[yy][xx] != WATER:
                            tiles[yy][xx] = SAND

    def _patch_rock_double_line(self, tiles):
        """Add authored double rock-line features to the desktop terrain."""
        start = {"x": 66, "y": 40}
        end = {"x": 63, "y": 50}
        steps = max(abs(end["x"] - start["x"]), abs(end["y"] - start["y"]))
        for index in range(steps + 1):
            progress = index / steps
            x = round(start["x"] + (end["x"] - start["x"]) * progress)
            y = round(start["y"] + (end["y"] - start["y"]) * progress)
            for offset_x in (0, 1):
                if self.in_bounds(x + offset_x, y):
                    tiles[y][x + offset_x] = ROCK

    def _patch_tall_rock_edges(self, tiles):
        """Mark desktop cliff-edge tiles as tall rocks."""
        tall_rocks = []
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if tiles[y][x] == ROCK and self._is_outer_rock_tile(tiles, x, y):
                    tall_rocks.append((x, y))
        for x, y in tall_rocks:
            tiles[y][x] = TALL_ROCK

    def _patch_cave_entrances(self, tiles):
        """Shape desktop cave entrance openings in rock terrain."""
        for entrance in CAVE_ENTRANCES:
            bounds = self._cave_entrance_bounds(entrance)
            for y in range(bounds["y"], bounds["y"] + bounds["h"]):
                for x in range(bounds["x"], bounds["x"] + bounds["w"]):
                    if self.in_bounds(x, y):
                        tiles[y][x] = TALL_ROCK

    def _cave_entrance_bounds(self, entrance):
        """Return the desktop tile rectangle occupied by a cave entrance."""
        return {
            "x": entrance["x"] - (entrance.get("w", 1) // 2),
            "y": entrance["y"],
            "w": entrance.get("w", 1),
            "h": entrance.get("h", 1),
        }

    def _cave_entrance_at_tile(self, tile_x, tile_y):
        """Return the cave entrance occupying a tile, if any."""
        for entrance in CAVE_ENTRANCES:
            bounds = self._cave_entrance_bounds(entrance)
            if bounds["x"] <= tile_x < bounds["x"] + bounds["w"] and bounds["y"] <= tile_y < bounds["y"] + bounds["h"]:
                return entrance
        return None

    def _is_outer_rock_tile(self, tiles, tile_x, tile_y):
        """Return whether a desktop rock tile borders non-rock terrain."""
        for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x = tile_x + offset_x
            y = tile_y + offset_y
            if not self.in_bounds(x, y) or tiles[y][x] != ROCK:
                return True
        return False

    def _patch_orchard_garden(self, tiles):
        """Apply the orchard garden terrain patch in the desktop map."""
        zone = DESIGN_ZONES["orchard_garden"]
        for y in range(zone["y1"], zone["y2"] + 1):
            for x in range(zone["x1"], zone["x2"] + 1):
                if self.in_bounds(x, y):
                    tiles[y][x] = SAND if self._is_orchard_garden_path_tile(x, y) else GRASS

    def _orchard_garden_area_for_tile(self, tile_x, tile_y):
        """Return which desktop orchard garden sub-area contains a tile."""
        zone = DESIGN_ZONES["orchard_garden"]
        if tile_y < zone["y1"] or tile_y > zone["y2"] or tile_x < zone["x1"] or tile_x > zone["x2"]:
            return None
        if tile_x <= zone["split_x"]:
            return {"x1": zone["x1"], "x2": zone["split_x"], "y1": zone["y1"], "y2": zone["y2"]}
        return {"x1": zone["split_x"] + 1, "x2": zone["x2"], "y1": zone["y1"], "y2": zone["y2"]}

    def _is_orchard_garden_path_tile(self, tile_x, tile_y):
        """Return whether a desktop tile is part of an orchard path."""
        area = self._orchard_garden_area_for_tile(tile_x, tile_y)
        if not area:
            return False
        path_x = (area["x1"] + area["x2"]) // 2
        path_y = (area["y1"] + area["y2"]) // 2
        return tile_x == path_x or tile_y == path_y

    def _patch_barley_field(self, tiles):
        """Apply the Barley Field terrain patch with cross paths."""
        zone = DESIGN_ZONES["barley_field"]
        for y in range(zone["y1"], zone["y2"] + 1):
            for x in range(zone["x1"], zone["x2"] + 1):
                if self.in_bounds(x, y):
                    tiles[y][x] = SAND if self._is_barley_field_path_tile(x, y) else GRASS

    def _barley_field_area_for_tile(self, tile_x, tile_y):
        """Return the Barley Field zone if a tile is inside it."""
        zone = DESIGN_ZONES["barley_field"]
        if zone["x1"] <= tile_x <= zone["x2"] and zone["y1"] <= tile_y <= zone["y2"]:
            return zone
        return None

    def _is_barley_field_path_tile(self, tile_x, tile_y):
        """Return whether a Barley Field tile belongs to the cross paths."""
        zone = self._barley_field_area_for_tile(tile_x, tile_y)
        return bool(zone) and (tile_x == zone["path_x"] or tile_y == zone["path_y"])

    def _patch_wheat_field(self, tiles):
        """Apply the Wheat Field terrain patch with cross paths."""
        zone = DESIGN_ZONES["wheat_field"]
        for y in range(zone["y1"], zone["y2"] + 1):
            for x in range(zone["x1"], zone["x2"] + 1):
                if self.in_bounds(x, y):
                    tiles[y][x] = SAND if self._is_wheat_field_path_tile(x, y) else GRASS

    def _wheat_field_area_for_tile(self, tile_x, tile_y):
        """Return the Wheat Field zone if a tile is inside it."""
        zone = DESIGN_ZONES["wheat_field"]
        if zone["x1"] <= tile_x <= zone["x2"] and zone["y1"] <= tile_y <= zone["y2"]:
            return zone
        return None

    def _is_wheat_field_path_tile(self, tile_x, tile_y):
        """Return whether a Wheat Field tile belongs to the cross paths."""
        zone = self._wheat_field_area_for_tile(tile_x, tile_y)
        return bool(zone) and (tile_x == zone["path_x"] or tile_y == zone["path_y"])

    def _place_buildings(self):
        """Place authored and generated buildings in the desktop world."""
        buildings = [dict(SHIP_BUILDING)]
        for site in BUILDING_SITES:
            tile_x = site["x"]
            tile_y = site["y"]
            if self._can_place_building(tile_x, tile_y):
                background = self._building_background(tile_x, tile_y)
                buildings.append(
                    {
                        "id": site["id"],
                        "name": site["name"],
                        "kind": "house",
                        "x": tile_x,
                        "y": tile_y,
                        "w": 3,
                        "h": 3,
                        "background": background,
                        "variant": len(buildings) % 3,
                        "door_x": 1,
                        "door_y": 2,
                        "entrances": [
                            {
                                "id": f"{site['id']}-entrance",
                                "name": "Front Door",
                                "area_id": site["area_id"],
                                "x": 1,
                                "y": 2,
                            }
                        ],
                    }
                )
                self._make_building_ground(tile_x, tile_y, background)
        return buildings

    def _can_place_building(self, tile_x, tile_y):
        """Return whether a desktop building can occupy the requested tiles."""
        for y in range(tile_y, tile_y + 3):
            for x in range(tile_x, tile_x + 3):
                if not self.in_bounds(x, y) or self.tiles[y][x] in (WATER, ROCK, TALL_ROCK):
                    return False
        return True

    def _building_background(self, tile_x, tile_y):
        """Choose terrain background for a desktop building footprint."""
        counts = {SAND: 0, GRASS: 0, FOREST: 0}
        for y in range(tile_y - 1, tile_y + 4):
            for x in range(tile_x - 1, tile_x + 4):
                if tile_x <= x < tile_x + 3 and tile_y <= y < tile_y + 3:
                    continue
                if self.in_bounds(x, y) and self.tiles[y][x] in counts:
                    counts[self.tiles[y][x]] += 1

        return max(counts, key=counts.get)

    def _make_building_ground(self, tile_x, tile_y, background):
        """Create desktop terrain under a building footprint."""
        for y in range(tile_y, tile_y + 3):
            for x in range(tile_x, tile_x + 3):
                self.tiles[y][x] = background

    def in_bounds(self, tile_x, tile_y):
        """Return whether tile coordinates are inside the map."""
        return 0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT

    def tile_at_pixel(self, pixel_x, pixel_y):
        """Return the terrain tile located under pixel coordinates."""
        tile_x = int(pixel_x // TILE_SIZE)
        tile_y = int(pixel_y // TILE_SIZE)
        if not self.in_bounds(tile_x, tile_y):
            return WATER
        return self.tiles[tile_y][tile_x]

    def building_at_pixel(self, pixel_x, pixel_y):
        """Return the building located under pixel coordinates, if any."""
        tile_x = int(pixel_x // TILE_SIZE)
        tile_y = int(pixel_y // TILE_SIZE)
        for building in self.buildings:
            if self._building_blocks_tile(building, tile_x, tile_y):
                return building
        return None

    def entrance_at_pixel(self, pixel_x, pixel_y):
        """Return the building entrance located under pixel coordinates, if any."""
        tile_x = int(pixel_x // TILE_SIZE)
        tile_y = int(pixel_y // TILE_SIZE)
        return self.entrance_at_tile(tile_x, tile_y)

    def entrance_at_tile(self, tile_x, tile_y):
        """Return the entrance occupying tile coordinates, if any."""
        cave_entrance = self._cave_entrance_at_tile(tile_x, tile_y)
        if cave_entrance:
            return {**cave_entrance, "world_x": tile_x, "world_y": tile_y}

        for building in self.buildings:
            local_x = tile_x - building["x"]
            local_y = tile_y - building["y"]
            entrance = self._entrance_for_building_local(building, local_x, local_y)
            if entrance:
                return {
                    **entrance,
                    "building_id": building["id"],
                    "building_name": building["name"],
                    "building_kind": building.get("kind", "house"),
                    "world_x": tile_x,
                    "world_y": tile_y,
                }
        return None

    def location_near_pixel(self, pixel_x, pixel_y, radius=TILE_SIZE * 2.25):
        """Return nearby named locations for dialogue and HUD hints."""
        nearest = None
        nearest_distance = radius

        for entrance in CAVE_ENTRANCES:
            bounds = self._cave_entrance_bounds(entrance)
            entrance_x = (bounds["x"] + bounds["w"] / 2) * TILE_SIZE
            entrance_y = (bounds["y"] + bounds["h"] / 2) * TILE_SIZE
            distance = math.hypot(pixel_x - entrance_x, pixel_y - entrance_y)
            if distance <= nearest_distance:
                nearest_distance = distance
                nearest = {**entrance, "type": "entrance"}

        for building in self.buildings:
            for entrance in building.get("entrances", ()):
                entrance_x = (building["x"] + entrance["x"] + entrance.get("w", 1) / 2) * TILE_SIZE
                entrance_y = (building["y"] + entrance["y"] + entrance.get("h", 1) / 2) * TILE_SIZE
                distance = math.hypot(pixel_x - entrance_x, pixel_y - entrance_y)
                if distance <= nearest_distance:
                    nearest_distance = distance
                    nearest = {
                        **entrance,
                        "type": "entrance",
                        "building_id": building["id"],
                        "building_name": building["name"],
                        "building_kind": building.get("kind", "house"),
                    }

        if nearest:
            return nearest

        for landmark in CLOISTER_LANDMARKS:
            distance = self._distance_to_landmark_point(pixel_x, pixel_y, landmark)
            if distance <= nearest_distance:
                nearest_distance = distance
                nearest = {
                    "type": "landmark",
                    "id": landmark["id"],
                    "name": landmark["name"],
                }

        lake_distance = self._distance_to_landmark_rect(pixel_x, pixel_y, LAKE_OF_TEARS)
        if lake_distance <= nearest_distance:
            nearest_distance = lake_distance
            nearest = {
                "type": "landmark",
                "id": LAKE_OF_TEARS["id"],
                "name": LAKE_OF_TEARS["name"],
            }

        if nearest and nearest["type"] == "landmark":
            return nearest

        for building in self.buildings:
            left = building["x"] * TILE_SIZE
            top = building["y"] * TILE_SIZE
            right = (building["x"] + building["w"]) * TILE_SIZE
            bottom = (building["y"] + building["h"]) * TILE_SIZE
            closest_x = max(left, min(pixel_x, right))
            closest_y = max(top, min(pixel_y, bottom))
            distance = math.hypot(pixel_x - closest_x, pixel_y - closest_y)
            if distance <= nearest_distance:
                nearest_distance = distance
                nearest = {
                    "type": "building",
                    "id": building["id"],
                    "name": building["name"],
                    "building_id": building["id"],
                    "building_name": building["name"],
                    "building_kind": building.get("kind", "house"),
                }

        return nearest

    def _distance_to_landmark_point(self, pixel_x, pixel_y, landmark):
        """Return the pixel distance from a point to a point landmark."""
        landmark_x = landmark["x"] * TILE_SIZE
        landmark_y = landmark["y"] * TILE_SIZE
        return math.hypot(pixel_x - landmark_x, pixel_y - landmark_y)

    def _distance_to_landmark_rect(self, pixel_x, pixel_y, landmark):
        """Return the pixel distance from a point to a landmark rectangle."""
        left = landmark["x1"] * TILE_SIZE
        top = landmark["y1"] * TILE_SIZE
        right = (landmark["x2"] + 1) * TILE_SIZE
        bottom = (landmark["y2"] + 1) * TILE_SIZE
        closest_x = max(left, min(pixel_x, right))
        closest_y = max(top, min(pixel_y, bottom))
        return math.hypot(pixel_x - closest_x, pixel_y - closest_y)

    def is_building_tile(self, tile_x, tile_y):
        """Return whether a tile is covered by a building footprint."""
        for building in self.buildings:
            if (
                building["x"] <= tile_x < building["x"] + building["w"]
                and building["y"] <= tile_y < building["y"] + building["h"]
            ):
                return True
        return False

    def _building_blocks_tile(self, building, tile_x, tile_y):
        """Return whether a building blocks movement on a local tile."""
        local_x = tile_x - building["x"]
        local_y = tile_y - building["y"]
        inside = 0 <= local_x < building["w"] and 0 <= local_y < building["h"]
        if not inside:
            return False
        return self._entrance_for_building_local(building, local_x, local_y) is None

    def _entrance_for_building_local(self, building, local_x, local_y):
        """Return the building entrance at local building coordinates."""
        inside = 0 <= local_x < building["w"] and 0 <= local_y < building["h"]
        if not inside:
            return None

        for entrance in building.get("entrances", ()):
            width = entrance.get("w", 1)
            height = entrance.get("h", 1)
            if (
                entrance["x"] <= local_x < entrance["x"] + width
                and entrance["y"] <= local_y < entrance["y"] + height
            ):
                return entrance
        return None

    def can_walk(self, rect):
        """Return whether a collision rectangle can move through the world."""
        def can_stand_on(pixel_x, pixel_y):
            """Return whether a sampled collision point is walkable."""
            entrance = self.entrance_at_pixel(pixel_x, pixel_y)
            if entrance and entrance.get("terrain_kind") == "cave":
                return True
            if entrance and entrance.get("building_kind") == "ship":
                return True
            return self.tile_at_pixel(pixel_x, pixel_y) not in (WATER, ROCK, TALL_ROCK)

        sample_points = (
            rect.midbottom,
            rect.bottomleft,
            rect.bottomright,
            rect.center,
        )
        return all(
            can_stand_on(x, y)
            and not self.building_at_pixel(x, y)
            and (
                y < rect.y + rect.height * 0.6
                or (
                    not self._is_orchard_garden_blocked_pixel(x, y)
                    and not self._is_barley_field_blocked_pixel(x, y)
                    and not self._is_wheat_field_blocked_pixel(x, y)
                )
            )
            for x, y in sample_points
        )

    def _is_orchard_garden_blocked_pixel(self, pixel_x, pixel_y):
        """Return whether an orchard garden pixel blocks movement."""
        tile_x = int(pixel_x // TILE_SIZE)
        tile_y = int(pixel_y // TILE_SIZE)
        return bool(self._orchard_garden_area_for_tile(tile_x, tile_y)) and not self._is_orchard_garden_path_tile(tile_x, tile_y)

    def _is_barley_field_blocked_pixel(self, pixel_x, pixel_y):
        """Return whether a Barley Field pixel blocks movement."""
        tile_x = int(pixel_x // TILE_SIZE)
        tile_y = int(pixel_y // TILE_SIZE)
        return bool(self._barley_field_area_for_tile(tile_x, tile_y)) and not self._is_barley_field_path_tile(tile_x, tile_y)

    def _is_wheat_field_blocked_pixel(self, pixel_x, pixel_y):
        """Return whether a Wheat Field pixel blocks movement."""
        tile_x = int(pixel_x // TILE_SIZE)
        tile_y = int(pixel_y // TILE_SIZE)
        return bool(self._wheat_field_area_for_tile(tile_x, tile_y)) and not self._is_wheat_field_path_tile(tile_x, tile_y)

    def draw(self, surface, camera):
        """Draw the object using the active camera or surface context."""
        start_x = max(0, camera.x // TILE_SIZE)
        start_y = max(0, camera.y // TILE_SIZE)
        end_x = min(MAP_WIDTH, (camera.x + SCREEN_WIDTH) // TILE_SIZE + 2)
        end_y = min(MAP_HEIGHT, (camera.y + SCREEN_HEIGHT) // TILE_SIZE + 2)

        lower_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for tile_y in range(start_y, end_y):
            for tile_x in range(start_x, end_x):
                tile = self.tiles[tile_y][tile_x]
                rect = pygame.Rect(
                    tile_x * TILE_SIZE - camera.x,
                    tile_y * TILE_SIZE - camera.y,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(lower_layer, self._tile_color(tile, tile_x, tile_y), rect)
                self._draw_tile_detail(lower_layer, rect, tile, tile_x, tile_y)

        self._draw_cave_entrances(lower_layer, camera)
        surface.blit(lower_layer, (0, 0))
        self._draw_buildings(surface, camera)

    def _tile_color(self, tile, tile_x, tile_y):
        """Return the base render color for a terrain tile."""
        base = COLORS[tile]
        wobble = math.sin(tile_x * 1.7 + tile_y * 0.9) * 7
        wobble += math.cos(tile_x * 0.4 - tile_y * 1.3) * 5
        if tile == WATER:
            wobble *= 0.7
        return tuple(max(0, min(255, int(channel + wobble))) for channel in base)

    def _draw_tile_detail(self, surface, rect, tile, tile_x, tile_y):
        """Draw decorative detail for a terrain tile."""
        if tile == WATER:
            if (tile_x + tile_y) % 4 == 0:
                pygame.draw.line(
                    surface,
                    (59, 101, 128),
                    (rect.left + 8, rect.centery - 4),
                    (rect.right - 8, rect.centery - 2),
                    2,
                )
            if self._touches_land(tile_x, tile_y):
                pygame.draw.circle(surface, (150, 173, 166), rect.center, TILE_SIZE // 3, 2)
        elif tile == SAND:
            pygame.draw.circle(surface, (125, 131, 133), (rect.left + 14, rect.top + 18), 3)
            pygame.draw.circle(surface, (157, 163, 164), (rect.right - 12, rect.bottom - 13), 2)
        elif tile == BEACH:
            pygame.draw.circle(surface, (148, 135, 97), (rect.left + 11, rect.top + 15), 3)
            pygame.draw.circle(surface, (94, 87, 66), (rect.right - 14, rect.bottom - 12), 2)
            pygame.draw.line(surface, (95, 88, 66), (rect.left + 5, rect.top + 38), (rect.left + 21, rect.top + 34), 2)
            pygame.draw.line(surface, (95, 88, 66), (rect.left + 27, rect.top + 18), (rect.left + 43, rect.top + 14), 2)
        elif tile == GRASS:
            self._draw_grass(surface, rect, tile_x, tile_y)
            self._draw_barley_field_detail(surface, rect, tile_x, tile_y)
            self._draw_wheat_field_detail(surface, rect, tile_x, tile_y)
        elif tile == FOREST:
            self._draw_tree(surface, rect, tile_x, tile_y)
        elif tile == ROCK:
            pygame.draw.ellipse(surface, (27, 26, 32), rect.inflate(-10, -22).move(0, 9))
            pygame.draw.polygon(
                surface,
                (68, 65, 78),
                (
                    (rect.left + 8, rect.bottom - 11),
                    (rect.centerx - 2, rect.top + 7),
                    (rect.right - 8, rect.bottom - 13),
                ),
            )
            pygame.draw.line(surface, (185, 77, 122), (rect.centerx - 3, rect.top + 12), (rect.right - 13, rect.bottom - 15), 2)
        elif tile == TALL_ROCK:
            self._draw_tall_rock(surface, rect, tile_x, tile_y)

    def _draw_tall_rock(self, surface, rect, tile_x, tile_y):
        """Draw a tall rock cliff tile in the desktop renderer."""
        ridge = (tile_x * 5 + tile_y * 7) % 8
        pygame.draw.ellipse(surface, (7, 8, 12), (rect.left + 4, rect.bottom - 9, TILE_SIZE - 8, 10))
        pygame.draw.rect(surface, (36, 38, 46), (rect.left + 3, rect.top + 12, TILE_SIZE - 6, TILE_SIZE - 12))
        pygame.draw.polygon(
            surface,
            (58, 59, 69),
            (
                (rect.left + 3, rect.top + 14),
                (rect.left + 14 + ridge, rect.top - 10),
                (rect.left + 25, rect.top + 5),
                (rect.left + 17, rect.bottom),
                (rect.left + 3, rect.bottom),
            ),
        )
        pygame.draw.polygon(
            surface,
            (81, 80, 93),
            (
                (rect.left + 18, rect.top + 5),
                (rect.left + 33 - ridge * 0.5, rect.top - 16),
                (rect.left + 45, rect.top + 13),
                (rect.left + 39, rect.bottom),
                (rect.left + 18, rect.bottom),
            ),
        )
        pygame.draw.polygon(
            surface,
            (26, 27, 34),
            (
                (rect.left + 28, rect.top + 7),
                (rect.left + 45, rect.top + 13),
                (rect.left + 39, rect.bottom),
                (rect.left + 30, rect.bottom),
            ),
        )
        pygame.draw.line(surface, (116, 113, 127), (rect.left + 17, rect.top + 6), (rect.left + 10, rect.top + 38), 2)
        pygame.draw.line(surface, (116, 113, 127), (rect.left + 32, rect.top), (rect.left + 38, rect.top + 42), 2)
        pygame.draw.line(surface, (17, 18, 23), (rect.left + 4, rect.bottom - 4), (rect.right - 4, rect.bottom - 6), 3)

    def _draw_cave_entrances(self, surface, camera):
        """Draw all visible cave entrance overlays."""
        for entrance in CAVE_ENTRANCES:
            bounds = self._cave_entrance_bounds(entrance)
            rect = pygame.Rect(
                bounds["x"] * TILE_SIZE - camera.x,
                bounds["y"] * TILE_SIZE - camera.y,
                bounds["w"] * TILE_SIZE,
                bounds["h"] * TILE_SIZE,
            )
            self._draw_cave_entrance_mouth(surface, rect)

    def _draw_cave_entrance_mouth(self, surface, rect):
        """Draw one cave entrance mouth shape."""
        left_x = rect.left + rect.width * 0.08
        right_x = rect.left + rect.width * 0.92
        center_x = rect.centerx
        crown_y = rect.top + rect.height * 0.08
        shoulder_y = rect.top + rect.height * 0.42

        pygame.draw.polygon(
            surface,
            (34, 35, 42),
            (
                (center_x, crown_y),
                (right_x + rect.width * 0.08, rect.top + rect.height * 0.28),
                (right_x + rect.width * 0.04, rect.bottom),
                (left_x - rect.width * 0.04, rect.bottom),
                (left_x - rect.width * 0.08, rect.top + rect.height * 0.32),
            ),
        )
        pygame.draw.polygon(
            surface,
            (17, 18, 23),
            (
                (center_x - rect.width * 0.38, rect.top + rect.height * 0.18),
                (center_x - rect.width * 0.12, crown_y + 4),
                (center_x + rect.width * 0.16, crown_y),
                (center_x + rect.width * 0.42, rect.top + rect.height * 0.24),
                (right_x, rect.bottom),
                (left_x, rect.bottom),
            ),
        )
        mouth_points = (
            (center_x - rect.width * 0.28, rect.bottom),
            (center_x - rect.width * 0.32, shoulder_y),
            (center_x - rect.width * 0.22, crown_y + rect.height * 0.08),
            (center_x - rect.width * 0.05, rect.top + rect.height * 0.18),
            (center_x + rect.width * 0.2, rect.top + rect.height * 0.12),
            (center_x + rect.width * 0.34, shoulder_y),
            (center_x + rect.width * 0.3, rect.bottom),
        )
        pygame.draw.polygon(surface, (5, 6, 10), mouth_points)
        pygame.draw.line(surface, (12, 13, 17), (left_x, rect.bottom - 4), (right_x, rect.bottom - 7), 3)
        pygame.draw.line(
            surface,
            (53, 52, 61),
            (left_x + rect.width * 0.08, rect.top + rect.height * 0.36),
            (center_x - rect.width * 0.1, rect.top + rect.height * 0.2),
            2,
        )
        pygame.draw.line(
            surface,
            (53, 52, 61),
            (right_x - rect.width * 0.08, rect.top + rect.height * 0.32),
            (center_x + rect.width * 0.12, rect.top + rect.height * 0.16),
            2,
        )
        pygame.draw.polygon(
            surface,
            (9, 10, 14),
            (
                (center_x - rect.width * 0.12, rect.top + rect.height * 0.18),
                (center_x - rect.width * 0.02, rect.top + rect.height * 0.31),
                (center_x + rect.width * 0.07, rect.top + rect.height * 0.18),
            ),
        )
        pygame.draw.polygon(
            surface,
            (9, 10, 14),
            (
                (center_x + rect.width * 0.14, rect.top + rect.height * 0.19),
                (center_x + rect.width * 0.2, rect.top + rect.height * 0.3),
                (center_x + rect.width * 0.27, rect.top + rect.height * 0.2),
            ),
        )

    def _touches_land(self, tile_x, tile_y):
        """Return whether a water tile touches land terrain."""
        for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x = tile_x + offset_x
            y = tile_y + offset_y
            if self.in_bounds(x, y) and self.tiles[y][x] != WATER:
                return True
        return False

    def _draw_grass(self, surface, rect, tile_x, tile_y):
        """Draw grass detail for a terrain tile."""
        rng = random.Random(tile_x * 92821 + tile_y * 193)
        for _ in range(3):
            x = rect.left + rng.randint(8, TILE_SIZE - 8)
            y = rect.top + rng.randint(14, TILE_SIZE - 7)
            pygame.draw.line(surface, (86, 107, 69), (x, y), (x + rng.choice((-3, 3)), y - 9), 2)
        if (tile_x * 5 + tile_y) % 13 == 0:
            center = (rect.left + 31, rect.top + 18)
            pygame.draw.circle(surface, (126, 49, 88), center, 3)
            pygame.draw.circle(surface, (176, 145, 88), (center[0] + 5, center[1] + 5), 3)

    def _draw_tree(self, surface, rect, tile_x, tile_y):
        """Draw a tree or forest detail for a terrain tile."""
        offset = ((tile_x * 17 + tile_y * 11) % 9) - 4
        trunk = pygame.Rect(rect.centerx - 3 + offset, rect.centery + 4, 7, 17)
        variant = (tile_x * 17 + tile_y * 11) % 3
        pygame.draw.ellipse(surface, (11, 13, 16), rect.inflate(-10, -20).move(offset, 12))
        pygame.draw.rect(surface, (48, 35, 31), trunk)

        if variant == 0:
            pygame.draw.line(surface, (44, 33, 29), (rect.centerx + offset, rect.bottom - 8), (rect.centerx + offset - 1, rect.top + 8), 6)
            pygame.draw.line(surface, (44, 33, 29), (rect.centerx + offset, rect.centery), (rect.left + 9, rect.top + 7), 4)
            pygame.draw.line(surface, (44, 33, 29), (rect.centerx + offset, rect.centery + 4), (rect.right - 5, rect.top + 11), 4)
            pygame.draw.circle(surface, (109, 29, 53), (rect.centerx + 8 + offset, rect.top + 16), 3)
        elif variant == 1:
            pygame.draw.polygon(
                surface,
                (19, 41, 31),
                (
                    (rect.centerx + offset, rect.top + 3),
                    (rect.left + 5, rect.bottom - 6),
                    (rect.right - 5, rect.bottom - 6),
                ),
            )
            pygame.draw.polygon(
                surface,
                (32, 63, 47),
                (
                    (rect.centerx + offset, rect.top + 8),
                    (rect.left + 13, rect.bottom - 11),
                    (rect.right - 13, rect.bottom - 11),
                ),
            )
        else:
            pygame.draw.ellipse(surface, (22, 42, 35), rect.inflate(-15, -4).move(offset, -4))
            pygame.draw.line(surface, (11, 23, 21), (rect.centerx + offset, rect.top + 7), (rect.centerx + offset, rect.bottom - 6), 2)

    def _draw_barley_field_detail(self, surface, rect, tile_x, tile_y):
        """Draw rows of barley in non-path Barley Field tiles."""
        zone = DESIGN_ZONES["barley_field"]
        if not (zone["x1"] <= tile_x <= zone["x2"] and zone["y1"] <= tile_y <= zone["y2"]):
            return
        if self._is_barley_field_path_tile(tile_x, tile_y):
            return

        pygame.draw.rect(surface, (63, 57, 28), rect.inflate(-6, -6))
        for col in range(4):
            stalk_x = rect.left + 10 + col * 9 + ((tile_x + tile_y + col) % 3)
            pygame.draw.line(surface, (181, 155, 82), (stalk_x, rect.top + 38), (stalk_x + 3, rect.top + 13), 2)
            pygame.draw.line(surface, (208, 185, 106), (stalk_x + 3, rect.top + 18), (stalk_x - 3, rect.top + 14), 2)
            pygame.draw.line(surface, (208, 185, 106), (stalk_x + 2, rect.top + 23), (stalk_x + 8, rect.top + 19), 2)

    def _draw_wheat_field_detail(self, surface, rect, tile_x, tile_y):
        """Draw rows of wheat in non-path Wheat Field tiles."""
        zone = DESIGN_ZONES["wheat_field"]
        if not (zone["x1"] <= tile_x <= zone["x2"] and zone["y1"] <= tile_y <= zone["y2"]):
            return
        if self._is_wheat_field_path_tile(tile_x, tile_y):
            return

        pygame.draw.rect(surface, (74, 80, 80), rect.inflate(-6, -6))
        for col in range(4):
            stalk_x = rect.left + 9 + col * 9 + ((tile_x * 2 + tile_y + col) % 4)
            pygame.draw.line(surface, (159, 166, 164), (stalk_x, rect.top + 39), (stalk_x + 2, rect.top + 12), 2)
            pygame.draw.line(surface, (196, 203, 201), (stalk_x + 2, rect.top + 17), (stalk_x - 4, rect.top + 13), 2)
            pygame.draw.line(surface, (196, 203, 201), (stalk_x + 2, rect.top + 21), (stalk_x + 8, rect.top + 16), 2)
            pygame.draw.line(surface, (196, 203, 201), (stalk_x + 1, rect.top + 25), (stalk_x - 4, rect.top + 21), 2)

    def _draw_buildings(self, surface, camera):
        """Draw all visible buildings in the desktop renderer."""
        for building in self.buildings:
            rect = pygame.Rect(
                building["x"] * TILE_SIZE - camera.x,
                building["y"] * TILE_SIZE - camera.y - 16,
                building["w"] * TILE_SIZE,
                building["h"] * TILE_SIZE + 16,
            )
            if rect.right < 0 or rect.left > SCREEN_WIDTH or rect.bottom < 0 or rect.top > SCREEN_HEIGHT:
                continue

            building_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            local_rect = pygame.Rect(0, 0, rect.width, rect.height)
            if building.get("kind") == "ship":
                self._draw_ship(building_surface, local_rect)
            elif building["variant"] == 0:
                self._draw_manor(building_surface, local_rect)
            elif building["variant"] == 1:
                self._draw_chapel(building_surface, local_rect)
            else:
                self._draw_ruin(building_surface, local_rect)

            self._apply_alpha_mask(building_surface)
            surface.blit(building_surface, rect.topleft)

    def _apply_alpha_mask(self, surface):
        """Apply transparent corner masking to a rendered surface."""
        mask = pygame.mask.from_surface(surface)
        mask_surface = mask.to_surface(
            setcolor=(255, 255, 255, 255),
            unsetcolor=(255, 255, 255, 0),
        ).convert_alpha()
        surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _draw_ship(self, surface, rect):
        """Draw the harbour ship building sprite."""
        bob = 2
        base_x = rect.left
        base_y = rect.top
        base_w = rect.width
        base_h = rect.height
        x = base_x + base_w * 0.14
        y = base_y + base_h * 0.1
        w = base_w * 0.72
        h = base_h * 0.72
        pygame.draw.ellipse(surface, (4, 7, 11, 142), (x + w * 0.04, y + h * 0.68 + bob, w * 0.92, h * 0.24))
        pygame.draw.polygon(
            surface,
            (36, 31, 37),
            (
                (x + 12, y + h * 0.42 + bob),
                (x + w - 5, y + h * 0.57 + bob),
                (x + w - 34, y + h * 0.83 + bob),
                (x + 18, y + h * 0.78 + bob),
                (x + 6, y + h * 0.55 + bob),
            ),
        )
        pygame.draw.polygon(
            surface,
            (58, 43, 49),
            (
                (x + 25, y + h * 0.49 + bob),
                (x + w - 30, y + h * 0.57 + bob),
                (x + w - 45, y + h * 0.7 + bob),
                (x + 30, y + h * 0.68 + bob),
                (x + 18, y + h * 0.54 + bob),
            ),
        )
        pygame.draw.polygon(
            surface,
            (43, 32, 40),
            (
                (x + 16, y + h * 0.34 + bob),
                (x + 48, y + h * 0.38 + bob),
                (x + 42, y + h * 0.52 + bob),
                (x + 18, y + h * 0.5 + bob),
            ),
        )
        pygame.draw.line(surface, (112, 95, 104), (x + 19, y + h * 0.38 + bob), (x + 43, y + h * 0.41 + bob), 2)
        pygame.draw.polygon(
            surface,
            (21, 19, 24),
            (
                (x + w * 0.31, y + h * 0.63 + bob),
                (x + w * 0.62, y + h * 0.66 + bob),
                (x + w * 0.55, y + h * 0.8 + bob),
                (x + w * 0.36, y + h * 0.77 + bob),
            ),
        )
        pygame.draw.line(surface, (12, 10, 14), (x + 11, y + h * 0.52 + bob), (x + w - 8, y + h * 0.58 + bob), 3)
        for rib_index in range(5):
            rib = 0.16 + rib_index * 0.17
            pygame.draw.line(
                surface,
                (103, 86, 94),
                (x + w * rib, y + h * 0.5 + bob),
                (x + w * (rib * 0.9 + 0.05), y + h * 0.74 + bob),
                2,
            )

        mast_x = x + w * 0.5
        pygame.draw.line(surface, (49, 36, 43), (mast_x, y + h * 0.49 + bob), (mast_x, y + 10 + bob), 5)
        pygame.draw.line(surface, (117, 100, 111), (mast_x, y + 16 + bob), (mast_x, y + 5 + bob), 2)
        pygame.draw.line(surface, (25, 20, 26), (mast_x, y + 18 + bob), (x + w * 0.82, y + h * 0.43 + bob), 2)
        pygame.draw.line(surface, (25, 20, 26), (mast_x, y + 18 + bob), (x + w * 0.7, y + h * 0.5 + bob), 2)

        pygame.draw.polygon(
            surface,
            (216, 208, 184),
            (
                (x + w * 0.53, y + 18 + bob),
                (x + w * 0.58, y + h * 0.46 + bob),
                (x + w * 0.86, y + h * 0.43 + bob),
                (x + w * 0.73, y + h * 0.25 + bob),
            ),
        )
        pygame.draw.polygon(
            surface,
            (185, 176, 155),
            (
                (x + w * 0.56, y + 22 + bob),
                (x + w * 0.62, y + h * 0.45 + bob),
                (x + w * 0.9, y + h * 0.41 + bob),
                (x + w * 0.74, y + h * 0.29 + bob),
            ),
        )
        pygame.draw.polygon(
            surface,
            (239, 232, 207),
            (
                (x + w * 0.54, y + h * 0.12 + bob),
                (x + w * 0.57, y + h * 0.31 + bob),
                (x + w * 0.78, y + h * 0.29 + bob),
            ),
        )
        pygame.draw.line(surface, (123, 108, 94), (x + w * 0.58, y + h * 0.21 + bob), (x + w * 0.82, y + h * 0.42 + bob), 2)
        pygame.draw.line(surface, (123, 108, 94), (x + w * 0.6, y + h * 0.24 + bob), (x + w * 0.86, y + h * 0.39 + bob), 2)
        pygame.draw.line(surface, (66, 54, 50), (x + w * 0.58, y + h * 0.28 + bob), (x + w * 0.8, y + h * 0.41 + bob), 1)
        pygame.draw.line(surface, (66, 54, 50), (x + w * 0.62, y + h * 0.29 + bob), (x + w * 0.84, y + h * 0.38 + bob), 1)

        pygame.draw.polygon(
            surface,
            (23, 20, 27),
            ((mast_x, y + 2 + bob), (x + w * 0.44, y + 24 + bob), (x + w * 0.56, y + 24 + bob)),
        )
        pygame.draw.rect(surface, (182, 165, 109), (mast_x - 2, y + 4 + bob, 4, 18))
        pygame.draw.rect(surface, (182, 165, 109), (mast_x - 10, y + 12 + bob, 20, 3))

        plank = pygame.Rect(base_x + TILE_SIZE * 2 - 10, base_y + TILE_SIZE * 3 - 6 + bob, 20, TILE_SIZE + 28)
        pygame.draw.rect(surface, (139, 104, 64), plank)
        pygame.draw.rect(surface, (61, 42, 27), plank, 2)
        for offset in range(12, plank.height, 12):
            pygame.draw.line(surface, (92, 67, 41), (plank.left + 3, plank.top + offset), (plank.right - 3, plank.top + offset), 1)

    def _draw_manor(self, surface, rect):
        """Draw the manor building sprite."""
        pygame.draw.ellipse(surface, (9, 10, 13), (rect.left + 22, rect.bottom - 18, rect.width - 44, 16))
        pygame.draw.polygon(
            surface,
            (23, 19, 27),
            ((rect.left + 10, rect.top + 72), (rect.centerx, rect.top + 21), (rect.right - 10, rect.top + 72)),
        )
        body = pygame.Rect(rect.left + 18, rect.top + 69, rect.width - 36, 72)
        inset = pygame.Rect(rect.left + 28, rect.top + 79, rect.width - 56, 60)
        pygame.draw.rect(surface, (47, 44, 52), body)
        pygame.draw.rect(surface, (65, 61, 73), inset)
        pygame.draw.rect(surface, (18, 18, 22), (rect.centerx - 12, rect.top + 101, 24, 42), border_radius=11)
        for x in (rect.left + 34, rect.right - 50):
            pygame.draw.rect(surface, (18, 18, 22), (x, rect.top + 91, 16, 22), border_radius=7)
            pygame.draw.line(surface, (157, 122, 79), (x + 8, rect.top + 91), (x + 8, rect.top + 113), 2)
            pygame.draw.line(surface, (157, 122, 79), (x, rect.top + 102), (x + 16, rect.top + 102), 2)
        for x in (rect.left + 25, rect.right - 53):
            pygame.draw.polygon(
                surface,
                (38, 32, 42),
                ((x, rect.top + 69), (x, rect.top + 45), (x + 14, rect.top + 32), (x + 28, rect.top + 45), (x + 28, rect.top + 69)),
            )
        pygame.draw.line(surface, (23, 21, 26), (rect.left + 19, rect.top + 139), (rect.centerx - 16, rect.top + 139), 5)
        pygame.draw.line(surface, (23, 21, 26), (rect.centerx + 16, rect.top + 139), (rect.right - 18, rect.top + 139), 5)

    def _draw_chapel(self, surface, rect):
        """Draw the chapel building sprite."""
        pygame.draw.ellipse(surface, (9, 10, 13), (rect.left + 24, rect.bottom - 17, rect.width - 48, 15))
        pygame.draw.polygon(
            surface,
            (22, 19, 27),
            ((rect.left + 14, rect.top + 65), (rect.centerx, rect.top + 17), (rect.right - 14, rect.top + 65)),
        )
        pygame.draw.polygon(
            surface,
            (56, 53, 65),
            ((rect.left + 20, rect.top + 140), (rect.left + 20, rect.top + 62), (rect.centerx, rect.top + 24), (rect.right - 20, rect.top + 62), (rect.right - 20, rect.top + 140)),
        )
        pygame.draw.polygon(
            surface,
            (72, 68, 81),
            ((rect.left + 33, rect.top + 133), (rect.left + 33, rect.top + 68), (rect.centerx, rect.top + 40), (rect.right - 33, rect.top + 68), (rect.right - 33, rect.top + 133)),
        )
        pygame.draw.rect(surface, (18, 18, 22), (rect.centerx - 13, rect.top + 106, 26, 36), border_radius=12)
        pygame.draw.rect(surface, (18, 18, 22), (rect.left + 38, rect.top + 89, 17, 22), border_radius=8)
        pygame.draw.rect(surface, (18, 18, 22), (rect.right - 55, rect.top + 89, 17, 22), border_radius=8)
        pygame.draw.line(surface, (156, 65, 95), (rect.centerx, rect.top + 18), (rect.centerx, rect.top + 42), 4)
        pygame.draw.line(surface, (156, 65, 95), (rect.centerx - 11, rect.top + 30), (rect.centerx + 11, rect.top + 30), 4)

    def _draw_ruin(self, surface, rect):
        """Draw the ruin building sprite."""
        pygame.draw.ellipse(surface, (9, 10, 13), (rect.left + 22, rect.bottom - 17, rect.width - 44, 15))
        points = (
            (rect.left + 17, rect.top + 140),
            (rect.left + 17, rect.top + 69),
            (rect.left + 35, rect.top + 69),
            (rect.left + 35, rect.top + 47),
            (rect.left + 58, rect.top + 47),
            (rect.left + 58, rect.top + 69),
            (rect.left + 84, rect.top + 69),
            (rect.left + 84, rect.top + 39),
            (rect.left + 109, rect.top + 39),
            (rect.left + 109, rect.top + 69),
            (rect.right - 17, rect.top + 69),
            (rect.right - 17, rect.top + 140),
        )
        pygame.draw.polygon(surface, (59, 57, 66), points)
        pygame.draw.rect(surface, (74, 70, 81), (rect.left + 27, rect.top + 76, rect.width - 54, 56))
        pygame.draw.rect(surface, (18, 18, 22), (rect.centerx - 13, rect.top + 107, 26, 35), border_radius=12)
        pygame.draw.rect(surface, (18, 18, 22), (rect.left + 27, rect.top + 92, 18, 25), border_radius=8)
        pygame.draw.rect(surface, (18, 18, 22), (rect.right - 45, rect.top + 91, 18, 27), border_radius=8)
        pygame.draw.polygon(surface, (18, 18, 22), ((rect.left + 48, rect.top + 72), (rect.left + 70, rect.top + 59), (rect.left + 86, rect.top + 71), (rect.left + 63, rect.top + 81)))
        pygame.draw.line(surface, (23, 21, 26), (rect.left + 18, rect.top + 140), (rect.centerx - 16, rect.top + 140), 5)
        pygame.draw.line(surface, (23, 21, 26), (rect.centerx + 17, rect.top + 140), (rect.right - 16, rect.top + 140), 5)


class Player:
    def __init__(self, world):
        """Initialize the player position, collision body, and movement state."""
        spawn_x, spawn_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
        if world.tiles[spawn_y][spawn_x] in (WATER, ROCK, TALL_ROCK) or world.is_building_tile(spawn_x, spawn_y):
            spawn_x, spawn_y = world.land_positions[0]

        self.rect = pygame.Rect(
            spawn_x * TILE_SIZE + 13,
            spawn_y * TILE_SIZE + 8,
            26,
            34,
        )
        self.speed = 225
        self.facing = pygame.Vector2(0, 1)
        self.step_timer = 0

    def update(self, dt, world):
        """Advance the object simulation for the current frame."""
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction.y += 1

        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.facing = direction
            self.step_timer += dt * 10
        else:
            self.step_timer = 0

        self._move_axis(direction.x * self.speed * dt, 0, world)
        self._move_axis(0, direction.y * self.speed * dt, world)

    def _move_axis(self, dx, dy, world):
        """Move the player along one axis while respecting collisions."""
        self.rect.x += round(dx)
        self.rect.y += round(dy)
        if not world.can_walk(self.rect):
            self.rect.x -= round(dx)
            self.rect.y -= round(dy)

    def draw(self, surface, camera):
        """Draw the object using the active camera or surface context."""
        x = self.rect.x - camera.x
        y = self.rect.y - camera.y
        bob = math.sin(self.step_timer) * 2 if self.step_timer else 0
        ear_sway = math.sin(self.step_timer) * 2 if self.step_timer else 0
        leg_step = math.sin(self.step_timer) * 2 if self.step_timer else 0

        shadow_rect = pygame.Rect(x - 5, y + self.rect.height - 1, self.rect.width + 10, 10)
        pygame.draw.ellipse(surface, (29, 41, 45), shadow_rect)

        body = pygame.Rect(x, y + bob + 12, self.rect.width, self.rect.height - 10)
        head_center = (x + self.rect.width // 2, y + bob + 11)
        pygame.draw.rect(surface, (18, 19, 24), body, border_radius=7)
        pygame.draw.rect(surface, (48, 48, 58), body.inflate(-8, -3), border_radius=4)
        pygame.draw.line(surface, (11, 12, 16), (head_center[0] - 7 + leg_step, y + bob + 35), (head_center[0] - 8 + leg_step, y + bob + 48), 3)
        pygame.draw.line(surface, (11, 12, 16), (head_center[0] + 7 - leg_step, y + bob + 35), (head_center[0] + 8 - leg_step, y + bob + 48), 3)
        pygame.draw.ellipse(surface, (8, 9, 13), (head_center[0] - 14 + leg_step, y + bob + 48, 10, 4))
        pygame.draw.ellipse(surface, (8, 9, 13), (head_center[0] + 4 - leg_step, y + bob + 48, 10, 4))
        pygame.draw.line(surface, (243, 240, 232), (head_center[0] - 12 + leg_step, y + bob + 49), (head_center[0] - 6 + leg_step, y + bob + 49), 1)
        pygame.draw.line(surface, (243, 240, 232), (head_center[0] + 6 - leg_step, y + bob + 49), (head_center[0] + 12 - leg_step, y + bob + 49), 1)
        pygame.draw.polygon(
            surface,
            (5, 7, 11),
            ((head_center[0] - 9 + ear_sway, head_center[1] - 12), (head_center[0] - 17 + ear_sway * 0.35, head_center[1] - 28), (head_center[0] - 2 + ear_sway, head_center[1] - 18)),
        )
        pygame.draw.polygon(
            surface,
            (5, 7, 11),
            ((head_center[0] + 9 - ear_sway, head_center[1] - 12), (head_center[0] + 17 - ear_sway * 0.35, head_center[1] - 28), (head_center[0] + 2 - ear_sway, head_center[1] - 18)),
        )
        pygame.draw.ellipse(surface, (17, 25, 35), (head_center[0] - 17, head_center[1] - 9, 34, 38))
        pygame.draw.ellipse(surface, (242, 239, 231), (head_center[0] - 12, head_center[1] - 13, 24, 21))
        pygame.draw.ellipse(surface, (216, 204, 209), (head_center[0] - 10, head_center[1] - 9, 20, 18))
        pygame.draw.rect(surface, (238, 240, 245), (head_center[0] - 9, head_center[1] - 12, 18, 7))
        for offset in (-5, 0, 5):
            pygame.draw.line(surface, (185, 189, 201), (head_center[0] + offset, head_center[1] - 11), (head_center[0] + offset - 1, head_center[1] + 5), 1)
        pygame.draw.line(surface, (139, 0, 27), (head_center[0] - 8, head_center[1]), (head_center[0] - 3, head_center[1] - 1), 2)
        pygame.draw.line(surface, (139, 0, 27), (head_center[0] + 3, head_center[1] - 1), (head_center[0] + 9, head_center[1]), 2)
        pygame.draw.circle(surface, (28, 106, 185), (head_center[0] - 4, head_center[1] + 1), 2)
        pygame.draw.circle(surface, (28, 106, 185), (head_center[0] + 5, head_center[1] + 1), 2)
        pygame.draw.line(surface, (101, 188, 169), (head_center[0] - 2, head_center[1] + 8), (head_center[0] + 3, head_center[1] + 8), 1)


class Camera:
    def __init__(self):
        """Initialize the camera offset used for desktop rendering."""
        self.x = 0
        self.y = 0

    def follow(self, target_rect):
        """Move the camera to keep the target rectangle centered."""
        world_width = MAP_WIDTH * TILE_SIZE
        world_height = MAP_HEIGHT * TILE_SIZE
        self.x = target_rect.centerx - SCREEN_WIDTH // 2
        self.y = target_rect.centery - SCREEN_HEIGHT // 2
        self.x = max(0, min(self.x, world_width - SCREEN_WIDTH))
        self.y = max(0, min(self.y, world_height - SCREEN_HEIGHT))


def draw_hud(surface):
    """Draw the desktop game heads-up display."""
    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)
    title = font.render("Abbey Island Mystery", True, (245, 244, 232))
    help_text = small_font.render("WASD or arrows to explore", True, (229, 231, 214))

    panel = pygame.Rect(18, 16, 244, 58)
    pygame.draw.rect(surface, (28, 42, 50), panel, border_radius=8)
    pygame.draw.rect(surface, (235, 226, 176), panel, 2, border_radius=8)
    surface.blit(title, (34, 24))
    surface.blit(help_text, (34, 50))


def wrapped_lines(font, text, max_width):
    """Wrap text into lines that fit a maximum pixel width."""
    lines = []
    line = ""
    for word in text.split():
        next_line = f"{line} {word}".strip()
        if font.size(next_line)[0] <= max_width or not line:
            line = next_line
            continue
        lines.append(line)
        line = word
    if line:
        lines.append(line)
    return lines


def ground_description_for_tile(world, tile_x, tile_y):
    """Return contextual text for authored gardens and fields."""
    garden_area = world._orchard_garden_area_for_tile(tile_x, tile_y)
    if garden_area:
        zone = DESIGN_ZONES["orchard_garden"]
        if tile_x <= zone["split_x"]:
            return "You are walking in the fruit orchard."
        return "You are walking in the vegetable garden."
    if world._barley_field_area_for_tile(tile_x, tile_y):
        return "You are walking in the barley field."
    if world._wheat_field_area_for_tile(tile_x, tile_y):
        return "You are walking in the wheat field."
    return ""


def island_direction_description(tile_x, tile_y):
    """Return directional island context for a tile."""
    if not (0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT):
        return ""
    center_x = (MAP_WIDTH - 1) / 2
    center_y = (MAP_HEIGHT - 1) / 2
    horizontal = "west" if tile_x < center_x - 8 else "east" if tile_x > center_x + 8 else ""
    vertical = "north" if tile_y < center_y - 6 else "south" if tile_y > center_y + 6 else ""
    direction = "-".join(part for part in (vertical, horizontal) if part)
    if not direction:
        return ""
    return f"You are on the {direction} side of the island."


def current_dialogue(world, player):
    """Choose the current dialogue text from nearby world context."""
    foot_tile_x = player.rect.centerx // TILE_SIZE
    foot_tile_y = player.rect.bottom // TILE_SIZE
    if foot_tile_y == 37 and foot_tile_x in (46, 47):
        return (
            PLAYER_NAME,
            "Secret passage in the rocks.",
        )
    if (
        world.in_bounds(foot_tile_x, foot_tile_y)
        and world.tiles[foot_tile_y][foot_tile_x] == WATER
        and LAKE_OF_TEARS["x1"] <= foot_tile_x <= LAKE_OF_TEARS["x2"]
        and LAKE_OF_TEARS["y1"] <= foot_tile_y <= LAKE_OF_TEARS["y2"]
    ):
        return (
            PLAYER_NAME,
            "Swimming in the Lake of Tears",
        )

    location = world.location_near_pixel(player.rect.centerx, player.rect.bottom)
    if location and location["type"] == "entrance":
        return (
            PLAYER_NAME,
            f"{location['building_name']}: {location['name']}",
        )
    if location and location["type"] == "landmark":
        return (
            PLAYER_NAME,
            f"You are near the {location['name']}.",
        )

    ground_description = ground_description_for_tile(world, foot_tile_x, foot_tile_y)
    if ground_description:
        return (
            PLAYER_NAME,
            ground_description,
        )

    if location and location["type"] == "building":
        if location.get("building_kind") == "monastery":
            return (
                PLAYER_NAME,
                "The abbey grounds are onminously gloomy...",
            )
        return (
            PLAYER_NAME,
            location["name"],
        )

    direction_description = island_direction_description(foot_tile_x, foot_tile_y)
    if direction_description:
        return (
            PLAYER_NAME,
            direction_description,
        )

    return (
        PLAYER_NAME,
        "The island is quiet and mysterious...",
    )


def draw_dialogue_box(surface, world, player):
    """Draw the contextual dialogue box above the HUD."""
    speaker_font = pygame.font.Font(None, 30)
    body_font = pygame.font.Font(None, 24)
    margin = 24
    panel = pygame.Rect(margin, SCREEN_HEIGHT - 138, SCREEN_WIDTH - margin * 2, 112)
    speaker, text = current_dialogue(world, player)

    overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
    pygame.draw.rect(overlay, (14, 13, 16, 232), overlay.get_rect(), border_radius=8)
    pygame.draw.rect(overlay, (224, 205, 148, 225), overlay.get_rect(), 2, border_radius=8)
    pygame.draw.line(overlay, (224, 205, 148, 42), (12, 12), (panel.width - 12, 12), 2)
    pygame.draw.line(overlay, (224, 205, 148, 42), (12, panel.height - 14), (panel.width - 12, panel.height - 14), 2)
    surface.blit(overlay, panel.topleft)

    speaker_surface = speaker_font.render(speaker, True, (240, 223, 170))
    surface.blit(speaker_surface, (panel.x + 22, panel.y + 18))

    for index, line in enumerate(wrapped_lines(body_font, text, panel.width - 44)[:3]):
        line_surface = body_font.render(line, True, (247, 241, 221))
        surface.blit(line_surface, (panel.x + 22, panel.y + 54 + index * 24))


def ensure_background_music():
    """Initialize pygame audio and load the background music if possible."""
    if os.path.exists(MUSIC_PATH):
        return

    os.makedirs(os.path.dirname(MUSIC_PATH), exist_ok=True)
    sample_rate = 22_050
    seconds = 16
    melody = [261.63, 329.63, 392.0, 493.88, 440.0, 392.0, 329.63, 293.66]
    bass = [130.81, 146.83, 164.81, 196.0]
    note_length = 0.5

    with wave.open(MUSIC_PATH, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        for i in range(sample_rate * seconds):
            t = i / sample_rate
            melody_freq = melody[int(t / note_length) % len(melody)]
            bass_freq = bass[int(t / 2.0) % len(bass)]
            envelope = 0.45 + 0.55 * math.sin((t % note_length) / note_length * math.pi)
            tone = math.sin(math.tau * melody_freq * t) * 0.22 * envelope
            tone += math.sin(math.tau * bass_freq * t) * 0.12
            tone += math.sin(math.tau * melody_freq * 2 * t) * 0.04 * envelope
            wav_file.writeframes(struct.pack("<h", int(tone * 32767)))


def start_background_music():
    """Start looping background music when audio is available."""
    try:
        ensure_background_music()
        pygame.mixer.music.load(MUSIC_PATH)
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass


def main():
    """Run the module entry point."""
    pygame.mixer.pre_init(22_050, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption("Abbey Island Mystery")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    start_background_music()

    world = World()
    player = Player(world)
    camera = Camera()

    while True:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        player.update(dt, world)
        camera.follow(player.rect)

        screen.fill(COLORS[WATER])
        world.draw(screen, camera)
        player.draw(screen, camera)
        draw_hud(screen)
        draw_dialogue_box(screen, world, player)

        pygame.display.flip()


if __name__ == "__main__":
    main()
