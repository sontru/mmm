# Abbey Island Mystery

A browser-playable adventure prototype with a tiny Python admin server.

Players open the game in a browser. The Python server owns accounts, sessions, saved games, lightweight gameplay events, and an admin dashboard that helps you inspect player activity and game design data while you iterate.

The older Pygame prototype is still available as `desktop_game.py`.

## Run

### Browser

```bash
python3 main.py
```

Then open the URL printed by the server, usually `http://localhost:8080`. Other people on the same network can use `http://<your-computer-ip>:8080`.

The local admin dashboard is available only on the host computer:

```text
http://localhost:8080/admin
```

If port 8080 is busy, the server will try the next available port. You can also choose one:

```bash
python3 main.py 8080
```

`python3 serve.py` still works as a compatibility alias.

### Pygame

```bash
python3 -m pip install -r requirements.txt
python3 desktop_game.py
```

Use `WASD` or the arrow keys to move. Press `Esc` to quit the pygame version.

## Editable Graphics

- `assets/graphics/tile-*.svg`: terrain tiles
- `assets/graphics/tree-*.svg`: varied gothic trees
- `assets/graphics/rock-*.svg`: solid, unwalkable rocks
- `assets/graphics/building-*.svg`: 3x3 map buildings
- `assets/graphics/player-gothic.svg`: player sprite

## Server Structure

- `main.py`: web server entry point
- `mmm_server/handlers.py`: HTTP routes for browser APIs and admin pages
- `mmm_server/auth.py`: password hashing, login, logout, sessions
- `mmm_server/database.py`: SQLite schema for players, saves, and events
- `mmm_server/game_design.py`: design metadata exposed to the admin dashboard
- `web_game.js`: browser rendering, movement, local fallback cache, server save/event calls
