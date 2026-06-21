from http import cookies
import hashlib
import hmac
import secrets

from .config import (
    ADMIN_PASSWORD,
    ADMIN_SESSION_COOKIE,
    ADMIN_USER,
    SESSION_COOKIE,
    SESSION_SECONDS,
)
from .database import connect, now_seconds


def password_hash(password, salt):
    """Return a PBKDF2 password digest for the given password and salt."""
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 120_000)
    return digest.hex()


def make_password(password):
    """Create a salted password hash suitable for storing with a player account."""
    salt = secrets.token_hex(16)
    return password_hash(password, salt), salt


def verify_password(password, stored_hash, salt):
    """Compare a submitted password against a stored salted hash."""
    return hmac.compare_digest(password_hash(password, salt), stored_hash)


def cookie_header(token):
    """Build the Set-Cookie header for a live player session token."""
    return (
        f"{SESSION_COOKIE}={token}; Max-Age={SESSION_SECONDS}; "
        "Path=/; SameSite=Lax; HttpOnly"
    )


def clear_cookie_header():
    """Build the Set-Cookie header that clears the player session cookie."""
    return f"{SESSION_COOKIE}=; Max-Age=0; Path=/; SameSite=Lax; HttpOnly"


def cookie_token(headers, cookie_name):
    """Extract a named session token from request cookies."""
    raw_cookie = headers.get("Cookie", "")
    jar = cookies.SimpleCookie()
    jar.load(raw_cookie)
    morsel = jar.get(cookie_name)
    return morsel.value if morsel else None


def session_token(headers):
    """Extract the current player session token from request cookies."""
    return cookie_token(headers, SESSION_COOKIE)


def admin_cookie_header(token):
    """Build the Set-Cookie header for a dedicated admin session."""
    return (
        f"{ADMIN_SESSION_COOKIE}={token}; Max-Age={SESSION_SECONDS}; "
        "Path=/; SameSite=Lax; HttpOnly"
    )


def clear_admin_cookie_header():
    """Build the Set-Cookie header that clears the admin session cookie."""
    return f"{ADMIN_SESSION_COOKIE}=; Max-Age=0; Path=/; SameSite=Lax; HttpOnly"


def login_admin(name, password):
    """Authenticate the hardwired administrator independently of players."""
    valid_name = hmac.compare_digest(name, ADMIN_USER)
    valid_password = hmac.compare_digest(password, ADMIN_PASSWORD)
    if not valid_name or not valid_password:
        return None

    token = secrets.token_urlsafe(32)
    now = now_seconds()
    with connect() as connection:
        connection.execute("DELETE FROM admin_sessions WHERE expires_at <= ?", (now,))
        connection.execute(
            """
            INSERT INTO admin_sessions (token, created_at, expires_at)
            VALUES (?, ?, ?)
            """,
            (token, now, now + SESSION_SECONDS),
        )
    return token


def current_admin(headers):
    """Return the hardwired admin identity for a valid admin session."""
    token = cookie_token(headers, ADMIN_SESSION_COOKIE)
    if not token:
        return None
    with connect() as connection:
        row = connection.execute(
            "SELECT token FROM admin_sessions WHERE token = ? AND expires_at > ?",
            (token, now_seconds()),
        ).fetchone()
    return {"name": ADMIN_USER} if row else None


def logout_admin(headers):
    """Delete the current dedicated admin session."""
    token = cookie_token(headers, ADMIN_SESSION_COOKIE)
    if token:
        with connect() as connection:
            connection.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))


def current_user(headers):
    """Return the logged-in player for the request headers, if any."""
    token = session_token(headers)
    if not token:
        return None
    now = now_seconds()
    with connect() as connection:
        row = connection.execute(
            """
            SELECT users.id, users.name
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ? AND sessions.expires_at > ?
            """,
            (token, now),
        ).fetchone()
    return dict(row) if row else None


def login_or_create_player(name, password, create_allowed):
    """Authenticate an existing player or create one when allowed."""
    now = now_seconds()
    with connect() as connection:
        user = connection.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
        created = False
        if user:
            if not verify_password(password, user["password_hash"], user["salt"]):
                return None, False
            user_id = user["id"]
        else:
            if not create_allowed:
                return None, False
            hashed, salt = make_password(password)
            cursor = connection.execute(
                """
                INSERT INTO users (name, password_hash, salt, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, hashed, salt, now, now),
            )
            user_id = cursor.lastrowid
            created = True

        token = secrets.token_urlsafe(32)
        connection.execute(
            """
            INSERT INTO sessions (token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, user_id, now, now + SESSION_SECONDS),
        )

    return {"id": user_id, "name": name, "token": token}, created


def logout(headers):
    """Delete the current session token from the session store."""
    token = session_token(headers)
    if token:
        with connect() as connection:
            connection.execute("DELETE FROM sessions WHERE token = ?", (token,))
