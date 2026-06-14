const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
let renderCtx = ctx;
const gameMenu = document.querySelector(".game-menu");
const menuActionsToggle = document.getElementById("menuActionsToggle");
const soundButton = document.getElementById("sound");
const hudSaveGameButton = document.getElementById("hudSaveGame");
const hudLoadGameButton = document.getElementById("hudLoadGame");
const exitGameButton = document.getElementById("exitGame");
const inventorySlotButtons = [...document.querySelectorAll("[data-inventory-slot]")];
const useItemButton = document.getElementById("useItem");
const dropItemButton = document.getElementById("dropItem");
const examineItemButton = document.getElementById("examineItem");
const consumeItemButton = document.getElementById("consumeItem");
const inventoryCrossButton = document.getElementById("inventoryCross");
const intro = document.getElementById("intro");
const introStatus = document.getElementById("introStatus");
const startGameButton = document.getElementById("startGame");
const settingsGameButton = document.getElementById("settingsGame");
const loginGameButton = document.getElementById("loginGame");
const progressGameButton = document.getElementById("progressGame");
const loadGameScreen = document.getElementById("loadGameScreen");
const loadGameList = document.getElementById("loadGameList");
const loadGameStatus = document.getElementById("loadGameStatus");
const cancelLoadGameButton = document.getElementById("cancelLoadGame");
const createGameFromLoadButton = document.getElementById("createGameFromLoad");
const newGameScreen = document.getElementById("newGameScreen");
const newGameForm = document.getElementById("newGameForm");
const newGameStatus = document.getElementById("newGameStatus");
const cancelNewGameButton = document.getElementById("cancelNewGame");
const newPlayerNameInput = document.getElementById("newPlayerName");
const newPlayerPasswordInput = document.getElementById("newPlayerPassword");
const resetPositionInput = document.getElementById("resetPosition");
const resetSavesInput = document.getElementById("resetSaves");
const resetInventoryInput = document.getElementById("resetInventory");
const prologueScreen = document.getElementById("prologueScreen");
const prologueCopy = document.getElementById("prologueCopy");
const prologuePageStatus = document.getElementById("prologuePageStatus");
const previousProloguePageButton = document.getElementById("previousProloguePage");
const nextProloguePageButton = document.getElementById("nextProloguePage");
const beginPrologueGameButton = document.getElementById("beginPrologueGame");
const loginScreen = document.getElementById("loginScreen");
const loginForm = document.getElementById("loginForm");
const loginStatus = document.getElementById("loginStatus");
const cancelLoginButton = document.getElementById("cancelLogin");
const loginPlayerNameInput = document.getElementById("loginPlayerName");
const loginPlayerPasswordInput = document.getElementById("loginPlayerPassword");

const TILE_SIZE = 48;
const PLAYER_SPRITE_HEIGHT = 84;
const MAP_WIDTH = 90;
const MAP_HEIGHT = 62;
const START_TILE = { x: 46, y: 14 };
let pendingPrologueStart = { loadSave: false };
let prologuePageIndex = 0;

const PROLOGUE_PAGES = [
  [
    { text: "For centuries, Black Forest Abbey stood alone upon Abbey Island, a remote speck of land surrounded by treacherous seas and perpetual mist." },
    { text: "Hidden from the world, the abbey and its surrounding settlement had become entirely self-sustaining." },
    { text: "The nuns who lived there farmed the fertile fields, tended livestock, maintained workshops, and watched over the ancient lighthouse that guarded ships from the jagged rocks surrounding the island." },
  ],
  [
    { text: "Life on Abbey Island was quiet." },
    { text: "Until three nights ago.", className: "beat" },
    { text: "A violent storm cut the island off from the mainland. During that storm, Reverend Mother Agnes Blackwood, the beloved leader of the abbey, was brutally murdered inside the abbey library." },
  ],
  [
    { text: "Her body was discovered at dawn." },
    { text: "The doors were locked." },
    { text: "The windows were barred." },
    { text: "And every resident of the island claims to know nothing." },
  ],
  [
    { text: "The local authorities were unable to reach the island until the seas calmed. By then, fear and suspicion had spread through the community." },
    { text: "No one has been allowed to leave." },
    { text: "No one can leave.", className: "beat" },
  ],
  [
    { text: () => `You are ${sisterPlayerName()}, a nun of the Order of Saint Brigid and one of the Church's most trusted investigators.` },
    { text: "Sent by the Bishop himself, you have arrived aboard the supply ship Mercy to uncover the truth behind the killing." },
    { text: "As the ship disappears into the fog behind you, a chilling realization settles in your mind." },
  ],
  [
    { text: "The murderer is still here.", className: "beat" },
    { text: "Somewhere among the island's inhabitants is a killer." },
    { text: "To uncover the truth, you must explore every corner of Abbey Island." },
  ],
  [
    { text: "Not everyone will tell the truth." },
    { text: "Not every clue is what it seems." },
    { text: "And some secrets have been hidden for generations." },
    { text: "The storm has passed." },
    { text: "The investigation begins.", className: "beat" },
  ],
  [
    { heading: "Your Objective" },
    { text: "Identify the murderer." },
    { text: "Discover the motive." },
    { text: "Uncover the secrets of Abbey Island." },
    { text: "And survive long enough to reveal the truth." },
  ],
];

const WATER = 0;
const SAND = 1;
const GRASS = 2;
const FOREST = 3;
const ROCK = 4;
const TALL_ROCK = 5;
const BEACH = 6;

const COLORS = {
  [WATER]: [23, 44, 69],
  [SAND]: [106, 110, 112],
  [GRASS]: [38, 57, 37],
  [FOREST]: [29, 45, 34],
  [ROCK]: [45, 45, 52],
  [TALL_ROCK]: [34, 35, 42],
  [BEACH]: [116, 109, 87],
};

const DESIGN_ZONES = {
  orchardGarden: {
    id: "orchard-garden",
    name: "Fruit Orchard and Vegetable Garden",
    x1: 27,
    y1: 43,
    x2: 43,
    y2: 53,
    splitX: 35,
  },
  barleyField: {
    id: "barley-field",
    name: "Barley Field",
    x1: 44,
    y1: 39,
    x2: 51,
    y2: 50,
    pathX: 47,
    pathY: 44,
  },
  wheatField: {
    id: "wheat-field",
    name: "Wheat Field",
    x1: 55,
    y1: 39,
    x2: 62,
    y2: 50,
    pathX: 58,
    pathY: 44,
  },
};

const CAVE_ENTRANCES = [
  { id: "north-cave-entrance", name: "North Cave Entrance", x: 67, y: 41, w: 1, h: 2, terrainKind: "cave" },
  { id: "south-cave-entrance", name: "South Cave Entrance", x: 64, y: 45, w: 1, h: 2, terrainKind: "cave" },
];

const LAKE_OF_TEARS = { id: "lake-of-tears", name: "Lake of Tears", x1: 52, y1: 13, x2: 63, y2: 22 };
const CLOISTER_LANDMARKS = [
  { id: "west-fountain", name: "West Fountain", x: 39.3, y: 29.35 },
  { id: "cloister-well", name: "Well", x: 45, y: 31 },
  { id: "east-fountain", name: "East Fountain", x: 50.7, y: 29.35 },
];

function footTileInsideRect(tileX, tileY, rect) {
  return tileX >= rect.x1 && tileX <= rect.x2 && tileY >= rect.y1 && tileY <= rect.y2;
}

function caveEntranceBounds(entrance) {
  return {
    x: entrance.x - Math.floor((entrance.w || 1) / 2),
    y: entrance.y,
    w: entrance.w || 1,
    h: entrance.h || 1,
  };
}

function caveEntranceAtTile(tileX, tileY) {
  return CAVE_ENTRANCES.find((entrance) => {
    const bounds = caveEntranceBounds(entrance);
    return tileX >= bounds.x && tileX < bounds.x + bounds.w && tileY >= bounds.y && tileY < bounds.y + bounds.h;
  }) || null;
}

function orchardGardenAreaForTile(tileX, tileY) {
  const zone = DESIGN_ZONES.orchardGarden;
  if (tileY < zone.y1 || tileY > zone.y2 || tileX < zone.x1 || tileX > zone.x2) {
    return null;
  }
  if (tileX <= zone.splitX) {
    return {
      x1: zone.x1,
      x2: zone.splitX,
      y1: zone.y1,
      y2: zone.y2,
    };
  }
  return {
    x1: zone.splitX + 1,
    x2: zone.x2,
    y1: zone.y1,
    y2: zone.y2,
  };
}

function isOrchardGardenPathTile(tileX, tileY) {
  const area = orchardGardenAreaForTile(tileX, tileY);
  if (!area) {
    return false;
  }
  const pathX = Math.floor((area.x1 + area.x2) / 2);
  const pathY = Math.floor((area.y1 + area.y2) / 2);
  return tileX === pathX || tileY === pathY;
}

function barleyFieldAreaForTile(tileX, tileY) {
  const zone = DESIGN_ZONES.barleyField;
  if (tileY < zone.y1 || tileY > zone.y2 || tileX < zone.x1 || tileX > zone.x2) {
    return null;
  }
  return zone;
}

function isBarleyFieldPathTile(tileX, tileY) {
  const zone = barleyFieldAreaForTile(tileX, tileY);
  return Boolean(zone) && (tileX === zone.pathX || tileY === zone.pathY);
}

function wheatFieldAreaForTile(tileX, tileY) {
  const zone = DESIGN_ZONES.wheatField;
  if (tileY < zone.y1 || tileY > zone.y2 || tileX < zone.x1 || tileX > zone.x2) {
    return null;
  }
  return zone;
}

function isWheatFieldPathTile(tileX, tileY) {
  const zone = wheatFieldAreaForTile(tileX, tileY);
  return Boolean(zone) && (tileX === zone.pathX || tileY === zone.pathY);
}

function groundDescriptionForTile(tileX, tileY) {
  const gardenArea = orchardGardenAreaForTile(tileX, tileY);
  if (gardenArea) {
    const zone = DESIGN_ZONES.orchardGarden;
    return tileX <= zone.splitX ? "You are walking in the fruit orchard." : "You are walking in the vegetable garden.";
  }
  if (barleyFieldAreaForTile(tileX, tileY)) {
    return "You are walking in the barley field.";
  }
  if (wheatFieldAreaForTile(tileX, tileY)) {
    return "You are walking in the wheat field.";
  }
  return "";
}

function islandDirectionDescription(tileX, tileY) {
  if (tileX < 0 || tileX >= MAP_WIDTH || tileY < 0 || tileY >= MAP_HEIGHT) {
    return "";
  }
  const centerX = (MAP_WIDTH - 1) / 2;
  const centerY = (MAP_HEIGHT - 1) / 2;
  const horizontal = tileX < centerX - 8 ? "west" : tileX > centerX + 8 ? "east" : "";
  const vertical = tileY < centerY - 6 ? "north" : tileY > centerY + 6 ? "south" : "";
  const direction = [vertical, horizontal].filter(Boolean).join("-");
  if (!direction) {
    return "";
  }
  return `You are on the ${direction} side of the island.`;
}

const SHIP_BUILDING = {
  id: "harbour-ship",
  name: "Harbour Ship",
  kind: "ship",
  x: 45,
  y: 10,
  w: 4,
  h: 4,
  background: WATER,
  entrances: [
    { id: "harbour-ship-boarding-plank", name: "Boarding Plank", areaId: "harbour-ship-deck", x: 1, y: 3, w: 2, h: 1 },
  ],
  doors: [{ x: 1, y: 3, w: 2, h: 1 }],
  pier: { x: 46, y: 14, w: 2, h: 2 },
};

const AREA_ISLAND = "island";
const AREA_SHIP_ROOM = "harbour-ship-deck";
const SHIP_ROOM = {
  id: AREA_SHIP_ROOM,
  name: "Supply Ship Mercy",
  width: 12,
  height: 8,
  entranceTile: { x: 5, y: 6 },
};

const GRAPHICS = {
  tiles: {
    [WATER]: "assets/graphics/tile-water.svg",
    [SAND]: "assets/graphics/tile-sand.svg",
    [GRASS]: "assets/graphics/tile-grass.svg",
    [FOREST]: "assets/graphics/tile-forest.svg",
    [ROCK]: "assets/graphics/tile-rock.svg",
    [TALL_ROCK]: "assets/graphics/tile-tall-rock.svg",
    [BEACH]: "assets/graphics/tile-beach.svg",
  },
  trees: [
    "assets/graphics/tree-dead.svg",
    "assets/graphics/tree-pine.svg",
    "assets/graphics/tree-cypress.svg",
  ],
  rocks: [
    "assets/graphics/rock-crag.svg",
    "assets/graphics/rock-obelisk.svg",
    "assets/graphics/rock-rune.svg",
  ],
  buildings: [
    "assets/graphics/building-manor.svg",
    "assets/graphics/building-chapel.svg",
    "assets/graphics/building-ruin.svg",
  ],
  player: "assets/graphics/player-gothic.svg",
};

const HOUSE_BUILDING_PLANS = [
  { id: "north-chapel", name: "North Chapel", areaId: "north-chapel-nave" },
  { id: "west-manor", name: "West Manor", areaId: "west-manor-hall" },
  { id: "east-ruin", name: "East Ruin", areaId: "east-ruin-vault" },
  { id: "south-lodge", name: "Beach Lodge", areaId: "south-lodge-room" },
  { id: "old-parish-house", name: "Old Parish House", areaId: "old-parish-house-room" },
];
const GRANARY_BUILDING = { id: "granary", name: "Granary", areaId: "granary-room", x: 45, y: 51, w: 3, h: 3 };

const images = loadImages(GRAPHICS);
const GAME_DB_KEY = "mmmDatabase";
const keys = new Set();
const pad = {
  up: false,
  down: false,
  left: false,
  right: false,
};

let screenWidth = 960;
let screenHeight = 640;
let lastTime = performance.now();
let audio = null;
let musicEnabled = false;
let soundMuted = false;
let gameStarted = localStorage.getItem("mmmScreen") === "game";
const inventory = Array.from({ length: inventorySlotButtons.length }, () => null);
let selectedInventorySlot = null;
let loggedInName = null;
let dialoguePage = 0;
let dialogueKey = "";
let dialogueMoreButtonRect = null;
let lastTelemetryAt = 0;
let lastTelemetryPosition = null;

function defaultGameDatabase() {
  return {
    activePlayer: null,
    settings: {
      soundMuted: false,
    },
    players: {},
  };
}

function loadGameDatabase() {
  try {
    const parsed = JSON.parse(localStorage.getItem(GAME_DB_KEY));
    if (parsed && typeof parsed === "object" && parsed.players) {
      return {
        activePlayer: parsed.activePlayer || null,
        settings: {
          soundMuted: Boolean(parsed.settings?.soundMuted),
          ...(parsed.settings || {}),
        },
        players: parsed.players || {},
      };
    }
  } catch (error) {
    console.warn("Could not read game database.", error);
  }
  return defaultGameDatabase();
}

function saveGameDatabase(database) {
  localStorage.setItem(GAME_DB_KEY, JSON.stringify(database));
}

function loggedInPlayerName() {
  return loggedInName;
}

function isLoggedIn() {
  return Boolean(loggedInPlayerName());
}

function sisterPlayerName() {
  const playerName = (loggedInPlayerName() || "Player").trim();
  return /^sister\b/i.test(playerName) ? playerName : `Sister ${playerName}`;
}

function syncLoginState() {
  const database = loadGameDatabase();
  database.activePlayer = loggedInName;
  saveGameDatabase(database);

  progressGameButton.disabled = !loggedInName;
  progressGameButton.setAttribute("aria-disabled", String(!loggedInName));
  startGameButton.disabled = !loggedInName;
  startGameButton.setAttribute("aria-disabled", String(!loggedInName));
  settingsGameButton.textContent = loggedInName ? "Settings" : "New Player";
  loginGameButton.textContent = loggedInName ? "Logout" : "Login";
}

function activePlayerRecord() {
  const database = loadGameDatabase();
  if (!database.activePlayer) {
    return null;
  }
  return database.players[database.activePlayer] || null;
}

function loadSoundSetting() {
  const database = loadGameDatabase();
  const activeName = database.activePlayer;
  const playerSetting = activeName ? database.players[activeName]?.settings?.soundMuted : undefined;
  soundMuted = typeof playerSetting === "boolean" ? playerSetting : Boolean(database.settings?.soundMuted);
  updateSoundButton();
}

function saveSoundSetting() {
  const database = loadGameDatabase();
  database.settings = {
    ...(database.settings || {}),
    soundMuted,
  };
  if (database.activePlayer && database.players[database.activePlayer]) {
    database.players[database.activePlayer].settings = {
      ...(database.players[database.activePlayer].settings || {}),
      soundMuted,
    };
  }
  saveGameDatabase(database);
}

function menuActionsCollapsed() {
  return gameMenu.classList.contains("actions-collapsed");
}

function loadMenuActionsSetting() {
  const database = loadGameDatabase();
  const activeName = database.activePlayer;
  const playerSetting = activeName ? database.players[activeName]?.settings?.menuActionsCollapsed : undefined;
  const storedSetting = typeof playerSetting === "boolean" ? playerSetting : database.settings?.menuActionsCollapsed;
  return typeof storedSetting === "boolean" ? storedSetting : defaultMenuActionsCollapsed();
}

function saveMenuActionsSetting(collapsed = menuActionsCollapsed()) {
  const database = loadGameDatabase();
  database.settings = {
    ...(database.settings || {}),
    menuActionsCollapsed: collapsed,
  };
  if (database.activePlayer && database.players[database.activePlayer]) {
    database.players[database.activePlayer].settings = {
      ...(database.players[database.activePlayer].settings || {}),
      menuActionsCollapsed: collapsed,
    };
  }
  saveGameDatabase(database);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    const error = new Error(data.error || "Server request failed");
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

async function refreshSessionState() {
  try {
    const data = await apiRequest("/api/session");
    loggedInName = data.loggedIn ? data.user.name : null;
  } catch (error) {
    console.warn("Could not refresh login session.", error);
    loggedInName = null;
  }
  syncLoginState();
  return loggedInName;
}

async function serverLogin(name, password, createAllowed = false) {
  const data = await apiRequest("/api/login", {
    method: "POST",
    body: JSON.stringify({ name, password, create: createAllowed }),
  });
  loggedInName = data.user.name;
  syncLoginState();
  return data;
}

async function serverLogout() {
  try {
    await apiRequest("/api/logout", { method: "POST", body: "{}" });
  } catch (error) {
    console.warn("Could not log out on server.", error);
  }
  loggedInName = null;
  syncLoginState();
}

async function serverLoadGameState() {
  const data = await apiRequest("/api/save");
  return data.save || null;
}

function serverSaveGameState(save, reason = "autosave", { beacon = false } = {}) {
  const body = JSON.stringify({ save, reason });
  if (beacon && navigator.sendBeacon) {
    navigator.sendBeacon("/api/save", new Blob([body], { type: "application/json" }));
    return Promise.resolve();
  }
  return apiRequest("/api/save", {
    method: "POST",
    body,
  }).catch((error) => {
    console.warn("Could not save game state on server.", error);
  });
}

function trackGameEvent(type, payload = {}, { beacon = false } = {}) {
  const body = JSON.stringify({ type, payload });
  if (beacon && navigator.sendBeacon) {
    navigator.sendBeacon("/api/events", new Blob([body], { type: "application/json" }));
    return Promise.resolve();
  }
  return apiRequest("/api/events", {
    method: "POST",
    body,
  }).catch((error) => {
    console.warn(`Could not track ${type} event.`, error);
  });
}

function mulberry32(seed) {
  return function random() {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function color([r, g, b], alpha = 1) {
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function image(path) {
  const img = new Image();
  img.src = path;
  return img;
}

function loadImages(graphics) {
  return {
    tiles: Object.fromEntries(
      Object.entries(graphics.tiles).map(([tile, path]) => [tile, image(path)])
    ),
    trees: graphics.trees.map(image),
    rocks: graphics.rocks.map(image),
    buildings: graphics.buildings.map(image),
    player: image(graphics.player),
  };
}

function drawAsset(img, x, y, w, h) {
  if (img && img.complete && img.naturalWidth > 0) {
    renderCtx.drawImage(img, x, y, w, h);
    return true;
  }
  return false;
}

function makeBitmapLayer(w, h) {
  const layer = document.createElement("canvas");
  layer.width = Math.ceil(w);
  layer.height = Math.ceil(h);
  return layer;
}

function drawMaskedAsset(img, x, y, w, h) {
  if (!img || !img.complete || img.naturalWidth <= 0) {
    return false;
  }

  const layer = makeBitmapLayer(w, h);
  const layerCtx = layer.getContext("2d");
  layerCtx.imageSmoothingEnabled = false;
  layerCtx.drawImage(img, 0, 0, w, h);

  const mask = makeBitmapLayer(w, h);
  const maskCtx = mask.getContext("2d");
  maskCtx.imageSmoothingEnabled = false;
  maskCtx.drawImage(img, 0, 0, w, h);

  layerCtx.globalCompositeOperation = "destination-in";
  layerCtx.drawImage(mask, 0, 0);
  layerCtx.globalCompositeOperation = "source-over";

  renderCtx.drawImage(layer, x, y);
  return true;
}

function drawMaskedFallback(x, y, w, h, drawFallback) {
  const layer = makeBitmapLayer(w, h);
  const layerCtx = layer.getContext("2d");
  const previousCtx = renderCtx;
  renderCtx = layerCtx;
  layerCtx.imageSmoothingEnabled = false;

  drawFallback(0, 0, w, h);

  renderCtx = previousCtx;
  renderCtx.drawImage(layer, x, y);
}

function graphicsList() {
  return [
    ...Object.values(images.tiles),
    ...images.trees,
    ...images.rocks,
    ...images.buildings,
    images.player,
  ];
}

async function loadDesignMap() {
  try {
    const response = await fetch("/api/design", { credentials: "same-origin" });
    const data = await response.json();
    if (!data.ok || !Array.isArray(data.design?.grid)) {
      return;
    }
    world.applyDesignGrid(data.design.grid, data.design.blockingOverrides || {});
  } catch (error) {
    console.warn("Could not load map edits.", error);
  }
}

function tileColor(tile, tileX, tileY) {
  const base = COLORS[tile];
  let wobble = Math.sin(tileX * 1.7 + tileY * 0.9) * 7;
  wobble += Math.cos(tileX * 0.4 - tileY * 1.3) * 5;
  if (tile === WATER) {
    wobble *= 0.7;
  }
  return color(base.map((channel) => clamp(Math.floor(channel + wobble), 0, 255)));
}

class World {
  constructor() {
    this.tiles = this.generateIsland();
    this.buildings = this.placeBuildings();
    this.patchSouthBeach(this.tiles);
    this.cacheCanvas = document.createElement("canvas");
    this.cacheCanvas.width = MAP_WIDTH * TILE_SIZE;
    this.cacheCanvas.height = MAP_HEIGHT * TILE_SIZE;
    this.cacheReady = false;
    this.blockingOverrides = new Map();
    this.rebuildLandPositions();
  }

  rebuildLandPositions() {
    this.landPositions = [];
    for (let y = 0; y < MAP_HEIGHT; y += 1) {
      for (let x = 0; x < MAP_WIDTH; x += 1) {
        const explicitlyOpen = this.blockingOverrides.get(x + "," + y) === false;
        const softBlocked = (
          (Boolean(orchardGardenAreaForTile(x, y)) && !isOrchardGardenPathTile(x, y)) ||
          (Boolean(barleyFieldAreaForTile(x, y)) && !isBarleyFieldPathTile(x, y)) ||
          (Boolean(wheatFieldAreaForTile(x, y)) && !isWheatFieldPathTile(x, y))
        );
        if (!this.isTileBlocked(x, y) && !this.isBuildingTile(x, y) && (!softBlocked || explicitlyOpen)) {
          this.landPositions.push({ x, y });
        }
      }
    }
  }

  applyDesignGrid(grid, blockingOverrides = {}) {
    if (!Array.isArray(grid) || grid.length !== MAP_HEIGHT) {
      return;
    }
    this.tiles = grid.map((row) => row.slice(0, MAP_WIDTH));
    this.blockingOverrides = new Map(
      Object.entries(blockingOverrides).map(([key, blocked]) => [key, Boolean(blocked)])
    );
    this.rebuildLandPositions();
    this.invalidateCache();
  }

  isTileBlocked(tileX, tileY) {
    const key = tileX + "," + tileY;
    if (this.blockingOverrides.has(key)) {
      return this.blockingOverrides.get(key);
    }
    const tile = this.tiles[tileY]?.[tileX] ?? WATER;
    return tile === WATER || tile === ROCK || tile === TALL_ROCK;
  }

  isTerrainBlockedAtPixel(pixelX, pixelY) {
    const tileX = Math.floor(pixelX / TILE_SIZE);
    const tileY = Math.floor(pixelY / TILE_SIZE);
    return !this.inBounds(tileX, tileY) || this.isTileBlocked(tileX, tileY);
  }

  invalidateCache() {
    this.cacheReady = false;
  }

  generateIsland() {
    const rng = mulberry32(18);
    const centerX = MAP_WIDTH / 2;
    const centerY = MAP_HEIGHT / 2;
    const maxDistance = Math.min(MAP_WIDTH, MAP_HEIGHT) * 0.48;
    const tiles = [];

    for (let y = 0; y < MAP_HEIGHT; y += 1) {
      const row = [];
      for (let x = 0; x < MAP_WIDTH; x += 1) {
        const dx = (x - centerX) / maxDistance;
        const dy = (y - centerY) / (maxDistance * 0.82);
        const distance = Math.sqrt(dx * dx + dy * dy);
        const coastWobble =
          Math.sin(x * 0.25) * 0.08 +
          Math.cos(y * 0.23) * 0.07 +
          Math.sin((x + y) * 0.17) * 0.05 +
          (rng() * 0.11 - 0.055);
        const height = 1.0 - distance + coastWobble;

        if (height < 0.03) {
          row.push(WATER);
        } else if (height < 0.14) {
          row.push(SAND);
        } else if (height < 0.46) {
          row.push(GRASS);
        } else if (height < 0.68) {
          row.push(FOREST);
        } else {
          row.push(ROCK);
        }
      }
      tiles.push(row);
    }

    this.carvePaths(tiles);
    this.patchTerrain(tiles);
    return tiles;
  }

  patchTerrain(tiles) {
    tiles[7][36] = SAND;
    this.patchHarbourShipWater(tiles);
    this.patchLakeOfTears(tiles);
    this.patchOrchardGarden(tiles);
    this.patchBarleyField(tiles);
    this.patchWheatField(tiles);
    this.patchRockDoubleLine(tiles);
    this.patchTallRockEdges(tiles);
    this.patchCaveEntrances(tiles);
  }

  patchLakeOfTears(tiles) {
    const lake = LAKE_OF_TEARS;
    const centerX = (lake.x1 + lake.x2) / 2;
    const centerY = (lake.y1 + lake.y2) / 2;
    const radiusX = (lake.x2 - lake.x1 + 1) / 2;
    const radiusY = (lake.y2 - lake.y1 + 1) / 2;
    for (let y = lake.y1; y <= lake.y2; y += 1) {
      for (let x = lake.x1; x <= lake.x2; x += 1) {
        const dx = (x + 0.5 - centerX) / radiusX;
        const dy = (y + 0.5 - centerY) / radiusY;
        if (this.inBounds(x, y) && dx * dx + dy * dy <= 1) {
          tiles[y][x] = WATER;
        }
      }
    }
  }

  patchSouthBeach(tiles) {
    for (let x = 53; x <= 63; x += 1) {
      for (let y = 51; y < MAP_HEIGHT; y += 1) {
        if (!this.inBounds(x, y)) {
          continue;
        }
        if (tiles[y][x] === WATER) {
          break;
        }
        if (y <= 54 || tiles[y][x] === SAND || tiles[y][x] === BEACH) {
          tiles[y][x] = BEACH;
        }
      }
    }
  }

  patchCaveEntrances(tiles) {
    for (const entrance of CAVE_ENTRANCES) {
      const bounds = caveEntranceBounds(entrance);
      for (let y = bounds.y; y < bounds.y + bounds.h; y += 1) {
        for (let x = bounds.x; x < bounds.x + bounds.w; x += 1) {
          if (this.inBounds(x, y)) {
            tiles[y][x] = TALL_ROCK;
          }
        }
      }
    }
  }

  patchRockDoubleLine(tiles) {
    const start = { x: 66, y: 40 };
    const end = { x: 63, y: 50 };
    const steps = Math.max(Math.abs(end.x - start.x), Math.abs(end.y - start.y));
    for (let index = 0; index <= steps; index += 1) {
      const progress = index / steps;
      const x = Math.round(start.x + (end.x - start.x) * progress);
      const y = Math.round(start.y + (end.y - start.y) * progress);
      for (const offsetX of [0, 1]) {
        if (this.inBounds(x + offsetX, y)) {
          tiles[y][x + offsetX] = ROCK;
        }
      }
    }
  }

  patchTallRockEdges(tiles) {
    const tallRocks = [];
    for (let y = 0; y < MAP_HEIGHT; y += 1) {
      for (let x = 0; x < MAP_WIDTH; x += 1) {
        if (tiles[y][x] !== ROCK) {
          continue;
        }
        if (this.isOuterRockTile(tiles, x, y)) {
          tallRocks.push({ x, y });
        }
      }
    }
    for (const { x, y } of tallRocks) {
      tiles[y][x] = TALL_ROCK;
    }
  }

  isOuterRockTile(tiles, tileX, tileY) {
    const offsets = [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ];
    return offsets.some(([offsetX, offsetY]) => {
      const x = tileX + offsetX;
      const y = tileY + offsetY;
      return !this.inBounds(x, y) || tiles[y][x] !== ROCK;
    });
  }

  patchHarbourShipWater(tiles) {
    for (let y = SHIP_BUILDING.y; y < SHIP_BUILDING.y + SHIP_BUILDING.h; y += 1) {
      for (let x = SHIP_BUILDING.x; x < SHIP_BUILDING.x + SHIP_BUILDING.w; x += 1) {
        if (this.inBounds(x, y)) {
          tiles[y][x] = WATER;
        }
      }
    }
    const pier = SHIP_BUILDING.pier;
    for (let y = pier.y; y < pier.y + pier.h; y += 1) {
      for (let x = pier.x; x < pier.x + pier.w; x += 1) {
        if (this.inBounds(x, y)) {
          tiles[y][x] = SAND;
        }
      }
    }
  }

  patchOrchardGarden(tiles) {
    const zone = DESIGN_ZONES.orchardGarden;
    for (let y = zone.y1; y <= zone.y2; y += 1) {
      for (let x = zone.x1; x <= zone.x2; x += 1) {
        if (this.inBounds(x, y)) {
          tiles[y][x] = isOrchardGardenPathTile(x, y) ? SAND : GRASS;
        }
      }
    }
  }

  patchBarleyField(tiles) {
    const zone = DESIGN_ZONES.barleyField;
    for (let y = zone.y1; y <= zone.y2; y += 1) {
      for (let x = zone.x1; x <= zone.x2; x += 1) {
        if (this.inBounds(x, y)) {
          tiles[y][x] = isBarleyFieldPathTile(x, y) ? SAND : GRASS;
        }
      }
    }
  }

  patchWheatField(tiles) {
    const zone = DESIGN_ZONES.wheatField;
    for (let y = zone.y1; y <= zone.y2; y += 1) {
      for (let x = zone.x1; x <= zone.x2; x += 1) {
        if (this.inBounds(x, y)) {
          tiles[y][x] = isWheatFieldPathTile(x, y) ? SAND : GRASS;
        }
      }
    }
  }

  carvePaths(tiles) {
    const center = { x: Math.floor(MAP_WIDTH / 2), y: Math.floor(MAP_HEIGHT / 2) };
    const targets = [
      { x: Math.floor(MAP_WIDTH / 2), y: 8 },
      { x: 14, y: Math.floor(MAP_HEIGHT / 2) },
      { x: MAP_WIDTH - 15, y: Math.floor(MAP_HEIGHT / 2) + 3 },
      { x: Math.floor(MAP_WIDTH / 2) + 8, y: MAP_HEIGHT - 9 },
    ];

    for (const target of targets) {
      let x = center.x;
      let y = center.y;
      while (x !== target.x || y !== target.y) {
        if (x < target.x) x += 1;
        else if (x > target.x) x -= 1;
        if (y < target.y) y += 1;
        else if (y > target.y) y -= 1;

        for (let yy = y - 1; yy <= y + 1; yy += 1) {
          for (let xx = x - 1; xx <= x + 1; xx += 1) {
            if (this.inBounds(xx, yy) && tiles[yy][xx] !== WATER) {
              tiles[yy][xx] = SAND;
            }
          }
        }
      }
    }
  }

  placeBuildings() {
    const monastery = {
      id: "black-abbey",
      name: "Black Forest Abbey",
      kind: "monastery",
      x: 30,
      y: 25,
      w: 30,
      h: 12,
      unit: 3,
      cols: 10,
      rows: 4,
      background: SAND,
      layout: [
        ["building", "building", "building", "building", "building", "open", "building", "building", "building", "building"],
        ["wall", "building", "open", "open", "open", "open", "open", "open", "building", "wall"],
        ["wall", "building", "open", "open", "open", "open", "open", "open", "building", "wall"],
        ["building", "building", "building", "building", "wall", "wall", "open", "building", "building", "building"],
      ],
      entrances: [
        { id: "black-abbey-gatehouse", name: "West Tower", areaId: "black-abbey-gatehouse", x: 13, y: 11 },
        { id: "black-abbey-north-cloister", name: "North Cloister", areaId: "black-abbey-north-cloister", x: 10, y: 2 },
        { id: "black-abbey-prior-room", name: "Prior's Room", areaId: "black-abbey-prior-room", x: 22, y: 2 },
        { id: "black-abbey-west-chapel", name: "West Chapel", areaId: "black-abbey-west-chapel", x: 5, y: 5 },
        { id: "black-abbey-crypt-stair", name: "Crypt Stair", areaId: "black-abbey-crypt-stair", x: 0, y: 5 },
        { id: "black-abbey-library", name: "Library", areaId: "black-abbey-library", x: 29, y: 8 },
        { id: "black-abbey-refectory", name: "Refectory", areaId: "black-abbey-refectory", x: 4, y: 11 },
        { id: "black-abbey-infirmary", name: "Infirmary", areaId: "black-abbey-infirmary", x: 22, y: 11 },
        { id: "black-abbey-east-tower", name: "East Tower", areaId: "black-abbey-east-tower", x: 16, y: 11 },
      ],
      doors: [],
      alcoves: [
        { x: 10, y: 2, w: 1, h: 1 },
        { x: 22, y: 2, w: 1, h: 1 },
        { x: 5, y: 5, w: 1, h: 1 },
        { x: 0, y: 5, w: 1, h: 1 },
        { x: 29, y: 8, w: 1, h: 1 },
        { x: 4, y: 11, w: 1, h: 1 },
        { x: 22, y: 11, w: 1, h: 1 },
      ],
      walkways: [
        { x: 15, y: 0, w: 3, h: 3 },
        { x: 18, y: 9, w: 3, h: 3 },
      ],
      towers: [
        { x: 4, y: 3, entrance: true },
        { x: 5, y: 3, entrance: true },
      ],
      solidFixtures: [
        { x: 9, y: 4, w: 1, h: 1 },
        { x: 14, y: 5, w: 2, h: 2 },
        { x: 20, y: 4, w: 1, h: 1 },
      ],
    };
    const candidates = [
      { x: 43, y: 8 },
      { x: 14, y: 29 },
      { x: 73, y: 33 },
      { x: 51, y: 51 },
      { x: 25, y: 18 },
    ];
    const ship = { ...SHIP_BUILDING };
    const buildings = [monastery, ship];
    this.makeBuildingGround(monastery.x, monastery.y, monastery.w, monastery.h, monastery.background);
    const granary = {
      id: GRANARY_BUILDING.id,
      name: GRANARY_BUILDING.name,
      kind: "house",
      x: GRANARY_BUILDING.x,
      y: GRANARY_BUILDING.y,
      w: GRANARY_BUILDING.w,
      h: GRANARY_BUILDING.h,
      background: this.buildingBackground(GRANARY_BUILDING.x, GRANARY_BUILDING.y, GRANARY_BUILDING.w, GRANARY_BUILDING.h),
      imageIndex: buildings.length % images.buildings.length,
      entrances: [{ id: "granary-entrance", name: "Front Door", areaId: GRANARY_BUILDING.areaId, x: 1, y: 2 }],
      doors: [{ x: 1, y: 2 }],
    };
    buildings.push(granary);
    this.makeBuildingGround(granary.x, granary.y, granary.w, granary.h, granary.background);

    for (const [index, candidate] of candidates.entries()) {
      const site = this.findBuildableSite(candidate.x, candidate.y, 3, 3, buildings);
      if (site) {
        const background = this.buildingBackground(site.x, site.y, 3, 3);
        const plan = HOUSE_BUILDING_PLANS[index];
        buildings.push({
          id: plan.id,
          name: plan.name,
          kind: "house",
          x: site.x,
          y: site.y,
          w: 3,
          h: 3,
          background,
          imageIndex: buildings.length % images.buildings.length,
          entrances: [{ id: `${plan.id}-entrance`, name: "Front Door", areaId: plan.areaId, x: 1, y: 2 }],
          doors: [{ x: 1, y: 2 }],
        });
        this.makeBuildingGround(site.x, site.y, 3, 3, background);
      }
    }

    return buildings;
  }

  findBuildableSite(tileX, tileY, w, h, buildings) {
    for (let radius = 0; radius <= 8; radius += 1) {
      for (let offsetY = -radius; offsetY <= radius; offsetY += 1) {
        for (let offsetX = -radius; offsetX <= radius; offsetX += 1) {
          if (Math.abs(offsetX) !== radius && Math.abs(offsetY) !== radius) {
            continue;
          }
          const x = tileX + offsetX;
          const y = tileY + offsetY;
          if (this.canPlaceBuilding(x, y, w, h, buildings)) {
            return { x, y };
          }
        }
      }
    }
    return null;
  }

  canPlaceBuilding(tileX, tileY, w, h, buildings = []) {
    for (let y = tileY; y < tileY + h; y += 1) {
      for (let x = tileX; x < tileX + w; x += 1) {
        if (!this.inBounds(x, y) || this.tiles[y][x] === WATER || this.tiles[y][x] === ROCK || this.tiles[y][x] === TALL_ROCK) {
          return false;
        }
      }
    }
    return !buildings.some((building) => this.rectsOverlap(
      { x: tileX, y: tileY, w, h },
      building
    ));
  }

  rectsOverlap(a, b) {
    return (
      a.x < b.x + b.w &&
      a.x + a.w > b.x &&
      a.y < b.y + b.h &&
      a.y + a.h > b.y
    );
  }

  buildingBackground(tileX, tileY, w, h) {
    const counts = {
      [SAND]: 0,
      [GRASS]: 0,
      [FOREST]: 0,
    };

    for (let y = tileY - 1; y < tileY + h + 1; y += 1) {
      for (let x = tileX - 1; x < tileX + w + 1; x += 1) {
        if (x >= tileX && x < tileX + w && y >= tileY && y < tileY + h) {
          continue;
        }
        if (this.inBounds(x, y) && Object.prototype.hasOwnProperty.call(counts, this.tiles[y][x])) {
          counts[this.tiles[y][x]] += 1;
        }
      }
    }

    return Number(Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0]);
  }

  makeBuildingGround(tileX, tileY, w, h, background) {
    for (let y = tileY; y < tileY + h; y += 1) {
      for (let x = tileX; x < tileX + w; x += 1) {
        this.tiles[y][x] = background;
      }
    }
  }

  inBounds(tileX, tileY) {
    return tileX >= 0 && tileX < MAP_WIDTH && tileY >= 0 && tileY < MAP_HEIGHT;
  }

  tileAtPixel(pixelX, pixelY) {
    const tileX = Math.floor(pixelX / TILE_SIZE);
    const tileY = Math.floor(pixelY / TILE_SIZE);
    if (!this.inBounds(tileX, tileY)) {
      return WATER;
    }
    return this.tiles[tileY][tileX];
  }

  buildingAtPixel(pixelX, pixelY) {
    const tileX = Math.floor(pixelX / TILE_SIZE);
    const tileY = Math.floor(pixelY / TILE_SIZE);
    return this.buildings.find((building) => (
      this.buildingBlocksTile(building, tileX, tileY)
    ));
  }

  entranceAtPixel(pixelX, pixelY) {
    return this.entranceAtTile(
      Math.floor(pixelX / TILE_SIZE),
      Math.floor(pixelY / TILE_SIZE)
    );
  }

  entranceAtTile(tileX, tileY) {
    const caveEntrance = caveEntranceAtTile(tileX, tileY);
    if (caveEntrance) {
      return {
        ...caveEntrance,
        worldX: tileX,
        worldY: tileY,
      };
    }

    for (const building of this.buildings) {
      const localX = tileX - building.x;
      const localY = tileY - building.y;
      const entrance = this.entranceForBuildingLocal(building, localX, localY);
      if (entrance) {
        return {
          ...entrance,
          buildingId: building.id,
          buildingName: building.name,
          buildingKind: building.kind,
          worldX: tileX,
          worldY: tileY,
        };
      }
    }
    return null;
  }

  locationNearPixel(pixelX, pixelY, radius = TILE_SIZE * 2.25) {
    let nearest = null;
    let nearestDistance = radius;

    for (const entrance of CAVE_ENTRANCES) {
      const bounds = caveEntranceBounds(entrance);
      const entranceX = (bounds.x + bounds.w / 2) * TILE_SIZE;
      const entranceY = (bounds.y + bounds.h / 2) * TILE_SIZE;
      const distance = Math.hypot(pixelX - entranceX, pixelY - entranceY);
      if (distance <= nearestDistance) {
        nearestDistance = distance;
        nearest = {
          ...entrance,
          type: "entrance",
        };
      }
    }

    for (const building of this.buildings) {
      for (const entrance of building.entrances || []) {
        const entranceX = (building.x + entrance.x + (entrance.w || 1) / 2) * TILE_SIZE;
        const entranceY = (building.y + entrance.y + (entrance.h || 1) / 2) * TILE_SIZE;
        const distance = Math.hypot(pixelX - entranceX, pixelY - entranceY);
        if (distance <= nearestDistance) {
          nearestDistance = distance;
          nearest = {
            type: "entrance",
            id: entrance.id,
            name: entrance.name,
            areaId: entrance.areaId,
            buildingId: building.id,
            buildingName: building.name,
            buildingKind: building.kind,
          };
        }
      }
    }

    if (nearest) {
      return nearest;
    }

    for (const landmark of CLOISTER_LANDMARKS) {
      const distance = this.distanceToLandmarkPoint(pixelX, pixelY, landmark);
      if (distance <= nearestDistance) {
        nearestDistance = distance;
        nearest = {
          type: "landmark",
          id: landmark.id,
          name: landmark.name,
        };
      }
    }

    const lakeDistance = this.distanceToLandmarkRect(pixelX, pixelY, LAKE_OF_TEARS);
    if (lakeDistance <= nearestDistance) {
      nearestDistance = lakeDistance;
      nearest = {
        type: "landmark",
        id: LAKE_OF_TEARS.id,
        name: LAKE_OF_TEARS.name,
      };
    }

    if (nearest?.type === "landmark") {
      return nearest;
    }

    for (const building of this.buildings) {
      const left = building.x * TILE_SIZE;
      const top = building.y * TILE_SIZE;
      const right = (building.x + building.w) * TILE_SIZE;
      const bottom = (building.y + building.h) * TILE_SIZE;
      const closestX = clamp(pixelX, left, right);
      const closestY = clamp(pixelY, top, bottom);
      const distance = Math.hypot(pixelX - closestX, pixelY - closestY);
      if (distance <= nearestDistance) {
        nearestDistance = distance;
        nearest = {
          type: "building",
          id: building.id,
          name: building.name,
          buildingId: building.id,
          buildingName: building.name,
          buildingKind: building.kind,
        };
      }
    }

    return nearest;
  }

  distanceToLandmarkPoint(pixelX, pixelY, landmark) {
    const landmarkX = landmark.x * TILE_SIZE;
    const landmarkY = landmark.y * TILE_SIZE;
    return Math.hypot(pixelX - landmarkX, pixelY - landmarkY);
  }

  distanceToLandmarkRect(pixelX, pixelY, landmark) {
    const left = landmark.x1 * TILE_SIZE;
    const top = landmark.y1 * TILE_SIZE;
    const right = (landmark.x2 + 1) * TILE_SIZE;
    const bottom = (landmark.y2 + 1) * TILE_SIZE;
    const closestX = clamp(pixelX, left, right);
    const closestY = clamp(pixelY, top, bottom);
    return Math.hypot(pixelX - closestX, pixelY - closestY);
  }

  isBuildingTile(tileX, tileY) {
    return this.buildings.some((building) => (
      tileX >= building.x &&
      tileX < building.x + building.w &&
      tileY >= building.y &&
      tileY < building.y + building.h
    ));
  }

  buildingBlocksTile(building, tileX, tileY) {
    const localX = tileX - building.x;
    const localY = tileY - building.y;
    const inside = (
      localX >= 0 &&
      localX < building.w &&
      localY >= 0 &&
      localY < building.h
    );
    if (!inside) {
      return false;
    }
    if (this.isDoorTile(building, localX, localY)) {
      return false;
    }
    if (building.kind === "monastery") {
      return this.monasteryBlocksLocal(building, localX, localY);
    }
    return true;
  }

  isDoorTile(building, localX, localY) {
    return Boolean(this.entranceForBuildingLocal(building, localX, localY));
  }

  entranceForBuildingLocal(building, localX, localY) {
    const inside = (
      localX >= 0 &&
      localX < building.w &&
      localY >= 0 &&
      localY < building.h
    );
    if (!inside) {
      return null;
    }

    return [...(building.entrances || []), ...(building.doors || [])].find((entrance) => (
      localX >= entrance.x &&
      localX < entrance.x + (entrance.w || 1) &&
      localY >= entrance.y &&
      localY < entrance.y + (entrance.h || 1)
    )) || null;
  }

  monasteryCellAt(building, localX, localY) {
    const col = Math.floor(localX / building.unit);
    const row = Math.floor(localY / building.unit);
    return building.layout[row]?.[col] || "wall";
  }

  monasteryBlocksLocal(building, localX, localY) {
    if (this.isMonasteryFixtureLocal(building, localX, localY)) {
      return true;
    }
    if (this.isMonasteryWalkwayLocal(building, localX, localY)) {
      return false;
    }
    if (this.isMonasteryTowerEntranceLocal(building, localX, localY)) {
      return false;
    }
    if (this.isMonasteryAlcoveLocal(building, localX, localY)) {
      return false;
    }
    const cell = this.monasteryCellAt(building, localX, localY);
    return cell !== "open";
  }

  isMonasteryWalkwayLocal(building, localX, localY) {
    return building.walkways.some((walkway) => (
      localX >= walkway.x &&
      localX < walkway.x + walkway.w &&
      localY >= walkway.y &&
      localY < walkway.y + walkway.h
    ));
  }

  isMonasteryAlcoveLocal(building, localX, localY) {
    return building.alcoves.some((alcove) => (
      localX >= alcove.x &&
      localX < alcove.x + alcove.w &&
      localY >= alcove.y &&
      localY < alcove.y + alcove.h
    ));
  }

  isMonasteryTowerEntranceLocal(building, localX, localY) {
    return (building.towers || []).some((tower) => (
      tower.entrance &&
      localX === tower.x * building.unit + 1 &&
      localY === tower.y * building.unit + 2
    ));
  }

  isMonasteryFixtureLocal(building, localX, localY) {
    return (building.solidFixtures || []).some((fixture) => (
      localX >= fixture.x &&
      localX < fixture.x + fixture.w &&
      localY >= fixture.y &&
      localY < fixture.y + fixture.h
    ));
  }

  canWalk(rect) {
    const points = [
      { x: rect.x + rect.w / 2, y: rect.y + rect.h },
      { x: rect.x, y: rect.y + rect.h },
      { x: rect.x + rect.w, y: rect.y + rect.h },
      { x: rect.x + rect.w / 2, y: rect.y + rect.h / 2 },
    ];
    return points.every((point) => {
      const entrance = this.entranceAtPixel(point.x, point.y);
      const boardableShip = entrance?.buildingKind === "ship";
      const caveEntrance = entrance?.terrainKind === "cave";
      const checksGardenCollision = point.y >= rect.y + rect.h * 0.6;
      const terrainBlocked = this.isTerrainBlockedAtPixel(point.x, point.y);
      return (
        (!terrainBlocked || ((boardableShip || caveEntrance) && !this.hasBlockingOverrideAtPixel(point.x, point.y))) &&
        !this.buildingAtPixel(point.x, point.y) &&
        (!checksGardenCollision || (
          !this.isOrchardGardenBlockedPixel(point.x, point.y) &&
          !this.isBarleyFieldBlockedPixel(point.x, point.y) &&
          !this.isWheatFieldBlockedPixel(point.x, point.y)
        ))
      );
    });
  }

  hasBlockingOverrideAtPixel(pixelX, pixelY) {
    const tileX = Math.floor(pixelX / TILE_SIZE);
    const tileY = Math.floor(pixelY / TILE_SIZE);
    return this.blockingOverrides.has(tileX + "," + tileY);
  }

  isExplicitlyOpenAtPixel(pixelX, pixelY) {
    const tileX = Math.floor(pixelX / TILE_SIZE);
    const tileY = Math.floor(pixelY / TILE_SIZE);
    return this.blockingOverrides.get(tileX + "," + tileY) === false;
  }

  isOrchardGardenBlockedPixel(pixelX, pixelY) {
    if (this.isExplicitlyOpenAtPixel(pixelX, pixelY)) {
      return false;
    }
    const tileX = Math.floor(pixelX / TILE_SIZE);
    const tileY = Math.floor(pixelY / TILE_SIZE);
    return Boolean(orchardGardenAreaForTile(tileX, tileY)) && !isOrchardGardenPathTile(tileX, tileY);
  }

  isBarleyFieldBlockedPixel(pixelX, pixelY) {
    if (this.isExplicitlyOpenAtPixel(pixelX, pixelY)) {
      return false;
    }
    const tileX = Math.floor(pixelX / TILE_SIZE);
    const tileY = Math.floor(pixelY / TILE_SIZE);
    return Boolean(barleyFieldAreaForTile(tileX, tileY)) && !isBarleyFieldPathTile(tileX, tileY);
  }

  isWheatFieldBlockedPixel(pixelX, pixelY) {
    if (this.isExplicitlyOpenAtPixel(pixelX, pixelY)) {
      return false;
    }
    const tileX = Math.floor(pixelX / TILE_SIZE);
    const tileY = Math.floor(pixelY / TILE_SIZE);
    return Boolean(wheatFieldAreaForTile(tileX, tileY)) && !isWheatFieldPathTile(tileX, tileY);
  }

  touchesLand(tileX, tileY) {
    const offsets = [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ];
    return offsets.some(([offsetX, offsetY]) => {
      const x = tileX + offsetX;
      const y = tileY + offsetY;
      return this.inBounds(x, y) && this.tiles[y][x] !== WATER;
    });
  }

  draw(camera) {
    if (!this.cacheReady) {
      this.buildCache();
    }

    const sourceX = Math.floor(camera.x);
    const sourceY = Math.floor(camera.y);
    const sourceW = Math.min(screenWidth, this.cacheCanvas.width - sourceX);
    const sourceH = Math.min(screenHeight, this.cacheCanvas.height - sourceY);
    ctx.drawImage(
      this.cacheCanvas,
      sourceX,
      sourceY,
      sourceW,
      sourceH,
      0,
      0,
      sourceW,
      sourceH
    );
  }

  drawForeground(camera) {
    for (const building of this.buildings) {
      if (building.kind !== "monastery") {
        continue;
      }

      for (const tower of this.monasteryTowerOrigins(building)) {
        this.drawMonasteryTowerTop(tower.pixelX - camera.x, tower.pixelY - camera.y, tower.size, tower.entrance);
      }
    }
  }

  hidesPlayer(rect) {
    return this.buildings.some((building) => {
      if (building.kind !== "monastery") {
        return false;
      }

      const spriteRect = {
        x: rect.x - 11,
        y: rect.y - 18,
        w: 48,
        h: PLAYER_SPRITE_HEIGHT,
      };

      return this.monasteryTowerOrigins(building).some((tower) => {
        const occluder = {
          x: tower.pixelX + tower.size * 0.08,
          y: tower.pixelY - tower.size * 0.55,
          w: tower.size * 0.84,
          h: tower.size * 0.92,
        };
        return this.rectsOverlap(spriteRect, occluder);
      });
    });
  }

  buildCache() {
    const cacheCtx = this.cacheCanvas.getContext("2d", { alpha: false });
    const previousCtx = renderCtx;
    renderCtx = cacheCtx;
    cacheCtx.imageSmoothingEnabled = false;

    this.drawLowerLayer();
    this.drawCaveEntrances();
    this.drawBuildings();

    renderCtx = previousCtx;
    this.cacheReady = true;
  }

  drawLowerLayer() {
    for (let tileY = 0; tileY < MAP_HEIGHT; tileY += 1) {
      for (let tileX = 0; tileX < MAP_WIDTH; tileX += 1) {
        this.drawTile(tileX, tileY, tileX * TILE_SIZE, tileY * TILE_SIZE);
      }
    }
  }

  drawBuildings() {
    for (const building of this.buildings) {
      if (building.kind === "monastery") {
        this.drawMonastery(building);
        continue;
      }
      if (building.kind === "ship") {
        this.drawShip(building);
        continue;
      }

      const img = images.buildings[building.imageIndex];
      const x = building.x * TILE_SIZE;
      const y = building.y * TILE_SIZE - 16;
      const w = building.w * TILE_SIZE;
      const h = building.h * TILE_SIZE + 16;

      if (!drawMaskedAsset(img, x, y, w, h)) {
        drawMaskedFallback(x, y, w, h, drawFallbackBuilding);
      }
    }
  }

  drawMonastery(building) {
    const unitPixels = building.unit * TILE_SIZE;
    const x = building.x * TILE_SIZE;
    const y = building.y * TILE_SIZE;

    fill("#554c46");
    renderCtx.fillRect(x, y, building.w * TILE_SIZE, building.h * TILE_SIZE);
    this.drawCloisterCobblestones(x + 2 * unitPixels, y + unitPixels, 6 * unitPixels, 2 * unitPixels);
    this.drawCloisterFountains(x, y, unitPixels);

    for (let row = 0; row < building.rows; row += 1) {
      for (let col = 0; col < building.cols; col += 1) {
        const cell = building.layout[row][col];
        const cellX = x + col * unitPixels;
        const cellY = y + row * unitPixels;
        if (cell === "building") {
          this.drawMonasteryCell(cellX, cellY, unitPixels, col, row);
        } else if (cell === "wall") {
          this.drawMonasteryWall(cellX, cellY, unitPixels);
        }
      }
    }

    this.drawMonasteryContinuousBands(x, y, unitPixels);
    this.drawMonasteryWalkways(building);
    this.drawMonasteryAlcoves(building);
    this.drawMonasteryTowers(building);
    this.drawMonasterySpire(x + 8 * unitPixels + unitPixels / 2, y + unitPixels * 0.5, unitPixels * 0.82);
    this.drawMonasterySpire(x + unitPixels * 1.35, y + unitPixels * 0.55, unitPixels * 0.62);
  }

  drawShip(building) {
    const x = building.x * TILE_SIZE;
    const y = building.y * TILE_SIZE;
    const w = building.w * TILE_SIZE;
    const h = building.h * TILE_SIZE;
    const bob = Math.sin((building.x + building.y) * 1.7) * 2;
    const centerX = x + w / 2;
    const centerY = y + h / 2;

    renderCtx.save();
    renderCtx.translate(centerX, centerY);
    renderCtx.scale(0.72, 0.72);
    renderCtx.translate(-centerX, -centerY);
    fill("rgba(4, 7, 11, 0.56)");
    ellipse(x + w / 2, y + h * 0.78 + bob, w * 0.92, h * 0.3);

    fill("#241f25");
    polygon([
      [x + 12, y + h * 0.42 + bob],
      [x + w - 5, y + h * 0.57 + bob],
      [x + w - 34, y + h * 0.83 + bob],
      [x + 18, y + h * 0.78 + bob],
      [x + 6, y + h * 0.55 + bob],
    ]);
    fill("#3a2b31");
    polygon([
      [x + 25, y + h * 0.49 + bob],
      [x + w - 30, y + h * 0.57 + bob],
      [x + w - 45, y + h * 0.7 + bob],
      [x + 30, y + h * 0.68 + bob],
      [x + 18, y + h * 0.54 + bob],
    ]);
    fill("#2b2028");
    polygon([
      [x + 16, y + h * 0.34 + bob],
      [x + 48, y + h * 0.38 + bob],
      [x + 42, y + h * 0.52 + bob],
      [x + 18, y + h * 0.5 + bob],
    ]);
    stroke("#705f68", 1.5);
    line(x + 19, y + h * 0.38 + bob, x + 43, y + h * 0.41 + bob);
    fill("#151318");
    polygon([
      [x + w * 0.31, y + h * 0.63 + bob],
      [x + w * 0.62, y + h * 0.66 + bob],
      [x + w * 0.55, y + h * 0.8 + bob],
      [x + w * 0.36, y + h * 0.77 + bob],
    ]);
    stroke("#0c0a0e", 3);
    line(x + 11, y + h * 0.52 + bob, x + w - 8, y + h * 0.58 + bob);
    stroke("#67565e", 1.5);
    for (let rib = 0.16; rib <= 0.84; rib += 0.17) {
      line(x + w * rib, y + h * 0.53 + bob, x + w * (rib * 0.9 + 0.05), y + h * 0.79 + bob);
    }

    this.drawGothicShipWindow(x + w * 0.27, y + h * 0.62 + bob, 13, 23);
    this.drawGothicShipWindow(x + w * 0.5, y + h * 0.61 + bob, 15, 27);
    this.drawGothicShipWindow(x + w * 0.73, y + h * 0.62 + bob, 13, 23);

    stroke("#31242b", 5);
    line(x + w * 0.5, y + h * 0.52 + bob, x + w * 0.5, y + 10 + bob);
    stroke("#75646f", 1.5);
    line(x + w * 0.5, y + 16 + bob, x + w * 0.5, y + 5 + bob);
    stroke("#19141a", 2);
    line(x + w * 0.5, y + 18 + bob, x + w * 0.82, y + h * 0.47 + bob);
    line(x + w * 0.5, y + 18 + bob, x + w * 0.7, y + h * 0.5 + bob);

    fill("#d8d0b8");
    polygon([
      [x + w * 0.53, y + 18 + bob],
      [x + w * 0.58, y + h * 0.5 + bob],
      [x + w * 0.86, y + h * 0.46 + bob],
      [x + w * 0.73, y + h * 0.27 + bob],
    ]);
    fill("#b9b09b");
    polygon([
      [x + w * 0.56, y + 22 + bob],
      [x + w * 0.62, y + h * 0.45 + bob],
      [x + w * 0.9, y + h * 0.41 + bob],
      [x + w * 0.74, y + h * 0.29 + bob],
    ]);
    fill("#efe8cf");
    polygon([
      [x + w * 0.54, y + h * 0.13 + bob],
      [x + w * 0.57, y + h * 0.34 + bob],
      [x + w * 0.78, y + h * 0.31 + bob],
    ]);
    stroke("#7b6c5e", 1.5);
    line(x + w * 0.58, y + h * 0.23 + bob, x + w * 0.82, y + h * 0.45 + bob);
    line(x + w * 0.6, y + h * 0.26 + bob, x + w * 0.86, y + h * 0.4 + bob);
    line(x + w * 0.57, y + h * 0.34 + bob, x + w * 0.78, y + h * 0.31 + bob);
    stroke("rgba(66, 54, 50, 0.55)", 1);
    line(x + w * 0.58, y + h * 0.3 + bob, x + w * 0.8, y + h * 0.44 + bob);
    line(x + w * 0.62, y + h * 0.31 + bob, x + w * 0.84, y + h * 0.39 + bob);

    fill("#17141b");
    polygon([
      [x + w * 0.5, y + 2 + bob],
      [x + w * 0.44, y + 24 + bob],
      [x + w * 0.56, y + 24 + bob],
    ]);
    fill("#b6a56d");
    renderCtx.fillRect(x + w * 0.492, y + 4 + bob, 3, 18);
    renderCtx.fillRect(x + w * 0.472, y + 12 + bob, 11, 3);

    this.drawGothicShipSpire(x + 18, y + h * 0.43 + bob, 22);
    this.drawGothicShipSpire(x + w - 18, y + h * 0.43 + bob, 22);

    stroke("rgba(154, 186, 196, 0.48)", 2);
    line(x + 7, y + h * 0.86 + bob, x + 28, y + h * 0.88 + bob);
    line(x + w - 30, y + h * 0.88 + bob, x + w - 8, y + h * 0.86 + bob);
    renderCtx.restore();
    this.drawShipBoardingPlank(building, x, y, w, h, bob);
  }

  drawGothicShipWindow(centerX, baseY, windowW, windowH) {
    fill("#09080c");
    polygon([
      [centerX, baseY - windowH],
      [centerX - windowW / 2, baseY - windowH * 0.55],
      [centerX - windowW / 2, baseY],
      [centerX + windowW / 2, baseY],
      [centerX + windowW / 2, baseY - windowH * 0.55],
    ]);
    stroke("#8d7650", 1.5);
    line(centerX, baseY - windowH + 2, centerX, baseY - 2);
    line(centerX - windowW / 2 + 2, baseY - windowH * 0.45, centerX + windowW / 2 - 2, baseY - windowH * 0.45);
  }

  drawGothicShipSpire(centerX, baseY, height) {
    fill("#18141b");
    polygon([
      [centerX, baseY - height],
      [centerX - 8, baseY],
      [centerX + 8, baseY],
    ]);
    fill("#3d333b");
    renderCtx.fillRect(centerX - 5, baseY - 2, 10, 14);
    fill("#a8935d");
    circle(centerX, baseY - height + 3, 2.5, true);
  }

  drawShipBoardingPlank(building, x, y, w, h, bob) {
    const entrance = building.entrances[0];
    const entranceCenterX = x + (entrance.x + entrance.w / 2) * TILE_SIZE;
    const plankX = entranceCenterX - 10;
    const plankY = y + entrance.y * TILE_SIZE - 6 + bob;
    const plankW = 20;
    const plankH = TILE_SIZE + 28;
    fill("#8b6840");
    renderCtx.fillRect(plankX, plankY, plankW, plankH);
    stroke("#3d2a1b", 2);
    renderCtx.strokeRect(plankX + 0.5, plankY + 0.5, plankW - 1, plankH - 1);
    stroke("#5c4329", 1);
    for (let offset = 12; offset < plankH; offset += 12) {
      line(plankX + 3, plankY + offset, plankX + plankW - 3, plankY + offset);
    }
    fill("#f0d36b");
    circle(plankX + plankW / 2, plankY + plankH / 2, 4, true);
  }

  monasteryTowerOrigins(building) {
    const unitPixels = building.unit * TILE_SIZE;
    return (building.towers || []).map((tower) => ({
      ...tower,
      pixelX: building.x * TILE_SIZE + tower.x * unitPixels,
      pixelY: building.y * TILE_SIZE + tower.y * unitPixels,
      size: unitPixels,
    }));
  }

  drawMonasteryTowers(building) {
    for (const tower of this.monasteryTowerOrigins(building)) {
      this.drawMonasteryTower(tower.pixelX, tower.pixelY, tower.size, tower.entrance);
    }
  }

  drawCloisterCobblestones(x, y, w, h) {
    fill("#4d4a47");
    renderCtx.fillRect(x, y, w, h);
    for (let yy = y + 8; yy < y + h - 8; yy += 18) {
      const offset = Math.floor((yy - y) / 18) % 2 === 0 ? 0 : 13;
      for (let xx = x + 8 - offset; xx < x + w - 6; xx += 26) {
        const wobble = Math.sin(xx * 0.09 + yy * 0.13) * 3;
        fill(((xx + yy) % 4 === 0) ? "#5c5854" : "#423f3d");
        renderCtx.beginPath();
        renderCtx.ellipse(xx + 10, yy + 6, 12 + wobble, 7, 0.12, 0, Math.PI * 2);
        renderCtx.fill();
      }
    }
  }

  drawMonasteryContinuousBands(x, y, unitPixels) {
    fill("#211820");
    renderCtx.fillRect(x + 4, y + 8, unitPixels * 10 - 8, 24);
    renderCtx.fillRect(x + 4, y + unitPixels * 3 + 8, unitPixels * 4 - 8, 24);
    renderCtx.fillRect(x + unitPixels * 6 + 4, y + unitPixels * 3 + 8, unitPixels * 4 - 8, 24);
    renderCtx.fillRect(x + 4, y + unitPixels + 8, 24, unitPixels * 2 - 8);
    renderCtx.fillRect(x + unitPixels * 9 + unitPixels - 28, y + unitPixels + 8, 24, unitPixels * 2 - 8);

    fill("#6a5f52");
    renderCtx.fillRect(x + 10, y + 28, unitPixels * 10 - 20, 8);
    renderCtx.fillRect(x + 10, y + unitPixels * 3 + 28, unitPixels * 4 - 20, 8);
    renderCtx.fillRect(x + unitPixels * 6 + 10, y + unitPixels * 3 + 28, unitPixels * 4 - 20, 8);

    this.drawStoneRail(x + 16, y + 14, unitPixels * 10 - 32);
    this.drawStoneRail(x + 16, y + unitPixels * 3 + 14, unitPixels * 4 - 32);
    this.drawStoneRail(x + unitPixels * 6 + 16, y + unitPixels * 3 + 14, unitPixels * 4 - 32);
  }

  drawMonasteryWalkways(building) {
    for (const walkway of building.walkways) {
      this.drawCloisterCobblestones(
        (building.x + walkway.x) * TILE_SIZE,
        (building.y + walkway.y) * TILE_SIZE,
        walkway.w * TILE_SIZE,
        walkway.h * TILE_SIZE
      );
    }
  }

  drawMonasteryAlcoves(building) {
    for (const alcove of building.alcoves) {
      const x = (building.x + alcove.x) * TILE_SIZE;
      const y = (building.y + alcove.y) * TILE_SIZE;
      const w = alcove.w * TILE_SIZE;
      const h = alcove.h * TILE_SIZE;
      const inset = 6;
      const archX = x + inset;
      const archY = y + h - PLAYER_SPRITE_HEIGHT;
      const archW = w - inset * 2;
      const archH = PLAYER_SPRITE_HEIGHT - 6;

      fill("#2b2930");
      renderCtx.beginPath();
      renderCtx.moveTo(archX, archY + archH);
      renderCtx.lineTo(archX, archY + archW / 2);
      renderCtx.quadraticCurveTo(archX + archW / 2, archY - 7, archX + archW, archY + archW / 2);
      renderCtx.lineTo(archX + archW, archY + archH);
      renderCtx.closePath();
      renderCtx.fill();

      fill("#111014");
      renderCtx.beginPath();
      renderCtx.moveTo(archX + 5, archY + archH - 3);
      renderCtx.lineTo(archX + 5, archY + archW / 2 + 2);
      renderCtx.quadraticCurveTo(archX + archW / 2, archY + 2, archX + archW - 5, archY + archW / 2 + 2);
      renderCtx.lineTo(archX + archW - 5, archY + archH - 3);
      renderCtx.closePath();
      renderCtx.fill();

    }
  }

  drawMonasteryCell(x, y, size, col, row) {
    const roofColor = row === 0 || row === 3 || col === 0 || col === 9 ? "#211820" : "#342c34";
    fill("#3c3840");
    renderCtx.fillRect(x + 5, y + 18, size - 10, size - 24);
    fill("#2b2930");
    renderCtx.fillRect(x + 11, y + 31, size - 22, size - 39);
    fill(roofColor);
    polygon([
      [x + 2, y + 22],
      [x + size / 2, y - 14],
      [x + size - 2, y + 22],
    ]);
    fill("#5f564f");
    renderCtx.fillRect(x + 9, y + 22, size - 18, 12);
    stroke("rgba(205, 190, 150, 0.22)", 1);
    for (let i = 1; i < 4; i += 1) {
      line(x + i * size / 4, y + 37, x + i * size / 4, y + size - 11);
    }

    this.drawMonasteryArchedWindow(x + size * 0.28, y + size * 0.52, 14, 28);
    this.drawMonasteryArchedWindow(x + size * 0.62, y + size * 0.52, 14, 28);
    if ((col + row) % 2 === 0) {
      this.drawMonasteryFinial(x + size / 2, y - 24, 22);
    }
    if (row === 0 || row === 3) {
      this.drawStoneRail(x + 8, y + 18, size - 16);
    }
  }

  drawMonasteryWall(x, y, size) {
    fill("#3b3740");
    renderCtx.fillRect(x + 5, y + 26, size - 10, size - 33);
    fill("#211820");
    renderCtx.fillRect(x + 4, y + 18, size - 8, 12);
    this.drawStoneRail(x + 9, y + 12, size - 18);
    stroke("rgba(198, 185, 150, 0.22)", 2);
    for (let i = 1; i < 3; i += 1) {
      line(x + i * size / 3, y + 32, x + i * size / 3, y + size - 14);
    }
  }

  drawCloisterFountains(originX, originY, unitPixels) {
    const fountains = [
      { x: 3.1, y: 1.45, r: 18 },
      { x: 5.0, y: 2.0, r: 24, kind: "well" },
      { x: 6.9, y: 1.45, r: 18 },
    ];

    for (const fountain of fountains) {
      const x = originX + fountain.x * unitPixels;
      const y = originY + fountain.y * unitPixels;
      if (fountain.kind === "well") {
        this.drawCloisterWell(x, y, fountain.r);
        continue;
      }
      this.drawCloisterFountain(x, y, fountain.r);
    }
  }

  drawCloisterFountain(x, y, radius) {
    const basinW = radius * 2.55;
    const basinH = radius * 0.78;
    const lipY = y - radius * 0.18;

    fill("rgba(24, 24, 26, 0.32)");
    ellipse(x, y + radius * 0.72, basinW * 1.08, radius * 0.46);
    fill("#3a3637");
    renderCtx.fillRect(x - basinW / 2, lipY, basinW, basinH);
    fill("#252329");
    ellipse(x, lipY + basinH, basinW, radius * 0.42);
    fill("#5c554b");
    ellipse(x, lipY, basinW, radius * 0.48);
    fill("#617f8d");
    ellipse(x, lipY - 2, basinW * 0.72, radius * 0.28);

    fill("#4d4741");
    renderCtx.fillRect(x - radius * 0.23, y - radius * 1.12, radius * 0.46, radius * 0.94);
    fill("#70664e");
    ellipse(x, y - radius * 1.12, radius * 0.72, radius * 0.28);
    fill("#9c8b63");
    circle(x, y - radius * 1.32, radius * 0.18, true);

    stroke("rgba(174, 210, 216, 0.76)", 2);
    line(x, y - radius * 1.26, x, lipY - 4);
    stroke("rgba(174, 210, 216, 0.5)", 1.5);
    line(x, y - radius * 1.12, x - radius * 0.34, lipY - 2);
    line(x, y - radius * 1.12, x + radius * 0.34, lipY - 2);
  }

  drawCloisterWell(x, y, radius) {
    const wellW = radius * 2.22;
    const wellH = radius * 1.15;
    const baseY = y + radius * 0.34;
    const rimY = y - radius * 0.22;

    fill("rgba(24, 24, 26, 0.34)");
    ellipse(x, baseY + radius * 0.36, wellW * 1.02, radius * 0.42);
    fill("#3a3637");
    renderCtx.fillRect(x - wellW / 2, rimY, wellW, wellH);
    fill("#252329");
    ellipse(x, rimY + wellH, wellW, radius * 0.48);
    fill("#665f52");
    ellipse(x, rimY, wellW, radius * 0.54);
    fill("#111014");
    ellipse(x, rimY - 2, wellW * 0.66, radius * 0.28);

    stroke("#6a5f52", 5);
    line(x - radius * 0.82, rimY + radius * 0.04, x - radius * 0.82, y - radius * 1.8);
    line(x + radius * 0.82, rimY + radius * 0.04, x + radius * 0.82, y - radius * 1.8);
    fill("#211820");
    polygon([
      [x - radius * 1.05, y - radius * 1.76],
      [x, y - radius * 2.42],
      [x + radius * 1.05, y - radius * 1.76],
    ]);
    fill("#3d3941");
    renderCtx.fillRect(x - radius * 0.86, y - radius * 1.76, radius * 1.72, radius * 0.2);
    stroke("#9c8b63", 3);
    line(x - radius * 0.62, y - radius * 1.42, x + radius * 0.62, y - radius * 1.42);
    stroke("#8a8062", 2);
    line(x, y - radius * 1.42, x, y - radius * 0.58);
    fill("#2b2524");
    renderCtx.fillRect(x - radius * 0.18, y - radius * 0.66, radius * 0.36, radius * 0.34);
  }

  drawMonasteryArchedWindow(x, y, w, h) {
    fill("#111820");
    renderCtx.beginPath();
    renderCtx.moveTo(x, y + h);
    renderCtx.lineTo(x, y + w / 2);
    renderCtx.quadraticCurveTo(x + w / 2, y - 6, x + w, y + w / 2);
    renderCtx.lineTo(x + w, y + h);
    renderCtx.closePath();
    renderCtx.fill();
    stroke("#9c8b63", 2);
    renderCtx.stroke();
    stroke("rgba(205, 190, 150, 0.62)", 1);
    line(x + w / 2, y + 3, x + w / 2, y + h - 2);
    line(x + 3, y + h / 2, x + w - 3, y + h / 2);
  }

  drawStoneRail(x, y, width) {
    fill("#8f815e");
    renderCtx.fillRect(x, y, width, 4);
    for (let i = 0; i <= width; i += 14) {
      renderCtx.fillRect(x + i, y - 8, 4, 12);
    }
  }

  drawMonasteryFinial(x, y, h) {
    fill("#a79770");
    polygon([[x, y], [x - 5, y + h], [x + 5, y + h]]);
    fill("#6f654e");
    circle(x, y - 3, 4, true);
  }

  drawMonasterySpire(x, y, size) {
    fill("#3d3941");
    renderCtx.fillRect(x - size * 0.18, y + size * 0.42, size * 0.36, size * 0.72);
    fill("#211820");
    polygon([
      [x - size * 0.28, y + size * 0.42],
      [x, y - size * 0.25],
      [x + size * 0.28, y + size * 0.42],
    ]);
    this.drawMonasteryArchedWindow(x - size * 0.08, y + size * 0.66, size * 0.16, size * 0.3);
    this.drawMonasteryFinial(x, y - size * 0.35, size * 0.22);
  }

  drawMonasteryTower(x, y, size, entrance = false) {
    fill("#423e45");
    renderCtx.fillRect(x + size * 0.08, y - size * 0.55, size * 0.84, size * 1.35);
    fill("#2a232b");
    renderCtx.beginPath();
    renderCtx.ellipse(x + size / 2, y - size * 0.52, size * 0.42, size * 0.34, 0, Math.PI, Math.PI * 2);
    renderCtx.lineTo(x + size * 0.92, y - size * 0.45);
    renderCtx.lineTo(x + size * 0.08, y - size * 0.45);
    renderCtx.closePath();
    renderCtx.fill();
    this.drawMonasteryArchedWindow(x + size * 0.38, y - size * 0.08, size * 0.24, size * 0.46);
    if (entrance) {
      this.drawMonasteryTowerEntrance(x, y, size);
    }
    this.drawStoneRail(x + size * 0.16, y + size * 0.2, size * 0.68);
    this.drawMonasteryFinial(x + size / 2, y - size * 0.98, size * 0.24);
  }

  drawMonasteryTowerEntrance(x, y, size) {
    const archW = size * 0.28;
    const archH = size * 0.44;
    const archX = x + size * 0.5 - archW / 2;
    const archY = y + size * 0.42;

    fill("#2b2930");
    renderCtx.beginPath();
    renderCtx.moveTo(archX, archY + archH);
    renderCtx.lineTo(archX, archY + archW / 2);
    renderCtx.quadraticCurveTo(archX + archW / 2, archY - 7, archX + archW, archY + archW / 2);
    renderCtx.lineTo(archX + archW, archY + archH);
    renderCtx.closePath();
    renderCtx.fill();

    fill("#111014");
    renderCtx.beginPath();
    renderCtx.moveTo(archX + 5, archY + archH);
    renderCtx.lineTo(archX + 5, archY + archW / 2 + 3);
    renderCtx.quadraticCurveTo(archX + archW / 2, archY + 3, archX + archW - 5, archY + archW / 2 + 3);
    renderCtx.lineTo(archX + archW - 5, archY + archH);
    renderCtx.closePath();
    renderCtx.fill();
  }

  drawMonasteryTowerTop(x, y, size, entrance = false) {
    renderCtx.save();
    renderCtx.beginPath();
    renderCtx.rect(x - 8, y - size, size + 16, size * 1.28);
    renderCtx.clip();
    this.drawMonasteryTower(x, y, size, entrance);
    renderCtx.restore();
  }

  drawTile(tileX, tileY, x, y) {
    const tile = this.tiles[tileY][tileX];
    if (!drawAsset(images.tiles[tile], x, y, TILE_SIZE, TILE_SIZE)) {
      renderCtx.fillStyle = tileColor(tile, tileX, tileY);
      renderCtx.fillRect(x, y, TILE_SIZE, TILE_SIZE);
    }
    this.drawTileDetail(x, y, tile, tileX, tileY);
  }

  drawTileDetail(x, y, tile, tileX, tileY) {
    if (tile === WATER) {
      if ((tileX + tileY) % 4 === 0) {
        stroke("#3b6580", 2);
        line(x + 8, y + TILE_SIZE / 2 - 4, x + TILE_SIZE - 8, y + TILE_SIZE / 2 - 2);
      }
      if (this.touchesLand(tileX, tileY)) {
        stroke("rgba(150, 173, 166, 0.6)", 2);
        circle(x + TILE_SIZE / 2, y + TILE_SIZE / 2, TILE_SIZE / 3, false);
      }
    } else if (tile === SAND) {
      fill("#7d8385");
      circle(x + 14, y + 18, 3, true);
      fill("#9da3a4");
      circle(x + TILE_SIZE - 12, y + TILE_SIZE - 13, 2, true);
    } else if (tile === BEACH) {
      fill("#948761");
      circle(x + 11, y + 15, 2.5, true);
      fill("#5e5742");
      circle(x + TILE_SIZE - 14, y + TILE_SIZE - 12, 1.8, true);
      stroke("rgba(95, 88, 66, 0.56)", 1.5);
      line(x + 5, y + 38, x + 21, y + 34);
      line(x + 27, y + 18, x + 43, y + 14);
    } else if (tile === GRASS) {
      drawGrass(x, y, tileX, tileY);
      this.drawOrchardGardenDetail(x, y, tileX, tileY);
      this.drawBarleyFieldDetail(x, y, tileX, tileY);
      this.drawWheatFieldDetail(x, y, tileX, tileY);
    } else if (tile === FOREST) {
      const tree = images.trees[Math.abs(tileX * 17 + tileY * 11) % images.trees.length];
      if (!drawAsset(tree, x, y - 16, TILE_SIZE, TILE_SIZE + 16)) {
        drawTree(x, y, tileX, tileY);
      }
    } else if (tile === ROCK) {
      const rock = images.rocks[Math.abs(tileX * 13 + tileY * 7) % images.rocks.length];
      if (!drawAsset(rock, x, y - 8, TILE_SIZE, TILE_SIZE + 8)) {
        fill("#45424e");
        ellipse(x + TILE_SIZE / 2, y + TILE_SIZE / 2 + 8, TILE_SIZE - 12, TILE_SIZE - 24);
        fill("#605c69");
        polygon([
          [x + 8, y + TILE_SIZE - 11],
          [x + TILE_SIZE / 2 - 2, y + 7],
          [x + TILE_SIZE - 8, y + TILE_SIZE - 13],
        ]);
      }
    } else if (tile === TALL_ROCK) {
      this.drawTallRockCliff(x, y, tileX, tileY);
    }
  }

  drawTallRockCliff(x, y, tileX, tileY) {
    const ridge = (tileX * 5 + tileY * 7) % 8;
    fill("rgba(7, 8, 12, 0.42)");
    ellipse(x + TILE_SIZE / 2, y + TILE_SIZE - 4, TILE_SIZE - 8, 10);
    fill("#24262e");
    renderCtx.fillRect(x + 3, y + 12, TILE_SIZE - 6, TILE_SIZE - 12);
    fill("#3a3b45");
    polygon([
      [x + 3, y + 14],
      [x + 14 + ridge, y - 10],
      [x + 25, y + 5],
      [x + 17, y + TILE_SIZE],
      [x + 3, y + TILE_SIZE],
    ]);
    fill("#51505d");
    polygon([
      [x + 18, y + 5],
      [x + 33 - ridge * 0.5, y - 16],
      [x + 45, y + 13],
      [x + 39, y + TILE_SIZE],
      [x + 18, y + TILE_SIZE],
    ]);
    fill("#1a1b22");
    polygon([
      [x + 28, y + 7],
      [x + 45, y + 13],
      [x + 39, y + TILE_SIZE],
      [x + 30, y + TILE_SIZE],
    ]);
    stroke("#74717f", 2);
    line(x + 17, y + 6, x + 10, y + 38);
    line(x + 32, y + 0, x + 38, y + 42);
    stroke("#111217", 3);
    line(x + 4, y + TILE_SIZE - 4, x + TILE_SIZE - 4, y + TILE_SIZE - 6);
  }

  drawCaveEntrances() {
    for (const entrance of CAVE_ENTRANCES) {
      const bounds = caveEntranceBounds(entrance);
      this.drawCaveEntranceMouth(
        bounds.x * TILE_SIZE,
        bounds.y * TILE_SIZE,
        bounds.w * TILE_SIZE,
        bounds.h * TILE_SIZE
      );
    }
  }

  drawCaveEntranceMouth(x, y, w, h) {
    const baseY = y + h;
    const crownY = y + h * 0.08;
    const shoulderY = y + h * 0.42;
    const leftX = x + w * 0.08;
    const rightX = x + w * 0.92;
    const centerX = x + w / 2;
    fill("#22232a");
    polygon([
      [centerX, crownY],
      [rightX + w * 0.08, y + h * 0.28],
      [rightX + w * 0.04, baseY],
      [leftX - w * 0.04, baseY],
      [leftX - w * 0.08, y + h * 0.32],
    ]);
    fill("#111217");
    polygon([
      [centerX - w * 0.38, y + h * 0.18],
      [centerX - w * 0.12, crownY + 4],
      [centerX + w * 0.16, crownY],
      [centerX + w * 0.42, y + h * 0.24],
      [rightX, baseY],
      [leftX, baseY],
    ]);
    fill("#05060a");
    renderCtx.beginPath();
    renderCtx.moveTo(centerX - w * 0.28, baseY);
    renderCtx.lineTo(centerX - w * 0.32, shoulderY);
    renderCtx.quadraticCurveTo(centerX - w * 0.22, crownY + h * 0.08, centerX - w * 0.05, y + h * 0.18);
    renderCtx.quadraticCurveTo(centerX + w * 0.2, y + h * 0.12, centerX + w * 0.34, shoulderY);
    renderCtx.lineTo(centerX + w * 0.3, baseY);
    renderCtx.closePath();
    renderCtx.fill();
    stroke("#0c0d11", 3);
    line(leftX, baseY - 4, rightX, baseY - 7);
    stroke("#35343d", 2);
    line(leftX + w * 0.08, y + h * 0.36, centerX - w * 0.1, y + h * 0.2);
    line(rightX - w * 0.08, y + h * 0.32, centerX + w * 0.12, y + h * 0.16);
    fill("#090a0e");
    polygon([
      [centerX - w * 0.12, y + h * 0.18],
      [centerX - w * 0.02, y + h * 0.31],
      [centerX + w * 0.07, y + h * 0.18],
    ]);
    polygon([
      [centerX + w * 0.14, y + h * 0.19],
      [centerX + w * 0.2, y + h * 0.3],
      [centerX + w * 0.27, y + h * 0.2],
    ]);
  }

  drawOrchardGardenDetail(x, y, tileX, tileY) {
    const zone = DESIGN_ZONES.orchardGarden;
    if (tileX < zone.x1 || tileX > zone.x2 || tileY < zone.y1 || tileY > zone.y2) {
      return;
    }

    const localX = tileX - zone.x1;
    const localY = tileY - zone.y1;
    fill("rgba(18, 31, 22, 0.35)");
    renderCtx.fillRect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4);

    if (tileX <= zone.splitX) {
      this.drawFruitOrchardTile(x, y, localX, localY);
      return;
    }
    this.drawVegetableGardenTile(x, y, localX, localY);
  }

  drawFruitOrchardTile(x, y, localX, localY) {
    const trunkX = x + 23 + ((localX * 7 + localY * 3) % 7) - 3;
    const trunkY = y + 28 + ((localX * 5 + localY * 11) % 5) - 2;
    fill("rgba(6, 8, 7, 0.28)");
    ellipse(trunkX, trunkY + 10, 30, 10);
    fill("#4a3425");
    renderCtx.fillRect(trunkX - 3, trunkY - 3, 6, 18);
    fill("#294c32");
    circle(trunkX - 8, trunkY - 10, 14, true);
    fill("#35633d");
    circle(trunkX + 7, trunkY - 12, 13, true);
    fill("#3f7147");
    circle(trunkX, trunkY - 20, 12, true);

    const fruitColors = ["#c7443e", "#d6b64b", "#b2466d"];
    const fruitColor = fruitColors[(localX + localY) % fruitColors.length];
    fill(fruitColor);
    circle(trunkX - 9, trunkY - 12, 3, true);
    circle(trunkX + 8, trunkY - 16, 3, true);
    if ((localX + localY) % 2 === 0) {
      circle(trunkX + 1, trunkY - 23, 2.5, true);
    }
  }

  drawVegetableGardenTile(x, y, localX, localY) {
    fill("#3d3325");
    for (let row = 0; row < 3; row += 1) {
      const rowY = y + 11 + row * 12;
      renderCtx.fillRect(x + 5, rowY, TILE_SIZE - 10, 5);
      stroke("#5f4a31", 1);
      line(x + 6, rowY + 5, x + TILE_SIZE - 6, rowY + 5);
    }

    const cropColors = ["#71a64b", "#8a3f62", "#c77a3a"];
    const cropColor = cropColors[(localX * 2 + localY) % cropColors.length];
    fill(cropColor);
    for (let row = 0; row < 3; row += 1) {
      for (let col = 0; col < 3; col += 1) {
        const plantX = x + 11 + col * 13 + ((localY + col) % 3);
        const plantY = y + 9 + row * 12 + ((localX + row) % 2);
        circle(plantX, plantY, 3, true);
        stroke("#89bd61", 1.5);
        line(plantX, plantY + 1, plantX - 4, plantY - 5);
        line(plantX, plantY + 1, plantX + 4, plantY - 5);
      }
    }
  }

  drawBarleyFieldDetail(x, y, tileX, tileY) {
    const zone = DESIGN_ZONES.barleyField;
    if (tileX < zone.x1 || tileX > zone.x2 || tileY < zone.y1 || tileY > zone.y2 || isBarleyFieldPathTile(tileX, tileY)) {
      return;
    }

    fill("rgba(74, 58, 24, 0.28)");
    renderCtx.fillRect(x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6);
    stroke("#b59b52", 2);
    for (let col = 0; col < 4; col += 1) {
      const stalkX = x + 10 + col * 9 + ((tileX + tileY + col) % 3);
      line(stalkX, y + 38, stalkX + 3, y + 13);
      stroke("#d0b96a", 1.5);
      line(stalkX + 3, y + 18, stalkX - 3, y + 14);
      line(stalkX + 2, y + 23, stalkX + 8, y + 19);
      stroke("#b59b52", 2);
    }
  }

  drawWheatFieldDetail(x, y, tileX, tileY) {
    const zone = DESIGN_ZONES.wheatField;
    if (tileX < zone.x1 || tileX > zone.x2 || tileY < zone.y1 || tileY > zone.y2 || isWheatFieldPathTile(tileX, tileY)) {
      return;
    }

    fill("rgba(78, 82, 83, 0.34)");
    renderCtx.fillRect(x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6);
    stroke("#9fa6a4", 2);
    for (let col = 0; col < 4; col += 1) {
      const stalkX = x + 9 + col * 9 + ((tileX * 2 + tileY + col) % 4);
      line(stalkX, y + 39, stalkX + 2, y + 12);
      stroke("#c4cbc9", 1.5);
      line(stalkX + 2, y + 17, stalkX - 4, y + 13);
      line(stalkX + 2, y + 21, stalkX + 8, y + 16);
      line(stalkX + 1, y + 25, stalkX - 4, y + 21);
      stroke("#9fa6a4", 2);
    }
  }
}

function drawFallbackBuilding(x, y, w, h) {
  fill("#2f2c34");
  renderCtx.fillRect(x + 12, y + 58, w - 24, h - 64);
  fill("#17131b");
  polygon([
    [x + 4, y + 62],
    [x + w / 2, y + 10],
    [x + w - 4, y + 62],
  ]);
  fill("#b0874d");
  renderCtx.fillRect(x + 34, y + 84, 16, 22);
  renderCtx.fillRect(x + w - 50, y + 84, 16, 22);
}

class ShipRoom {
  constructor() {
    this.id = SHIP_ROOM.id;
    this.name = SHIP_ROOM.name;
    this.width = SHIP_ROOM.width;
    this.height = SHIP_ROOM.height;
    this.pixelWidth = this.width * TILE_SIZE;
    this.pixelHeight = this.height * TILE_SIZE;
    this.entranceTile = SHIP_ROOM.entranceTile;
    this.blockedTiles = new Set([
      "1,1", "2,1", "9,1", "10,1",
      "1,5", "2,5", "8,5", "9,5",
      "4,2", "7,2",
      "5,3", "6,3",
    ]);
  }

  spawnAtEntrance(player) {
    player.rect.x = this.entranceTile.x * TILE_SIZE + 13;
    player.rect.y = this.entranceTile.y * TILE_SIZE + 8;
    player.facing = { x: 0, y: -1 };
    player.stepTimer = 0;
    player.walking = false;
  }

  inBounds(tileX, tileY) {
    return tileX >= 0 && tileX < this.width && tileY >= 0 && tileY < this.height;
  }

  isTileBlocked(tileX, tileY) {
    if (!this.inBounds(tileX, tileY)) {
      return true;
    }
    if (tileY === this.height - 1 && (tileX === this.entranceTile.x || tileX === this.entranceTile.x + 1)) {
      return false;
    }
    return tileX === 0 ||
      tileY === 0 ||
      tileX === this.width - 1 ||
      tileY === this.height - 1 ||
      this.blockedTiles.has(tileX + "," + tileY);
  }

  canWalk(rect) {
    const points = [
      { x: rect.x + rect.w / 2, y: rect.y + rect.h },
      { x: rect.x, y: rect.y + rect.h },
      { x: rect.x + rect.w, y: rect.y + rect.h },
      { x: rect.x + rect.w / 2, y: rect.y + rect.h / 2 },
    ];
    return points.every((point) => !this.isTileBlocked(
      Math.floor(point.x / TILE_SIZE),
      Math.floor(point.y / TILE_SIZE)
    ));
  }

  draw(camera) {
    const x = -camera.x;
    const y = -camera.y;
    fill("#10141b");
    renderCtx.fillRect(x, y, this.pixelWidth, this.pixelHeight);
    this.drawPlanks(x, y);
    this.drawHull(x, y);
    this.drawGangway(x, y);
    this.drawFixtures(x, y);
  }

  drawPlanks(x, y) {
    for (let tileY = 1; tileY < this.height - 1; tileY += 1) {
      for (let tileX = 1; tileX < this.width - 1; tileX += 1) {
        const px = x + tileX * TILE_SIZE;
        const py = y + tileY * TILE_SIZE;
        fill((tileX + tileY) % 2 === 0 ? "#4b3427" : "#563b2b");
        renderCtx.fillRect(px, py, TILE_SIZE, TILE_SIZE);
        stroke("rgba(28, 18, 14, 0.72)", 1);
        line(px, py + TILE_SIZE - 1, px + TILE_SIZE, py + TILE_SIZE - 1);
        line(px + 8, py, px + 8, py + TILE_SIZE);
      }
    }
  }

  drawHull(x, y) {
    fill("#241922");
    renderCtx.fillRect(x, y, this.pixelWidth, TILE_SIZE);
    renderCtx.fillRect(x, y, TILE_SIZE, this.pixelHeight);
    renderCtx.fillRect(x + (this.width - 1) * TILE_SIZE, y, TILE_SIZE, this.pixelHeight);
    renderCtx.fillRect(x, y + (this.height - 1) * TILE_SIZE, this.pixelWidth, TILE_SIZE);
    fill("#342530");
    renderCtx.fillRect(x + TILE_SIZE, y + 8, this.pixelWidth - TILE_SIZE * 2, 16);
    stroke("#7d6a57", 2);
    line(x + TILE_SIZE, y + TILE_SIZE - 7, x + this.pixelWidth - TILE_SIZE, y + TILE_SIZE - 7);
    line(x + TILE_SIZE + 4, y + this.pixelHeight - TILE_SIZE + 7, x + this.pixelWidth - TILE_SIZE - 4, y + this.pixelHeight - TILE_SIZE + 7);
  }

  drawGangway(x, y) {
    const entranceX = x + this.entranceTile.x * TILE_SIZE;
    const entranceY = y + (this.height - 1) * TILE_SIZE;
    fill("#8b6840");
    renderCtx.fillRect(entranceX, entranceY, TILE_SIZE * 2, TILE_SIZE);
    stroke("#3d2a1b", 2);
    renderCtx.strokeRect(entranceX + 0.5, entranceY + 0.5, TILE_SIZE * 2 - 1, TILE_SIZE - 1);
    stroke("#5c4329", 1);
    for (let offset = 10; offset < TILE_SIZE * 2; offset += 16) {
      line(entranceX + offset, entranceY + 4, entranceX + offset, entranceY + TILE_SIZE - 4);
    }
  }

  drawFixtures(x, y) {
    this.drawCrate(x + TILE_SIZE, y + TILE_SIZE, TILE_SIZE * 2, TILE_SIZE);
    this.drawCrate(x + TILE_SIZE, y + TILE_SIZE * 5, TILE_SIZE * 2, TILE_SIZE);
    this.drawCrate(x + TILE_SIZE * 8, y + TILE_SIZE * 5, TILE_SIZE * 2, TILE_SIZE);
    this.drawCrate(x + TILE_SIZE * 9, y + TILE_SIZE, TILE_SIZE * 2, TILE_SIZE);
    fill("#2c2024");
    renderCtx.fillRect(x + TILE_SIZE * 5, y + TILE_SIZE * 3, TILE_SIZE * 2, TILE_SIZE);
    stroke("#8d7650", 2);
    renderCtx.strokeRect(x + TILE_SIZE * 5 + 4, y + TILE_SIZE * 3 + 4, TILE_SIZE * 2 - 8, TILE_SIZE - 8);
    fill("#d8d0b8");
    ellipse(x + TILE_SIZE * 6, y + TILE_SIZE * 3 + 24, 34, 14);
    fill("#16131a");
    renderCtx.fillRect(x + TILE_SIZE * 4, y + TILE_SIZE * 2, TILE_SIZE, TILE_SIZE);
    renderCtx.fillRect(x + TILE_SIZE * 7, y + TILE_SIZE * 2, TILE_SIZE, TILE_SIZE);
    stroke("#6f5b4a", 2);
    circle(x + TILE_SIZE * 4.5, y + TILE_SIZE * 2.5, 12, false);
    circle(x + TILE_SIZE * 7.5, y + TILE_SIZE * 2.5, 12, false);
  }

  drawCrate(x, y, w, h) {
    fill("#5e412b");
    renderCtx.fillRect(x + 3, y + 5, w - 6, h - 10);
    stroke("#2f2016", 2);
    renderCtx.strokeRect(x + 3.5, y + 5.5, w - 7, h - 11);
    stroke("#8b6840", 2);
    line(x + 8, y + 10, x + w - 8, y + h - 10);
    line(x + w - 8, y + 10, x + 8, y + h - 10);
  }

  drawForeground() {}

  hidesPlayer() {
    return false;
  }

  locationNearPixel() {
    return {
      type: "room",
      id: this.id,
      name: this.name,
    };
  }
}

class Player {
  constructor(world) {
    this.rect = {
      x: 0,
      y: 0,
      w: 26,
      h: 34,
    };
    this.speed = 225;
    this.facing = { x: 0, y: 1 };
    this.stepTimer = 0;
    this.walking = false;
    this.resetToStart(world);
  }

  resetToStart(world) {
    let spawnX = START_TILE.x;
    let spawnY = START_TILE.y;
    if (world.isTileBlocked(spawnX, spawnY) || world.isBuildingTile(spawnX, spawnY)) {
      spawnX = world.landPositions[0].x;
      spawnY = world.landPositions[0].y;
    }
    this.rect.x = spawnX * TILE_SIZE + 13;
    this.rect.y = spawnY * TILE_SIZE + 8;
    this.facing = { x: 0, y: 1 };
    this.stepTimer = 0;
    this.walking = false;
  }

  update(dt, world) {
    let dx = 0;
    let dy = 0;
    if (keys.has("arrowleft") || keys.has("a") || pad.left) dx -= 1;
    if (keys.has("arrowright") || keys.has("d") || pad.right) dx += 1;
    if (keys.has("arrowup") || keys.has("w") || pad.up) dy -= 1;
    if (keys.has("arrowdown") || keys.has("s") || pad.down) dy += 1;

    const length = Math.hypot(dx, dy);
    this.walking = length > 0;
    if (length > 0) {
      dx /= length;
      dy /= length;
      this.facing = { x: dx, y: dy };
      this.stepTimer += dt * 10;
    } else {
      this.stepTimer = 0;
    }

    this.moveAxis(dx * this.speed * dt, 0, world);
    this.moveAxis(0, dy * this.speed * dt, world);
  }

  moveAxis(dx, dy, world) {
    this.rect.x += Math.round(dx);
    this.rect.y += Math.round(dy);
    if (!world.canWalk(this.rect)) {
      this.rect.x -= Math.round(dx);
      this.rect.y -= Math.round(dy);
    }
  }

  draw(camera) {
    const x = this.rect.x - camera.x;
    const y = this.rect.y - camera.y;
    const stride = this.walking ? Math.sin(this.stepTimer) : 0;
    const counterStride = this.walking ? Math.cos(this.stepTimer) : 0;
    const bob = this.walking ? Math.abs(stride) * -3 : 0;
    const sway = this.walking ? counterStride * 1.4 : 0;
    const headX = x + this.rect.w / 2;
    const headY = y + bob + 11;
    const spriteX = x - 11 + sway;
    const spriteY = y + bob - 38;

    if (this.drawSprite(spriteX, spriteY, stride)) {
      this.drawLegStep(spriteX, spriteY, stride);
      this.drawEarSway(spriteX, spriteY, stride);
      return;
    }

    fill("#1d292d");
    ellipse(x + this.rect.w / 2, y + this.rect.h + 4, this.rect.w + 10, 10);
    roundRect(x, y + bob + 12, this.rect.w, this.rect.h - 10, 7, "#161720");
    roundRect(x + 4, y + bob + 13.5, this.rect.w - 8, this.rect.h - 13, 4, "#313044");
    stroke("#0b0c10", 2.5);
    line(headX - 7, y + bob + 35, headX - 8, y + bob + 48);
    line(headX + 7, y + bob + 35, headX + 8, y + bob + 48);
    fill("#08090d");
    ellipse(headX - 9, y + bob + 50, 10, 4);
    ellipse(headX + 9, y + bob + 50, 10, 4);
    stroke("rgba(243, 240, 232, 0.8)", 0.8);
    line(headX - 12, y + bob + 49, headX - 6, y + bob + 49);
    line(headX + 6, y + bob + 49, headX + 12, y + bob + 49);
    fill("#05070b");
    polygon([[headX - 9, headY - 12], [headX - 17, headY - 28], [headX - 2, headY - 18]]);
    polygon([[headX + 9, headY - 12], [headX + 17, headY - 28], [headX + 2, headY - 18]]);
    fill("#111923");
    ellipse(headX, headY + 10, 34, 38);
    fill("#f2efe7");
    ellipse(headX, headY - 3, 25, 21);
    fill("#d8ccd1");
    ellipse(headX, headY + 1, 20, 18);
    fill("#eef0f5");
    renderCtx.fillRect(headX - 9, headY - 9, 18, 7);
    stroke("#b9bdc9", 1);
    line(headX - 5, headY - 8, headX - 6, headY + 5);
    line(headX, headY - 8, headX, headY + 6);
    line(headX + 5, headY - 8, headX + 4, headY + 5);
    fill("#1c6ab9");
    circle(headX - 4, headY + 1, 2, true);
    circle(headX + 5, headY + 1, 2, true);
    stroke("#8b001b", 1.3);
    line(headX - 8, headY, headX - 3, headY - 1);
    line(headX + 3, headY - 1, headX + 9, headY);
    stroke("#65bca9", 1.2);
    line(headX - 2, headY + 8, headX + 3, headY + 8);
  }

  drawSprite(x, y, stride) {
    const img = images.player;
    if (!img || !img.complete || img.naturalWidth <= 0) {
      return false;
    }

    renderCtx.save();
    renderCtx.translate(x + 24, y + 52);
    renderCtx.rotate(stride * 0.035);
    renderCtx.scale(1 + Math.abs(stride) * 0.025, 1 - Math.abs(stride) * 0.025);
    renderCtx.drawImage(img, -24, -52, 48, 84);
    renderCtx.restore();
    return true;
  }

  drawLegStep(x, y, stride) {
    if (!this.walking) {
      return;
    }

    const step = stride * 1.8;
    renderCtx.save();
    renderCtx.translate(x, y);
    stroke("#0b0c10", 2.5);
    renderCtx.lineCap = "round";
    line(18 + step, 60, 17 + step, 71);
    line(30 - step, 60, 31 - step, 71);
    fill("#08090d");
    ellipse(18 + step, 71, 10, 4);
    ellipse(30 - step, 71, 10, 4);
    stroke("rgba(243, 240, 232, 0.78)", 0.75);
    line(15 + step, 70, 22 + step, 70);
    line(26 - step, 70, 33 - step, 70);
    renderCtx.restore();
  }

  drawEarSway(x, y, stride) {
    if (!this.walking) {
      return;
    }

    const swing = stride * 1.8;
    renderCtx.save();
    renderCtx.translate(x + 24, y + 32);
    renderCtx.rotate(stride * 0.035);
    renderCtx.translate(-24, -32);

    fill("rgba(5, 7, 11, 0.92)");
    polygon([
      [13 + swing, 14],
      [7 + swing * 0.35, 1],
      [20 + swing, 10],
    ]);
    polygon([
      [35 - swing, 14],
      [41 - swing * 0.35, 1],
      [28 - swing, 10],
    ]);

    fill("rgba(86, 96, 111, 0.74)");
    polygon([
      [14 + swing, 11],
      [10 + swing * 0.35, 4],
      [19 + swing, 10],
    ]);
    polygon([
      [34 - swing, 11],
      [38 - swing * 0.35, 4],
      [29 - swing, 10],
    ]);

    stroke("rgba(216, 185, 255, 0.78)", 1);
    line(10 + swing * 0.35, 5, 17 + swing, 11);
    line(38 - swing * 0.35, 5, 31 - swing, 11);
    renderCtx.restore();
  }
}

class Camera {
  constructor() {
    this.x = 0;
    this.y = 0;
  }

  follow(rect, map = world) {
    const worldWidth = map.pixelWidth || MAP_WIDTH * TILE_SIZE;
    const worldHeight = map.pixelHeight || MAP_HEIGHT * TILE_SIZE;
    this.x = clamp(rect.x + rect.w / 2 - screenWidth / 2, 0, worldWidth - screenWidth);
    this.y = clamp(rect.y + rect.h / 2 - screenHeight / 2, 0, worldHeight - screenHeight);
  }
}

function fill(style) {
  renderCtx.fillStyle = style;
}

function stroke(style, width = 1) {
  renderCtx.strokeStyle = style;
  renderCtx.lineWidth = width;
}

function line(x1, y1, x2, y2) {
  renderCtx.beginPath();
  renderCtx.moveTo(x1, y1);
  renderCtx.lineTo(x2, y2);
  renderCtx.stroke();
}

function circle(x, y, radius, filled) {
  renderCtx.beginPath();
  renderCtx.arc(x, y, radius, 0, Math.PI * 2);
  if (filled) renderCtx.fill();
  else renderCtx.stroke();
}

function ellipse(x, y, w, h) {
  renderCtx.beginPath();
  renderCtx.ellipse(x, y, w / 2, h / 2, 0, 0, Math.PI * 2);
  renderCtx.fill();
}

function polygon(points) {
  renderCtx.beginPath();
  renderCtx.moveTo(points[0][0], points[0][1]);
  for (let i = 1; i < points.length; i += 1) {
    renderCtx.lineTo(points[i][0], points[i][1]);
  }
  renderCtx.closePath();
  renderCtx.fill();
}

function roundRect(x, y, w, h, radius, style) {
  renderCtx.fillStyle = style;
  renderCtx.beginPath();
  renderCtx.roundRect(x, y, w, h, radius);
  renderCtx.fill();
}

function drawGrass(x, y, tileX, tileY) {
  const rng = mulberry32(tileX * 92821 + tileY * 193);
  for (let i = 0; i < 3; i += 1) {
    const bladeX = x + 8 + Math.floor(rng() * (TILE_SIZE - 16));
    const bladeY = y + 14 + Math.floor(rng() * (TILE_SIZE - 21));
    stroke("#566b45", 2);
    line(bladeX, bladeY, bladeX + (rng() > 0.5 ? 3 : -3), bladeY - 9);
  }
  if ((tileX * 5 + tileY) % 13 === 0) {
    fill("#7e3158");
    circle(x + 31, y + 18, 3, true);
    fill("#b09158");
    circle(x + 36, y + 23, 3, true);
  }
}

function drawTree(x, y, tileX, tileY) {
  const offset = ((tileX * 17 + tileY * 11) % 9) - 4;
  fill("#1f2d26");
  ellipse(x + TILE_SIZE / 2 + offset, y + TILE_SIZE / 2 - 2, TILE_SIZE - 10, TILE_SIZE - 12);
  fill("#3a2a22");
  renderCtx.fillRect(x + TILE_SIZE / 2 - 3 + offset, y + TILE_SIZE / 2 + 4, 7, 17);
  fill("#223f30");
  circle(x + TILE_SIZE / 2 - 6 + offset, y + TILE_SIZE / 2 - 7, 13, true);
  fill("#304a38");
  circle(x + TILE_SIZE / 2 + 8 + offset, y + TILE_SIZE / 2 - 5, 11, true);
  fill("#3a5540");
  circle(x + TILE_SIZE / 2 + offset, y + TILE_SIZE / 2 - 15, 10, true);
}

function currentDialogue() {
  const playerName = sisterPlayerName();
  const speaker = `Abbey Island Mystery - ${playerName}`;
  if (currentAreaId === AREA_SHIP_ROOM) {
    return {
      speaker,
      text: "You stand aboard the supply ship Mercy. The wet deck creaks underfoot as the island fog presses close.",
    };
  }
  const footTileX = Math.floor((player.rect.x + player.rect.w / 2) / TILE_SIZE);
  const footTileY = Math.floor((player.rect.y + player.rect.h) / TILE_SIZE);
  if (footTileY === 37 && (footTileX === 46 || footTileX === 47)) {
    return {
      speaker,
      text: "Secret passage in the rocks.",
    };
  }
  if (world.tiles[footTileY]?.[footTileX] === WATER && footTileInsideRect(footTileX, footTileY, LAKE_OF_TEARS)) {
    return {
      speaker,
      text: "Swimming in the Lake of Tears",
    };
  }
  if (world.hidesPlayer(player.rect)) {
    return {
      speaker,
      text: "The south Towers loom tall casting shadows that hide you from view...",
    };
  }

  const location = world.locationNearPixel(player.rect.x + player.rect.w / 2, player.rect.y + player.rect.h);
  if (location?.type === "entrance") {
    return {
      speaker,
      text: `${location.buildingName}: ${location.name}`,
    };
  }

  if (location?.type === "landmark") {
    return {
      speaker,
      text: `You are near the ${location.name}.`,
    };
  }

  const groundDescription = groundDescriptionForTile(footTileX, footTileY);
  if (groundDescription) {
    return {
      speaker,
      text: groundDescription,
    };
  }

  if (location?.type === "building") {
    if (location.buildingKind === "monastery") {
      return {
        speaker,
        text: "The abbey grounds are onminously gloomy...",
      };
    }
    return {
      speaker,
      text: location.name,
    };
  }

  const directionDescription = islandDirectionDescription(footTileX, footTileY);
  if (directionDescription) {
    return {
      speaker,
      text: directionDescription,
    };
  }

  return {
    speaker,
    text: "The island is quiet and mysterious...",
  };
}

function wrapCanvasText(text, maxWidth, font) {
  ctx.font = font;
  const words = text.split(/\s+/);
  const lines = [];
  let line = "";

  for (const word of words) {
    const nextLine = line ? `${line} ${word}` : word;
    if (ctx.measureText(nextLine).width <= maxWidth || !line) {
      line = nextLine;
      continue;
    }
    lines.push(line);
    line = word;
  }

  if (line) {
    lines.push(line);
  }
  return lines;
}

function drawDialogueBox() {
  const margin = Math.max(14, Math.min(30, screenWidth * 0.035));
  const viewport = window.visualViewport;
  const visibleTop = viewport?.offsetTop || 0;
  const visibleHeight = viewport?.height || screenHeight;
  const visibleBottom = Math.min(screenHeight, visibleTop + visibleHeight);
  const touchBottomClearance = window.matchMedia?.("(pointer: coarse)")?.matches ? 96 : 18;
  const browserInset = Math.max(0, screenHeight - visibleBottom);
  const safeBottom = Math.max(touchBottomClearance, browserInset + 18);
  const width = screenWidth - margin * 2;
  const maxDialogueHeight = touchBottomClearance > 18 ? 108 : 124;
  const height = Math.min(maxDialogueHeight, Math.max(88, visibleHeight * 0.16));
  const x = margin;
  const y = Math.max(margin, visibleBottom - height - safeBottom);
  const dialogue = currentDialogue();
  const speakerFont = "400 22px Creepster, Arial, Helvetica, sans-serif";
  const bodyFont = "15px Arial, Helvetica, sans-serif";
  const textMaxWidth = width - 48;
  const visibleLineCount = 2;
  const allLines = wrapCanvasText(dialogue.text, textMaxWidth, bodyFont);
  const currentKey = `${dialogue.speaker}\n${dialogue.text}`;
  if (currentKey !== dialogueKey) {
    dialogueKey = currentKey;
    dialoguePage = 0;
  }
  const maxPage = Math.max(0, Math.ceil(allLines.length / visibleLineCount) - 1);
  dialoguePage = clamp(dialoguePage, 0, maxPage);
  const hasMoreDialogue = dialoguePage < maxPage;
  const lines = allLines.slice(
    dialoguePage * visibleLineCount,
    dialoguePage * visibleLineCount + visibleLineCount
  );
  dialogueMoreButtonRect = {
    x: x + width - 88,
    y: y + 18,
    w: 64,
    h: 28,
    enabled: hasMoreDialogue,
  };

  ctx.save();
  ctx.fillStyle = "rgba(14, 13, 16, 0.9)";
  ctx.strokeStyle = "rgba(224, 205, 148, 0.88)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, 8);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "rgba(224, 205, 148, 0.16)";
  ctx.fillRect(x + 12, y + 12, width - 24, 2);
  ctx.fillRect(x + 12, y + height - 14, width - 24, 2);

  ctx.font = speakerFont;
  ctx.fillStyle = "#f0dfaa";
  ctx.textBaseline = "top";
  const speakerMaxWidth = Math.max(80, dialogueMoreButtonRect.x - x - 36);
  if (ctx.measureText(dialogue.speaker).width > speakerMaxWidth) {
    ctx.font = "400 18px Creepster, Arial, Helvetica, sans-serif";
  }
  ctx.fillText(dialogue.speaker, x + 24, y + 20);

  ctx.font = "400 18px Creepster, Arial, Helvetica, sans-serif";
  ctx.textAlign = "center";
  ctx.fillStyle = hasMoreDialogue ? "rgba(49, 48, 68, 0.92)" : "rgba(49, 48, 68, 0.42)";
  ctx.strokeStyle = hasMoreDialogue ? "rgba(235, 226, 176, 0.92)" : "rgba(235, 226, 176, 0.38)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.roundRect(
    dialogueMoreButtonRect.x,
    dialogueMoreButtonRect.y,
    dialogueMoreButtonRect.w,
    dialogueMoreButtonRect.h,
    7
  );
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = hasMoreDialogue ? "#f5f4e8" : "rgba(245, 244, 232, 0.38)";
  ctx.fillText("More", dialogueMoreButtonRect.x + dialogueMoreButtonRect.w / 2, dialogueMoreButtonRect.y + 5);
  ctx.textAlign = "start";

  ctx.font = bodyFont;
  ctx.fillStyle = "#f7f1dd";
  lines.forEach((lineText, index) => {
    ctx.fillText(lineText, x + 24, y + 54 + index * 21);
  });
  ctx.restore();
}

function resize() {
  const scale = Math.min(window.devicePixelRatio || 1, 1.5);
  screenWidth = window.innerWidth;
  screenHeight = window.innerHeight;
  canvas.width = Math.floor(screenWidth * scale);
  canvas.height = Math.floor(screenHeight * scale);
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  ctx.imageSmoothingEnabled = false;
}

function startMusic({ userInitiated = false } = {}) {
  if (soundMuted && !userInitiated) {
    updateSoundButton();
    return;
  }
  soundMuted = false;
  saveSoundSetting();
  if (!audio) {
    const context = new AudioContext();
    const master = context.createGain();
    master.gain.value = 0.045;
    master.connect(context.destination);
    audio = { context, master, timers: [], tones: [] };
  }

  if (audio.context.state === "suspended") {
    audio.context.resume();
  }
  audio.master.gain.cancelScheduledValues(audio.context.currentTime);
  audio.master.gain.setValueAtTime(0.045, audio.context.currentTime);
  if (!musicEnabled) {
    musicEnabled = true;
    scheduleMusic();
  }
  updateSoundButton();
}

function stopAllSounds() {
  soundMuted = true;
  musicEnabled = false;
  saveSoundSetting();
  if (!audio) {
    updateSoundButton();
    return;
  }
  audio.master.gain.cancelScheduledValues(audio.context.currentTime);
  audio.master.gain.setValueAtTime(0.0001, audio.context.currentTime);
  audio.timers.forEach((timer) => window.clearTimeout(timer));
  audio.timers = [];
  audio.tones.forEach(({ osc, gain }) => {
    try {
      osc.stop();
    } catch (error) {
      // Already stopped oscillators throw in some browsers.
    }
    disconnectAudioNode(osc);
    disconnectAudioNode(gain);
  });
  audio.tones = [];
  updateSoundButton();
}

function updateSoundButton() {
  soundButton.classList.toggle("muted", soundMuted);
  soundButton.setAttribute("aria-pressed", String(soundMuted));
  soundButton.setAttribute("aria-label", soundMuted ? "Unmute sound" : "Mute sound");
}

function disconnectAudioNode(node) {
  try {
    node.disconnect();
  } catch (error) {
    // Some browsers throw if a node has no remaining connections.
  }
}

function playTone(freq, start, duration, gainValue, type = "triangle") {
  const osc = audio.context.createOscillator();
  const gain = audio.context.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  gain.gain.setValueAtTime(0.0001, start);
  gain.gain.exponentialRampToValueAtTime(gainValue, start + 0.04);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  osc.connect(gain);
  gain.connect(audio.master);
  audio.tones.push({ osc, gain });
  osc.addEventListener("ended", () => {
    audio.tones = audio.tones.filter((tone) => tone.osc !== osc);
    disconnectAudioNode(osc);
    disconnectAudioNode(gain);
  }, { once: true });
  osc.start(start);
  osc.stop(start + duration + 0.04);
}

function scheduleMusic() {
  if (!audio || !musicEnabled) return;
  const melody = [
    220.0, 261.63, 293.66, 261.63,
    220.0, 196.0, 220.0, 246.94,
    261.63, 329.63, 311.13, 293.66,
    261.63, 246.94, 220.0, 196.0,
    174.61, 220.0, 261.63, 329.63,
    293.66, 261.63, 246.94, 220.0,
    207.65, 246.94, 293.66, 349.23,
    329.63, 293.66, 261.63, 220.0,
  ];
  const bassLine = [
    55.0, 82.41, 110.0, 82.41,
    49.0, 73.42, 98.0, 73.42,
    65.41, 98.0, 130.81, 98.0,
    61.74, 92.5, 123.47, 92.5,
  ];
  const lowPulse = [55.0, 49.0, 65.41, 61.74];
  const now = audio.context.currentTime + 0.05;
  const beat = 0.375;

  for (let i = 0; i < 64; i += 1) {
    const start = now + i * beat;
    const phraseAccent = i % 8 === 0 ? 0.08 : 0;
    playTone(melody[i % melody.length], start, beat * 0.82, 0.34 + phraseAccent, "triangle");
    playTone(bassLine[i % bassLine.length], start, beat * 0.9, 0.24, "sine");
    if (i % 4 === 0) {
      playTone(lowPulse[Math.floor(i / 4) % lowPulse.length], start, beat * 3.65, 0.28, "sine");
    }
  }

  const timer = window.setTimeout(scheduleMusic, 23000);
  audio.timers.push(timer);
}

const world = new World();
const shipRoom = new ShipRoom();
const player = new Player(world);
const camera = new Camera();
const backdropCamera = new Camera();
let currentAreaId = AREA_ISLAND;

function activeMap() {
  return currentAreaId === AREA_SHIP_ROOM ? shipRoom : world;
}

function setCurrentArea(areaId) {
  currentAreaId = areaId === AREA_SHIP_ROOM ? AREA_SHIP_ROOM : AREA_ISLAND;
}

function playerFootTile() {
  return {
    x: Math.floor((player.rect.x + player.rect.w / 2) / TILE_SIZE),
    y: Math.floor((player.rect.y + player.rect.h) / TILE_SIZE),
  };
}

function setPlayerToIslandPlank() {
  player.rect.x = 46 * TILE_SIZE + 13;
  player.rect.y = 14 * TILE_SIZE + 8;
  player.facing = { x: 0, y: 1 };
  player.stepTimer = 0;
  player.walking = false;
}

function stopPlayerInput() {
  keys.clear();
  Object.keys(pad).forEach((direction) => {
    pad[direction] = false;
  });
}

function enterShipRoom() {
  setCurrentArea(AREA_SHIP_ROOM);
  shipRoom.spawnAtEntrance(player);
  stopPlayerInput();
}

function exitShipRoom() {
  setCurrentArea(AREA_ISLAND);
  setPlayerToIslandPlank();
  stopPlayerInput();
}

function maybeEnterShipRoom() {
  if (currentAreaId !== AREA_ISLAND) {
    return;
  }
  const foot = playerFootTile();
  const onBoardingPlank = foot.x >= 46 && foot.x <= 47 && foot.y <= 13;
  if (onBoardingPlank) {
    enterShipRoom();
  }
}

function maybeExitShipRoom() {
  if (currentAreaId !== AREA_SHIP_ROOM) {
    return;
  }
  const foot = playerFootTile();
  const atGangwayExit = foot.y >= shipRoom.height - 1 && foot.x >= shipRoom.entranceTile.x && foot.x <= shipRoom.entranceTile.x + 1;
  if (atGangwayExit) {
    exitShipRoom();
  }
}

function centerCameraOnMap(camera, map) {
  const worldWidth = map.pixelWidth || MAP_WIDTH * TILE_SIZE;
  const worldHeight = map.pixelHeight || MAP_HEIGHT * TILE_SIZE;
  camera.x = (worldWidth - screenWidth) / 2;
  camera.y = (worldHeight - screenHeight) / 2;
}

function setHarbourBackdropCamera() {
  const harborX = (SHIP_BUILDING.x + SHIP_BUILDING.w / 2) * TILE_SIZE;
  const harborY = (SHIP_BUILDING.y + SHIP_BUILDING.h / 2) * TILE_SIZE;
  backdropCamera.x = clamp(harborX - screenWidth / 2, 0, MAP_WIDTH * TILE_SIZE - screenWidth);
  backdropCamera.y = clamp(harborY - screenHeight / 2, 0, MAP_HEIGHT * TILE_SIZE - screenHeight);
}

for (const img of graphicsList()) {
  if (!img.complete) {
    img.addEventListener("load", () => world.invalidateCache(), { once: true });
    img.addEventListener("error", () => world.invalidateCache(), { once: true });
  }
}
loadDesignMap();

function frame(now) {
  const dt = Math.min((now - lastTime) / 1000, 0.05);
  lastTime = now;

  if (gameStarted) {
    player.update(dt, activeMap());
    maybeEnterShipRoom();
    maybeExitShipRoom();
    const position = currentGameState().position;
    const movedSinceTelemetry = !lastTelemetryPosition ||
      Math.hypot(position.x - lastTelemetryPosition.x, position.y - lastTelemetryPosition.y) > 8;
    if (movedSinceTelemetry && now - lastTelemetryAt > 1000) {
      lastTelemetryAt = now;
      lastTelemetryPosition = position;
      trackGameEvent("position", position);
    }
  }
  const map = activeMap();

  ctx.fillStyle = color(COLORS[WATER]);
  ctx.fillRect(0, 0, screenWidth, screenHeight);
  if (currentAreaId === AREA_SHIP_ROOM) {
    setHarbourBackdropCamera();
    world.draw(backdropCamera);
    world.drawForeground(backdropCamera);
    ctx.fillStyle = "rgba(6, 8, 11, 0.48)";
    ctx.fillRect(0, 0, screenWidth, screenHeight);
    centerCameraOnMap(camera, map);
    map.draw(camera);
    player.draw(camera);
    map.drawForeground(camera);
  } else {
    camera.follow(player.rect, map);
    map.draw(camera);
    if (!map.hidesPlayer(player.rect)) {
      player.draw(camera);
    }
    map.drawForeground(camera);
  }
  if (gameStarted) {
    drawDialogueBox();
  }
  requestAnimationFrame(frame);
}

function showIntroStatus(message) {
  if (!introStatus) {
    return;
  }
  introStatus.textContent = message;
}

function showLoadGameStatus(message) {
  if (!loadGameStatus) {
    return;
  }
  loadGameStatus.textContent = message;
}

function showNewGameStatus(message) {
  if (!newGameStatus) {
    return;
  }
  newGameStatus.textContent = message;
}

function showLoginStatus(message) {
  if (!loginStatus) {
    return;
  }
  loginStatus.textContent = message;
}

function hideSetupScreens() {
  loadGameScreen.classList.add("hidden");
  newGameScreen.classList.add("hidden");
  prologueScreen.classList.add("hidden");
  loginScreen.classList.add("hidden");
}

function serializeInventory() {
  return inventory.map((item) => item ? { ...item } : null);
}

function restoreInventory(items = []) {
  inventory.forEach((_, index) => {
    inventory[index] = items[index] ? { ...items[index] } : null;
  });
  selectedInventorySlot = null;
  renderInventory();
}

function resetInventory() {
  inventory.fill(null);
  selectedInventorySlot = null;
  renderInventory();
}

function restorePlayerPosition(position) {
  if (!position) {
    return;
  }
  setCurrentArea(position.area || AREA_ISLAND);
  player.rect.x = position.x;
  player.rect.y = position.y;
}

function restoreUiState(ui) {
  if (!ui || typeof ui.menuActionsCollapsed !== "boolean") {
    return;
  }
  setMenuActionsCollapsed(ui.menuActionsCollapsed, { persist: true });
}

function savedGamesForRecord(record) {
  if (!record) {
    return [];
  }
  const saves = [];
  const seen = new Set();
  const addSave = (save) => {
    if (!save || typeof save !== "object") {
      return;
    }
    const key = save.id || save.savedAt || JSON.stringify(save.position || {});
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    saves.push(save);
  };

  addSave(record.currentSave);
  (record.saves || []).forEach(addSave);
  return saves;
}

function saveLabel(save, index) {
  if (save.name) {
    return save.name;
  }
  const savedAt = save.savedAt ? new Date(save.savedAt) : null;
  if (savedAt && !Number.isNaN(savedAt.getTime())) {
    return `Investigation ${index + 1} - ${savedAt.toLocaleString()}`;
  }
  return `Investigation ${index + 1}`;
}

function saveDetail(save) {
  const position = save.position || {};
  const locationName = save.location?.name;
  if (position.area === AREA_SHIP_ROOM) {
    return `${locationName || SHIP_ROOM.name}: ${position.tileX},${position.tileY}`;
  }
  if (Number.isFinite(position.tileX) && Number.isFinite(position.tileY)) {
    return `${locationName || "Last position"}: ${position.tileX},${position.tileY}`;
  }
  return "No position recorded yet";
}

function renderLoadGameList(record) {
  if (!loadGameList) {
    return [];
  }

  const saves = savedGamesForRecord(record);
  loadGameList.replaceChildren();

  if (!saves.length) {
    const empty = document.createElement("div");
    empty.className = "saved-game-empty";
    empty.textContent = "No saved investigations for this player yet.";
    loadGameList.append(empty);
    return saves;
  }

  saves.forEach((save, index) => {
    const button = document.createElement("button");
    button.className = "saved-game-button";
    button.type = "button";
    button.dataset.saveIndex = String(index);

    const title = document.createElement("strong");
    title.textContent = saveLabel(save, index);
    const detail = document.createElement("span");
    detail.textContent = saveDetail(save);

    button.append(title, detail);
    button.addEventListener("click", () => loadSelectedGame(save));
    loadGameList.append(button);
  });

  return saves;
}

async function syncServerSaveIntoActiveRecord() {
  if (!isLoggedIn()) {
    return;
  }
  try {
    const serverSave = await serverLoadGameState();
    if (!serverSave) {
      return;
    }
    const database = loadGameDatabase();
    const activeName = database.activePlayer;
    if (!activeName) {
      return;
    }
    const existing = database.players[activeName] || { name: activeName };
    database.players[activeName] = {
      ...existing,
      name: activeName,
      currentSave: existing.currentSave || serverSave,
      saves: savedGamesForRecord({ ...existing, currentSave: existing.currentSave || serverSave, saves: existing.saves || [serverSave] }),
      updatedAt: new Date().toISOString(),
    };
    saveGameDatabase(database);
  } catch (error) {
    console.warn("Could not fetch server save for load list.", error);
  }
}

function nearestSaveLocation() {
  if (currentAreaId === AREA_SHIP_ROOM) {
    return {
      id: SHIP_ROOM.id,
      name: SHIP_ROOM.name,
    };
  }
  const centerX = player.rect.x + player.rect.w / 2;
  const footY = player.rect.y + player.rect.h;
  const location = world.locationNearPixel(centerX, footY, TILE_SIZE * 5);
  return {
    id: location?.id || "open-island",
    name: location?.name || location?.buildingName || "Abbey Island",
  };
}

function formatSaveDate(date) {
  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function currentGameState({ named = false } = {}) {
  const now = new Date();
  const centerX = player.rect.x + player.rect.w / 2;
  const centerY = player.rect.y + player.rect.h / 2;
  const location = nearestSaveLocation();
  const save = {
    id: `${now.toISOString()}-${Math.round(player.rect.x)}-${Math.round(player.rect.y)}`,
    name: named ? `${location.name} - ${formatSaveDate(now)}` : undefined,
    savedAt: now.toISOString(),
    location,
    position: {
      area: currentAreaId,
      x: player.rect.x,
      y: player.rect.y,
      tileX: Math.floor(centerX / TILE_SIZE),
      tileY: Math.floor(centerY / TILE_SIZE),
    },
    inventory: serializeInventory(),
    ui: {
      menuActionsCollapsed: menuActionsCollapsed(),
    },
  };
  if (!save.name) {
    delete save.name;
  }
  return {
    ...save,
  };
}

function saveActiveGameState(reason = "autosave", { beacon = false } = {}) {
  const database = loadGameDatabase();
  const activeName = database.activePlayer;
  if (!activeName || !database.players[activeName]) {
    return;
  }

  const isManualSave = reason === "manual_save";
  const save = currentGameState({ named: isManualSave });
  database.players[activeName].currentSave = save;
  database.players[activeName].saves = database.players[activeName].saves || [];
  if (isManualSave) {
    database.players[activeName].saves = [
      save,
      ...database.players[activeName].saves.filter((saved) => saved.id !== save.id),
    ];
  } else if (!database.players[activeName].saves.length) {
    database.players[activeName].saves = [save];
  }
  saveGameDatabase(database);
  serverSaveGameState(save, reason, { beacon });
  return save;
}

async function loadActiveGameState({ preferServer = true } = {}) {
  const record = activePlayerRecord();
  let save = record?.currentSave || null;

  if (preferServer && isLoggedIn()) {
    try {
      save = await serverLoadGameState() || save;
    } catch (error) {
      console.warn("Could not load server save, using local save if present.", error);
    }
  }

  if (!save) {
    return false;
  }

  restorePlayerPosition(save.position);
  restoreInventory(save.inventory);
  restoreUiState(save.ui);
  return true;
}

async function startGame({ loadSave = false } = {}) {
  if (!isLoggedIn()) {
    gameStarted = false;
    localStorage.setItem("mmmScreen", "title");
    syncLoginState();
    intro.classList.remove("hidden");
    hideSetupScreens();
    showIntroStatus("Login or create a new game first.");
    return;
  }
  if (loadSave) {
    await loadActiveGameState();
  }
  gameStarted = true;
  localStorage.setItem("mmmScreen", "game");
  intro.classList.add("hidden");
  hideSetupScreens();
  syncLoginState();
  startMusic();
  trackGameEvent("game_start", {
    loadSave,
    position: currentGameState().position,
  });
}

function exitToTitle() {
  saveActiveGameState("exit");
  trackGameEvent("game_exit", { position: currentGameState().position }, { beacon: true });
  gameStarted = false;
  localStorage.setItem("mmmScreen", "title");
  keys.clear();
  Object.keys(pad).forEach((direction) => {
    pad[direction] = false;
  });
  hideSetupScreens();
  intro.classList.remove("hidden");
  showIntroStatus("");
  syncLoginState();
}

function syncIntroVisibility() {
  intro.classList.toggle("hidden", gameStarted);
  hideSetupScreens();
  syncLoginState();
}

function renderProloguePage() {
  prologueCopy.replaceChildren();
  let pageContainer = prologueCopy;

  PROLOGUE_PAGES[prologuePageIndex].forEach((entry) => {
    if (entry.heading) {
      const objective = document.createElement("div");
      objective.className = "prologue-objective";
      const heading = document.createElement("h3");
      heading.textContent = entry.heading;
      objective.append(heading);
      prologueCopy.append(objective);
      pageContainer = objective;
      return;
    }

    const paragraph = document.createElement("p");
    paragraph.textContent = typeof entry.text === "function" ? entry.text() : entry.text;
    if (entry.className) {
      paragraph.className = entry.className;
    }
    pageContainer.append(paragraph);
  });

  const lastPageIndex = PROLOGUE_PAGES.length - 1;
  previousProloguePageButton.disabled = prologuePageIndex === 0;
  nextProloguePageButton.disabled = prologuePageIndex === lastPageIndex;
  nextProloguePageButton.hidden = prologuePageIndex === lastPageIndex;
  beginPrologueGameButton.hidden = prologuePageIndex !== lastPageIndex;
  prologuePageStatus.textContent = `Page ${prologuePageIndex + 1} of ${PROLOGUE_PAGES.length}`;
}

function showProloguePage(pageIndex) {
  prologuePageIndex = Math.max(0, Math.min(PROLOGUE_PAGES.length - 1, pageIndex));
  renderProloguePage();
}

function nextProloguePage() {
  showProloguePage(prologuePageIndex + 1);
  if (prologuePageIndex === PROLOGUE_PAGES.length - 1) {
    beginPrologueGameButton.focus();
  } else {
    nextProloguePageButton.focus();
  }
}

function previousProloguePage() {
  showProloguePage(prologuePageIndex - 1);
  if (prologuePageIndex === 0) {
    nextProloguePageButton.focus();
  } else {
    previousProloguePageButton.focus();
  }
}

function openPrologueScreen({ loadSave = false } = {}) {
  gameStarted = false;
  pendingPrologueStart = { loadSave };
  localStorage.setItem("mmmScreen", "prologue");
  intro.classList.add("hidden");
  hideSetupScreens();
  showProloguePage(0);
  prologueScreen.classList.remove("hidden");
  nextProloguePageButton.focus();
}

async function beginPrologueGame() {
  await startGame(pendingPrologueStart);
}

async function openLoadGameScreen() {
  gameStarted = false;
  localStorage.setItem("mmmScreen", "title");
  intro.classList.add("hidden");
  hideSetupScreens();
  loadGameScreen.classList.remove("hidden");
  showLoadGameStatus("");

  await refreshSessionState();
  if (!isLoggedIn()) {
    renderLoadGameList(null);
    createGameFromLoadButton.textContent = "Create Player";
    showLoadGameStatus("Login first, or create a player to start a new investigation.");
    return;
  }

  createGameFromLoadButton.textContent = "New Investigation";
  await syncServerSaveIntoActiveRecord();
  const record = activePlayerRecord();
  const saves = renderLoadGameList(record);
  if (!saves.length) {
    showLoadGameStatus("Start a new investigation for this player.");
  }
}

function closeLoadGameScreen() {
  loadGameScreen.classList.add("hidden");
  intro.classList.remove("hidden");
  showLoadGameStatus("");
}

function openNewGameSetup({ loginMode = false } = {}) {
  gameStarted = false;
  localStorage.setItem("mmmScreen", "title");
  intro.classList.add("hidden");
  hideSetupScreens();
  newGameScreen.classList.remove("hidden");
  showNewGameStatus("");

  const record = activePlayerRecord();
  newPlayerNameInput.value = record?.name || "";
  newPlayerPasswordInput.value = "";
  resetPositionInput.checked = !loginMode;
  resetSavesInput.checked = !loginMode;
  resetInventoryInput.checked = !loginMode;
  newPlayerNameInput.focus();
}

function closeNewGameSetup() {
  newGameScreen.classList.add("hidden");
  intro.classList.remove("hidden");
  showNewGameStatus("");
}

function openLoginScreen() {
  gameStarted = false;
  localStorage.setItem("mmmScreen", "title");
  intro.classList.add("hidden");
  hideSetupScreens();
  loginScreen.classList.remove("hidden");
  showLoginStatus("");

  const record = activePlayerRecord();
  loginPlayerNameInput.value = record?.name || "";
  loginPlayerPasswordInput.value = "";
  loginPlayerNameInput.focus();
}

function closeLoginScreen() {
  loginScreen.classList.add("hidden");
  intro.classList.remove("hidden");
  showLoginStatus("");
}

async function loadSelectedGame(save) {
  restorePlayerPosition(save.position);
  restoreInventory(save.inventory);
  restoreUiState(save.ui);
  const database = loadGameDatabase();
  const activeName = database.activePlayer;
  if (activeName && database.players[activeName]) {
    database.players[activeName].currentSave = save;
    database.players[activeName].updatedAt = new Date().toISOString();
    saveGameDatabase(database);
  }
  await startGame();
}

async function createGameFromLoadScreen() {
  if (!isLoggedIn()) {
    openNewGameSetup();
    return;
  }

  setCurrentArea(AREA_ISLAND);
  player.resetToStart(world);
  resetInventory();

  const currentSave = currentGameState();
  const database = loadGameDatabase();
  const activeName = database.activePlayer;
  const existing = database.players[activeName] || { name: activeName };
  database.players[activeName] = {
    ...existing,
    name: activeName,
    inventory: serializeInventory(),
    currentSave,
    saves: [currentSave],
    updatedAt: new Date().toISOString(),
  };
  saveGameDatabase(database);
  await serverSaveGameState(currentSave, "new_game_reset");
  openPrologueScreen();
}

async function createNewGame(event) {
  event.preventDefault();

  const playerName = newPlayerNameInput.value.trim();
  const password = newPlayerPasswordInput.value;
  if (!playerName || !password) {
    showNewGameStatus("Player name and set password are required.");
    return;
  }

  let auth;
  try {
    auth = await serverLogin(playerName, password, true);
  } catch (error) {
    if (error.status === 409) {
      openLoginScreen();
      loginPlayerNameInput.value = playerName;
      loginPlayerPasswordInput.value = "";
      showLoginStatus("Player already exists. Enter the password to log in.");
      loginPlayerPasswordInput.focus();
      return;
    }
    showNewGameStatus(error.message);
    return;
  }

  const database = loadGameDatabase();
  const existing = database.players[playerName] || {};
  const isExistingPlayer = Boolean(existing.name);
  const resetPosition = resetPositionInput.checked || !isExistingPlayer;
  const resetSaves = resetSavesInput.checked || !isExistingPlayer;
  const resetItems = resetInventoryInput.checked || !isExistingPlayer;

  if (resetPosition) {
    setCurrentArea(AREA_ISLAND);
    player.resetToStart(world);
  } else {
    restorePlayerPosition(existing.currentSave?.position);
  }

  if (resetItems) {
    resetInventory();
  } else {
    restoreInventory(existing.currentSave?.inventory || existing.inventory || []);
  }

  const currentSave = currentGameState();
  database.activePlayer = playerName;
  database.players[playerName] = {
    name: playerName,
    settings: {
      ...(existing.settings || {}),
      resetPosition,
      resetSaves,
      resetInventory: resetItems,
      soundMuted,
      menuActionsCollapsed: menuActionsCollapsed(),
    },
    inventory: serializeInventory(),
    currentSave,
    saves: resetSaves ? [currentSave] : (existing.saves || [currentSave]),
    updatedAt: new Date().toISOString(),
  };
  saveGameDatabase(database);
  await serverSaveGameState(currentSave, auth.created ? "new_game" : "new_game_reset");
  loggedInName = playerName;
  syncLoginState();
  showNewGameStatus(auth.created ? "Game created." : "Logged in.");
  if (auth.created) {
    openPrologueScreen();
  } else {
    await startGame({ loadSave: !resetPosition || !resetItems });
  }
}

async function loginExistingUser(event) {
  event.preventDefault();

  const playerName = loginPlayerNameInput.value.trim();
  const password = loginPlayerPasswordInput.value;
  if (!playerName || !password) {
    showLoginStatus("Player name and password are required.");
    return;
  }

  try {
    await serverLogin(playerName, password, false);
  } catch (error) {
    showLoginStatus(error.message);
    return;
  }

  const database = loadGameDatabase();
  database.activePlayer = playerName;
  database.players[playerName] = database.players[playerName] || {
    name: playerName,
    settings: {
      soundMuted,
      menuActionsCollapsed: menuActionsCollapsed(),
    },
    inventory: [],
    saves: [],
    updatedAt: new Date().toISOString(),
  };
  saveGameDatabase(database);
  syncLoginState();
  loadSoundSetting();
  closeLoginScreen();
  showIntroStatus("Logged in.");
}

function openSettingsMenu() {
  // Pseudocode: replace this with a real settings panel.
  // settings = loadSettings()
  // show controls for music, effects volume, text speed, fullscreen, and input mapping
  // onSave(settings): persist settings and apply them to audio/UI/gameplay
  showIntroStatus("Settings menu placeholder: music, controls, fullscreen, and accessibility options will live here.");
}

async function logoutUser() {
  saveActiveGameState("logout");
  const database = loadGameDatabase();
  database.activePlayer = null;
  saveGameDatabase(database);
  await serverLogout();
  gameStarted = false;
  localStorage.setItem("mmmScreen", "title");
  hideSetupScreens();
  intro.classList.remove("hidden");
  showIntroStatus("Logged out locally. Login or create a new game.");
}

async function continueGame() {
  await refreshSessionState();
  if (!isLoggedIn()) {
    syncLoginState();
    showIntroStatus("Login or create a new game first.");
    return;
  }
  if (!await loadActiveGameState()) {
    showIntroStatus("No saved investigation found. Start a new game first.");
    return;
  }
  await startGame();
}

function renderInventory() {
  inventorySlotButtons.forEach((button, index) => {
    const item = inventory[index];
    button.classList.toggle("empty", !item);
    button.classList.toggle("selected", selectedInventorySlot === index);
    button.textContent = item ? item.icon : "";
    button.title = item ? item.name : "Empty";
    button.setAttribute("aria-label", item ? `Use ${item.name}` : "Empty inventory slot");
  });
}

function addInventoryItem(item) {
  const slotIndex = inventory.findIndex((slot) => !slot);
  if (slotIndex === -1) {
    return false;
  }
  inventory[slotIndex] = item;
  renderInventory();
  return true;
}

function useInventorySlot(slotIndex) {
  const item = inventory[slotIndex];
  selectedInventorySlot = selectedInventorySlot === slotIndex ? null : slotIndex;
  renderInventory();

  if (!item) {
    return;
  }
}

function selectedInventoryItem() {
  if (selectedInventorySlot === null) {
    return null;
  }
  return inventory[selectedInventorySlot];
}

function useSelectedInventoryItem() {
  const item = selectedInventoryItem();
  if (!item) {
    return;
  }

  // Pseudocode: route item use through the current room, target, or nearby clue.
  // game.useItem(item, player, world)
  console.info(`Inventory placeholder: use ${item.name}.`);
}

function dropSelectedInventoryItem() {
  const item = selectedInventoryItem();
  if (!item) {
    return;
  }

  // Pseudocode: spawn the dropped item near the player once world pickups exist.
  // world.dropItem(item, player.rect)
  inventory[selectedInventorySlot] = null;
  selectedInventorySlot = null;
  renderInventory();
  saveActiveGameState("inventory_drop");
  trackGameEvent("inventory_drop", { item: item.name });
  console.info(`Inventory placeholder: drop ${item.name}.`);
}

function examineSelectedInventoryItem() {
  const item = selectedInventoryItem();
  if (!item) {
    return;
  }

  // Pseudocode: open an item detail panel with clue text and usable targets.
  console.info(`Inventory placeholder: examine ${item.name}.`);
}

function consumeSelectedInventoryItem() {
  const item = selectedInventoryItem();
  if (!item) {
    return;
  }

  // Pseudocode: apply consumable effects once food, medicine, or ritual items exist.
  console.info(`Inventory placeholder: consume ${item.name}.`);
}

function toggleInventoryActions() {
  // Pseudocode: use this as an inventory action mode toggle if needed later.
  console.info("Inventory cross placeholder: action mode toggle.");
}

function saveGameFromHud() {
  const save = saveActiveGameState("manual_save");
  if (!save) {
    return;
  }
  const originalText = hudSaveGameButton.textContent;
  hudSaveGameButton.textContent = "Saved";
  hudSaveGameButton.title = save.name || "Game saved";
  window.setTimeout(() => {
    hudSaveGameButton.textContent = originalText;
  }, 1200);
  console.info(`Game saved: ${save.name || save.savedAt}.`);
}

function loadGameFromHud() {
  openLoadGameScreen();
}

function handleCanvasPointerDown(event) {
  if (!gameStarted || !dialogueMoreButtonRect?.enabled) {
    return;
  }

  const rect = canvas.getBoundingClientRect();
  const pointerX = (event.clientX - rect.left) * (screenWidth / rect.width);
  const pointerY = (event.clientY - rect.top) * (screenHeight / rect.height);
  const insideMoreButton = (
    pointerX >= dialogueMoreButtonRect.x &&
    pointerX <= dialogueMoreButtonRect.x + dialogueMoreButtonRect.w &&
    pointerY >= dialogueMoreButtonRect.y &&
    pointerY <= dialogueMoreButtonRect.y + dialogueMoreButtonRect.h
  );

  if (!insideMoreButton) {
    return;
  }

  event.preventDefault();
  dialoguePage += 1;
}

function setMenuActionsCollapsed(collapsed, { persist = false } = {}) {
  gameMenu.classList.toggle("actions-collapsed", collapsed);
  menuActionsToggle.setAttribute("aria-expanded", String(!collapsed));
  menuActionsToggle.setAttribute("aria-label", collapsed ? "Show menu actions" : "Hide menu actions");
  if (persist) {
    saveMenuActionsSetting(collapsed);
  }
}

function defaultMenuActionsCollapsed() {
  return window.matchMedia?.("(max-width: 560px), (pointer: coarse)")?.matches || false;
}

window.addEventListener("resize", resize);
window.visualViewport?.addEventListener("resize", resize);
window.addEventListener("beforeunload", () => saveActiveGameState("beforeunload", { beacon: true }));
canvas.addEventListener("pointerdown", handleCanvasPointerDown);
window.addEventListener("keydown", (event) => {
  const activeElement = document.activeElement;
  const introControlFocused = activeElement && intro.contains(activeElement);
  const newGameControlFocused = activeElement && newGameScreen.contains(activeElement);
  const loadGameControlFocused = activeElement && loadGameScreen.contains(activeElement);
  const prologueControlFocused = activeElement && prologueScreen.contains(activeElement);
  const loginControlFocused = activeElement && loginScreen.contains(activeElement);
  if (!gameStarted && event.key.toLowerCase() === "enter" && !introControlFocused && !loadGameControlFocused && !newGameControlFocused && !prologueControlFocused && !loginControlFocused) {
    openLoadGameScreen();
    return;
  }

  if (!gameStarted && !prologueScreen.classList.contains("hidden")) {
    if (["arrowright", "pagedown", " "].includes(event.key.toLowerCase())) {
      event.preventDefault();
      nextProloguePage();
      return;
    }
    if (["arrowleft", "pageup"].includes(event.key.toLowerCase())) {
      event.preventDefault();
      previousProloguePage();
      return;
    }
  }

  if (!gameStarted) {
    return;
  }

  keys.add(event.key.toLowerCase());
  if (["arrowup", "arrowdown", "arrowleft", "arrowright", " "].includes(event.key.toLowerCase())) {
    event.preventDefault();
  }
  startMusic();
});
window.addEventListener("keyup", (event) => keys.delete(event.key.toLowerCase()));

document.querySelectorAll("[data-pad]").forEach((button) => {
  const direction = button.dataset.pad;
  const press = (event) => {
    event.preventDefault();
    pad[direction] = true;
    startMusic();
  };
  const release = (event) => {
    event.preventDefault();
    pad[direction] = false;
  };
  button.addEventListener("pointerdown", press);
  button.addEventListener("pointerup", release);
  button.addEventListener("pointercancel", release);
  button.addEventListener("pointerleave", release);
});

inventorySlotButtons.forEach((button) => {
  button.addEventListener("click", () => {
    useInventorySlot(Number(button.dataset.inventorySlot));
  });
});
useItemButton.addEventListener("click", useSelectedInventoryItem);
dropItemButton.addEventListener("click", dropSelectedInventoryItem);
examineItemButton.addEventListener("click", examineSelectedInventoryItem);
consumeItemButton.addEventListener("click", consumeSelectedInventoryItem);
inventoryCrossButton.addEventListener("click", toggleInventoryActions);

soundButton.addEventListener("click", () => {
  if (!soundMuted) stopAllSounds();
  else startMusic({ userInitiated: true });
});
menuActionsToggle.addEventListener("click", () => {
  const collapsed = !menuActionsCollapsed();
  setMenuActionsCollapsed(collapsed, { persist: true });
  if (gameStarted) {
    saveActiveGameState("ui_menu");
  }
});
hudSaveGameButton.addEventListener("click", saveGameFromHud);
hudLoadGameButton.addEventListener("click", loadGameFromHud);
exitGameButton.addEventListener("click", exitToTitle);

startGameButton.addEventListener("click", openLoadGameScreen);
settingsGameButton.addEventListener("click", () => {
  if (!isLoggedIn()) {
    openNewGameSetup();
    return;
  }
  openSettingsMenu();
});
loginGameButton.addEventListener("click", () => {
  if (isLoggedIn()) {
    logoutUser();
    return;
  }
  openLoginScreen();
});
progressGameButton.addEventListener("click", continueGame);
cancelLoadGameButton.addEventListener("click", closeLoadGameScreen);
createGameFromLoadButton.addEventListener("click", createGameFromLoadScreen);
newGameForm.addEventListener("submit", createNewGame);
cancelNewGameButton.addEventListener("click", closeNewGameSetup);
previousProloguePageButton.addEventListener("click", previousProloguePage);
nextProloguePageButton.addEventListener("click", nextProloguePage);
beginPrologueGameButton.addEventListener("click", beginPrologueGame);
loginForm.addEventListener("submit", loginExistingUser);
cancelLoginButton.addEventListener("click", closeLoginScreen);

async function bootGame() {
  const storedScreen = localStorage.getItem("mmmScreen");
  setMenuActionsCollapsed(loadMenuActionsSetting());
  renderInventory();
  await refreshSessionState();
  loadSoundSetting();
  setMenuActionsCollapsed(loadMenuActionsSetting());
  if (gameStarted && !isLoggedIn()) {
    gameStarted = false;
    localStorage.setItem("mmmScreen", "title");
    showIntroStatus("Login or create a new game first.");
  } else if (gameStarted) {
    await loadActiveGameState();
  }
  syncIntroVisibility();
  if (!gameStarted && storedScreen === "prologue" && isLoggedIn()) {
    openPrologueScreen();
  }
  resize();
  requestAnimationFrame(frame);
}

bootGame();
