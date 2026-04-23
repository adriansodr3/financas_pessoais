from database.schema import get_connection
from datetime import date as _date


class TransactionModel:
    @staticmethod
    def create(user_id, category_id, type_, amount, description, date_str,
               is_fixed=0, fixed_expense_id=None,
               installment_id=None, installment_number=None) -> int:
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute(
                """INSERT INTO transactions
                   (user_id,category_id,type,amount,description,date,
                    is_fixed,fixed_expense_id,installment_id,installment_number)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (user_id, category_id, type_, amount, description, date_str,
                 is_fixed, fixed_expense_id, installment_id, installment_number))
            conn.commit()
            return c.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_by_period(user_id, year, month, category_id=None):
        conn = get_connection()
        try:
            start = f"{year:04d}-{month:02d}-01"
            end = f"{year+1:04d}-01-01" if month == 12 else f"{year:04d}-{month+1:02d}-01"
            q = """SELECT t.*,c.name as category_name,c.color,c.icon
                   FROM transactions t LEFT JOIN categories c ON t.category_id=c.id
                   WHERE t.user_id=? AND t.date>=? AND t.date<?"""
            params = [user_id, start, end]
            if category_id:
                q += " AND t.category_id=?"
                params.append(category_id)
            q += " ORDER BY t.date DESC,t.id DESC"
            return [dict(r) for r in conn.execute(q, params).fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_all_for_projection(user_id):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE user_id=? ORDER BY date", (user_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_balance_before_month(user_id, year, month):
        cutoff = f"{year:04d}-{month:02d}-01"
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT type,SUM(amount) as t FROM transactions WHERE user_id=? AND date<? GROUP BY type",
                (user_id, cutoff)).fetchall()
            inc = sum(r["t"] for r in rows if r["type"] == "income")
            exp = sum(r["t"] for r in rows if r["type"] == "expense")
            return inc - exp
        finally:
            conn.close()

    @staticmethod
    def get_pending_expenses_from(user_id, year, month):
        cutoff = f"{year:04d}-{month:02d}-01"
        conn = get_connection()
        try:
            row = conn.execute(
                """SELECT COALESCE(SUM(amount),0) as total FROM transactions
                   WHERE user_id=? AND type='expense' AND date>=? AND is_fixed=0""",
                (user_id, cutoff)).fetchone()
            return row["total"] if row else 0.0
        finally:
            conn.close()

    @staticmethod
    def get_summary_by_category(user_id, year, month):
        conn = get_connection()
        try:
            start = f"{year:04d}-{month:02d}-01"
            end = f"{year:04d}-{month+1:02d}-01" if month < 12 else f"{year+1:04d}-01-01"
            rows = conn.execute(
                """SELECT c.name,c.color,c.icon,t.type,SUM(t.amount) as total
                   FROM transactions t LEFT JOIN categories c ON t.category_id=c.id
                   WHERE t.user_id=? AND t.date>=? AND t.date<?
                   GROUP BY t.category_id,t.type ORDER BY total DESC""",
                (user_id, start, end)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def delete(tid, user_id):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM transactions WHERE id=? AND user_id=?", (tid, user_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update(tid, user_id, category_id, amount, description, date_str, clear_fixed=False):
        conn = get_connection()
        try:
            if clear_fixed:
                conn.execute(
                    "UPDATE transactions SET category_id=?,amount=?,description=?,date=?,is_fixed=0,fixed_expense_id=NULL WHERE id=? AND user_id=?",
                    (category_id, amount, description, date_str, tid, user_id))
            else:
                conn.execute(
                    "UPDATE transactions SET category_id=?,amount=?,description=?,date=? WHERE id=? AND user_id=?",
                    (category_id, amount, description, date_str, tid, user_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def mark_fixed_skipped(user_id, fixed_expense_id, year, month):
        month_str = f"{year:04d}-{month:02d}"
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO fixed_skipped (user_id,fixed_expense_id,month) VALUES (?,?,?)",
                (user_id, fixed_expense_id, month_str))
            conn.commit()
        finally:
            conn.close()


class FixedExpenseModel:
    @staticmethod
    def create(user_id, category_id, type_, amount, description, valid_from=None) -> int:
        if valid_from is None:
            t = _date.today()
            valid_from = f"{t.year:04d}-{t.month:02d}-01"
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO fixed_expenses (user_id,category_id,type,amount,description,valid_from) VALUES (?,?,?,?,?,?)",
                (user_id, category_id, type_, amount, description, valid_from))
            conn.commit()
            return c.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_active(user_id):
        conn = get_connection()
        try:
            rows = conn.execute(
                """SELECT fe.*,c.name as category_name,c.color,c.icon
                   FROM fixed_expenses fe LEFT JOIN categories c ON fe.category_id=c.id
                   WHERE fe.user_id=? AND fe.active=1 ORDER BY fe.description""",
                (user_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def deactivate(fid, user_id):
        conn = get_connection()
        try:
            conn.execute("UPDATE fixed_expenses SET active=0 WHERE id=? AND user_id=?", (fid, user_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update(fid, user_id, category_id, type_, amount, description):
        t = _date.today()
        nm = f"{t.year+1:04d}-01-01" if t.month == 12 else f"{t.year:04d}-{t.month+1:02d}-01"
        conn = get_connection()
        try:
            conn.execute("UPDATE fixed_expenses SET active=0 WHERE id=? AND user_id=?", (fid, user_id))
            conn.execute(
                "INSERT INTO fixed_expenses (user_id,category_id,type,amount,description,valid_from) VALUES (?,?,?,?,?,?)",
                (user_id, category_id, type_, amount, description, nm))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_for_month(user_id, year, month):
        ms = f"{year:04d}-{month:02d}-01"
        conn = get_connection()
        try:
            rows = conn.execute(
                """SELECT fe.*,c.name as category_name,c.color,c.icon
                   FROM fixed_expenses fe LEFT JOIN categories c ON fe.category_id=c.id
                   WHERE fe.user_id=? AND fe.active=1 AND fe.valid_from<=?
                   ORDER BY fe.description""",
                (user_id, ms)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def materialize_for_month(user_id, year, month):
        ms = f"{year:04d}-{month:02d}-01"
        ym = f"{year:04d}-{month:02d}"
        conn = get_connection()
        try:
            frows = conn.execute(
                "SELECT * FROM fixed_expenses WHERE user_id=? AND active=1 AND valid_from<=?",
                (user_id, ms)).fetchall()
            for fe in frows:
                skipped = conn.execute(
                    "SELECT 1 FROM fixed_skipped WHERE user_id=? AND fixed_expense_id=? AND month=?",
                    (user_id, fe["id"], ym)).fetchone()
                if skipped:
                    continue
                already = conn.execute(
                    "SELECT id FROM transactions WHERE user_id=? AND is_fixed=1 AND fixed_expense_id=? AND strftime('%Y-%m',date)=?",
                    (user_id, fe["id"], ym)).fetchone()
                if not already:
                    conn.execute(
                        "INSERT INTO transactions (user_id,category_id,type,amount,description,date,is_fixed,fixed_expense_id) VALUES (?,?,?,?,?,?,1,?)",
                        (user_id, fe["category_id"], fe["type"], fe["amount"], fe["description"], ms, fe["id"]))
            conn.commit()
        finally:
            conn.close()


class InstallmentModel:
    @staticmethod
    def create(user_id, category_id, description, total_amount, installment_amount, total_parcelas, start_date) -> int:
        from datetime import datetime
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO installments (user_id,category_id,description,total_amount,installment_amount,total_parcelas,start_date) VALUES (?,?,?,?,?,?,?)",
                (user_id, category_id, description, total_amount, installment_amount, total_parcelas, start_date))
            iid = c.lastrowid
            dt = datetime.strptime(start_date, "%Y-%m-%d")
            y, m = dt.year, dt.month
            for i in range(total_parcelas):
                pd = f"{y:04d}-{m:02d}-01"
                desc = f"{description} ({i+1}/{total_parcelas})"
                c.execute(
                    "INSERT INTO transactions (user_id,category_id,type,amount,description,date,installment_id,installment_number) VALUES (?,?,'expense',?,?,?,?,?)",
                    (user_id, category_id, installment_amount, desc, pd, iid, i+1))
                if m == 12:
                    y += 1; m = 1
                else:
                    m += 1
            conn.commit()
            return iid
        finally:
            conn.close()

    @staticmethod
    def get_all(user_id):
        conn = get_connection()
        try:
            rows = conn.execute(
                """SELECT i.*,c.name as category_name,c.color,c.icon
                   FROM installments i LEFT JOIN categories c ON i.category_id=c.id
                   WHERE i.user_id=? ORDER BY i.start_date DESC""",
                (user_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_parcelas(iid, user_id):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE installment_id=? AND user_id=? ORDER BY installment_number",
                (iid, user_id)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_paid_pending(iid, user_id):
        cutoff = f"{_date.today().year:04d}-{_date.today().month:02d}-01"
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT date,amount FROM transactions WHERE installment_id=? AND user_id=?",
                (iid, user_id)).fetchall()
            paid = sum(r["amount"] for r in rows if r["date"] < cutoff)
            pending = sum(r["amount"] for r in rows if r["date"] >= cutoff)
            return paid, pending
        finally:
            conn.close()

    @staticmethod
    def settle(iid, user_id, category_id, description):
        today_str = _date.today().strftime("%Y-%m-%d")
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(amount),0) as t FROM transactions WHERE installment_id=? AND user_id=?",
                (iid, user_id)).fetchone()
            total = row["t"] if row else 0.0
            conn.execute("DELETE FROM transactions WHERE installment_id=? AND user_id=?", (iid, user_id))
            conn.execute(
                "INSERT INTO transactions (user_id,category_id,type,amount,description,date) VALUES (?,?,'expense',?,?,?)",
                (user_id, category_id, total, f"Quitacao: {description}", today_str))
            conn.execute("DELETE FROM installments WHERE id=? AND user_id=?", (iid, user_id))
            conn.commit()
            return total
        finally:
            conn.close()

    @staticmethod
    def delete(iid, user_id):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM installments WHERE id=? AND user_id=?", (iid, user_id))
            conn.execute("DELETE FROM transactions WHERE installment_id=? AND user_id=?", (iid, user_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete_fixed_month(uid, tx_id, fixed_expense_id, year, month):
        """Exclui lancamento fixo de um mes especifico: marca como skipped + deleta (atomico)."""
        month_str = f"{year:04d}-{month:02d}"
        conn = get_connection()
        try:
            # 1) Marca como pulado ANTES de deletar (evita que materialize recrie)
            conn.execute(
                "INSERT OR IGNORE INTO fixed_skipped (user_id,fixed_expense_id,month) VALUES (?,?,?)",
                (uid, fixed_expense_id, month_str))
            # 2) Deleta a instancia do mes
            conn.execute("DELETE FROM transactions WHERE id=? AND user_id=?", (tx_id, uid))
            conn.commit()
        finally:
            conn.close()
