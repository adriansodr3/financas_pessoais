from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp
from screens.widgets import confirm_dialog, BG, CARD_BG, PURPLE, GREEN, RED, ORANGE, MUTED, WHITE, fmt_currency
from utils.helpers import fmt_date, today_str
from models.transaction import InstallmentModel
from models.category import CategoryModel

Builder.load_string("""
<InstallmentsScreen>:
    name: "tab_installments"
    md_bg_color: 0.06, 0.07, 0.09, 1
    FloatLayout:
        BoxLayout:
            orientation: "vertical"
            size_hint: 1, 1
            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(52)
                md_bg_color: 0.10, 0.11, 0.15, 1
                MDLabel:
                    text: "Parcelamentos"
                    font_style: "Subtitle1"
                    theme_text_color: "Custom"
                    text_color: 0.89, 0.91, 0.94, 1
                    padding_x: dp(16)
            MDBoxLayout:
                id: undo_bar
                orientation: "horizontal"
                size_hint_y: None
                height: dp(52)
                padding: dp(12), dp(4)
                spacing: dp(8)
                md_bg_color: 0.12, 0.11, 0.30, 1
                opacity: 0
                disabled: True
                MDLabel:
                    id: undo_lbl
                    text: ""
                    font_style: "Body2"
                    theme_text_color: "Custom"
                    text_color: 0.65, 0.64, 0.98, 1
                MDRaisedButton:
                    text: "Desfazer"
                    size_hint: None, None
                    width: dp(100)
                    height: dp(36)
                    md_bg_color: 0.39, 0.40, 0.95, 1
                    on_release: root.do_undo()
                MDFlatButton:
                    text: "OK"
                    size_hint: None, None
                    width: dp(60)
                    height: dp(36)
                    on_release: root.dismiss_undo()
            ScrollView:
                do_scroll_x: False
                MDBoxLayout:
                    id: cards_box
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(10)
                    padding: dp(8), dp(8), dp(8), dp(80)
        MDFloatingActionButton:
            icon: "plus"
            md_bg_color: 0.39, 0.40, 0.95, 1
            pos_hint: {"right": 0.95, "y": 0.02}
            on_release: root.add_installment()
""")


class InstallmentsScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._snap = None
        self._sel_cat = None

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        box = self.ids.cards_box
        box.clear_widgets()
        items = InstallmentModel.get_all(uid)
        if not items:
            box.add_widget(MDLabel(
                text="Nenhum parcelamento.", halign="center",
                theme_text_color="Secondary", size_hint_y=None, height=dp(80)))
            return
        for inst in items:
            paid, pending = InstallmentModel.get_paid_pending(inst["id"], uid)
            box.add_widget(self._make_card(inst, paid, pending, uid))

    def _make_card(self, inst, paid, pending, uid):
        card = MDCard(orientation="vertical", padding=dp(12), spacing=dp(6),
                      size_hint_y=None, height=dp(190), md_bg_color=CARD_BG, radius=[dp(12)])
        r1 = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
        r1.add_widget(MDLabel(text=inst["description"], font_style="Subtitle1",
                              theme_text_color="Custom", text_color=WHITE))
        r1.add_widget(MDLabel(text=inst.get("category_name") or "", font_style="Caption",
                              theme_text_color="Custom", text_color=MUTED, halign="right"))
        card.add_widget(r1)
        parcelas = InstallmentModel.get_parcelas(inst["id"], uid)
        card.add_widget(MDLabel(
            text="{} | {}x de {} | Inicio: {}".format(
                fmt_currency(inst["total_amount"]), len(parcelas),
                fmt_currency(inst["installment_amount"]), fmt_date(inst["start_date"])),
            font_style="Caption", theme_text_color="Custom", text_color=MUTED,
            size_hint_y=None, height=dp(22)))
        r3 = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(52))
        cp = MDCard(md_bg_color=(0.05,0.15,0.10,1), radius=[dp(8)], padding=dp(8))
        cp.add_widget(MDLabel(text="Pago\n{}".format(fmt_currency(paid)),
                              theme_text_color="Custom", text_color=GREEN,
                              font_style="Caption", halign="center"))
        cpe = MDCard(md_bg_color=(0.15,0.10,0.05,1), radius=[dp(8)], padding=dp(8))
        cpe.add_widget(MDLabel(text="Falta\n{}".format(fmt_currency(pending)),
                               theme_text_color="Custom", text_color=ORANGE,
                               font_style="Caption", halign="center"))
        r3.add_widget(cp); r3.add_widget(cpe)
        card.add_widget(r3)
        r4 = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(40))
        r4.add_widget(MDRaisedButton(
            text="Quitar", md_bg_color=GREEN, size_hint=(1,None), height=dp(36),
            on_release=lambda *a, i=dict(inst), pa=paid, pe=pending: self._settle(i, pa, pe, uid)))
        r4.add_widget(MDRaisedButton(
            text="Cancelar", md_bg_color=RED, size_hint=(1,None), height=dp(36),
            on_release=lambda *a, iid=inst["id"], d=inst["description"]: self._cancel(iid, d, uid)))
        card.add_widget(r4)
        return card

    def _settle(self, inst, paid, pending, uid):
        total = paid + pending
        def do_settle():
            snap = self._get_snap(inst["id"], uid)
            settled = InstallmentModel.settle(inst["id"], uid, inst.get("category_id"), inst["description"])
            from database.schema import get_connection
            conn = get_connection()
            row = conn.execute("SELECT id FROM transactions WHERE user_id=? AND description=? ORDER BY id DESC LIMIT 1",
                               (uid, "Quitacao: " + inst["description"])).fetchone()
            conn.close()
            snap["quitacao_tx_id"] = row["id"] if row else None
            self._snap = snap
            self._show_undo("'{}' quitado - {}".format(inst["description"], fmt_currency(settled)))
            self.refresh()
        confirm_dialog("Quitar parcelamento",
            "{}\n\nPago: {}\nFalta: {}\nTotal: {}".format(
                inst["description"], fmt_currency(paid), fmt_currency(pending), fmt_currency(total)),
            do_settle, "Confirmar")

    def _get_snap(self, iid, uid):
        from database.schema import get_connection
        conn = get_connection()
        ir = conn.execute("SELECT * FROM installments WHERE id=?", (iid,)).fetchone()
        pr = conn.execute("SELECT * FROM transactions WHERE installment_id=? AND user_id=?", (iid, uid)).fetchall()
        conn.close()
        return {"installment": dict(ir) if ir else {}, "parcelas": [dict(p) for p in pr], "quitacao_tx_id": None}

    def _cancel(self, iid, desc, uid):
        def do_cancel():
            InstallmentModel.delete(iid, uid)
            self.dismiss_undo()
            self.refresh()
        confirm_dialog("Cancelar", "'{}'\nRemover TODAS as parcelas?".format(desc),
                       do_cancel, "Cancelar tudo", danger=True)

    def _show_undo(self, msg):
        self.ids.undo_lbl.text = msg
        self.ids.undo_bar.opacity = 1
        self.ids.undo_bar.disabled = False

    def dismiss_undo(self, *a):
        self._snap = None
        self.ids.undo_bar.opacity = 0
        self.ids.undo_bar.disabled = True

    def do_undo(self, *a):
        if not self._snap: return
        from database.schema import get_connection
        conn = get_connection()
        try:
            inst = self._snap["installment"]
            conn.execute("INSERT OR REPLACE INTO installments (id,user_id,category_id,description,total_amount,installment_amount,total_parcelas,start_date,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (inst["id"], inst["user_id"], inst.get("category_id"), inst["description"],
                 inst["total_amount"], inst["installment_amount"], inst["total_parcelas"],
                 inst["start_date"], inst.get("created_at")))
            for p in self._snap["parcelas"]:
                conn.execute("INSERT OR REPLACE INTO transactions (id,user_id,category_id,type,amount,description,date,is_fixed,fixed_expense_id,installment_id,installment_number,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (p["id"], p["user_id"], p.get("category_id"), p["type"], p["amount"],
                     p.get("description"), p["date"], p.get("is_fixed",0), p.get("fixed_expense_id"),
                     p.get("installment_id"), p.get("installment_number"), p.get("created_at")))
            if self._snap.get("quitacao_tx_id"):
                conn.execute("DELETE FROM transactions WHERE id=?", (self._snap["quitacao_tx_id"],))
            conn.commit()
        finally:
            conn.close()
        self.dismiss_undo()
        self.refresh()

    def add_installment(self):
        uid = MDApp.get_running_app().current_user["id"]
        cats = CategoryModel.get_all(uid, "expense")
        opts = [(c["id"], "{} {}".format(c.get("icon",""), c["name"])) for c in cats]
        self._sel_cat = opts[0][0] if opts else None
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(310), padding=[0, dp(8), 0, 0])
        f_desc  = MDTextField(hint_text="Descricao (ex: Notebook)", mode="rectangle", size_hint_y=None, height=dp(52))
        f_total = MDTextField(hint_text="Valor Total (ex: 1200.00)", mode="rectangle", input_filter="float", size_hint_y=None, height=dp(52))
        f_parc  = MDTextField(hint_text="Num Parcelas (ex: 12)", mode="rectangle", input_filter="int", size_hint_y=None, height=dp(52))
        f_date  = MDTextField(hint_text="Inicio (AAAA-MM-DD)", mode="rectangle", text=today_str(), size_hint_y=None, height=dp(52))
        btn_cat = MDRaisedButton(text=opts[0][1] if opts else "Categoria", size_hint=(1,None), height=dp(44), md_bg_color=CARD_BG)
        def open_menu(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda cid=cid, n=nm: (setattr(self,"_sel_cat",cid), btn.__setattr__("text",n), menu.dismiss())} for cid,nm in opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()
        btn_cat.bind(on_release=open_menu)
        for w in [f_desc, f_total, f_parc, f_date, btn_cat]: content.add_widget(w)
        dlg = [None]
        def save(*a):
            try: total = float(f_total.text.replace(",",".")); n = int(f_parc.text)
            except: return
            if not f_desc.text.strip() or n < 1: return
            InstallmentModel.create(uid, self._sel_cat, f_desc.text.strip(), total, round(total/n,2), n, f_date.text.strip() or today_str())
            dlg[0].dismiss(); self.refresh()
        dlg[0] = MDDialog(title="Novo Parcelamento", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                                   MDRaisedButton(text="Lancar", md_bg_color=PURPLE, on_release=save)])
        dlg[0].open()
