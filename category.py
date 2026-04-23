from database.schema import get_connection


class CategoryModel:
    @staticmethod
    def get_all(user_id: int, type_: str = None):
        conn = get_connection()
        try:
            if type_:
                rows = conn.execute(
                    "SELECT * FROM categories WHERE user_id=? AND type=? ORDER BY name",
                    (user_id, type_)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM categories WHERE user_id=? ORDER BY type,name",
                    (user_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def create(user_id: int, name: str, type_: str, color: str = "#6366f1", icon: str = "💰") -> int:
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO categories (user_id,name,type,color,icon) VALUES (?,?,?,?,?)",
                (user_id, name, type_, color, icon))
            conn.commit()
            return c.lastrowid
        finally:
            conn.close()

    @staticmethod
    def delete(cat_id: int, user_id: int):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM categories WHERE id=? AND user_id=?", (cat_id, user_id))
            conn.commit()
        finally:
            conn.close()
