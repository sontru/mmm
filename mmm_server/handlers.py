from http.server import SimpleHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse

from .admin import admin_assets_page, admin_page, admin_rooms_page, admin_summary
from .asset_editor import graphics_assets, read_graphics_asset, save_graphics_asset
from .auth import (
    admin_cookie_header,
    clear_admin_cookie_header,
    clear_cookie_header,
    cookie_header,
    current_admin,
    current_user,
    login_admin,
    login_or_create_player,
    logout,
    logout_admin,
)
from .code_editor import code_files, read_code_file, save_code_file
from .config import ADMIN_USER
from .database import connect, now_seconds
from .design_settings import save_map_overrides, save_room_overrides
from .game_design import design_payload


class GameHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript",
        ".svg": "image/svg+xml",
        ".html": "text/html; charset=utf-8",
    }

    # ------------------------------------------------------------------
    # Common HTTP behavior
    # ------------------------------------------------------------------

    def end_headers(self):
        """Keep dynamic data fresh while allowing static game assets to be reused."""
        path = urlparse(self.path).path
        if path.startswith("/api/") or path.startswith("/admin"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        elif path.startswith("/assets/"):
            self.send_header("Cache-Control", "public, max-age=300, stale-while-revalidate=86400")
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    # ------------------------------------------------------------------
    # Route dispatch
    # ------------------------------------------------------------------

    def do_GET(self):
        """Dispatch supported GET routes or fall back to static file serving."""
        routes = {
            "/api/session": self.handle_session,
            "/api/save": self.handle_get_save,
            "/api/design": self.handle_design,
            "/api/admin/summary": self.handle_admin_summary,
            "/api/admin/assets": self.handle_admin_assets,
            "/api/admin/asset": self.handle_admin_asset,
            "/api/admin/code-files": self.handle_admin_code_files,
            "/api/admin/code-file": self.handle_admin_code_file,
            "/admin": self.handle_admin_page,
            "/admin/": self.handle_admin_page,
            "/admin/rooms": self.handle_admin_rooms_page,
            "/admin/assets": self.handle_admin_assets_page,
        }
        handler = routes.get(self.path.split("?", 1)[0])
        if handler:
            handler()
            return
        super().do_GET()

    def do_POST(self):
        """Dispatch supported POST routes or return a JSON 404 response."""
        routes = {
            "/api/login": self.handle_login,
            "/api/logout": self.handle_logout,
            "/api/admin/login": self.handle_admin_login,
            "/api/admin/logout": self.handle_admin_logout,
            "/api/save": self.handle_save,
            "/api/events": self.handle_event,
            "/api/admin/map": self.handle_admin_map,
            "/api/admin/asset": self.handle_admin_asset_save,
            "/api/admin/code-file": self.handle_admin_code_file_save,
            "/api/admin/room": self.handle_admin_room_save,
        }
        handler = routes.get(self.path.split("?", 1)[0])
        if handler:
            handler()
            return
        self.send_json({"ok": False, "error": "Not found"}, 404)

    # ------------------------------------------------------------------
    # Request and response helpers
    # ------------------------------------------------------------------

    def read_json(self):
        """Read and decode a JSON request body from the client."""
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def send_json(self, payload, status=200, extra_headers=None):
        """Send a JSON response with status and optional extra headers."""
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if extra_headers:
            for name, value in extra_headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, markup, status=200):
        """Send an HTML response with the requested status code."""
        body = markup.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def require_user(self):
        """Return the current player or send a login-required response."""
        user = current_user(self.headers)
        if not user:
            self.send_json({"ok": False, "error": "Login required"}, 401)
            return None
        return user

    # ------------------------------------------------------------------
    # Player session routes
    # ------------------------------------------------------------------

    def handle_session(self):
        """Report whether the current request has a logged-in player."""
        user = current_user(self.headers)
        if not user:
            self.send_json({"ok": True, "loggedIn": False, "user": None})
            return
        self.send_json({"ok": True, "loggedIn": True, "user": {"name": user["name"]}})

    def handle_login(self):
        """Authenticate or create a player and issue a session cookie."""
        payload = self.read_json()
        if payload is None:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return

        name = str(payload.get("name", "")).strip()
        password = str(payload.get("password", ""))
        create_allowed = bool(payload.get("create", False))
        if not name or not password:
            self.send_json({"ok": False, "error": "Name and password are required"}, 400)
            return
        if len(name) > 32 or len(password) > 128:
            self.send_json({"ok": False, "error": "Name or password is too long"}, 400)
            return

        if name == ADMIN_USER:
            self.send_json({"ok": False, "error": "That name is reserved for the separate admin login"}, 403)
            return

        if create_allowed:
            with connect() as connection:
                existing = connection.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
            if existing:
                self.send_json({"ok": False, "error": "Player name already exists. Choose another name."}, 409)
                return

        player, created = login_or_create_player(name, password, create_allowed)
        if not player:
            status = 404 if create_allowed is False else 401
            self.send_json({"ok": False, "error": "Player not found or password did not match"}, status)
            return

        self.track_event(player["id"], "login", {"created": created})
        self.send_json(
            {"ok": True, "created": created, "user": {"name": name}},
            extra_headers={"Set-Cookie": cookie_header(player["token"])},
        )

    def handle_logout(self):
        """Log out the current player and clear the session cookie."""
        user = current_user(self.headers)
        if user:
            self.track_event(user["id"], "logout", {})
        logout(self.headers)
        self.send_json({"ok": True}, extra_headers={"Set-Cookie": clear_cookie_header()})

    def handle_admin_login(self):
        """Authenticate the administrator without creating a game player."""
        payload = self.read_json()
        if payload is None:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return
        name = str(payload.get("name", "")).strip()
        password = str(payload.get("password", ""))
        token = login_admin(name, password)
        if not token:
            self.send_json({"ok": False, "error": "Admin name or password did not match"}, 401)
            return
        self.send_json(
            {"ok": True, "admin": {"name": ADMIN_USER}},
            extra_headers={"Set-Cookie": admin_cookie_header(token)},
        )

    def handle_admin_logout(self):
        """Log out only the dedicated administrator session."""
        logout_admin(self.headers)
        self.send_json({"ok": True}, extra_headers={"Set-Cookie": clear_admin_cookie_header()})

    def handle_get_save(self):
        """Return the logged-in player saved game state."""
        user = self.require_user()
        if not user:
            return
        with connect() as connection:
            row = connection.execute("SELECT save_json, updated_at FROM player_state WHERE user_id = ?", (user["id"],)).fetchone()
        if not row:
            self.send_json({"ok": True, "save": None})
            return
        self.send_json({"ok": True, "save": json.loads(row["save_json"]), "updatedAt": row["updated_at"]})

    def handle_save(self):
        """Persist the logged-in player save data and presence."""
        user = self.require_user()
        if not user:
            return
        payload = self.read_json()
        if payload is None:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return
        save = payload.get("save")
        if not isinstance(save, dict):
            self.send_json({"ok": False, "error": "Save payload is required"}, 400)
            return
        now = now_seconds()
        save_json = json.dumps(save, separators=(",", ":"), sort_keys=True)
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO player_state (user_id, save_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET save_json = excluded.save_json, updated_at = excluded.updated_at
                """,
                (user["id"], save_json, now),
            )
        position = save.get("position", {})
        if isinstance(position, dict):
            self.update_presence(user["id"], position, payload.get("reason", "save"))
        self.track_event(user["id"], "save", {"reason": payload.get("reason", "manual")})
        self.send_json({"ok": True, "updatedAt": now})

    def handle_event(self):
        """Record a browser gameplay event and update presence when relevant."""
        user = current_user(self.headers)
        payload = self.read_json()
        if payload is None:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return
        event_type = str(payload.get("type", "")).strip()[:64]
        event_payload = payload.get("payload", {})
        if not event_type:
            self.send_json({"ok": False, "error": "Event type is required"}, 400)
            return
        clean_payload = event_payload if isinstance(event_payload, dict) else {}
        if user and event_type in {"position", "game_start", "game_exit"}:
            position = clean_payload.get("position") if event_type != "position" else clean_payload
            if isinstance(position, dict):
                self.update_presence(user["id"], position, event_type)
        self.track_event(user["id"] if user else None, event_type, clean_payload)
        self.send_json({"ok": True})

    # ------------------------------------------------------------------
    # Game design and local admin routes
    # ------------------------------------------------------------------

    def handle_design(self):
        """Return the generated game design payload for the browser client."""
        self.send_json({"ok": True, "design": design_payload()})

    def handle_admin_summary(self):
        """Return dashboard summary data to the authorized API user."""
        if not self.is_admin():
            self.send_json({"ok": False, "error": f"Login as {ADMIN_USER} to access the admin dashboard"}, 401)
            return
        self.send_json({"ok": True, "summary": admin_summary()})

    def handle_admin_assets(self):
        """Return editable graphics assets to the local admin interface."""
        if not self.is_admin():
            self.send_json({"ok": False, "error": f"Login as {ADMIN_USER} to access the admin dashboard"}, 401)
            return
        self.send_json({"ok": True, "assets": graphics_assets()})

    def handle_admin_asset(self):
        """Return one SVG asset to the local admin editor."""
        if not self.is_admin():
            self.send_json({"ok": False, "error": f"Login as {ADMIN_USER} to access the admin dashboard"}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        asset_path = params.get("path", [""])[0]
        try:
            asset = read_graphics_asset(asset_path)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, 400)
            return
        self.send_json({"ok": True, "asset": asset})

    def handle_admin_code_files(self):
        """Return editable project code files to the local admin interface."""
        if not self.is_admin():
            self.send_json({"ok": False, "error": f"Login as {ADMIN_USER} to access the admin dashboard"}, 401)
            return
        self.send_json({"ok": True, "files": code_files()})

    def handle_admin_code_file(self):
        """Return one project code file to the local admin editor."""
        if not self.is_admin():
            self.send_json({"ok": False, "error": f"Login as {ADMIN_USER} to access the admin dashboard"}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        file_path = params.get("path", [""])[0]
        try:
            file_data = read_code_file(file_path)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, 400)
            return
        self.send_json({"ok": True, "file": file_data})

    def handle_admin_page(self):
        """Serve the admin dashboard to the authorized API user."""
        if not self.is_admin():
            self.send_html(self.admin_login_page())
            return
        self.send_html(admin_page())

    def handle_admin_map(self):
        """Persist local admin map tile and blocking edits."""
        if not self.is_admin():
            self.send_json({"ok": False, "error": f"Login as {ADMIN_USER} to access the admin dashboard"}, 401)
            return
        payload = self.read_json()
        if payload is None:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return
        overrides = payload.get("tileOverrides")
        if not isinstance(overrides, dict):
            self.send_json({"ok": False, "error": "tileOverrides is required"}, 400)
            return
        blocking_overrides = payload.get("blockingOverrides", None)
        try:
            save_map_overrides(overrides, blocking_overrides)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, 400)
            return
        self.send_json({"ok": True, "design": design_payload()})

    def handle_admin_asset_save(self):
        """Persist an edited SVG asset from the local admin editor."""
        if not self.is_admin():
            self.send_json({"ok": False, "error": f"Login as {ADMIN_USER} to access the admin dashboard"}, 401)
            return
        payload = self.read_json()
        if payload is None:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return
        try:
            asset = save_graphics_asset(payload.get("path", ""), payload.get("svg", ""))
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, 400)
            return
        self.send_json({"ok": True, "asset": asset})

    def handle_admin_code_file_save(self):
        """Persist an edited project code file from the local admin editor."""
        if not self.is_admin():
            self.send_json({"ok": False, "error": f"Login as {ADMIN_USER} to access the admin dashboard"}, 401)
            return
        payload = self.read_json()
        if payload is None:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return
        try:
            file_data = save_code_file(payload.get("path", ""), payload.get("content", ""))
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, 400)
            return
        self.send_json({"ok": True, "file": file_data})

    def handle_admin_rooms_page(self):
        """Serve the room editor to the authorized API user."""
        if not self.is_admin():
            self.send_html(self.admin_login_page())
            return
        self.send_html(admin_rooms_page())

    def handle_admin_assets_page(self):
        """Serve the asset editor to the authorized API user."""
        if not self.is_admin():
            self.send_html(self.admin_login_page())
            return
        self.send_html(admin_assets_page())

    def handle_admin_room_save(self):
        """Persist a single room override from the local admin interface."""
        if not self.is_admin():
            self.send_json({"ok": False, "error": f"Login as {ADMIN_USER} to access the admin dashboard"}, 401)
            return
        payload = self.read_json()
        if payload is None:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return
        room = payload.get("room")
        if not isinstance(room, dict) or not isinstance(room.get("id"), str):
            self.send_json({"ok": False, "error": "Room data is required"}, 400)
            return
        try:
            settings = save_room_overrides({room["id"]: room})
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, 400)
            return
        self.send_json({"ok": True, "roomOverrides": settings["roomOverrides"], "design": design_payload()})

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def track_event(self, user_id, event_type, payload):
        """Insert a gameplay or session event into the event log."""
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO game_events (user_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, event_type, json.dumps(payload, separators=(",", ":"), sort_keys=True), now_seconds()),
            )

    def update_presence(self, user_id, position, last_event):
        """Store the latest known map position for an active player."""
        try:
            x = float(position.get("x", 0))
            y = float(position.get("y", 0))
            tile_x = int(position.get("tileX", x // 48))
            tile_y = int(position.get("tileY", y // 48))
        except (TypeError, ValueError):
            return

        with connect() as connection:
            connection.execute(
                """
                INSERT INTO player_presence (user_id, x, y, tile_x, tile_y, last_event, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    x = excluded.x,
                    y = excluded.y,
                    tile_x = excluded.tile_x,
                    tile_y = excluded.tile_y,
                    last_event = excluded.last_event,
                    last_seen = excluded.last_seen
                """,
                (user_id, x, y, tile_x, tile_y, str(last_event)[:64], now_seconds()),
            )

    # ------------------------------------------------------------------
    # Admin authentication guard
    # ------------------------------------------------------------------

    def admin_login_page(self):
        """Render a login form that returns to the requested admin page."""
        return_path = json.dumps(urlparse(self.path).path)
        admin_user = json.dumps(ADMIN_USER)
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Admin Login · Abbey Island Mystery</title>
  <style>
    :root {{ color-scheme: dark; }}
    * {{ box-sizing: border-box; }}
    body {{
      min-height: 100vh;
      margin: 0;
      display: grid;
      place-items: center;
      padding: 24px;
      color: #ddd6c7;
      background:
        radial-gradient(circle at 50% 15%, rgba(103, 91, 81, .22), transparent 38%),
        #151619;
      font: 16px/1.5 Georgia, "Times New Roman", serif;
    }}
    main {{
      width: min(100%, 420px);
      padding: 32px;
      border: 1px solid #514c45;
      border-radius: 8px;
      background: rgba(35, 36, 41, .96);
      box-shadow: 0 24px 70px rgba(0, 0, 0, .45);
    }}
    h1 {{ margin: 0 0 8px; color: #f0e9da; font-size: 1.8rem; }}
    p {{ margin: 0 0 24px; color: #aaa396; }}
    label {{ display: block; margin: 16px 0 6px; color: #d8d0c1; }}
    input {{
      width: 100%;
      padding: 11px 12px;
      border: 1px solid #625d54;
      border-radius: 4px;
      color: #f3eee4;
      background: #1b1c20;
      font: inherit;
    }}
    input:focus {{ outline: 2px solid #8f8068; outline-offset: 1px; }}
    input[readonly] {{ color: #b9b1a3; background: #202126; }}
    button {{
      width: 100%;
      margin-top: 22px;
      padding: 11px 16px;
      border: 1px solid #8e8069;
      border-radius: 4px;
      color: #171719;
      background: #c7b99f;
      font: 700 16px Georgia, "Times New Roman", serif;
      cursor: pointer;
    }}
    button:disabled {{ cursor: wait; opacity: .65; }}
    #status {{ min-height: 24px; margin: 14px 0 0; color: #db9d91; }}
  </style>
</head>
<body>
  <main>
    <h1>Admin Login</h1>
    <p>Enter the administrator password to continue.</p>
    <form id="adminLoginForm">
      <label for="adminUser">User</label>
      <input id="adminUser" type="text" value="{ADMIN_USER}" autocomplete="username" readonly>
      <label for="adminPassword">Password</label>
      <input id="adminPassword" type="password" autocomplete="current-password" autofocus required>
      <button type="submit">Log in</button>
      <div id="status" role="status" aria-live="polite"></div>
    </form>
  </main>
  <script>
    const form = document.getElementById("adminLoginForm");
    const password = document.getElementById("adminPassword");
    const button = form.querySelector("button");
    const status = document.getElementById("status");
    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      button.disabled = true;
      status.textContent = "Logging in…";
      try {{
        const response = await fetch("/api/admin/login", {{
          method: "POST",
          credentials: "same-origin",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{
            name: {admin_user},
            password: password.value,
            create: false
          }})
        }});
        const result = await response.json();
        if (!response.ok || !result.ok) {{
          throw new Error(result.error || "Login failed");
        }}
        window.location.replace({return_path});
      }} catch (error) {{
        status.textContent = error.message || "Login failed";
        password.select();
        button.disabled = false;
      }}
    }});
  </script>
</body>
</html>"""

    def is_admin(self):
        """Return whether the request has a dedicated admin session."""
        return current_admin(self.headers) is not None
