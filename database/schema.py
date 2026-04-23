import sqlite3
import os

_DB_PATH = None  # Cache global do caminho


def _get_db_path():
    """Caminho cacheado — garante sempre o mesmo arquivo."""
    global _DB_PATH
    if _DB_PATH:
        return _DB_PATH
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app and hasattr(app, 'user_data_dir') and app.user_data_dir:
            d = app.user_data_dir
            os.makedirs(d, exist_ok=True)
            _DB_PATH = os.path.join(d, 'financas.db')
            return _DB_PATH
    except Exception:
        pass
    _DB_PATH = os.path.join(os.path.expanduser('~'), 'financas_pessoais.db')
    return _DB_PATH


def get_connection():
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    global _DB_PATH
    _DB_PATH = None          # Reseta cache para usar user_data_dir correto
    _get_db_path()           # Inicializa com App ja rodando
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            color TEXT DEFAULT '#6366f1',
            icon TEXT DEFAULT '?',
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, name, type)
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            amount REAL NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            is_fixed INTEGER DEFAULT 0,
            fixed_expense_id INTEGER DEFAULT NULL,
            installment_id INTEGER DEFAULT NULL,
            installment_number INTEGER DEFAULT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS fixed_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            valid_from TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS fixed_skipped (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fixed_expense_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            UNIQUE(user_id, fixed_expense_id, month)
        );
        CREATE TABLE IF NOT EXISTS installments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            description TEXT NOT NULL,
            total_amount REAL NOT NULL,
            installment_amount REAL NOT NULL,
            total_parcelas INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(transactions)").fetchall()]
    for col, td in [
        ("fixed_expense_id", "INTEGER DEFAULT NULL"),
        ("installment_id",   "INTEGER DEFAULT NULL"),
        ("installment_number","INTEGER DEFAULT NULL"),
    ]:
        if col not in cols:
            conn.execute(f"ALTER TABLE transactions ADD COLUMN {col} {td}")
    conn.commit()
    conn.close()
