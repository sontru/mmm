import html
import json
from collections import Counter

from .database import connect, now_seconds
from .game_design import design_payload


def admin_summary():
    """Collect player, event, presence, and design data for the dashboard."""
    with connect() as connection:
        player_count = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        active_sessions = connection.execute(
            "SELECT COUNT(*) AS total FROM sessions WHERE expires_at > strftime('%s', 'now')"
        ).fetchone()["total"]
        save_count = connection.execute("SELECT COUNT(*) AS total FROM player_state").fetchone()["total"]
        event_rows = connection.execute(
            """
            SELECT event_type, COUNT(*) AS total
            FROM game_events
            GROUP BY event_type
            ORDER BY total DESC, event_type ASC
            LIMIT 12
            """
        ).fetchall()
        recent_players = connection.execute(
            """
            SELECT users.name, users.created_at, users.updated_at, player_state.updated_at AS saved_at
            FROM users
            LEFT JOIN player_state ON player_state.user_id = users.id
            ORDER BY COALESCE(player_state.updated_at, users.updated_at) DESC
            LIMIT 12
            """
        ).fetchall()
        recent_events = connection.execute(
            """
            SELECT users.name, game_events.event_type, game_events.payload_json, game_events.created_at
            FROM game_events
            LEFT JOIN users ON users.id = game_events.user_id
            ORDER BY game_events.id DESC
            LIMIT 20
            """
        ).fetchall()
        online_rows = connection.execute(
            """
            SELECT users.id, users.name, player_presence.x, player_presence.y,
                   player_presence.tile_x, player_presence.tile_y,
                   player_presence.last_event, player_presence.last_seen,
                   player_state.save_json
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            LEFT JOIN player_presence ON player_presence.user_id = users.id
            LEFT JOIN player_state ON player_state.user_id = users.id
            WHERE sessions.expires_at > strftime('%s', 'now')
            GROUP BY users.id
            ORDER BY COALESCE(player_presence.last_seen, sessions.created_at) DESC
            """
        ).fetchall()

    design = design_payload()
    events = [{"type": row["event_type"], "total": row["total"]} for row in event_rows]
    return {
        "players": player_count,
        "activeSessions": active_sessions,
        "saves": save_count,
        "events": events,
        "eventTotals": dict(Counter({event["type"]: event["total"] for event in events})),
        "recentPlayers": [dict(row) for row in recent_players],
        "onlinePlayers": [_online_player(row) for row in online_rows],
        "recentEvents": [
            {
                "player": row["name"] or "anonymous",
                "type": row["event_type"],
                "payload": _safe_json(row["payload_json"]),
                "createdAt": row["created_at"],
            }
            for row in recent_events
        ],
        "design": design,
    }


def admin_page():
    """Render the local admin dashboard HTML."""
    summary = admin_summary()
    initial_summary = html.escape(json.dumps(summary), quote=False)
    events_rows = "".join(
        f"<tr><td>{html.escape(event['type'])}</td><td>{event['total']}</td></tr>"
        for event in summary["events"]
    ) or "<tr><td colspan='2'>No events yet</td></tr>"
    player_rows = "".join(
        f"<tr><td>{html.escape(row['name'])}</td><td>{row['saved_at'] or '-'}</td></tr>"
        for row in summary["recentPlayers"]
    ) or "<tr><td colspan='2'>No players yet</td></tr>"

    page = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MMM Game Map</title>
  <style>
    /* Page shell */
    body { margin: 0; font: 15px/1.45 system-ui, sans-serif; background: #101416; color: #edf0e8; }
    main { width: min(1800px, calc(100% - 32px)); margin: 20px auto 48px; }
    h1, h2 { margin: 0 0 12px; }
    h1 { font-size: 24px; }
    h2 { font-size: 15px; color: #cfd8cd; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }
    .panel { border: 1px solid #344148; border-radius: 8px; padding: 14px; background: #182023; }
    .metric { font-size: 32px; font-weight: 800; }

    /* Live map and map editing controls */
    .map-panel { margin-top: 12px; padding: 0; overflow: hidden; }
    .map-toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-start; gap: 10px 18px; padding: 12px 14px; border-bottom: 1px solid #344148; }
    .map-toolbar h2 { flex: 0 0 auto; margin-bottom: 0; }
    .legend { flex: 1 1 720px; display: flex; flex-wrap: wrap; align-items: center; gap: 10px; color: #b9c4bd; font-size: 13px; }
    .legend span { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
    .legend label { white-space: nowrap; }
    #mapCoords { flex: 0 0 330px; justify-content: flex-end; overflow: hidden; text-align: right; text-overflow: ellipsis; font-variant-numeric: tabular-nums; }
    .swatch { width: 13px; height: 13px; border: 1px solid rgba(255,255,255,.22); }
    .map-layers { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; padding: 10px 14px; border-bottom: 1px solid #344148; color: #cfd8cd; font-size: 13px; }
    .map-layers strong { color: #edf0e8; }
    .map-layers label { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
    .map-layers input { accent-color: #d8e7b5; }
    .edit-panel { margin-top: 12px; }
    .edit-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
    .edit-toolbar button { padding: 8px 12px; border: 1px solid #58676c; border-radius: 6px; background: #d8e7b5; color: #11181b; font-weight: 800; cursor: pointer; }
    .edit-toolbar button.secondary { background: #11181b; color: #edf0e8; }
    .edit-toolbar button:disabled { opacity: .55; cursor: wait; }
    .edit-toolbar select { min-width: 160px; padding: 7px 8px; border: 1px solid #425157; border-radius: 6px; background: #0b1114; color: #edf0e8; }
    .edit-toolbar label { color: #cfd8cd; font-size: 13px; font-weight: 700; }
    #editStatus, #selectionCount { color: #b9c4bd; font-size: 13px; }
    body.map-editing #adminMap { cursor: crosshair; }
    .map-scroll { overflow: auto; max-height: 72vh; background: #0b1114; }
    #adminMap { display: block; image-rendering: crisp-edges; }

    .admin-nav { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
    .nav-button { display: inline-flex; align-items: center; justify-content: center; padding: 10px 14px; border-radius: 8px; border: 1px solid #425157; background: #182023; color: #edf0e8; text-decoration: none; font-weight: 700; }
    .nav-button:hover { background: #213034; }

    /* Shared content tables */
    table { width: 100%; border-collapse: collapse; }
    td, th { padding: 7px 8px; border-bottom: 1px solid #344148; text-align: left; }
    code, pre { color: #d8e7b5; }
    pre { overflow: auto; max-height: 300px; }
    ul { margin: 0; padding-left: 20px; }
  </style>
</head>
<body>
  <main>
    <div class="admin-nav">
      <a class="nav-button" href="/admin">Game Map</a>
      <a class="nav-button" href="/admin/rooms">Rooms</a>
      <a class="nav-button" href="/admin/assets">Assets & Code</a>
    </div>
    <h1>Game Map</h1>
    <section class="panel edit-panel">
      <h2>Map Edit</h2>
      <div class="edit-toolbar">
        <button id="editModeToggle" type="button">Enter Edit Mode</button>
        <label for="tilePaintSelect">Texture</label>
        <select id="tilePaintSelect"></select>
        <button id="applyTilePaint" class="secondary" type="button" disabled>Reassign Selection</button>
        <label for="blockingSelect">Blocking</label>
        <select id="blockingSelect">
          <option value="default">Texture Default</option>
          <option value="blocked">Blocking</option>
          <option value="open">Non-blocking</option>
        </select>
        <button id="applyBlocking" class="secondary" type="button" disabled>Apply Blocking</button>
        <button id="clearSelection" class="secondary" type="button" disabled>Clear Selection</button>
        <span id="selectionCount">0 selected</span>
        <span id="editStatus">Click a square in edit mode. Hold Shift to add more.</span>
      </div>
    </section>
    <section class="panel map-panel">
      <div class="map-toolbar">
        <h2>Live Map</h2>
        <div class="legend">
          <span><i class="swatch" style="background:#172c45"></i>Water</span>
          <span><i class="swatch" style="background:#6f6555"></i>Sand</span>
          <span><i class="swatch" style="background:#263925"></i>Grass</span>
          <span><i class="swatch" style="background:#1d2d22"></i>Forest</span>
          <span><i class="swatch" style="background:#2d2d34"></i>Rock</span>
          <span><i class="swatch" style="background:#746d57"></i>Beach</span>
          <span><i class="swatch" style="background:#f0d36b"></i>Online player</span>
          <span id="mapCoords">Tile -, - · Pixel -, -</span>
        </div>
      </div>
      <div class="map-layers" id="mapLayerToggles">
        <strong>Layers</strong>
        <label><input type="checkbox" data-layer="grid" checked>Grid</label>
        <label><input type="checkbox" data-layer="zones" checked>Zones</label>
        <label><input type="checkbox" data-layer="buildings" checked>Buildings</label>
        <label><input type="checkbox" data-layer="landmarks" checked>Landmarks</label>
        <label><input type="checkbox" data-layer="entrances" checked>Entrances</label>
        <label><input type="checkbox" data-layer="blocking" checked>Blocking</label>
        <label><input type="checkbox" data-layer="start" checked>Start</label>
        <label><input type="checkbox" data-layer="selection" checked>Selection</label>
        <label><input type="checkbox" data-layer="hover" checked>Hover</label>
        <label><input type="checkbox" data-layer="players" checked>Players</label>
      </div>
      <div class="map-scroll">
        <canvas id="adminMap" aria-label="Live game map"></canvas>
      </div>
    </section>
    <section class="grid" style="margin-top: 12px;">
      <div class="panel"><h2>Event Totals</h2><table><tbody id="eventTotals">__EVENT_ROWS__</tbody></table></div>
      <div class="panel"><h2>Recent Players</h2><table><tbody id="recentPlayers">__PLAYER_ROWS__</tbody></table></div>
    </section>
    <section class="grid" style="margin-top: 12px;">
      <div class="panel"><h2>Players</h2><div class="metric" id="playerCount">__PLAYER_COUNT__</div></div>
      <div class="panel"><h2>Active Sessions</h2><div class="metric" id="sessionCount">__SESSION_COUNT__</div></div>
      <div class="panel"><h2>Saved Games</h2><div class="metric" id="saveCount">__SAVE_COUNT__</div></div>
      <div class="panel"><h2>Online On Map</h2><div class="metric" id="onlineCount">__ONLINE_COUNT__</div></div>
    </section>
  </main>
  <script id="initialSummary" type="application/json">__INITIAL_SUMMARY__</script>
  <script>
    // ---------------------------------------------------------------------
    // DOM references and shared admin state
    // ---------------------------------------------------------------------

    const canvas = document.getElementById("adminMap");
    const ctx = canvas.getContext("2d");
    const mapCoords = document.getElementById("mapCoords");
    const mapScroll = document.querySelector(".map-scroll");
    const mapLayerToggles = document.getElementById("mapLayerToggles");
    const editModeToggle = document.getElementById("editModeToggle");
    const tilePaintSelect = document.getElementById("tilePaintSelect");
    const applyTilePaint = document.getElementById("applyTilePaint");
    const blockingSelect = document.getElementById("blockingSelect");
    const applyBlocking = document.getElementById("applyBlocking");
    const clearSelection = document.getElementById("clearSelection");
    const selectionCount = document.getElementById("selectionCount");
    const editStatus = document.getElementById("editStatus");
    let summary = JSON.parse(document.getElementById("initialSummary").textContent);
    let players = new Map();
    let hoverTile = null;
    let tileImages = new Map();
    let editMode = false;
    let editDirty = false;
    let savingEdits = false;
    let selectedTiles = new Set();
    let liveMapCentered = false;
    const mapLayers = {
      grid: true,
      zones: true,
      buildings: true,
      landmarks: true,
      entrances: true,
      blocking: true,
      start: true,
      selection: true,
      hover: true,
      players: true,
    };

    // ---------------------------------------------------------------------
    // Live summary refresh
    // ---------------------------------------------------------------------

    function applySummary(next) {
      summary = next;
      document.getElementById("playerCount").textContent = next.players;
      document.getElementById("sessionCount").textContent = next.activeSessions;
      document.getElementById("saveCount").textContent = next.saves;
      document.getElementById("onlineCount").textContent = next.onlinePlayers.length;

      const seen = new Set();
      for (const player of next.onlinePlayers) {
        seen.add(player.name);
        const existing = players.get(player.name);
        const target = { x: player.position.x, y: player.position.y };
        if (existing) {
          existing.target = target;
          existing.tile = player.position.tileX + "," + player.position.tileY;
          existing.lastEvent = player.lastEvent;
          existing.lastSeen = player.lastSeen;
        } else {
          players.set(player.name, {
            name: player.name,
            x: target.x,
            y: target.y,
            target,
            tile: player.position.tileX + "," + player.position.tileY,
            lastEvent: player.lastEvent,
            lastSeen: player.lastSeen,
          });
        }
      }
      for (const name of players.keys()) {
        if (!seen.has(name)) players.delete(name);
      }
      renderTilePaintOptions();
      loadTileImages(next.design.tileOptions || []);
      updateEditControls();
    }

    async function refresh() {
      try {
        const response = await fetch("/api/admin/summary", { credentials: "same-origin" });
        const data = await response.json();
        if (data.ok) {
          const nextSummary = (editMode || editDirty)
            ? {
                ...data.summary,
                design: {
                  ...data.summary.design,
                  grid: summary.design.grid,
                  tileOverrides: summary.design.tileOverrides,
                  blockingOverrides: summary.design.blockingOverrides,
                },
              }
            : data.summary;
          applySummary(nextSummary);
        }
      } catch (error) {
        console.warn("Could not refresh admin map.", error);
      }
      window.setTimeout(refresh, 2000);
    }

    function draw() {
      const design = summary.design;
      const map = design.map;
      const scale = map.adminScale;
      const tile = map.adminTileSize;
      if (canvas.width !== map.adminPixelWidth || canvas.height !== map.adminPixelHeight) {
        canvas.width = map.adminPixelWidth;
        canvas.height = map.adminPixelHeight;
      }
      if (!liveMapCentered) {
        liveMapCentered = true;
        requestAnimationFrame(centerLiveMap);
      }

      for (let y = 0; y < map.height; y += 1) {
        for (let x = 0; x < map.width; x += 1) {
          const tileKind = design.grid[y][x];
          const texture = tileImages.get(String(tileKind));
          if (texture && texture.complete && texture.naturalWidth > 0) {
            ctx.drawImage(texture, x * tile, y * tile, tile, tile);
          } else {
            ctx.fillStyle = design.tileColors[tileKind];
            ctx.fillRect(x * tile, y * tile, tile, tile);
          }
        }
      }
      if (mapLayers.grid) drawGrid(tile, map.width, map.height);
      if (mapLayers.zones) drawZones(design.zones || [], tile);
      if (mapLayers.buildings) drawBuildings(design.buildings, tile);
      if (mapLayers.landmarks) drawLandmarks(design.landmarks || [], tile);
      if (mapLayers.entrances) drawCaveEntrances(design.caveEntrances || [], tile);
      if (mapLayers.start) drawStartMarker(design.start, tile);
      if (mapLayers.blocking) drawBlockingOverrides(tile);
      if (mapLayers.selection) drawSelectedTiles(tile);
      if (mapLayers.hover) drawHoverTile(tile);
      if (mapLayers.players) drawPlayers(scale);
      requestAnimationFrame(draw);
    }

    function centerLiveMap() {
      requestAnimationFrame(() => {
        mapScroll.scrollLeft = Math.max(0, (mapScroll.scrollWidth - mapScroll.clientWidth) / 2);
        mapScroll.scrollTop = Math.max(0, (mapScroll.scrollHeight - mapScroll.clientHeight) / 2);
      });
    }

    // ---------------------------------------------------------------------
    // Map rendering layers
    // ---------------------------------------------------------------------

    function drawGrid(tile, width, height) {
      ctx.strokeStyle = "rgba(255,255,255,0.035)";
      ctx.lineWidth = 1;
      for (let x = 0; x <= width; x += 1) {
        ctx.beginPath();
        ctx.moveTo(x * tile + 0.5, 0);
        ctx.lineTo(x * tile + 0.5, height * tile);
        ctx.stroke();
      }
      for (let y = 0; y <= height; y += 1) {
        ctx.beginPath();
        ctx.moveTo(0, y * tile + 0.5);
        ctx.lineTo(width * tile, y * tile + 0.5);
        ctx.stroke();
      }
    }

    function drawBuildings(buildings, tile) {
      ctx.textBaseline = "top";
      for (const building of buildings) {
        const x = building.x * tile;
        const y = building.y * tile;
        const w = building.w * tile;
        const h = building.h * tile;
        if (building.kind === "ship") {
          drawShipBuilding(building, x, y, w, h, tile);
          continue;
        }
        if (building.kind === "lighthouse") {
          drawLighthouseBuilding(building, x, y, w, h, tile);
          continue;
        }
        ctx.fillStyle = building.kind === "monastery" ? "rgba(32, 28, 34, 0.86)" : "rgba(61, 54, 64, 0.88)";
        ctx.fillRect(x, y, w, h);
        ctx.strokeStyle = "#e2c66e";
        ctx.lineWidth = building.kind === "monastery" ? 2 : 1;
        ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
        ctx.fillStyle = "#fff4c5";
        ctx.font = building.kind === "monastery" ? "700 13px system-ui" : "700 11px system-ui";
        ctx.fillText(building.name, x + 5, y + 5);
        ctx.font = "10px system-ui";
        ctx.fillStyle = "#9dd8d1";
        for (const entrance of building.entrances || []) {
          const ex = x + entrance.x * tile + tile / 2;
          const ey = y + entrance.y * tile + tile / 2;
          ctx.beginPath();
          ctx.arc(ex, ey, 4, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillText(entrance.name, ex + 6, ey - 5);
        }
      }
    }

    function drawLighthouseBuilding(building, x, y, w, h, tile) {
      const centerX = x + w / 2;
      const topY = y - tile * 0.45;
      const baseY = y + h;
      ctx.fillStyle = "rgba(7, 11, 15, 0.48)";
      ctx.beginPath();
      ctx.ellipse(centerX, baseY - 4, w * 0.42, 8, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#302c32";
      ctx.beginPath();
      ctx.moveTo(x + 8, baseY - 4);
      ctx.lineTo(x + 15, y + 18);
      ctx.lineTo(centerX - 9, topY + 20);
      ctx.lineTo(centerX + 9, topY + 20);
      ctx.lineTo(x + w - 15, y + 18);
      ctx.lineTo(x + w - 8, baseY - 4);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "#5e5860";
      ctx.beginPath();
      ctx.moveTo(x + 16, baseY - 5);
      ctx.lineTo(x + 20, y + 20);
      ctx.lineTo(centerX - 6, topY + 22);
      ctx.lineTo(centerX + 6, topY + 22);
      ctx.lineTo(x + w - 20, y + 20);
      ctx.lineTo(x + w - 16, baseY - 5);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "rgba(27, 24, 29, 0.72)";
      ctx.lineWidth = 1;
      for (let band = 0; band < 3; band += 1) {
        const bandY = y + 12 + band * 13;
        ctx.beginPath();
        ctx.moveTo(x + 17 - band, bandY);
        ctx.lineTo(x + w - 17 + band, bandY);
        ctx.stroke();
      }
      ctx.fillStyle = "#18141b";
      ctx.fillRect(centerX - 12, topY + 12, 24, 10);
      ctx.fillStyle = "#f0d36b";
      ctx.fillRect(centerX - 8, topY + 14, 16, 6);
      ctx.fillStyle = "rgba(240, 211, 107, 0.24)";
      ctx.beginPath();
      ctx.moveTo(centerX + 8, topY + 17);
      ctx.lineTo(centerX + tile, topY + 7);
      ctx.lineTo(centerX + tile, topY + 27);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "#211820";
      ctx.beginPath();
      ctx.moveTo(centerX - 15, topY + 12);
      ctx.lineTo(centerX, topY - 2);
      ctx.lineTo(centerX + 15, topY + 12);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "#111014";
      ctx.fillRect(x + 7, y + h - 18, 12, 18);
      ctx.fillStyle = "rgba(9, 14, 10, 0.82)";
      ctx.fillRect(x + 2, y + 2, 92, 16);
      ctx.fillStyle = "#fff4c5";
      ctx.font = "700 10px system-ui";
      ctx.fillText(building.name + " · " + building.x + "," + building.y, x + 5, y + 5);
    }

    function drawShipBuilding(building, x, y, w, h, tile) {
      const baseX = x;
      const baseY = y;
      x = baseX + w * 0.15;
      y = baseY + h * 0.1;
      w *= 0.7;
      h *= 0.72;
      ctx.fillStyle = "rgba(7, 11, 15, 0.42)";
      ctx.beginPath();
      ctx.ellipse(x + w / 2, y + h * 0.78, w * 0.43, h * 0.14, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#68462f";
      ctx.beginPath();
      ctx.moveTo(x + 10, y + h * 0.42);
      ctx.lineTo(x + w - 3, y + h * 0.57);
      ctx.lineTo(x + w - 17, y + h * 0.83);
      ctx.lineTo(x + 10, y + h * 0.78);
      ctx.lineTo(x + 3, y + h * 0.55);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "#e2c66e";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.fillStyle = "#3a2b31";
      ctx.beginPath();
      ctx.moveTo(x + 13, y + h * 0.34);
      ctx.lineTo(x + 34, y + h * 0.38);
      ctx.lineTo(x + 28, y + h * 0.52);
      ctx.lineTo(x + 12, y + h * 0.5);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "#705f68";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x + 15, y + h * 0.38);
      ctx.lineTo(x + 30, y + h * 0.41);
      ctx.stroke();
      ctx.strokeStyle = "#4f3626";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(x + w / 2, y + h * 0.5);
      ctx.lineTo(x + w / 2, y + 5);
      ctx.stroke();
      ctx.strokeStyle = "#201820";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(x + w / 2, y + 8);
      ctx.lineTo(x + w * 0.86, y + h * 0.47);
      ctx.moveTo(x + w / 2, y + 10);
      ctx.lineTo(x + w * 0.7, y + h * 0.5);
      ctx.stroke();
      ctx.fillStyle = "#d8d0b8";
      ctx.beginPath();
      ctx.moveTo(x + w * 0.53, y + 8);
      ctx.lineTo(x + w * 0.56, y + h * 0.48);
      ctx.lineTo(x + w * 0.88, y + h * 0.45);
      ctx.lineTo(x + w * 0.72, y + h * 0.25);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "#b9b09b";
      ctx.beginPath();
      ctx.moveTo(x + w * 0.56, y + 10);
      ctx.lineTo(x + w * 0.62, y + h * 0.46);
      ctx.lineTo(x + w * 0.9, y + h * 0.41);
      ctx.lineTo(x + w * 0.74, y + h * 0.27);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "#7b6c5e";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x + w * 0.58, y + h * 0.24);
      ctx.lineTo(x + w * 0.82, y + h * 0.44);
      ctx.moveTo(x + w * 0.6, y + h * 0.25);
      ctx.lineTo(x + w * 0.86, y + h * 0.39);
      ctx.stroke();
      ctx.fillStyle = "#8b6840";
      for (const entrance of building.entrances || []) {
        const px = baseX + (entrance.x + entrance.w / 2) * tile - 5;
        const py = baseY + entrance.y * tile - 3;
        const pw = 10;
        const ph = tile + 14;
        ctx.fillRect(px, py, pw, ph);
        ctx.strokeStyle = "#3d2a1b";
        ctx.lineWidth = 1;
        ctx.strokeRect(px + 0.5, py + 0.5, pw - 1, ph - 1);
        ctx.strokeStyle = "#5c4329";
        for (let offset = 6; offset < ph; offset += 6) {
          ctx.beginPath();
          ctx.moveTo(px + 2, py + offset);
          ctx.lineTo(px + pw - 2, py + offset);
          ctx.stroke();
        }
        ctx.fillStyle = "#f0d36b";
        ctx.beginPath();
        ctx.arc(px + pw / 2, py + ph / 2, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#fff4c5";
        ctx.font = "10px system-ui";
        ctx.fillText(entrance.name, px + 3, py + ph + 3);
      }
      ctx.fillStyle = "rgba(9, 14, 10, 0.82)";
      ctx.fillRect(x + 3, y + 3, 96, 20);
      ctx.fillStyle = "#fff4c5";
      ctx.font = "700 11px system-ui";
      ctx.fillText(building.name + " · " + building.x + "," + building.y, x + 8, y + 7);
    }

    function drawZones(zones, tile) {
      ctx.textBaseline = "top";
      for (const zone of zones) {
        const x = zone.x1 * tile;
        const y = zone.y1 * tile;
        const w = (zone.x2 - zone.x1 + 1) * tile;
        const h = (zone.y2 - zone.y1 + 1) * tile;

        ctx.fillStyle = "rgba(91, 130, 61, 0.20)";
        ctx.fillRect(x, y, w, h);
        if (Number.isFinite(zone.splitX)) {
          const splitX = (zone.splitX - zone.x1 + 1) * tile;
          ctx.fillStyle = "rgba(123, 93, 50, 0.24)";
          ctx.fillRect(x + splitX, y, w - splitX, h);
        }
        ctx.strokeStyle = "#9fc96f";
        ctx.lineWidth = 2;
        ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
        ctx.strokeStyle = "rgba(255, 244, 197, 0.55)";
        ctx.setLineDash([5, 5]);
        if (Number.isFinite(zone.splitX)) {
          const splitX = (zone.splitX - zone.x1 + 1) * tile;
          ctx.beginPath();
          ctx.moveTo(x + splitX + 0.5, y + 1);
          ctx.lineTo(x + splitX + 0.5, y + h - 1);
          ctx.stroke();
        }
        if (Number.isFinite(zone.pathX)) {
          const pathX = (zone.pathX - zone.x1) * tile;
          ctx.beginPath();
          ctx.moveTo(x + pathX + tile / 2, y + 1);
          ctx.lineTo(x + pathX + tile / 2, y + h - 1);
          ctx.stroke();
        }
        if (Number.isFinite(zone.pathY)) {
          const pathY = (zone.pathY - zone.y1) * tile;
          ctx.beginPath();
          ctx.moveTo(x + 1, y + pathY + tile / 2);
          ctx.lineTo(x + w - 1, y + pathY + tile / 2);
          ctx.stroke();
        }
        ctx.setLineDash([]);

        ctx.fillStyle = "rgba(9, 14, 10, 0.82)";
        ctx.fillRect(x + 5, y + 5, 236, 24);
        ctx.fillStyle = "#ecf4cb";
        ctx.font = "700 12px system-ui";
        ctx.fillText(zone.name + " · " + zone.x1 + "," + zone.y1 + " to " + zone.x2 + "," + zone.y2, x + 12, y + 10);

        for (const part of zone.parts || []) {
          const partX = part.x1 * tile + 6;
          const partY = part.y1 * tile + 34;
          ctx.fillStyle = "rgba(9, 14, 10, 0.62)";
          ctx.fillRect(partX, partY, 112, 20);
          ctx.fillStyle = "#dff0be";
          ctx.font = "11px system-ui";
          ctx.fillText(part.name, partX + 6, partY + 5);
        }
      }
    }

    function drawLandmarks(landmarks, tile) {
      ctx.textBaseline = "top";
      ctx.font = "700 11px system-ui";
      for (const landmark of landmarks) {
        const isRect = Number.isFinite(landmark.x1) && Number.isFinite(landmark.y1) && Number.isFinite(landmark.x2) && Number.isFinite(landmark.y2);
        const label = isRect
          ? landmark.name + " · " + landmark.x1 + "," + landmark.y1 + " to " + landmark.x2 + "," + landmark.y2
          : landmark.name + " · " + landmark.x + "," + landmark.y;

        if (isRect) {
          const x = landmark.x1 * tile;
          const y = landmark.y1 * tile;
          const w = (landmark.x2 - landmark.x1 + 1) * tile;
          const h = (landmark.y2 - landmark.y1 + 1) * tile;
          ctx.fillStyle = "rgba(71, 127, 170, 0.18)";
          ctx.fillRect(x, y, w, h);
          ctx.strokeStyle = "#8fd3ff";
          ctx.lineWidth = 2;
          ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
          drawMapLabel(label, x + 6, y + 6, "#dff4ff", "rgba(7, 18, 28, 0.86)", "rgba(143, 211, 255, 0.72)");
          continue;
        }

        const x = landmark.x * tile;
        const y = landmark.y * tile;
        ctx.fillStyle = "rgba(11, 15, 17, 0.78)";
        ctx.beginPath();
        ctx.arc(x, y, 9, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#f0d36b";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = "#9dd8d1";
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        drawMapLabel(label, x + 12, y - 13, "#fff4c5", "rgba(11, 15, 17, 0.88)", "rgba(240, 211, 107, 0.72)");
      }
    }

    function drawMapLabel(label, x, y, fillColor, backgroundColor, borderColor) {
      const paddingX = 7;
      const labelWidth = ctx.measureText(label).width + paddingX * 2;
      const labelHeight = 24;
      const labelX = Math.max(4, Math.min(x, canvas.width - labelWidth - 4));
      const labelY = Math.max(4, Math.min(y, canvas.height - labelHeight - 4));
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(labelX, labelY, labelWidth, labelHeight);
      ctx.strokeStyle = borderColor;
      ctx.lineWidth = 1;
      ctx.strokeRect(labelX + 0.5, labelY + 0.5, labelWidth - 1, labelHeight - 1);
      ctx.fillStyle = fillColor;
      ctx.fillText(label, labelX + paddingX, labelY + 6);
    }

    function drawCaveEntrances(entrances, tile) {
      ctx.textBaseline = "top";
      for (const entrance of entrances) {
        const w = entrance.w || 1;
        const h = entrance.h || 1;
        const x = (entrance.x - Math.floor(w / 2)) * tile;
        const y = entrance.y * tile;
        const width = w * tile;
        const height = h * tile;
        const label = entrance.name + " · " + entrance.x + "," + entrance.y;

        ctx.fillStyle = "rgba(5, 7, 10, 0.76)";
        ctx.fillRect(x + 3, y + 2, Math.max(12, width - 6), Math.max(22, height - 4));
        ctx.strokeStyle = "#30313a";
        ctx.lineWidth = 2;
        ctx.strokeRect(x + 3.5, y + 2.5, Math.max(11, width - 7), Math.max(21, height - 5));

        ctx.font = "700 11px system-ui";
        const labelWidth = ctx.measureText(label).width + 14;
        const labelX = Math.min(x + width + 6, canvas.width - labelWidth - 4);
        const labelY = Math.max(4, y + height / 2 - 12);
        ctx.fillStyle = "rgba(11, 15, 17, 0.88)";
        ctx.fillRect(labelX, labelY, labelWidth, 24);
        ctx.strokeStyle = "rgba(76, 76, 88, 0.86)";
        ctx.strokeRect(labelX + 0.5, labelY + 0.5, labelWidth - 1, 23);
        ctx.fillStyle = "#fff4c5";
        ctx.fillText(label, labelX + 7, labelY + 6);
      }
    }

    function drawStartMarker(start, tile) {
      if (!start) return;
      const x = start.x * tile + tile / 2;
      const y = start.y * tile + tile / 2;
      ctx.fillStyle = "rgba(11, 15, 17, 0.82)";
      ctx.fillRect(x + 9, y - 12, 124, 24);
      ctx.fillStyle = "#8fd3ff";
      ctx.beginPath();
      ctx.arc(x, y, 7, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#0b0f11";
      ctx.lineWidth = 3;
      ctx.stroke();
      ctx.fillStyle = "#e8f7ff";
      ctx.font = "700 11px system-ui";
      ctx.fillText(start.label + " · " + start.x + "," + start.y, x + 16, y - 3);
    }

    function drawPlayers(scale) {
      ctx.textBaseline = "middle";
      for (const player of players.values()) {
        player.x += (player.target.x - player.x) * 0.12;
        player.y += (player.target.y - player.y) * 0.12;
        const x = player.x * scale;
        const y = player.y * scale;
        ctx.fillStyle = "rgba(8, 10, 12, 0.72)";
        ctx.beginPath();
        ctx.ellipse(x, y + 8, 14, 5, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#f0d36b";
        ctx.strokeStyle = "#111619";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        const label = player.name + " · " + player.tile;
        ctx.font = "700 12px system-ui";
        const labelWidth = ctx.measureText(label).width + 14;
        ctx.fillStyle = "rgba(11, 15, 17, 0.86)";
        ctx.fillRect(x + 11, y - 14, labelWidth, 26);
        ctx.strokeStyle = "rgba(240, 211, 107, 0.72)";
        ctx.strokeRect(x + 11.5, y - 13.5, labelWidth - 1, 25);
        ctx.fillStyle = "#fff4c5";
        ctx.fillText(label, x + 18, y - 1);
      }
    }

    function drawHoverTile(tile) {
      if (!hoverTile) return;
      ctx.fillStyle = "rgba(255, 244, 197, 0.18)";
      ctx.fillRect(hoverTile.x * tile, hoverTile.y * tile, tile, tile);
      ctx.strokeStyle = "#fff4c5";
      ctx.lineWidth = 2;
      ctx.strokeRect(hoverTile.x * tile + 1, hoverTile.y * tile + 1, tile - 2, tile - 2);
    }

    function drawSelectedTiles(tile) {
      if (!selectedTiles.size) return;
      ctx.fillStyle = "rgba(143, 211, 255, 0.22)";
      ctx.strokeStyle = "#8fd3ff";
      ctx.lineWidth = 2;
      for (const key of selectedTiles) {
        const [x, y] = key.split(",").map(Number);
        ctx.fillRect(x * tile, y * tile, tile, tile);
        ctx.strokeRect(x * tile + 1, y * tile + 1, tile - 2, tile - 2);
      }
    }

    function drawBlockingOverrides(tile) {
      const overrides = summary.design.blockingOverrides || {};
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = "700 13px system-ui";
      for (const [key, blocked] of Object.entries(overrides)) {
        const [x, y] = key.split(",").map(Number);
        const px = x * tile;
        const py = y * tile;
        ctx.fillStyle = blocked ? "rgba(196, 64, 64, 0.34)" : "rgba(92, 206, 132, 0.30)";
        ctx.fillRect(px + 2, py + 2, tile - 4, tile - 4);
        ctx.strokeStyle = blocked ? "#ff8c8c" : "#8cffb4";
        ctx.lineWidth = 2;
        ctx.strokeRect(px + 3, py + 3, tile - 6, tile - 6);
        ctx.fillStyle = blocked ? "#ffdede" : "#dcffe8";
        ctx.fillText(blocked ? "B" : "O", px + tile / 2, py + tile / 2);
      }
      ctx.textAlign = "start";
      ctx.textBaseline = "alphabetic";
    }

    // ---------------------------------------------------------------------
    // Map pointer interaction and editing
    // ---------------------------------------------------------------------

    function updateMapCoordinates(event) {
      const design = summary.design;
      const map = design.map;
      const rect = canvas.getBoundingClientRect();
      const canvasX = (event.clientX - rect.left) * (canvas.width / rect.width);
      const canvasY = (event.clientY - rect.top) * (canvas.height / rect.height);
      const worldX = Math.max(0, Math.min(map.pixelWidth - 1, Math.floor(canvasX / map.adminScale)));
      const worldY = Math.max(0, Math.min(map.pixelHeight - 1, Math.floor(canvasY / map.adminScale)));
      const tileX = Math.floor(worldX / map.tileSize);
      const tileY = Math.floor(worldY / map.tileSize);
      hoverTile = { x: tileX, y: tileY };
      mapCoords.textContent = "Tile " + tileX + ", " + tileY + " · Pixel " + worldX + ", " + worldY;
    }

    function tileFromPointer(event) {
      const design = summary.design;
      const map = design.map;
      const rect = canvas.getBoundingClientRect();
      const canvasX = (event.clientX - rect.left) * (canvas.width / rect.width);
      const canvasY = (event.clientY - rect.top) * (canvas.height / rect.height);
      const tileX = Math.floor(canvasX / map.adminTileSize);
      const tileY = Math.floor(canvasY / map.adminTileSize);
      if (tileX < 0 || tileX >= map.width || tileY < 0 || tileY >= map.height) {
        return null;
      }
      return { x: tileX, y: tileY, key: tileX + "," + tileY };
    }

    function renderTilePaintOptions() {
      const design = summary.design;
      const options = design.tileOptions || [];
      const signature = JSON.stringify(options);
      if (tilePaintSelect.dataset.signature === signature) {
        return;
      }
      const current = tilePaintSelect.value;
      tilePaintSelect.dataset.signature = signature;
      tilePaintSelect.innerHTML = "";

      for (const tile of options) {
        const option = document.createElement("option");
        option.value = String(tile.id);
        option.textContent = tile.name;
        tilePaintSelect.appendChild(option);
      }
      if (current) tilePaintSelect.value = current;
    }

    function loadTileImages(options) {
      const nextImages = new Map();
      for (const tile of options) {
        const tileId = String(tile.id);
        const path = tile.asset;
        const existing = tileImages.get(tileId);
        if (existing && existing.getAttribute("data-path") === path) {
          nextImages.set(tileId, existing);
          continue;
        }
        const img = new Image();
        img.setAttribute("data-path", path);
        img.src = path;
        nextImages.set(tileId, img);
      }
      tileImages = nextImages;
    }

    function selectMapTile(event) {
      if (!editMode) return;
      const tile = tileFromPointer(event);
      if (!tile) return;
      event.preventDefault();
      if (!event.shiftKey) {
        selectedTiles.clear();
      }
      if (event.shiftKey && selectedTiles.has(tile.key)) {
        selectedTiles.delete(tile.key);
      } else {
        selectedTiles.add(tile.key);
      }
      updateEditControls();
    }

    function applyPaintToSelection() {
      if (!selectedTiles.size) return;
      const nextTile = Number(tilePaintSelect.value);
      const overrides = { ...(summary.design.tileOverrides || {}) };
      for (const key of selectedTiles) {
        const [x, y] = key.split(",").map(Number);
        summary.design.grid[y][x] = nextTile;
        if (summary.design.baseGrid[y][x] === nextTile) {
          delete overrides[key];
        } else {
          overrides[key] = nextTile;
        }
      }
      summary.design.tileOverrides = overrides;
      editDirty = true;
      editStatus.textContent = "Unsaved map changes.";
      updateEditControls();
    }

    function applyBlockingToSelection() {
      if (!selectedTiles.size) return;
      const mode = blockingSelect.value;
      const overrides = { ...(summary.design.blockingOverrides || {}) };
      for (const key of selectedTiles) {
        if (mode === "default") {
          delete overrides[key];
        } else {
          overrides[key] = mode === "blocked";
        }
      }
      summary.design.blockingOverrides = overrides;
      editDirty = true;
      editStatus.textContent = "Unsaved blocking changes.";
      updateEditControls();
    }

    async function saveMapEdits() {
      if (!editDirty || savingEdits) return true;
      savingEdits = true;
      updateEditControls();
      editStatus.textContent = "Saving map changes...";
      try {
        const response = await fetch("/api/admin/map", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({
            tileOverrides: summary.design.tileOverrides || {},
            blockingOverrides: summary.design.blockingOverrides || {},
          }),
        });
        const data = await response.json();
        if (!data.ok) {
          throw new Error(data.error || "Could not save map changes.");
        }
        applySummary({ ...summary, design: data.design });
        editDirty = false;
        editStatus.textContent = "Map changes saved.";
        return true;
      } catch (error) {
        editStatus.textContent = error.message;
        return false;
      } finally {
        savingEdits = false;
        updateEditControls();
      }
    }

    async function toggleEditMode() {
      if (editMode) {
        const saved = await saveMapEdits();
        if (!saved) return;
        editMode = false;
        selectedTiles.clear();
        document.body.classList.remove("map-editing");
        editStatus.textContent = "Edit mode off.";
      } else {
        editMode = true;
        document.body.classList.add("map-editing");
        editStatus.textContent = "Edit mode on. Click a square; hold Shift to add more.";
      }
      updateEditControls();
    }

    function updateEditControls() {
      editModeToggle.textContent = editMode ? "Leave Edit Mode" : "Enter Edit Mode";
      editModeToggle.disabled = savingEdits;
      applyTilePaint.disabled = !editMode || !selectedTiles.size || savingEdits;
      applyBlocking.disabled = !editMode || !selectedTiles.size || savingEdits;
      clearSelection.disabled = !editMode || !selectedTiles.size || savingEdits;
      selectionCount.textContent = selectedTiles.size + " selected";
    }

    function updateMapLayer(event) {
      const layer = event.target?.dataset?.layer;
      if (!layer || !(layer in mapLayers)) return;
      mapLayers[layer] = event.target.checked;
    }

    // ---------------------------------------------------------------------
    // Event bindings and startup
    // ---------------------------------------------------------------------

    editModeToggle.addEventListener("click", toggleEditMode);
    applyTilePaint.addEventListener("click", applyPaintToSelection);
    applyBlocking.addEventListener("click", applyBlockingToSelection);
    mapLayerToggles.addEventListener("change", updateMapLayer);
    clearSelection.addEventListener("click", () => {
      selectedTiles.clear();
      updateEditControls();
    });
    canvas.addEventListener("click", selectMapTile);
    canvas.addEventListener("mousemove", updateMapCoordinates);
    canvas.addEventListener("mouseleave", () => {
      hoverTile = null;
      mapCoords.textContent = "Tile -, - · Pixel -, -";
    });

    applySummary(summary);
    refresh();
    draw();
  </script>
</body>
</html>"""
    return (
        page.replace("__PLAYER_COUNT__", str(summary["players"]))
        .replace("__SESSION_COUNT__", str(summary["activeSessions"]))
        .replace("__SAVE_COUNT__", str(summary["saves"]))
        .replace("__ONLINE_COUNT__", str(len(summary["onlinePlayers"])))
        .replace("__EVENT_ROWS__", events_rows)
        .replace("__PLAYER_ROWS__", player_rows)
        .replace("__INITIAL_SUMMARY__", initial_summary)
    )


def admin_assets_page():
    """Render the local admin graphics and code editor page."""
    page = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MMM Admin Assets</title>
  <style>
    body { margin: 0; font: 15px/1.45 system-ui, sans-serif; background: #101416; color: #edf0e8; }
    main { width: min(1800px, calc(100% - 32px)); margin: 20px auto 48px; }
    h1, h2 { margin: 0 0 12px; }
    h1 { font-size: 24px; }
    h2 { font-size: 15px; color: #cfd8cd; }
    .admin-nav { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
    .nav-button { display: inline-flex; align-items: center; justify-content: center; padding: 10px 14px; border-radius: 8px; border: 1px solid #425157; background: #182023; color: #edf0e8; text-decoration: none; font-weight: 700; }
    .nav-button:hover { background: #213034; }
    .panel { border: 1px solid #344148; border-radius: 8px; padding: 14px; background: #182023; margin-top: 12px; }
    .asset-toolbar, .code-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 12px; }
    button { padding: 8px 12px; border: 1px solid #58676c; border-radius: 6px; background: #d8e7b5; color: #11181b; font-weight: 800; cursor: pointer; }
    button.secondary { background: #11181b; color: #edf0e8; }
    button:disabled { opacity: .55; cursor: wait; }
    select, input { padding: 7px 8px; border: 1px solid #425157; border-radius: 6px; background: #0b1114; color: #edf0e8; }
    input[type="color"] { width: 42px; height: 34px; padding: 2px; }
    label { color: #cfd8cd; font-size: 13px; font-weight: 700; }
    .asset-workspace { display: grid; grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr); gap: 12px; }
    .asset-stage { min-height: 420px; display: grid; place-items: center; overflow: auto; border: 1px solid #344148; border-radius: 6px; background: #0b1114; }
    #svgEditorSurface { display: grid; place-items: center; min-width: 320px; min-height: 320px; padding: 18px; }
    #svgEditorSurface svg { width: min(420px, 70vw); height: min(420px, 70vw); image-rendering: pixelated; background: rgba(255,255,255,.04); cursor: crosshair; }
    #svgSource { width: 100%; min-height: 420px; box-sizing: border-box; padding: 10px; border: 1px solid #344148; border-radius: 6px; background: #0b1114; color: #d8e7b5; font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; resize: vertical; }
    .code-toolbar select { min-width: min(520px, 100%); }
    .code-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; color: #b9c4bd; font-size: 13px; margin-bottom: 8px; }
    #codeSource { width: 100%; min-height: 620px; box-sizing: border-box; padding: 12px; border: 1px solid #344148; border-radius: 6px; background: #0b1114; color: #e5efd4; font: 13px/1.48 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; resize: vertical; tab-size: 4; }
    #assetStatus, #codeStatus { color: #b9c4bd; font-size: 13px; }
    @media (max-width: 860px) { .asset-workspace { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main>
    <div class="admin-nav">
      <a class="nav-button" href="/admin">Game Map</a>
      <a class="nav-button" href="/admin/rooms">Rooms</a>
      <a class="nav-button" href="/admin/assets">Assets & Code</a>
    </div>
    <h1>Graphics Assets & Code Files</h1>
    <section class="panel asset-editor">
      <h2>Graphics Assets</h2>
      <div class="asset-toolbar">
        <label for="assetSelect">SVG</label>
        <select id="assetSelect"></select>
        <label for="assetTool">Tool</label>
        <select id="assetTool">
          <option value="brush">Brush</option>
          <option value="line">Line</option>
          <option value="rect">Rectangle</option>
          <option value="circle">Circle</option>
          <option value="erase">Erase Last</option>
        </select>
        <label for="assetColor">Color</label>
        <input id="assetColor" type="color" value="#d8e7b5">
        <label for="assetStroke">Size</label>
        <input id="assetStroke" type="number" min="1" max="16" value="3">
        <button id="undoAssetEdit" class="secondary" type="button">Undo</button>
        <button id="applySvgSource" class="secondary" type="button">Apply Source</button>
        <button id="saveAsset" type="button">Save SVG</button>
        <span id="assetStatus">Select an SVG to edit.</span>
      </div>
      <div class="asset-workspace">
        <div class="asset-stage"><div id="svgEditorSurface"></div></div>
        <textarea id="svgSource" spellcheck="false" aria-label="SVG source"></textarea>
      </div>
    </section>
    <section class="panel code-editor">
      <h2>Code Files</h2>
      <div class="code-toolbar">
        <label for="codeFileSelect">File</label>
        <select id="codeFileSelect"></select>
        <button id="reloadCodeFile" class="secondary" type="button">Reload</button>
        <button id="saveCodeFile" type="button">Save File</button>
        <span id="codeStatus">Select a code file to edit.</span>
      </div>
      <div class="code-meta">
        <span id="codeFilePath">No file loaded</span>
        <span id="codeFileLanguage">Language -</span>
        <span id="codeFileSize">0 bytes</span>
      </div>
      <textarea id="codeSource" spellcheck="false" aria-label="Project code file source"></textarea>
    </section>
  </main>
  <script>
    const assetSelect = document.getElementById("assetSelect");
    const assetTool = document.getElementById("assetTool");
    const assetColor = document.getElementById("assetColor");
    const assetStroke = document.getElementById("assetStroke");
    const undoAssetEdit = document.getElementById("undoAssetEdit");
    const applySvgSource = document.getElementById("applySvgSource");
    const saveAsset = document.getElementById("saveAsset");
    const assetStatus = document.getElementById("assetStatus");
    const svgEditorSurface = document.getElementById("svgEditorSurface");
    const svgSource = document.getElementById("svgSource");
    const codeFileSelect = document.getElementById("codeFileSelect");
    const reloadCodeFile = document.getElementById("reloadCodeFile");
    const saveCodeFile = document.getElementById("saveCodeFile");
    const codeStatus = document.getElementById("codeStatus");
    const codeFilePath = document.getElementById("codeFilePath");
    const codeFileLanguage = document.getElementById("codeFileLanguage");
    const codeFileSize = document.getElementById("codeFileSize");
    const codeSource = document.getElementById("codeSource");
    let activeAssetPath = "";
    let assetDirty = false;
    let assetHistory = [];
    let activeDraw = null;
    let activeCodePath = "";
    let codeDirty = false;
    let savingCode = false;

    async function loadAssetList() {
      try {
        const response = await fetch("/api/admin/assets", { credentials: "same-origin" });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || "Could not load assets.");
        assetSelect.innerHTML = "";
        for (const asset of data.assets) {
          const option = document.createElement("option");
          option.value = asset.path;
          option.textContent = asset.name;
          assetSelect.appendChild(option);
        }
        if (data.assets.length) await loadAsset(data.assets[0].path);
      } catch (error) {
        assetStatus.textContent = error.message;
      }
    }

    async function loadAsset(path) {
      if (assetDirty && !window.confirm("Discard unsaved SVG edits?")) {
        assetSelect.value = activeAssetPath;
        return;
      }
      try {
        const response = await fetch("/api/admin/asset?path=" + encodeURIComponent(path), { credentials: "same-origin" });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || "Could not load SVG.");
        activeAssetPath = data.asset.path;
        assetHistory = [];
        setEditorSvg(data.asset.svg, { dirty: false });
        assetStatus.textContent = "Editing " + data.asset.name;
      } catch (error) {
        assetStatus.textContent = error.message;
      }
    }

    function setEditorSvg(svg, { dirty = true } = {}) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(svg, "image/svg+xml");
      if (doc.querySelector("parsererror") || !doc.documentElement || doc.documentElement.localName !== "svg") {
        throw new Error("Invalid SVG source.");
      }
      svgEditorSurface.replaceChildren(document.importNode(doc.documentElement, true));
      svgSource.value = serializeEditorSvg();
      assetDirty = dirty;
      bindSvgDrawing();
    }

    function editorSvg() {
      return svgEditorSurface.querySelector("svg");
    }

    function serializeEditorSvg() {
      const svg = editorSvg();
      return svg ? new XMLSerializer().serializeToString(svg) : "";
    }

    function pushAssetHistory() {
      const svg = serializeEditorSvg();
      if (svg) assetHistory.push(svg);
      if (assetHistory.length > 40) assetHistory.shift();
    }

    function markAssetDirty(message = "Unsaved SVG edits.") {
      svgSource.value = serializeEditorSvg();
      assetDirty = true;
      assetStatus.textContent = message;
    }

    function bindSvgDrawing() {
      const svg = editorSvg();
      if (!svg) return;
      svg.addEventListener("pointerdown", startAssetDraw);
      svg.addEventListener("pointermove", moveAssetDraw);
      svg.addEventListener("pointerup", finishAssetDraw);
      svg.addEventListener("pointercancel", finishAssetDraw);
      svg.addEventListener("pointerleave", finishAssetDraw);
    }

    function svgPoint(event) {
      const svg = editorSvg();
      const point = svg.createSVGPoint();
      point.x = event.clientX;
      point.y = event.clientY;
      const transformed = point.matrixTransform(svg.getScreenCTM().inverse());
      return { x: Math.round(transformed.x * 10) / 10, y: Math.round(transformed.y * 10) / 10 };
    }

    function svgElement(name, attrs) {
      const element = document.createElementNS("http://www.w3.org/2000/svg", name);
      for (const [key, value] of Object.entries(attrs)) {
        element.setAttribute(key, String(value));
      }
      element.setAttribute("data-admin-draw", "true");
      return element;
    }

    function startAssetDraw(event) {
      const svg = editorSvg();
      if (!svg || event.button !== 0) return;
      const tool = assetTool.value;
      if (tool === "erase") {
        eraseLastSvgShape();
        return;
      }
      event.preventDefault();
      pushAssetHistory();
      const start = svgPoint(event);
      const color = assetColor.value;
      const strokeWidth = Number(assetStroke.value) || 3;
      let element;
      if (tool === "brush") {
        element = svgElement("path", { d: "M " + start.x + " " + start.y, fill: "none", stroke: color, "stroke-width": strokeWidth, "stroke-linecap": "round", "stroke-linejoin": "round" });
      } else if (tool === "line") {
        element = svgElement("line", { x1: start.x, y1: start.y, x2: start.x, y2: start.y, stroke: color, "stroke-width": strokeWidth, "stroke-linecap": "round" });
      } else if (tool === "rect") {
        element = svgElement("rect", { x: start.x, y: start.y, width: 0, height: 0, fill: color, opacity: "0.85" });
      } else if (tool === "circle") {
        element = svgElement("circle", { cx: start.x, cy: start.y, r: 0, fill: color, opacity: "0.85" });
      }
      if (!element) return;
      svg.appendChild(element);
      svg.setPointerCapture(event.pointerId);
      activeDraw = { tool, start, element };
    }

    function moveAssetDraw(event) {
      if (!activeDraw) return;
      event.preventDefault();
      const point = svgPoint(event);
      const { tool, start, element } = activeDraw;
      if (tool === "brush") {
        element.setAttribute("d", element.getAttribute("d") + " L " + point.x + " " + point.y);
      } else if (tool === "line") {
        element.setAttribute("x2", point.x);
        element.setAttribute("y2", point.y);
      } else if (tool === "rect") {
        element.setAttribute("x", Math.min(start.x, point.x));
        element.setAttribute("y", Math.min(start.y, point.y));
        element.setAttribute("width", Math.abs(point.x - start.x));
        element.setAttribute("height", Math.abs(point.y - start.y));
      } else if (tool === "circle") {
        element.setAttribute("r", Math.hypot(point.x - start.x, point.y - start.y).toFixed(1));
      }
      markAssetDirty();
    }

    function finishAssetDraw(event) {
      if (!activeDraw) return;
      editorSvg()?.releasePointerCapture?.(event.pointerId);
      activeDraw = null;
      markAssetDirty();
    }

    function eraseLastSvgShape() {
      const svg = editorSvg();
      if (!svg) return;
      const drawable = Array.from(svg.querySelectorAll("[data-admin-draw]"));
      const target = drawable.at(-1) || Array.from(svg.children).at(-1);
      if (!target) return;
      pushAssetHistory();
      target.remove();
      markAssetDirty("Removed last SVG element.");
    }

    function undoSvgEdit() {
      const previous = assetHistory.pop();
      if (!previous) return;
      setEditorSvg(previous, { dirty: true });
      assetStatus.textContent = "Undo applied.";
    }

    function applySvgSourceEdit() {
      try {
        pushAssetHistory();
        setEditorSvg(svgSource.value, { dirty: true });
        assetStatus.textContent = "Source applied.";
      } catch (error) {
        assetStatus.textContent = error.message;
      }
    }

    async function saveCurrentAsset() {
      if (!activeAssetPath) return;
      saveAsset.disabled = true;
      assetStatus.textContent = "Saving SVG...";
      try {
        const response = await fetch("/api/admin/asset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ path: activeAssetPath, svg: serializeEditorSvg() }),
        });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || "Could not save SVG.");
        setEditorSvg(data.asset.svg, { dirty: false });
        assetStatus.textContent = "Saved " + data.asset.name + ". Refresh the game to see asset changes.";
      } catch (error) {
        assetStatus.textContent = error.message;
      } finally {
        saveAsset.disabled = false;
      }
    }

    async function loadCodeFileList() {
      try {
        const response = await fetch("/api/admin/code-files", { credentials: "same-origin" });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || "Could not load code files.");
        codeFileSelect.innerHTML = "";
        for (const file of data.files) {
          const option = document.createElement("option");
          option.value = file.path;
          option.textContent = file.path;
          option.dataset.language = file.language;
          option.dataset.size = String(file.size);
          codeFileSelect.appendChild(option);
        }
        if (data.files.length) {
          await loadCodeFile(data.files[0].path, { confirmDiscard: false });
        } else {
          codeStatus.textContent = "No editable code files found.";
        }
      } catch (error) {
        codeStatus.textContent = error.message;
      }
    }

    async function loadCodeFile(path, { confirmDiscard = true } = {}) {
      if (codeDirty && confirmDiscard && !window.confirm("Discard unsaved code edits?")) {
        codeFileSelect.value = activeCodePath;
        return;
      }
      setCodeSaving(true);
      codeStatus.textContent = "Loading file...";
      try {
        const response = await fetch("/api/admin/code-file?path=" + encodeURIComponent(path), { credentials: "same-origin" });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || "Could not load code file.");
        setCodeEditorFile(data.file, { dirty: false });
        codeStatus.textContent = "Editing " + data.file.path;
      } catch (error) {
        codeStatus.textContent = error.message;
      } finally {
        setCodeSaving(false);
      }
    }

    function setCodeEditorFile(file, { dirty = false } = {}) {
      activeCodePath = file.path;
      codeFileSelect.value = file.path;
      codeSource.value = file.content;
      codeDirty = dirty;
      codeFilePath.textContent = file.path;
      codeFileLanguage.textContent = "Language " + file.language;
      codeFileSize.textContent = new Blob([file.content]).size + " bytes";
      updateCodeControls();
    }

    function markCodeDirty() {
      if (!activeCodePath) return;
      codeDirty = true;
      codeStatus.textContent = "Unsaved code changes.";
      codeFileSize.textContent = new Blob([codeSource.value]).size + " bytes";
      updateCodeControls();
    }

    async function saveCurrentCodeFile() {
      if (!activeCodePath || savingCode) return;
      setCodeSaving(true);
      codeStatus.textContent = "Saving code file...";
      try {
        const response = await fetch("/api/admin/code-file", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ path: activeCodePath, content: codeSource.value }),
        });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || "Could not save code file.");
        setCodeEditorFile(data.file, { dirty: false });
        codeStatus.textContent = "Saved " + data.file.path + ". Restart the server if this file affects server code.";
      } catch (error) {
        codeStatus.textContent = error.message;
      } finally {
        setCodeSaving(false);
      }
    }

    function setCodeSaving(nextSaving) {
      savingCode = nextSaving;
      updateCodeControls();
    }

    function updateCodeControls() {
      const disabled = savingCode || !activeCodePath;
      reloadCodeFile.disabled = disabled;
      saveCodeFile.disabled = disabled || !codeDirty;
      codeSource.disabled = savingCode || !activeCodePath;
      codeFileSelect.disabled = savingCode;
    }

    assetSelect.addEventListener("change", () => loadAsset(assetSelect.value));
    undoAssetEdit.addEventListener("click", undoSvgEdit);
    applySvgSource.addEventListener("click", applySvgSourceEdit);
    saveAsset.addEventListener("click", saveCurrentAsset);
    codeFileSelect.addEventListener("change", () => loadCodeFile(codeFileSelect.value));
    reloadCodeFile.addEventListener("click", () => loadCodeFile(activeCodePath));
    saveCodeFile.addEventListener("click", saveCurrentCodeFile);
    codeSource.addEventListener("input", markCodeDirty);

    loadAssetList();
    loadCodeFileList();
  </script>
</body>
</html>"""
    return page


def admin_rooms_page():
    """Render the local admin room editor page."""
    summary = admin_summary()
    initial_summary = html.escape(json.dumps(summary["design"]), quote=False)
    page = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MMM Admin Rooms</title>
  <style>
    body { margin: 0; font: 15px/1.45 system-ui, sans-serif; background: #101416; color: #edf0e8; }
    main { width: min(1800px, calc(100% - 32px)); margin: 20px auto 48px; }
    h1, h2 { margin: 0 0 12px; }
    h1 { font-size: 24px; }
    .admin-nav { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
    .nav-button { display: inline-flex; align-items: center; justify-content: center; padding: 10px 14px; border-radius: 8px; border: 1px solid #425157; background: #182023; color: #edf0e8; text-decoration: none; font-weight: 700; }
    .nav-button:hover { background: #213034; }
    .panel { border: 1px solid #344148; border-radius: 8px; padding: 16px; background: #182023; }
    .room-page-head { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
    .room-page-head h1 { margin-bottom: 4px; }
    .room-page-head .status { max-width: 720px; }
    .room-shell { display: grid; grid-template-columns: minmax(240px, 300px) minmax(640px, 1fr) minmax(260px, 330px); gap: 12px; align-items: start; }
    .room-side { display: grid; gap: 12px; }
    .map-panel { padding: 0; overflow: hidden; min-height: 620px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    label { display: block; margin-bottom: 4px; color: #cfd8cd; font-size: 13px; font-weight: 700; }
    input, select, textarea { width: 100%; box-sizing: border-box; margin-bottom: 10px; padding: 9px 10px; border: 1px solid #425157; border-radius: 7px; background: #0b1114; color: #edf0e8; }
    textarea { min-height: 300px; font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; resize: vertical; }
    .form-row { margin-bottom: 10px; }
    .button { padding: 10px 16px; border: 1px solid #58676c; border-radius: 8px; background: #d8e7b5; color: #11181b; font-weight: 800; cursor: pointer; }
    .button.full { width: 100%; }
    .button.secondary { background: #11181b; color: #edf0e8; }
    .button:disabled { opacity: .55; cursor: not-allowed; }
    .status { color: #b9c4bd; font-size: 13px; }
    .room-meta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
    .room-meta span { display: block; color: #b9c4bd; font-size: 13px; }
    .room-editor-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px; padding: 12px 14px; border-bottom: 1px solid #344148; }
    .room-editor-toolbar h2 { margin: 0; }
    .room-toolbox { display: grid; gap: 10px; }
    .tool-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .room-toolbox label.inline { display: inline-flex; align-items: center; gap: 7px; margin: 0; }
    .room-toolbox label.inline input { width: auto; margin: 0; }
    .room-canvas-wrapper { overflow: auto; height: min(64vh, 620px); min-height: 420px; background: #0b1114; padding: 22px; display: grid; place-items: center; }
    #roomEditorCanvas { display: block; width: auto; max-width: none; height: auto; background: #11181f; image-rendering: pixelated; border-radius: 6px; cursor: default; touch-action: none; box-shadow: 0 18px 42px rgba(0,0,0,.32); }
    body.room-editing #roomEditorCanvas { cursor: grab; }
    #roomEditorCanvas.dragging { cursor: grabbing; }
    .room-guide, #roomCoords { color: #b9c4bd; font-size: 13px; }
    .room-guide { display: block; flex: 1 1 360px; min-height: 0; }
    #roomCoords { display: block; flex: 0 0 128px; margin-left: auto; padding: 9px 10px; border: 1px solid #344148; border-radius: 7px; background: #11181b; text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
    .json-file-name { display: block; margin: -4px 0 10px; color: #b9c4bd; font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; }

    @media (max-width: 1220px) {
      .room-shell { grid-template-columns: minmax(240px, 320px) minmax(560px, 1fr); }
      .room-tools { grid-column: 1 / -1; }
      .room-toolbox { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); align-items: end; }
    }
    @media (max-width: 840px) {
      .grid, .room-shell { grid-template-columns: 1fr; }
      .room-canvas-wrapper { min-height: 420px; height: 62vh; }
      #roomEditorCanvas { max-width: none; }
    }
  </style>
</head>
<body>
  <main>
    <div class="admin-nav">
      <a class="nav-button" href="/admin">Game Map</a>
      <a class="nav-button" href="/admin/rooms">Rooms</a>
      <a class="nav-button" href="/admin/assets">Assets & Code</a>
    </div>
    <div class="room-page-head">
      <div>
        <h1>Room Editor</h1>
        <span id="roomStatus" class="status">Choose a room to edit.</span>
      </div>
      <div class="room-meta" style="min-width: min(420px, 100%);">
        <button type="button" id="roomEditModeToggle" class="button">Enter Edit Mode</button>
        <button type="button" id="reloadRooms" class="button secondary">Reload Rooms</button>
      </div>
    </div>
    <div class="room-shell">
      <aside class="room-side">
        <section class="panel">
          <h2>Room</h2>
          <div class="form-row">
            <label for="roomSelect">Select a room</label>
            <select id="roomSelect"></select>
          </div>
          <div class="form-row"><label for="roomId">Room ID</label><input id="roomId" readonly></div>
          <div class="form-row"><label for="roomName">Name</label><input id="roomName"></div>
          <div class="form-row"><label for="roomKind">Kind</label><input id="roomKind" readonly></div>
          <div class="room-meta">
            <div><label for="roomWidth">Width</label><input id="roomWidth" type="number" min="1"></div>
            <div><label for="roomHeight">Height</label><input id="roomHeight" type="number" min="1"></div>
            <div><label for="spawnX">Spawn X</label><input id="spawnX" type="number"></div>
            <div><label for="spawnY">Spawn Y</label><input id="spawnY" type="number"></div>
          </div>
        </section>
        <section class="panel">
          <h2>Entrance</h2>
          <div class="form-row"><label for="entranceName">Entrance Name</label><input id="entranceName"></div>
          <div class="room-meta">
            <div><label for="entranceX">X</label><input id="entranceX" type="number"></div>
            <div><label for="entranceY">Y</label><input id="entranceY" type="number"></div>
            <div><label for="entranceW">W</label><input id="entranceW" type="number" min="1"></div>
            <div><label for="entranceH">H</label><input id="entranceH" type="number" min="1"></div>
          </div>
        </section>
      </aside>
      <section class="panel map-panel">
        <div class="room-editor-toolbar">
          <h2>Map</h2>
          <span id="roomGuide" class="room-guide">Click the preview to edit the selected room element.</span>
          <span id="roomCoords">Tile -, -</span>
        </div>
        <div class="room-canvas-wrapper">
          <canvas id="roomEditorCanvas" width="640" height="420" aria-label="Room editor preview"></canvas>
        </div>
      </section>
      <aside class="room-side room-tools">
        <section class="panel room-toolbox">
          <h2>Tools</h2>
          <div>
            <label for="roomTool">Tool</label>
            <select id="roomTool">
              <option value="selectMove">Drag/Move</option>
              <option value="moveSpawn">Move Spawn</option>
              <option value="moveEntrance">Move Entrance</option>
              <option value="resize">Resize Room</option>
              <option value="placeFixture">Place Fixture</option>
              <option value="removeFixture">Remove Fixture</option>
              <option value="blockTile">Block Tile</option>
              <option value="unblockTile">Unblock Tile</option>
            </select>
          </div>
          <div>
            <label for="fixtureKind">Fixture</label>
            <select id="fixtureKind">
              <option value="crate">Crate</option>
              <option value="crate-long">Long Crate</option>
              <option value="crate-stacked">Stacked Crate</option>
              <option value="barrel">Barrel</option>
              <option value="ships-wheel">Ship Wheel</option>
              <option value="ship-sail-rig">Sail Rig</option>
              <option value="table">Table</option>
              <option value="porthole">Porthole</option>
            </select>
          </div>
          <div class="tool-grid">
            <div><label for="fixtureWidth">W</label><input id="fixtureWidth" type="number" min="1" value="2"></div>
            <div><label for="fixtureHeight">H</label><input id="fixtureHeight" type="number" min="1" value="1"></div>
          </div>
          <button type="button" id="centerRoom" class="button secondary full">Center Preview</button>
          <label class="inline"><input id="roomLabelsToggle" type="checkbox" checked>Labels</label>
        </section>
      </aside>
    </div>
    <section class="panel" style="margin-top: 12px;">
      <h2>Raw Room JSON</h2>
      <span id="roomJsonFileName" class="json-file-name">rooms/-.json</span>
      <textarea id="roomJson" spellcheck="false" aria-label="Room JSON"></textarea>
    </section>
  </main>
  <script id="initialSummary" type="application/json">__INITIAL_SUMMARY__</script>
  <script>
    const initialDesign = JSON.parse(document.getElementById("initialSummary").textContent);
    const rooms = initialDesign.rooms || [];
    const roomSelect = document.getElementById("roomSelect");
    const roomId = document.getElementById("roomId");
    const roomName = document.getElementById("roomName");
    const roomKind = document.getElementById("roomKind");
    const roomWidth = document.getElementById("roomWidth");
    const roomHeight = document.getElementById("roomHeight");
    const spawnX = document.getElementById("spawnX");
    const spawnY = document.getElementById("spawnY");
    const entranceName = document.getElementById("entranceName");
    const entranceX = document.getElementById("entranceX");
    const entranceY = document.getElementById("entranceY");
    const entranceW = document.getElementById("entranceW");
    const entranceH = document.getElementById("entranceH");
    const roomJsonFileName = document.getElementById("roomJsonFileName");
    const roomJson = document.getElementById("roomJson");
    const reloadRooms = document.getElementById("reloadRooms");
    const roomEditModeToggle = document.getElementById("roomEditModeToggle");
    const roomStatus = document.getElementById("roomStatus");
    const roomCanvas = document.getElementById("roomEditorCanvas");
    const roomCanvasWrapper = document.querySelector(".room-canvas-wrapper");
    const roomCtx = roomCanvas.getContext("2d");
    const roomTool = document.getElementById("roomTool");
    const fixtureKind = document.getElementById("fixtureKind");
    const fixtureWidth = document.getElementById("fixtureWidth");
    const fixtureHeight = document.getElementById("fixtureHeight");
    const centerRoom = document.getElementById("centerRoom");
    const roomLabelsToggle = document.getElementById("roomLabelsToggle");
    const roomGuide = document.getElementById("roomGuide");
    const roomCoords = document.getElementById("roomCoords");
    let currentRoom = null;
    let roomScale = 36;
    let roomOffset = { x: 0, y: 0 };
    let roomDrag = null;
    let roomEditMode = false;
    let roomDirty = false;
    let savingRoom = false;
    let showRoomLabels = true;
    const fixtureAssets = {
      barrel: "assets/graphics/barrel.svg",
      crate: "assets/graphics/crate.svg",
      "crate-long": "assets/graphics/crate-long.svg",
      "crate-stacked": "assets/graphics/crate-stacked.svg",
      "ship-sail-rig": "assets/graphics/ship-sail-rig.svg",
      "ships-wheel": "assets/graphics/ships-wheel.svg",
    };
    const fixtureImages = Object.fromEntries(Object.entries(fixtureAssets).map(([kind, path]) => {
      const img = new Image();
      img.onload = () => renderRoomEditor();
      img.src = "/" + path;
      return [kind, img];
    }));

    function populateRoomList(preferredRoomId = roomSelect.value) {
      roomSelect.innerHTML = "";
      for (const room of rooms) {
        const option = document.createElement("option");
        option.value = room.id;
        option.textContent = room.name + " (" + room.id + ")";
        roomSelect.appendChild(option);
      }
      if (rooms.length) {
        const selected = rooms.find((room) => room.id === preferredRoomId) || rooms[0];
        roomSelect.value = selected.id;
        setActiveRoom(selected);
      }
    }

    function replaceRooms(nextRooms, preferredRoomId = roomSelect.value) {
      rooms.length = 0;
      rooms.push(...nextRooms);
      populateRoomList(preferredRoomId);
    }

    function setActiveRoom(room) {
      currentRoom = JSON.parse(JSON.stringify(room));
      roomId.value = currentRoom.id || "";
      roomName.value = currentRoom.name || "";
      roomKind.value = currentRoom.kind || "";
      roomWidth.value = currentRoom.width || "";
      roomHeight.value = currentRoom.height || "";
      spawnX.value = currentRoom.spawn?.x ?? "";
      spawnY.value = currentRoom.spawn?.y ?? "";
      entranceName.value = currentRoom.entrance?.name || "";
      entranceX.value = currentRoom.entrance?.x ?? "";
      entranceY.value = currentRoom.entrance?.y ?? "";
      entranceW.value = currentRoom.entrance?.w ?? "";
      entranceH.value = currentRoom.entrance?.h ?? "";
      normalizeBlockedTiles();
      roomJson.value = JSON.stringify(currentRoom, null, 2);
      updateRoomJsonFileName();
      roomStatus.textContent = "Editing room " + currentRoom.id + ".";
      roomOffset = { x: 0, y: 0 };
      roomDirty = false;
      renderRoomEditor();
      requestAnimationFrame(centerRoomPreview);
      updateRoomEditControls();
    }

    function syncFormToRoom({ markDirty = true } = {}) {
      if (!currentRoom) return;
      currentRoom.name = roomName.value;
      currentRoom.width = Math.max(1, Number(roomWidth.value) || 1);
      currentRoom.height = Math.max(1, Number(roomHeight.value) || 1);
      currentRoom.spawn = { x: Number(spawnX.value) || 0, y: Number(spawnY.value) || 0 };
      currentRoom.entrance = {
        ...currentRoom.entrance,
        name: entranceName.value,
        x: Number(entranceX.value) || 0,
        y: Number(entranceY.value) || 0,
        w: Math.max(1, Number(entranceW.value) || 1),
        h: Math.max(1, Number(entranceH.value) || 1),
      };
      normalizeBlockedTiles();
      roomJson.value = JSON.stringify(currentRoom, null, 2);
      if (markDirty) markRoomDirty("Unsaved room changes.");
      renderRoomEditor();
    }

    function markRoomDirty(message = "Unsaved room changes.") {
      roomDirty = true;
      roomStatus.textContent = message;
      updateRoomEditControls();
    }

    function clamp(value, min, max) {
      return Math.max(min, Math.min(max, value));
    }

    function clampRectToRoom(rect) {
      const width = Math.max(1, rect.w || 1);
      const height = Math.max(1, rect.h || 1);
      rect.w = Math.min(width, currentRoom.width);
      rect.h = Math.min(height, currentRoom.height);
      rect.x = clamp(Number(rect.x) || 0, 0, Math.max(0, currentRoom.width - rect.w));
      rect.y = clamp(Number(rect.y) || 0, 0, Math.max(0, currentRoom.height - rect.h));
    }

    function normalizeBlockedTiles() {
      if (!currentRoom) return;
      const blocked = new Set();
      for (const key of currentRoom.blockedTiles || []) {
        const [x, y] = String(key).split(",", 2).map(Number);
        if (Number.isInteger(x) && Number.isInteger(y) && x >= 0 && y >= 0 && x < currentRoom.width && y < currentRoom.height) {
          blocked.add(x + "," + y);
        }
      }
      currentRoom.blockedTiles = Array.from(blocked).sort((a, b) => {
        const [ax, ay] = a.split(",").map(Number);
        const [bx, by] = b.split(",").map(Number);
        return ay - by || ax - bx;
      });
    }

    function setTileBlocked(tile, blocked) {
      if (!currentRoom || !tileInRoom(tile)) return;
      const blockedTiles = new Set(currentRoom.blockedTiles || []);
      const key = tile.x + "," + tile.y;
      if (blocked) {
        blockedTiles.add(key);
      } else {
        blockedTiles.delete(key);
      }
      currentRoom.blockedTiles = Array.from(blockedTiles);
      normalizeBlockedTiles();
      syncRoomJson();
      markRoomDirty((blocked ? "Blocked " : "Unblocked ") + tile.x + "," + tile.y + ".");
      renderRoomEditor();
    }

    function syncRoomJson() {
      roomJson.value = JSON.stringify(currentRoom, null, 2);
      updateRoomJsonFileName();
    }

    function updateRoomJsonFileName() {
      roomJsonFileName.textContent = "rooms/" + (currentRoom?.id || "-") + ".json";
    }

    function renderRoomEditor() {
      if (!currentRoom) return;
      const width = currentRoom.width || 1;
      const height = currentRoom.height || 1;
      const tileSize = Math.max(18, Math.min(36, Math.floor(Math.min(560 / width, 380 / height))));
      roomScale = tileSize;
      roomCanvas.width = width * tileSize + 2;
      roomCanvas.height = height * tileSize + 2;
      roomCtx.clearRect(0, 0, roomCanvas.width, roomCanvas.height);
      roomCtx.fillStyle = "#10181e";
      roomCtx.fillRect(0, 0, roomCanvas.width, roomCanvas.height);

      roomCtx.strokeStyle = "#425157";
      roomCtx.lineWidth = 1;
      for (let x = 0; x <= width; x += 1) {
        roomCtx.beginPath();
        roomCtx.moveTo(x * tileSize + 0.5, 0);
        roomCtx.lineTo(x * tileSize + 0.5, height * tileSize);
        roomCtx.stroke();
      }
      for (let y = 0; y <= height; y += 1) {
        roomCtx.beginPath();
        roomCtx.moveTo(0, y * tileSize + 0.5);
        roomCtx.lineTo(width * tileSize, y * tileSize + 0.5);
        roomCtx.stroke();
      }

      roomCtx.fillStyle = "rgba(57, 105, 156, 0.16)";
      roomCtx.fillRect(0, 0, width * tileSize, height * tileSize);
      roomCtx.strokeStyle = "#d8e7b5";
      roomCtx.lineWidth = 2;
      roomCtx.strokeRect(0.5, 0.5, width * tileSize - 1, height * tileSize - 1);

      const blockedTiles = new Set(currentRoom.blockedTiles || []);
      for (const key of blockedTiles) {
        const [blockedX, blockedY] = key.split(",").map(Number);
        if (blockedX < 0 || blockedY < 0 || blockedX >= width || blockedY >= height) continue;
        const px = blockedX * tileSize;
        const py = blockedY * tileSize;
        roomCtx.fillStyle = "rgba(196, 64, 64, 0.34)";
        roomCtx.fillRect(px + 2, py + 2, tileSize - 4, tileSize - 4);
        roomCtx.strokeStyle = "#ff8c8c";
        roomCtx.lineWidth = 2;
        roomCtx.beginPath();
        roomCtx.moveTo(px + 8, py + 8);
        roomCtx.lineTo(px + tileSize - 8, py + tileSize - 8);
        roomCtx.moveTo(px + tileSize - 8, py + 8);
        roomCtx.lineTo(px + 8, py + tileSize - 8);
        roomCtx.stroke();
      }

      if (currentRoom.entrance) {
        const ex = Math.min(width - 1, Math.max(0, currentRoom.entrance.x));
        const ey = Math.min(height - 1, Math.max(0, currentRoom.entrance.y));
        const ew = Math.max(1, Math.min(width - ex, currentRoom.entrance.w || 1));
        const eh = Math.max(1, Math.min(height - ey, currentRoom.entrance.h || 1));
        roomCtx.fillStyle = "rgba(240, 211, 107, 0.28)";
        roomCtx.fillRect(ex * tileSize + 1, ey * tileSize + 1, ew * tileSize - 2, eh * tileSize - 2);
        roomCtx.strokeStyle = "#f0d36b";
        roomCtx.lineWidth = 2;
        roomCtx.strokeRect(ex * tileSize + 1.5, ey * tileSize + 1.5, ew * tileSize - 3, eh * tileSize - 3);
        roomCtx.fillStyle = "#f0d36b";
        roomCtx.font = "12px system-ui";
        roomCtx.fillText("ENT", ex * tileSize + 6, ey * tileSize + 18);
        if (showRoomLabels) {
          drawRoomEditorLabel(currentRoom.entrance.name || "Entrance", ex * tileSize + 4, ey * tileSize + eh * tileSize + 6, "#fff4c5", "rgba(20, 18, 12, 0.88)", "#f0d36b");
        }
      }

      for (const entrance of currentRoom.entrances || []) {
        const ex = Math.min(width - 1, Math.max(0, entrance.x));
        const ey = Math.min(height - 1, Math.max(0, entrance.y));
        const ew = Math.max(1, Math.min(width - ex, entrance.w || 1));
        const eh = Math.max(1, Math.min(height - ey, entrance.h || 1));
        roomCtx.fillStyle = "rgba(216, 208, 184, 0.22)";
        roomCtx.fillRect(ex * tileSize + 1, ey * tileSize + 1, ew * tileSize - 2, eh * tileSize - 2);
        roomCtx.strokeStyle = "#d8d0b8";
        roomCtx.lineWidth = 2;
        roomCtx.strokeRect(ex * tileSize + 1.5, ey * tileSize + 1.5, ew * tileSize - 3, eh * tileSize - 3);
        roomCtx.fillStyle = "#d8d0b8";
        roomCtx.font = "12px system-ui";
        roomCtx.fillText("DOWN", ex * tileSize + 6, ey * tileSize + 18);
        if (showRoomLabels) {
          drawRoomEditorLabel(entrance.name || "Entrance", ex * tileSize + 4, ey * tileSize + eh * tileSize + 6, "#f7f0d9", "rgba(20, 18, 12, 0.88)", "#d8d0b8");
        }
      }

      if (currentRoom.spawn) {
        const sx = Math.min(width - 1, Math.max(0, currentRoom.spawn.x));
        const sy = Math.min(height - 1, Math.max(0, currentRoom.spawn.y));
        const centerX = sx * tileSize + tileSize / 2;
        const centerY = sy * tileSize + tileSize / 2;
        roomCtx.fillStyle = "#8fd3ff";
        roomCtx.beginPath();
        roomCtx.arc(centerX, centerY, Math.max(6, tileSize * 0.22), 0, Math.PI * 2);
        roomCtx.fill();
        roomCtx.strokeStyle = "#0b1114";
        roomCtx.lineWidth = 2;
        roomCtx.stroke();
        if (showRoomLabels) {
          drawRoomEditorLabel("Spawn", centerX + 8, centerY - 12, "#dff4ff", "rgba(7, 18, 28, 0.88)", "#8fd3ff");
        }
      }

      if (Array.isArray(currentRoom.fixtures)) {
        for (const [index, fixture] of currentRoom.fixtures.entries()) {
          const fx = Math.max(0, Math.min(width - 1, fixture.x || 0));
          const fy = Math.max(0, Math.min(height - 1, fixture.y || 0));
          const fw = Math.max(1, Math.min(width - fx, fixture.w || 1));
          const fh = Math.max(1, Math.min(height - fy, fixture.h || 1));
          const px = fx * tileSize + 2;
          const py = fy * tileSize + 2;
          const pw = fw * tileSize - 4;
          const ph = fh * tileSize - 4;
          roomCtx.fillStyle = "rgba(76, 63, 48, 0.78)";
          roomCtx.fillRect(px, py, pw, ph);
          const fixtureImg = fixtureImages[fixture.kind || ""];
          if (fixtureImg && fixtureImg.complete && fixtureImg.naturalWidth > 0) {
            roomCtx.drawImage(fixtureImg, px, py, pw, ph);
          }
          roomCtx.strokeStyle = "#b9c4bd";
          roomCtx.lineWidth = 1;
          roomCtx.strokeRect(px + 0.5, py + 0.5, pw - 1, ph - 1);
          if (showRoomLabels) {
            drawRoomEditorLabel((fixture.kind || "Fixture") + " " + (index + 1), fx * tileSize + 5, fy * tileSize + 5, "#edf0e8", "rgba(20, 14, 10, 0.88)", "#b9c4bd");
          }
        }
      }

      if (showRoomLabels) {
        for (const key of blockedTiles) {
          const [blockedX, blockedY] = key.split(",").map(Number);
          if (blockedX < 0 || blockedY < 0 || blockedX >= width || blockedY >= height) continue;
          drawRoomEditorLabel("Blocked", blockedX * tileSize + 5, blockedY * tileSize + tileSize - 21, "#ffdede", "rgba(35, 12, 12, 0.88)", "#ff8c8c");
        }
      }
    }

    function drawRoomEditorLabel(label, x, y, fillColor, backgroundColor, borderColor) {
      roomCtx.save();
      roomCtx.font = "700 11px system-ui";
      roomCtx.textBaseline = "top";
      const paddingX = 6;
      const labelWidth = roomCtx.measureText(label).width + paddingX * 2;
      const labelHeight = 20;
      const labelX = Math.max(3, Math.min(x, roomCanvas.width - labelWidth - 3));
      const labelY = Math.max(3, Math.min(y, roomCanvas.height - labelHeight - 3));
      roomCtx.fillStyle = backgroundColor;
      roomCtx.fillRect(labelX, labelY, labelWidth, labelHeight);
      roomCtx.strokeStyle = borderColor;
      roomCtx.lineWidth = 1;
      roomCtx.strokeRect(labelX + 0.5, labelY + 0.5, labelWidth - 1, labelHeight - 1);
      roomCtx.fillStyle = fillColor;
      roomCtx.fillText(label, labelX + paddingX, labelY + 5);
      roomCtx.restore();
    }

    function getRoomTileFromEvent(event) {
      const rect = roomCanvas.getBoundingClientRect();
      const clientX = (event.clientX - rect.left) * (roomCanvas.width / rect.width);
      const clientY = (event.clientY - rect.top) * (roomCanvas.height / rect.height);
      const x = Math.floor(clientX / roomScale);
      const y = Math.floor(clientY / roomScale);
      return { x, y };
    }

    function updateRoomCoordinates(event) {
      if (!currentRoom) return;
      const tile = getRoomTileFromEvent(event);
      if (tileInRoom(tile)) {
        roomCoords.textContent = "Tile " + tile.x + ", " + tile.y;
      } else {
        roomCoords.textContent = "Tile -, -";
      }
    }

    function tileInRoom(tile) {
      return Boolean(tile && tile.x >= 0 && tile.y >= 0 && tile.x < currentRoom.width && tile.y < currentRoom.height);
    }

    function fixtureAtTile(tile) {
      if (!tileInRoom(tile)) return null;
      for (let index = (currentRoom.fixtures || []).length - 1; index >= 0; index -= 1) {
        const fixture = currentRoom.fixtures[index];
        const w = Math.max(1, fixture.w || 1);
        const h = Math.max(1, fixture.h || 1);
        if (tile.x >= fixture.x && tile.y >= fixture.y && tile.x < fixture.x + w && tile.y < fixture.y + h) {
          return { index, fixture };
        }
      }
      return null;
    }

    function rectContainsTile(rect, tile) {
      if (!rect || !tileInRoom(tile)) return false;
      const w = Math.max(1, rect.w || 1);
      const h = Math.max(1, rect.h || 1);
      return tile.x >= rect.x && tile.y >= rect.y && tile.x < rect.x + w && tile.y < rect.y + h;
    }

    function syncRoomFormFromCurrent({ markDirty = true } = {}) {
      roomName.value = currentRoom.name || "";
      roomKind.value = currentRoom.kind || "";
      roomWidth.value = currentRoom.width || "";
      roomHeight.value = currentRoom.height || "";
      spawnX.value = currentRoom.spawn?.x ?? "";
      spawnY.value = currentRoom.spawn?.y ?? "";
      entranceName.value = currentRoom.entrance?.name || "";
      entranceX.value = currentRoom.entrance?.x ?? "";
      entranceY.value = currentRoom.entrance?.y ?? "";
      entranceW.value = currentRoom.entrance?.w ?? "";
      entranceH.value = currentRoom.entrance?.h ?? "";
      syncRoomJson();
      if (markDirty) markRoomDirty();
    }

    function moveDragTarget(tile) {
      if (!roomDrag || !tileInRoom(tile)) return;
      if (roomDrag.type === "fixture") {
        const fixture = currentRoom.fixtures[roomDrag.index];
        if (!fixture) return;
        fixture.x = tile.x - roomDrag.offsetX;
        fixture.y = tile.y - roomDrag.offsetY;
        clampRectToRoom(fixture);
        roomStatus.textContent = "Moved " + fixture.kind + " to " + fixture.x + "," + fixture.y + ".";
      } else if (roomDrag.type === "entrance") {
        currentRoom.entrance.x = tile.x - roomDrag.offsetX;
        currentRoom.entrance.y = tile.y - roomDrag.offsetY;
        clampRectToRoom(currentRoom.entrance);
        roomStatus.textContent = "Moved entrance to " + currentRoom.entrance.x + "," + currentRoom.entrance.y + ".";
      } else if (roomDrag.type === "spawn") {
        currentRoom.spawn = { x: tile.x, y: tile.y };
        roomStatus.textContent = "Moved spawn to " + tile.x + "," + tile.y + ".";
      } else if (roomDrag.type === "blockPaint") {
        setTileBlocked(tile, roomDrag.blocked);
        roomStatus.textContent = (roomDrag.blocked ? "Blocked " : "Unblocked ") + tile.x + "," + tile.y + ".";
        return;
      }
      normalizeBlockedTiles();
      syncRoomFormFromCurrent();
      renderRoomEditor();
    }

    function handleRoomPointerDown(event) {
      if (!roomEditMode || !currentRoom || event.button !== 0) return;
      const tile = getRoomTileFromEvent(event);
      if (!tileInRoom(tile)) return;
      event.preventDefault();
      roomCanvas.setPointerCapture(event.pointerId);
      roomCanvas.classList.add("dragging");
      const tool = roomTool.value;

      if (tool === "blockTile" || tool === "unblockTile") {
        roomDrag = { type: "blockPaint", blocked: tool === "blockTile" };
        moveDragTarget(tile);
        return;
      }
      if (tool === "moveSpawn") {
        roomDrag = { type: "spawn" };
        moveDragTarget(tile);
        return;
      }
      if (tool === "moveEntrance" && currentRoom.entrance) {
        roomDrag = {
          type: "entrance",
          offsetX: clamp(tile.x - currentRoom.entrance.x, 0, Math.max(0, (currentRoom.entrance.w || 1) - 1)),
          offsetY: clamp(tile.y - currentRoom.entrance.y, 0, Math.max(0, (currentRoom.entrance.h || 1) - 1)),
        };
        moveDragTarget(tile);
        return;
      }
      if (tool === "selectMove") {
        const hitFixture = fixtureAtTile(tile);
        if (hitFixture) {
          roomDrag = {
            type: "fixture",
            index: hitFixture.index,
            offsetX: tile.x - hitFixture.fixture.x,
            offsetY: tile.y - hitFixture.fixture.y,
          };
        } else if (rectContainsTile(currentRoom.entrance, tile)) {
          roomDrag = {
            type: "entrance",
            offsetX: tile.x - currentRoom.entrance.x,
            offsetY: tile.y - currentRoom.entrance.y,
          };
        } else if (currentRoom.spawn && currentRoom.spawn.x === tile.x && currentRoom.spawn.y === tile.y) {
          roomDrag = { type: "spawn" };
        }
        if (roomDrag) {
          moveDragTarget(tile);
          return;
        }
      }
      handleRoomClick(event);
    }

    function handleRoomPointerMove(event) {
      updateRoomCoordinates(event);
      if (!roomEditMode || !roomDrag || !currentRoom) return;
      event.preventDefault();
      moveDragTarget(getRoomTileFromEvent(event));
    }

    function finishRoomDrag(event) {
      roomCanvas.classList.remove("dragging");
      if (roomCanvas.hasPointerCapture?.(event.pointerId)) {
        roomCanvas.releasePointerCapture(event.pointerId);
      }
      if (!roomDrag) return;
      roomDrag = null;
    }

    function handleRoomClick(event) {
      if (!currentRoom) return;
      const tile = getRoomTileFromEvent(event);
      if (!tileInRoom(tile)) return;
      if (roomTool.value === "moveSpawn") {
        roomStatus.textContent = "Spawn moved to " + tile.x + "," + tile.y + ".";
        spawnX.value = tile.x;
        spawnY.value = tile.y;
      } else if (roomTool.value === "moveEntrance") {
        roomStatus.textContent = "Entrance moved to " + tile.x + "," + tile.y + ".";
        entranceX.value = tile.x;
        entranceY.value = tile.y;
      } else if (roomTool.value === "resize") {
        roomStatus.textContent = "Room resized to " + (tile.x + 1) + "×" + (tile.y + 1) + ".";
        roomWidth.value = tile.x + 1;
        roomHeight.value = tile.y + 1;
      } else if (roomTool.value === "placeFixture") {
        const kind = fixtureKind.value;
        const width = Math.max(1, Number(fixtureWidth.value) || 1);
        const height = Math.max(1, Number(fixtureHeight.value) || 1);
        const fixture = { kind, x: tile.x, y: tile.y, w: kind === "porthole" ? 1 : width, h: kind === "porthole" ? 1 : height };
        currentRoom.fixtures = currentRoom.fixtures || [];
        currentRoom.fixtures.push(fixture);
        roomStatus.textContent = "Added " + kind + " at " + tile.x + "," + tile.y + ".";
      } else if (roomTool.value === "removeFixture") {
        const before = (currentRoom.fixtures || []).length;
        currentRoom.fixtures = (currentRoom.fixtures || []).filter((fixture) => {
          return !(tile.x >= fixture.x && tile.y >= fixture.y && tile.x < fixture.x + fixture.w && tile.y < fixture.y + fixture.h);
        });
        const removed = before - currentRoom.fixtures.length;
        roomStatus.textContent = removed ? "Removed " + removed + " fixture(s)." : "No fixture found at " + tile.x + "," + tile.y + ".";
      } else if (roomTool.value === "blockTile") {
        setTileBlocked(tile, true);
        roomStatus.textContent = "Blocked " + tile.x + "," + tile.y + ".";
        return;
      } else if (roomTool.value === "unblockTile") {
        setTileBlocked(tile, false);
        roomStatus.textContent = "Unblocked " + tile.x + "," + tile.y + ".";
        return;
      }
      syncFormToRoom();
    }

    function updateRoomGuide() {
      if (roomTool.value === "selectMove") {
        roomGuide.textContent = "Drag the entrance, spawn marker, or a fixture to move it.";
      } else if (roomTool.value === "moveSpawn") {
        roomGuide.textContent = "Click or drag on the room grid to place the player spawn.";
      } else if (roomTool.value === "moveEntrance") {
        roomGuide.textContent = "Click or drag on the room grid to position the entrance.";
      } else if (roomTool.value === "resize") {
        roomGuide.textContent = "Click the room grid to resize the room from the top-left.";
      } else if (roomTool.value === "placeFixture") {
        roomGuide.textContent = "Click the room grid to place a fixture at the selected tile.";
      } else if (roomTool.value === "removeFixture") {
        roomGuide.textContent = "Click a fixture to remove it from the room.";
      } else if (roomTool.value === "blockTile") {
        roomGuide.textContent = "Click or drag across tiles to block movement.";
      } else if (roomTool.value === "unblockTile") {
        roomGuide.textContent = "Click or drag across tiles to unblock movement.";
      }
    }

    function centerRoomPreview() {
      roomCanvasWrapper.scrollLeft = Math.max(0, (roomCanvasWrapper.scrollWidth - roomCanvasWrapper.clientWidth) / 2);
      roomCanvasWrapper.scrollTop = Math.max(0, (roomCanvasWrapper.scrollHeight - roomCanvasWrapper.clientHeight) / 2);
    }

    function syncRoomToForm() {
      try {
        const parsed = JSON.parse(roomJson.value);
        if (parsed.id !== roomId.value) {
          roomStatus.textContent = "Room JSON id must match the selected room.";
          return;
        }
        currentRoom = parsed;
        normalizeBlockedTiles();
        syncRoomFormFromCurrent();
        updateRoomJsonFileName();
        roomStatus.textContent = "Room JSON parsed.";
        renderRoomEditor();
      } catch (error) {
        roomStatus.textContent = "Invalid JSON: " + error.message;
      }
    }

    async function reloadDesign() {
      roomStatus.textContent = "Reloading room list...";
      try {
        const response = await fetch("/api/admin/summary", { credentials: "same-origin" });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || "Could not load summary.");
        const nextRooms = data.summary.design.rooms || [];
        replaceRooms(nextRooms);
        roomStatus.textContent = "Room list reloaded.";
      } catch (error) {
        roomStatus.textContent = error.message;
      }
    }

    async function saveCurrentRoom() {
      if (!currentRoom) return;
      roomStatus.textContent = "Saving room...";
      savingRoom = true;
      updateRoomEditControls();
      try {
        syncFormToRoom({ markDirty: false });
        const response = await fetch("/api/admin/room", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ room: currentRoom }),
        });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || "Could not save room.");
        if (data.design?.rooms) {
          replaceRooms(data.design.rooms, currentRoom.id);
        }
        roomDirty = false;
        roomStatus.textContent = "Saved room " + currentRoom.id + ".";
        return true;
      } catch (error) {
        roomStatus.textContent = error.message;
        return false;
      } finally {
        savingRoom = false;
        updateRoomEditControls();
      }
    }

    async function toggleRoomEditMode() {
      if (roomEditMode) {
        const saved = await saveCurrentRoom();
        if (!saved) return;
        roomEditMode = false;
        roomDrag = null;
        roomCanvas.classList.remove("dragging");
        document.body.classList.remove("room-editing");
        roomStatus.textContent = "Edit mode off.";
      } else {
        roomEditMode = true;
        document.body.classList.add("room-editing");
        roomStatus.textContent = "Edit mode on. Drag objects or paint blocked tiles.";
      }
      updateRoomEditControls();
    }

    function updateRoomEditControls() {
      roomEditModeToggle.textContent = roomEditMode ? "Exit Edit Mode & Save" : "Enter Edit Mode";
      roomEditModeToggle.disabled = savingRoom || !currentRoom;
      roomSelect.disabled = roomEditMode || savingRoom;
      reloadRooms.disabled = roomEditMode || savingRoom;
      roomTool.disabled = !roomEditMode || savingRoom;
      fixtureKind.disabled = !roomEditMode || savingRoom;
      fixtureWidth.disabled = !roomEditMode || savingRoom;
      fixtureHeight.disabled = !roomEditMode || savingRoom;
      centerRoom.disabled = savingRoom;
      roomLabelsToggle.disabled = savingRoom;
      const formDisabled = !roomEditMode || savingRoom;
      roomName.disabled = formDisabled;
      roomWidth.disabled = formDisabled;
      roomHeight.disabled = formDisabled;
      spawnX.disabled = formDisabled;
      spawnY.disabled = formDisabled;
      entranceName.disabled = formDisabled;
      entranceX.disabled = formDisabled;
      entranceY.disabled = formDisabled;
      entranceW.disabled = formDisabled;
      entranceH.disabled = formDisabled;
      roomJson.disabled = formDisabled;
    }

    roomSelect.addEventListener("change", () => {
      const selected = rooms.find((room) => room.id === roomSelect.value);
      if (selected) setActiveRoom(selected);
    });
    reloadRooms.addEventListener("click", reloadDesign);
    roomEditModeToggle.addEventListener("click", toggleRoomEditMode);
    roomName.addEventListener("input", syncFormToRoom);
    roomWidth.addEventListener("input", syncFormToRoom);
    roomHeight.addEventListener("input", syncFormToRoom);
    spawnX.addEventListener("input", syncFormToRoom);
    spawnY.addEventListener("input", syncFormToRoom);
    entranceName.addEventListener("input", syncFormToRoom);
    entranceX.addEventListener("input", syncFormToRoom);
    entranceY.addEventListener("input", syncFormToRoom);
    entranceW.addEventListener("input", syncFormToRoom);
    entranceH.addEventListener("input", syncFormToRoom);
    fixtureKind.addEventListener("change", updateRoomGuide);
    fixtureWidth.addEventListener("input", updateRoomGuide);
    fixtureHeight.addEventListener("input", updateRoomGuide);
    roomLabelsToggle.addEventListener("change", () => {
      showRoomLabels = roomLabelsToggle.checked;
      renderRoomEditor();
    });
    roomTool.addEventListener("change", updateRoomGuide);
    centerRoom.addEventListener("click", centerRoomPreview);
    roomCanvas.addEventListener("pointerdown", handleRoomPointerDown);
    roomCanvas.addEventListener("pointermove", handleRoomPointerMove);
    roomCanvas.addEventListener("pointerup", finishRoomDrag);
    roomCanvas.addEventListener("pointercancel", finishRoomDrag);
    roomCanvas.addEventListener("pointerleave", (event) => {
      roomCoords.textContent = "Tile -, -";
      finishRoomDrag(event);
    });
    roomJson.addEventListener("input", syncRoomToForm);

    updateRoomGuide();
    populateRoomList();
    updateRoomEditControls();
  </script>
</body>
</html>"""
    return page.replace("__INITIAL_SUMMARY__", initial_summary)


def _safe_json(raw):
    """Parse stored JSON data, returning an empty object on invalid input."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _online_player(row):
    """Build a normalized online-player payload for the admin map."""
    save = _safe_json(row["save_json"] or "{}")
    save_position = save.get("position") if isinstance(save, dict) else None
    position = {
        "x": row["x"],
        "y": row["y"],
        "tileX": row["tile_x"],
        "tileY": row["tile_y"],
    }
    if position["x"] is None and isinstance(save_position, dict):
        position = {
            "x": save_position.get("x", 0),
            "y": save_position.get("y", 0),
            "tileX": save_position.get("tileX", 0),
            "tileY": save_position.get("tileY", 0),
        }
    return {
        "id": row["id"],
        "name": row["name"],
        "position": {
            "x": float(position["x"] or 0),
            "y": float(position["y"] or 0),
            "tileX": int(position["tileX"] or 0),
            "tileY": int(position["tileY"] or 0),
        },
        "lastEvent": row["last_event"] or "session",
        "lastSeen": row["last_seen"] or now_seconds(),
    }
