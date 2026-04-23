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

from screens.widgets import confirm_dialog, BG, CARD_BG, PURPLE, GREEN, RED, MUTED, WHITE, fmt_currency
from utils.helpers import month_label, prev_month, next_month, current_ym, fmt_date, today_str
from models.transaction import TransactionModel, FixedExpenseModel
from models.category import CategoryModel

Builder.load_string("""
<TransactionsScreen>:
    name: "tab_transactions"
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
                MDIconButton:
                    icon: "chevron-left"
                    on_release: root.prev_month()
                MDLabel:
                    id: month_lbl
                    text: ""
                    halign: "center"
                    font_style: "Subtitle1"
                    theme_text_color: "Custom"
                    text_color: 0.89, 0.91, 0.94, 1
                MDIconButton:
                    icon: "chevron-right"
                    on_release: root.next_month()
                MDIconButton:
                    icon: "calendar-today"
                    on_release: root.go_today()
            ScrollView:
                do_scroll_x: False
                MDBoxLayout:
                    id: tx_box
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(8), dp(8), dp(8), dp(80)
                    spacing: dp(4)
        MDFloatingActionButton:
            icon: "plus"
            md_bg_color: 0.13, 0.77, 0.37, 1
            pos_hint: {"right": 0.95, "y": 0.11}
            on_release: root.open_form("income")
        MDFloatingActionButton:
            icon: "minus"
            md_bg_color: 0.94, 0.27, 0.27, 1
            pos_hint: {"right": 0.95, "y": 0.02}
            on_release: root.open_form("expense")
""")


class TransactionsScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.year, self.month = current_ym()
        self._sel_cat = None

    def refresh(self):
        try:
            app = MDApp.get_running_app()
            if not hasattr(app, 'current_user') or not app.current_user:
                return
            uid = app.current_user["id"]
            self.ids.month_lbl.text = month_label(self.year, self.month)
            FixedExpenseModel.materialize_for_month(uid, self.year, self.month)
            txs = TransactionModel.get_by_period(uid, self.year, self.month)
            box = self.ids.tx_box
            box.clear_widgets()
            for t in txs:
                box.add_widget(self._make_card(t, uid))
        except Exception as e:
            from kivy.logger import Logger
            Logger.exception("FINANCAS: transactions refresh: {}".format(e))

    def _make_card(self, t, uid):
        is_inc = t["type"] == "income"
        color  = GREEN if is_inc else RED
        badge  = " Fix" if t.get("is_fixed") else (
                 " P{}x".format(t.get("installment_number","?")) if t.get("installment_id") else "")
        card = MDCard(
            orientation="horizontal",
            size_hint_y=None, height=dp(60),
            md_bg_color=CARD_BG, radius=[dp(8)],
            padding=[dp(12),dp(6)], spacing=dp(8))
        ind = MDBoxLayout(size_hint=(None,1), width=dp(4), md_bg_color=color)
        info = MDBoxLayout(orientation="vertical")
        info.add_widget(MDLabel(
            text="{}{}".format(t.get("description") or "—", badge),
            font_style="Body2", theme_text_color="Custom", text_color=WHITE,
            size_hint_y=None, height=dp(24), shorten=True, shorten_from="right"))
        info.add_widget(MDLabel(
            text="{} | {}".format(fmt_date(t["date"]), t.get("category_name") or "—"),
            font_style="Caption", theme_text_color="Secondary",
            size_hint_y=None, height=dp(18)))
        val = MDLabel(
            text=fmt_currency(t["amount"]),
            font_style="Body1", theme_text_color="Custom", text_color=color,
            size_hint=(None,1), width=dp(90), halign="right")
        card.add_widget(ind); card.add_widget(info); card.add_widget(val)
        card.bind(on_release=lambda x, td=dict(t): self._on_tx(td, uid))
        return card

    def _on_tx(self, t, uid):
        is_inst  = t.get("installment_id") is not None
        is_fixed = bool(t.get("is_fixed"))
        tipo = "Entrada" if t["type"] == "income" else "Despesa"
        obs  = "\n[Lancamento fixo - acao somente neste mes]" if is_fixed else (
               "\n[Parcela - nao pode ser editada]" if is_inst else "")
        dlg = [None]

        def on_close(*a): dlg[0].dismiss()

        def on_del(*a):
            dlg[0].dismiss()
            if is_fixed:
                # Busca feid direto do banco para garantir
                from database.schema import get_connection
                conn = get_connection()
                row = conn.execute(
                    "SELECT fixed_expense_id FROM transactions WHERE id=?", (t["id"],)).fetchone()
                conn.close()
                feid = (row["fixed_expense_id"] if row else None) or t.get("fixed_expense_id")
                if feid:
                    TransactionModel.delete_fixed_month(uid, t["id"], feid, self.year, self.month)
                else:
                    TransactionModel.delete(t["id"], uid)
            else:
                TransactionModel.delete(t["id"], uid)
            self.refresh()

        def on_edit(*a):
            dlg[0].dismiss()
            self._open_edit(t, uid)

        btns = [MDFlatButton(text="Fechar", on_release=on_close)]
        if not is_inst:
            btns.append(MDRaisedButton(text="Editar", md_bg_color=PURPLE, on_release=on_edit))
        btns.append(MDRaisedButton(text="Excluir", md_bg_color=RED, on_release=on_del))

        dlg[0] = MDDialog(
            title="{}: {}".format(tipo, fmt_currency(t["amount"])),
            text="{}{}".format(t.get("description") or "—", obs),
            buttons=btns)
        dlg[0].open()

    def _open_edit(self, t, uid):
        is_fixed = bool(t.get("is_fixed"))
        cats = CategoryModel.get_all(uid, t["type"])
        opts = [(c["id"], "{} {}".format(c.get("icon",""), c["name"])) for c in cats]
        self._sel_cat = t.get("category_id") or (opts[0][0] if opts else None)
        cur = next((nm for cid,nm in opts if cid==self._sel_cat), opts[0][1] if opts else "—")

        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(240), padding=[0,dp(8),0,0])
        f_amt  = MDTextField(hint_text="Valor", mode="rectangle", input_filter="float",
                             text="{:.2f}".format(t["amount"]), size_hint_y=None, height=dp(52))
        f_desc = MDTextField(hint_text="Descricao", mode="rectangle",
                             text=t.get("description") or "", size_hint_y=None, height=dp(52))
        f_date = MDTextField(hint_text="Data AAAA-MM-DD", mode="rectangle",
                             text=t["date"], size_hint_y=None, height=dp(52))
        btn_cat = MDRaisedButton(text=cur, size_hint=(1,None), height=dp(44), md_bg_color=CARD_BG)
        hint = MDLabel(
            text="Edicao afeta somente este mes" if is_fixed else "",
            font_style="Caption", theme_text_color="Secondary",
            size_hint_y=None, height=dp(20))

        def open_menu(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda cid=cid,n=nm: (
                          setattr(self,"_sel_cat",cid),
                          btn.__setattr__("text",n),
                          menu.dismiss())} for cid,nm in opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()
        btn_cat.bind(on_release=open_menu)
        for w in [f_amt, f_desc, f_date, btn_cat, hint]: content.add_widget(w)

        dlg = [None]
        def save(*a):
            try: amt = float(f_amt.text.replace(",","."))
            except: return
            date_s = f_date.text.strip() or t["date"]
            desc_s = f_desc.text.strip()
            if is_fixed and t.get("fixed_expense_id"):
                TransactionModel.delete_fixed_month(uid, t["id"], t["fixed_expense_id"], self.year, self.month)
                TransactionModel.create(uid, self._sel_cat, t["type"], amt, desc_s, date_s)
            else:
                TransactionModel.update(t["id"], uid, self._sel_cat, amt, desc_s, date_s)
            dlg[0].dismiss(); self.refresh()

        dlg[0] = MDDialog(title="Editar (este mes)", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                                   MDRaisedButton(text="Salvar", md_bg_color=GREEN, on_release=save)])
        dlg[0].open()

    def open_form(self, type_):
        uid  = MDApp.get_running_app().current_user["id"]
        cats = CategoryModel.get_all(uid, type_)
        opts = [(c["id"], "{} {}".format(c.get("icon",""), c["name"])) for c in cats]
        self._sel_cat = opts[0][0] if opts else None
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(220), padding=[0,dp(8),0,0])
        f_amt  = MDTextField(hint_text="Valor (ex: 150.00)", mode="rectangle",
                             input_filter="float", size_hint_y=None, height=dp(52))
        f_desc = MDTextField(hint_text="Descricao", mode="rectangle", size_hint_y=None, height=dp(52))
        f_date = MDTextField(hint_text="Data AAAA-MM-DD", mode="rectangle",
                             text="{:04d}-{:02d}-01".format(self.year, self.month),
                             size_hint_y=None, height=dp(52))
        btn_cat = MDRaisedButton(text=opts[0][1] if opts else "Categoria",
                                 size_hint=(1,None), height=dp(44), md_bg_color=CARD_BG)
        def open_menu(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda cid=cid,n=nm: (
                          setattr(self,"_sel_cat",cid),
                          btn.__setattr__("text",n),
                          menu.dismiss())} for cid,nm in opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()
        btn_cat.bind(on_release=open_menu)
        for w in [f_amt, f_desc, f_date, btn_cat]: content.add_widget(w)
        dlg = [None]
        def save(*a):
            try: amt = float(f_amt.text.replace(",","."))
            except: return
            TransactionModel.create(uid, self._sel_cat, type_, amt,
                                    f_desc.text.strip(), f_date.text.strip() or today_str())
            dlg[0].dismiss(); self.refresh()
        dlg[0] = MDDialog(
            title="Nova Entrada" if type_=="income" else "Nova Despesa",
            type="custom", content_cls=content,
            buttons=[MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                     MDRaisedButton(text="Salvar",
                                    md_bg_color=GREEN if type_=="income" else RED,
                                    on_release=save)])
        dlg[0].open()

    def prev_month(self): self.year, self.month = prev_month(self.year, self.month); self.refresh()
    def next_month(self): self.year, self.month = next_month(self.year, self.month); self.refresh()
    def go_today(self):   self.year, self.month = current_ym();                      self.refresh()
