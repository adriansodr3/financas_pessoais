from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDFloatingActionButton
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

from screens.widgets import (confirm_dialog, BG, CARD_BG, PURPLE,
                              GREEN, RED, ORANGE, MUTED, WHITE, fmt_currency)
from utils.helpers import fmt_date, today_str
from models.transaction import InstallmentModel
from models.category import CategoryModel


class InstallmentsScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "tab_installments"
        self._built = False
        self._undo_snapshot = None

    def on_enter(self):
        if not self._built:
            self._build()
            self._built = True
        self.refresh()

    def _build(self):
        root = FloatLayout(md_bg_color=BG)
        col = MDBoxLayout(orientation="vertical", md_bg_color=BG, size_hint=(1, 1))

        # Header
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56),
                             padding=[16, 8], md_bg_color=CARD_BG)
        header.add_widget(MDLabel(text="Parcelamentos", font_style="Subtitle1",
                                  theme_text_color="Custom", text_color=WHITE))
        col.add_widget(header)

        # Barra de desfazer (sempre visivel, oculta quando sem acao)
        self._undo_bar = MDBoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(52),
            padding=[12, 4], spacing=8,
            md_bg_color=(0.12, 0.11, 0.30, 1))
        self._undo_lbl = MDLabel(
            text="", font_style="Body2",
            theme_text_color="Custom", text_color=(0.65, 0.64, 0.98, 1))
        btn_undo = MDRaisedButton(
            text="Desfazer", size_hint=(None, None),
            height=dp(36), width=dp(100),
            md_bg_color=PURPLE, on_release=self._do_undo)
        btn_dismiss = MDFlatButton(
            text="OK", size_hint=(None, None),
            height=dp(36), on_release=self._dismiss_undo)
        self._undo_bar.add_widget(self._undo_lbl)
        self._undo_bar.add_widget(btn_undo)
        self._undo_bar.add_widget(btn_dismiss)
        self._undo_bar.opacity = 0
        self._undo_bar.disabled = True
        col.add_widget(self._undo_bar)

        # Lista scrollavel
        sv = ScrollView()
        self._content = MDBoxLayout(
            orientation="vertical", spacing=10,
            padding=[8, 8, 8, 80], size_hint_y=None)
        self._content.bind(minimum_height=self._content.setter("height"))
        sv.add_widget(self._content)
        col.add_widget(sv)

        root.add_widget(col)

        # FAB para adicionar
        fab = MDFloatingActionButton(
            icon="plus", md_bg_color=PURPLE,
            pos_hint={"right": 0.96, "y": 0.04},
            on_release=lambda *a: self._add())
        root.add_widget(fab)
        self.add_widget(root)

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self._content.clear_widgets()
        items = InstallmentModel.get_all(uid)
        if not items:
            self._content.add_widget(
                MDLabel(text="Nenhum parcelamento cadastrado.",
                        halign="center", theme_text_color="Secondary",
                        size_hint_y=None, height=dp(80)))
            return
        for inst in items:
            paid, pending = InstallmentModel.get_paid_pending(inst["id"], uid)
            self._content.add_widget(self._make_card(inst, paid, pending, uid))

    def _make_card(self, inst, paid, pending, uid):
        card = MDCard(
            orientation="vertical", padding=12, spacing=6,
            size_hint_y=None, height=dp(190),
            md_bg_color=CARD_BG, radius=[12])

        # Linha titulo
        row1 = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
        row1.add_widget(MDLabel(text=inst["description"], font_style="Subtitle1",
                                theme_text_color="Custom", text_color=WHITE))
        row1.add_widget(MDLabel(text=inst.get("category_name") or "",
                                font_style="Caption",
                                theme_text_color="Custom", text_color=MUTED,
                                halign="right"))
        card.add_widget(row1)

        # Info
        parcelas = InstallmentModel.get_parcelas(inst["id"], uid)
        row2 = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        row2.add_widget(MDLabel(
            text="{} | {}x de {} | Inicio: {}".format(
                fmt_currency(inst["total_amount"]),
                len(parcelas),
                fmt_currency(inst["installment_amount"]),
                fmt_date(inst["start_date"])),
            font_style="Caption", theme_text_color="Custom", text_color=MUTED))
        card.add_widget(row2)

        # Pago / Falta pagar
        row3 = MDBoxLayout(orientation="horizontal", spacing=8,
                           size_hint_y=None, height=dp(52))
        c_paid = MDCard(md_bg_color=(0.05, 0.15, 0.10, 1), radius=[8], padding=8)
        c_paid.add_widget(MDLabel(
            text="Pago\n{}".format(fmt_currency(paid)),
            theme_text_color="Custom", text_color=GREEN,
            font_style="Caption", halign="center"))
        c_pend = MDCard(md_bg_color=(0.15, 0.10, 0.05, 1), radius=[8], padding=8)
        c_pend.add_widget(MDLabel(
            text="Falta\n{}".format(fmt_currency(pending)),
            theme_text_color="Custom", text_color=ORANGE,
            font_style="Caption", halign="center"))
        row3.add_widget(c_paid)
        row3.add_widget(c_pend)
        card.add_widget(row3)

        # Botoes
        row4 = MDBoxLayout(orientation="horizontal", spacing=8,
                           size_hint_y=None, height=dp(40))
        btn_s = MDRaisedButton(
            text="Quitar", md_bg_color=GREEN,
            size_hint=(1, None), height=dp(36),
            on_release=lambda *a, i=dict(inst), pa=paid, pe=pending:
                self._settle(i, pa, pe, uid))
        btn_c = MDRaisedButton(
            text="Cancelar", md_bg_color=RED,
            size_hint=(1, None), height=dp(36),
            on_release=lambda *a, iid=inst["id"], d=inst["description"]:
                self._cancel(iid, d, uid))
        row4.add_widget(btn_s)
        row4.add_widget(btn_c)
        card.add_widget(row4)
        return card

    def _settle(self, inst, paid, pending, uid):
        total = paid + pending
        text = (
            "{}\n\n"
            "Ja pago:     {}\n"
            "Falta pagar: {}\n"
            "Total:       {}\n\n"
            "Sera lancada despesa de {} no mes atual."
        ).format(inst["description"],
                 fmt_currency(paid), fmt_currency(pending),
                 fmt_currency(total), fmt_currency(total))

        def do_settle():
            snap = self._get_snapshot(inst["id"], uid)
            settled = InstallmentModel.settle(
                inst["id"], uid, inst.get("category_id"), inst["description"])
            # capturar id da tx de quitacao para undo
            from database.schema import get_connection
            conn = get_connection()
            row = conn.execute(
                "SELECT id FROM transactions WHERE user_id=? AND description=? "
                "ORDER BY id DESC LIMIT 1",
                (uid, "Quitacao: " + inst["description"])).fetchone()
            conn.close()
            snap["quitacao_tx_id"] = row["id"] if row else None
            self._undo_snapshot = snap
            self._show_undo(
                "'{}' quitado - {}".format(inst["description"], fmt_currency(settled)))
            self.refresh()

        confirm_dialog("Quitar parcelamento", text, do_settle, "Confirmar quitacao")

    def _get_snapshot(self, iid, uid):
        from database.schema import get_connection
        conn = get_connection()
        ir = conn.execute("SELECT * FROM installments WHERE id=?", (iid,)).fetchone()
        pr = conn.execute(
            "SELECT * FROM transactions WHERE installment_id=? AND user_id=?",
            (iid, uid)).fetchall()
        conn.close()
        return {
            "installment": dict(ir) if ir else {},
            "parcelas": [dict(p) for p in pr],
            "quitacao_tx_id": None
        }

    def _cancel(self, iid, desc, uid):
        def do_cancel():
            InstallmentModel.delete(iid, uid)
            self._dismiss_undo()
            self.refresh()
        confirm_dialog(
            "Cancelar parcelamento",
            "'{}'\n\nRemover TODAS as parcelas?\nEssa acao nao pode ser desfeita.".format(desc),
            do_cancel, "Cancelar tudo", danger=True)

    def _show_undo(self, msg):
        self._undo_lbl.text = msg
        self._undo_bar.opacity = 1
        self._undo_bar.disabled = False

    def _dismiss_undo(self, *a):
        self._undo_snapshot = None
        self._undo_bar.opacity = 0
        self._undo_bar.disabled = True

    def _do_undo(self, *a):
        if not self._undo_snapshot:
            return
        snap = self._undo_snapshot
        from database.schema import get_connection
        conn = get_connection()
        try:
            inst = snap["installment"]
            conn.execute(
                "INSERT OR REPLACE INTO installments "
                "(id,user_id,category_id,description,total_amount,"
                "installment_amount,total_parcelas,start_date,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (inst["id"], inst["user_id"], inst.get("category_id"),
                 inst["description"], inst["total_amount"],
                 inst["installment_amount"], inst["total_parcelas"],
                 inst["start_date"], inst.get("created_at")))
            for p in snap["parcelas"]:
                conn.execute(
                    "INSERT OR REPLACE INTO transactions "
                    "(id,user_id,category_id,type,amount,description,date,"
                    "is_fixed,fixed_expense_id,installment_id,installment_number,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (p["id"], p["user_id"], p.get("category_id"), p["type"],
                     p["amount"], p.get("description"), p["date"],
                     p.get("is_fixed", 0), p.get("fixed_expense_id"),
                     p.get("installment_id"), p.get("installment_number"),
                     p.get("created_at")))
            if snap.get("quitacao_tx_id"):
                conn.execute("DELETE FROM transactions WHERE id=?",
                             (snap["quitacao_tx_id"],))
            conn.commit()
        finally:
            conn.close()
        self._dismiss_undo()
        self.refresh()

    def _add(self):
        app = MDApp.get_running_app()
        uid = app.current_user["id"]
        cats = CategoryModel.get_all(uid, "expense")
        cat_opts = [(c["id"], "{} {}".format(c.get("icon", ""), c["name"])) for c in cats]
        self._sel_cat = cat_opts[0][0] if cat_opts else None

        content = MDBoxLayout(orientation="vertical", spacing=8,
                              size_hint_y=None, height=dp(300), padding=[0, 8, 0, 0])
        f_desc   = MDTextField(hint_text="Descricao (ex: Notebook)", mode="rectangle",
                               size_hint_y=None, height=dp(48))
        f_total  = MDTextField(hint_text="Valor Total (ex: 1200.00)", mode="rectangle",
                               input_filter="float", size_hint_y=None, height=dp(48))
        f_parc   = MDTextField(hint_text="Num. Parcelas (ex: 12)", mode="rectangle",
                               input_filter="int", size_hint_y=None, height=dp(48))
        f_date   = MDTextField(hint_text="Inicio (AAAA-MM-DD)", mode="rectangle",
                               text=today_str(), size_hint_y=None, height=dp(48))
        btn_cat  = MDRaisedButton(
            text=cat_opts[0][1] if cat_opts else "Categoria",
            size_hint=(1, None), height=dp(40), md_bg_color=CARD_BG)

        def open_menu(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda cid=cid, n=nm: (
                          setattr(self, '_sel_cat', cid),
                          btn.__setattr__('text', n),
                          menu.dismiss()
                      )} for cid, nm in cat_opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()
        btn_cat.bind(on_release=open_menu)

        for w in [f_desc, f_total, f_parc, f_date, btn_cat]:
            content.add_widget(w)

        def save(*a):
            try:
                total = float(f_total.text.replace(",", "."))
                n = int(f_parc.text)
            except Exception:
                return
            if not f_desc.text.strip() or n < 1:
                return
            date_s = f_date.text.strip() or today_str()
            InstallmentModel.create(
                uid, self._sel_cat, f_desc.text.strip(),
                total, round(total / n, 2), n, date_s)
            dlg.dismiss()
            self.refresh()

        dlg = MDDialog(
            title="Novo Parcelamento", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(text="Lancar", md_bg_color=PURPLE, on_release=save)])
        dlg.open()
