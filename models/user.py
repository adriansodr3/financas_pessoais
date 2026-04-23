import hashlib
import os
import base64
from database.schema import get_connection

DEFAULT_CATEGORIES = [
    ("Salario",      "income",  "#22c55e", "💼"),
    ("Freelance",    "income",  "#10b981", "💻"),
    ("Outros Ent.",  "income",  "#8b5cf6", "➕"),
    ("Moradia",      "expense", "#ef4444", "🏠"),
    ("Alimentacao",  "expense", "#f97316", "🛒"),
    ("Transporte",   "expense", "#eab308", "🚗"),
    ("Saude",        "expense", "#14b8a6", "❤️"),
    ("Educacao",     "expense", "#6366f1", "📚"),
    ("Lazer",        "expense", "#ec4899", "🎉"),
    ("Contas",       "expense", "#64748b", "📋"),
    ("Outros Sai.",  "expense", "#94a3b8", "➖"),
]


def _hash(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
    return base64.b64encode(salt + key).decode()


def _verify(password: str, stored: str) -> bool:
    try:
        data = base64.b64decode(stored.encode())
        salt, key = data[:32], data[32:]
        check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
        return check == key
    except Exception:
        return False


class UserModel:
    @staticmethod
    def create(username: str, password: str) -> int:
        hashed = _hash(password)
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password_hash) VALUES (?,?)",
                      (username, hashed))
            conn.commit()
            uid = c.lastrowid
            # seed categories
            for name, tp, color, icon in DEFAULT_CATEGORIES:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO categories (user_id,name,type,color,icon) VALUES (?,?,?,?,?)",
                        (uid, name, tp, color, icon))
                except Exception:
                    pass
            conn.commit()
            return uid
        finally:
            conn.close()

    @staticmethod
    def authenticate(username: str, password: str):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            if row and _verify(password, row["password_hash"]):
                return dict(row)
            return None
        finally:
            conn.close()

    @staticmethod
    def exists_any() -> bool:
        conn = get_connection()
        try:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0
        finally:
            conn.close()

    @staticmethod
    def list_users():
        conn = get_connection()
        try:
            return [dict(r) for r in conn.execute("SELECT id,username FROM users").fetchall()]
        finally:
            conn.close()
