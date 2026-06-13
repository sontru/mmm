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
  <title>MMM Admin</title>
  <style>
    /* Page shell */
    body { margin: 0; font: 15px/1.45 system-ui, sans-serif; background: #101416; color: #edf0e8; }
    main { width: min(1400px, calc(100% - 32px)); margin: 20px auto 48px; }
    h1, h2 { margin: 0 0 12px; }
    h1 { font-size: 24px; }
    h2 { font-size: 15px; color: #cfd8cd; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }
    .panel { border: 1px solid #344148; border-radius: 8px; padding: 14px; background: #182023; }
    .metric { font-size: 32px; font-weight: 800; }

    /* Live map and map editing controls */
    .map-panel { margin-top: 12px; padding: 0; overflow: hidden; }
    .map-toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; padding: 12px 14px; border-bottom: 1px solid #344148; }
    .legend { display: flex; flex-wrap: wrap; gap: 10px; color: #b9c4bd; font-size: 13px; }
    .legend span { display: inline-flex; align-items: center; gap: 5px; }
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

    /* SVG graphics editor */
    .asset-editor { margin-top: 12px; }
    .asset-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 12px; }
    .asset-toolbar button { padding: 8px 12px; border: 1px solid #58676c; border-radius: 6px; background: #d8e7b5; color: #11181b; font-weight: 800; cursor: pointer; }
    .asset-toolbar button.secondary { background: #11181b; color: #edf0e8; }
    .asset-toolbar button:disabled { opacity: .55; cursor: wait; }
    .asset-toolbar select, .asset-toolbar input { padding: 7px 8px; border: 1px solid #425157; border-radius: 6px; background: #0b1114; color: #edf0e8; }
    .asset-toolbar input[type="color"] { width: 42px; height: 34px; padding: 2px; }
    .asset-toolbar label { color: #cfd8cd; font-size: 13px; font-weight: 700; }
    .asset-workspace { display: grid; grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr); gap: 12px; }
    .asset-stage { min-height: 420px; display: grid; place-items: center; overflow: auto; border: 1px solid #344148; border-radius: 6px; background: #0b1114; }
    #svgEditorSurface { display: grid; place-items: center; min-width: 320px; min-height: 320px; padding: 18px; }
    #svgEditorSurface svg { width: min(420px, 70vw); height: min(420px, 70vw); image-rendering: pixelated; background: rgba(255,255,255,.04); cursor: crosshair; }
    #svgSource { width: 100%; min-height: 420px; box-sizing: border-box; padding: 10px; border: 1px solid #344148; border-radius: 6px; background: #0b1114; color: #d8e7b5; font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; resize: vertical; }
    #assetStatus { color: #b9c4bd; font-size: 13px; }
    @media (max-width: 860px) { .asset-workspace { grid-template-columns: 1fr; } }

    /* Project code file editor */
    .code-editor { margin-top: 12px; }
    .code-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 12px; }
    .code-toolbar button { padding: 8px 12px; border: 1px solid #58676c; border-radius: 6px; background: #d8e7b5; color: #11181b; font-weight: 800; cursor: pointer; }
    .code-toolbar button.secondary { background: #11181b; color: #edf0e8; }
    .code-toolbar button:disabled { opacity: .55; cursor: wait; }
    .code-toolbar select { min-width: min(520px, 100%); padding: 7px 8px; border: 1px solid #425157; border-radius: 6px; background: #0b1114; color: #edf0e8; }
    .code-toolbar label { color: #cfd8cd; font-size: 13px; font-weight: 700; }
    .code-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; color: #b9c4bd; font-size: 13px; margin-bottom: 8px; }
    #codeSource { width: 100%; min-height: 620px; box-sizing: border-box; padding: 12px; border: 1px solid #344148; border-radius: 6px; background: #0b1114; color: #e5efd4; font: 13px/1.48 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; resize: vertical; tab-size: 4; }
    #codeStatus { color: #b9c4bd; font-size: 13px; }

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
    <h1>Abbey Island Mystery Admin</h1>
    <section class="grid">
      <div class="panel"><h2>Players</h2><div class="metric" id="playerCount">__PLAYER_COUNT__</div></div>
      <div class="panel"><h2>Active Sessions</h2><div class="metric" id="sessionCount">__SESSION_COUNT__</div></div>
      <div class="panel"><h2>Saved Games</h2><div class="metric" id="saveCount">__SAVE_COUNT__</div></div>
      <div class="panel"><h2>Online On Map</h2><div class="metric" id="onlineCount">__ONLINE_COUNT__</div></div>
    </section>
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
        <h2>Half-Scale Live Map</h2>
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
        <label><input type="checkbox" data-layer="entrances" checked>Entrances</label>
        <label><input type="checkbox" data-layer="blocking" checked>Blocking</label>
        <label><input type="checkbox" data-layer="start" checked>Start</label>
        <label><input type="checkbox" data-layer="selection" checked>Selection</label>
        <label><input type="checkbox" data-layer="hover" checked>Hover</label>
        <label><input type="checkbox" data-layer="players" checked>Players</label>
      </div>
      <div class="map-scroll">
        <canvas id="adminMap" aria-label="Half-scale live game map"></canvas>
      </div>
    </section>
    <section class="grid" style="margin-top: 12px;">
      <div class="panel"><h2>Event Totals</h2><table><tbody id="eventTotals">__EVENT_ROWS__</tbody></table></div>
      <div class="panel"><h2>Recent Players</h2><table><tbody id="recentPlayers">__PLAYER_ROWS__</tbody></table></div>
    </section>
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
  <script id="initialSummary" type="application/json">__INITIAL_SUMMARY__</script>
  <script>
    // ---------------------------------------------------------------------
    // DOM references and shared admin state
    // ---------------------------------------------------------------------

    const canvas = document.getElementById("adminMap");
    const ctx = canvas.getContext("2d");
    const mapCoords = document.getElementById("mapCoords");
    const mapLayerToggles = document.getElementById("mapLayerToggles");
    const editModeToggle = document.getElementById("editModeToggle");
    const tilePaintSelect = document.getElementById("tilePaintSelect");
    const applyTilePaint = document.getElementById("applyTilePaint");
    const blockingSelect = document.getElementById("blockingSelect");
    const applyBlocking = document.getElementById("applyBlocking");
    const clearSelection = document.getElementById("clearSelection");
    const selectionCount = document.getElementById("selectionCount");
    const editStatus = document.getElementById("editStatus");
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
    let summary = JSON.parse(document.getElementById("initialSummary").textContent);
    let players = new Map();
    let hoverTile = null;
    let tileImages = new Map();
    let editMode = false;
    let editDirty = false;
    let savingEdits = false;
    let selectedTiles = new Set();
    let activeAssetPath = "";
    let assetDirty = false;
    let assetHistory = [];
    let activeDraw = null;
    let activeCodePath = "";
    let codeDirty = false;
    let savingCode = false;
    const mapLayers = {
      grid: true,
      zones: true,
      buildings: true,
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
          const nextSummary = (editMode || editDirty) ? { ...data.summary, design: summary.design } : data.summary;
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
      if (mapLayers.entrances) drawCaveEntrances(design.caveEntrances || [], tile);
      if (mapLayers.start) drawStartMarker(design.start, tile);
      if (mapLayers.blocking) drawBlockingOverrides(tile);
      if (mapLayers.selection) drawSelectedTiles(tile);
      if (mapLayers.hover) drawHoverTile(tile);
      if (mapLayers.players) drawPlayers(scale);
      requestAnimationFrame(draw);
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
    // SVG graphics asset editor
    // ---------------------------------------------------------------------

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
        if (data.assets.length) {
          await loadAsset(data.assets[0].path);
        }
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

    // ---------------------------------------------------------------------
    // Project code file editor
    // ---------------------------------------------------------------------

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
    assetSelect.addEventListener("change", () => loadAsset(assetSelect.value));
    undoAssetEdit.addEventListener("click", undoSvgEdit);
    applySvgSource.addEventListener("click", applySvgSourceEdit);
    saveAsset.addEventListener("click", saveCurrentAsset);
    codeFileSelect.addEventListener("change", () => loadCodeFile(codeFileSelect.value));
    reloadCodeFile.addEventListener("click", () => loadCodeFile(activeCodePath));
    saveCodeFile.addEventListener("click", saveCurrentCodeFile);
    codeSource.addEventListener("input", markCodeDirty);

    applySummary(summary);
    loadAssetList();
    loadCodeFileList();
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
