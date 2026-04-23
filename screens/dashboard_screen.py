from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.list import MDList, TwoLineIconListItem, IconLeftWidget
from kivymd.app import MDApp

from screens.widgets import (summary_card, update_card, month_nav_bar,
                              BG, CARD_BG, GREEN, RED, ORANGE, PURPLE, MUTED, WHITE, fmt_currency)
from utils.helpers import month_label, prev_month, next_month, current_ym, fmt_date
from models.transaction import TransactionModel, FixedExpenseModel


class DashboardScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "tab_dashboard"
        self.year, self.month = current_ym()
        self._built = False

    def on_enter(self):
        if not self._built:
            self._build()
            self._built = True
        self.refresh()

    def _build(self):
        root = MDBoxLayout(orientation="vertical", md_bg_color=BG)

        nav, self._month_lbl = month_nav_bar(self._prev, self._next, self._today)
        root.add_widget(nav)

        sv = ScrollView(size_hint=(1, 1))
        content = MDBoxLayout(
            orientation="vertical", spacing=dp(10),
            padding=[dp(10), dp(10), dp(10), dp(10)],
            size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # Linha 1: Entradas | Saidas
        row1 = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(80))
        self.c_income  = summary_card("ENTRADAS+SALDO ANT.", 0, GREEN)
        self.c_expense = summary_card("SAIDAS DO MES", 0, RED)
        row1.add_widget(self.c_income)
        row1.add_widget(self.c_expense)
        content.add_widget(row1)

        # Linha 2: Saldo | Fixos | Falta Pagar
        row2 = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(80))
        self.c_balance  = summary_card("SALDO", 0, PURPLE)
        self.c_fixed    = summary_card("FIXOS", 0, RED)
        self.c_pending  = summary_card("FALTA PAGAR", 0, ORANGE)
        row2.add_widget(self.c_balance)
        row2.add_widget(self.c_fixed)
        row2.add_widget(self.c_pending)
        content.add_widget(row2)

        # Botoes de acao
        btn_row = MDBoxLayout(
            orientation="horizontal", spacing=dp(8),
            size_hint_y=None, height=dp(52))
        btn_inc = MDRaisedButton(
            text="+ Entrada", md_bg_color=GREEN,
            size_hint=(1, None), height=dp(44),
            on_release=lambda *a: self._open_form("income"))
        btn_exp = MDRaisedButton(
            text="- Despesa", md_bg_color=RED,
            size_hint=(1, None), height=dp(44),
            on_release=lambda *a: self._open_form("expense"))
        btn_row.add_widget(btn_inc)
        btn_row.add_widget(btn_exp)
        content.add_widget(btn_row)

        content.add_widget(MDLabel(
            text="Lancamentos do mes", font_style="Overline",
            theme_text_color="Custom", text_color=MUTED,
            size_hint_y=None, height=dp(28), halign="left"))

        self._tx_list = MDList(size_hint_y=None)
        self._tx_list.bind(minimum_height=self._tx_list.setter("height"))
        content.add_widget(self._tx_list)

        sv.add_widget(content)
        root.add_widget(sv)
        self.add_widget(root)

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self._month_lbl.text = month_label(self.year, self.month)

        FixedExpenseModel.materialize_for_month(uid, self.year, self.month)
        txs = TransactionModel.get_by_period(uid, self.year, self.month)
        income  = sum(t["amount"] for t in txs if t["type"] == "income")
        expense = sum(t["amount"] for t in txs if t["type"] == "expense")
        balance = income - expense

        prev_bal = TransactionModel.get_balance_before_month(uid, self.year, self.month)
        income_w = income + max(prev_bal, 0)

        fixed = FixedExpenseModel.get_for_month(uid, self.year, self.month)
        fixed_total = sum(f["amount"] for f in fixed if f["type"] == "expense")
        pending = TransactionModel.get_pending_expenses_from(uid, self.year, self.month)

        update_card(self.c_income,  income_w, GREEN)
        update_card(self.c_expense, expense, RED)
        update_card(self.c_balance, balance, GREEN if balance >= 0 else RED)
        update_card(self.c_fixed,   fixed_total, RED)
        update_card(self.c_pending, pending, ORANGE)

        self._tx_list.clear_widgets()
        for t in txs[:25]:
            is_inc = t["type"] == "income"
            icon = "arrow-up-circle-outline" if is_inc else "arrow-down-circle-outline"
            badge = " Fix" if t.get("is_fixed") else (
                " P{}x".format(t.get("installment_number", "?")) if t.get("installment_id") else "")
            item = TwoLineIconListItem(
                text="{}{}".format(t.get("description") or "—", badge),
                secondary_text="{} | {} | {}".format(
                    fmt_date(t["date"]),
                    t.get("category_name") or "—",
                    fmt_currency(t["amount"])),
                on_release=lambda x, td=dict(t): self._on_tx(td))
            ico = IconLeftWidget(
                icon=icon, theme_icon_color="Custom",
                icon_color=GREEN if is_inc else RED)
            item.add_widget(ico)
            self._tx_list.add_widget(item)

    def _on_tx(self, t):
        from screens.widgets import confirm_dialog
        from models.transaction import TransactionModel as TM
        app = MDApp.get_running_app()
        uid = app.current_user["id"]

        def do_del():
            TM.delete(t["id"], uid)
            self.refresh()

        tipo = "Entrada" if t["type"] == "income" else "Despesa"
        confirm_dialog(
            "Excluir lancamento",
            "{}: {}\n{}\n{}".format(tipo, fmt_currency(t["amount"]),
                                     t.get("description", ""), fmt_date(t["date"])),
            do_del, "Excluir", danger=True)

    def _open_form(self, type_):
        app = MDApp.get_running_app()
        uid = app.current_user["id"]
        from models.category import CategoryModel
        from models.transaction import TransactionModel as TM
        from utils.helpers import today_str
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDRaisedButton, MDFlatButton
        cats = CategoryModel.get_all(uid, type_)
        cat_opts = [(c["id"], "{} {}".format(c.get("icon",""), c["name"])) for c in cats]
        self._sel_cat = cat_opts[0][0] if cat_opts else None

        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(220), padding=[0, dp(8), 0, 0])
        f_amt  = MDTextField(hint_text="Valor (ex: 150.00)", mode="rectangle",
                             input_filter="float", size_hint_y=None, height=dp(52))
        f_desc = MDTextField(hint_text="Descricao", mode="rectangle",
                             size_hint_y=None, height=dp(52))
        f_date = MDTextField(hint_text="Data (AAAA-MM-DD)", mode="rectangle",
                             text="{:04d}-{:02d}-01".format(self.year, self.month),
                             size_hint_y=None, height=dp(52))
        btn_cat = MDRaisedButton(
            text=cat_opts[0][1] if cat_opts else "Categoria",
            size_hint=(1, None), height=dp(44), md_bg_color=CARD_BG)

        def open_menu(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda cid=cid, n=nm: (
                          setattr(self, "_sel_cat", cid),
                          btn.__setattr__("text", n),
                          menu.dismiss())} for cid, nm in cat_opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()
        btn_cat.bind(on_release=open_menu)

        for w in [f_amt, f_desc, f_date, btn_cat]:
            content.add_widget(w)

        dlg = [None]

        def save(*a):
            try:
                amt = float(f_amt.text.replace(",", "."))
            except Exception:
                return
            TM.create(uid, self._sel_cat, type_, amt,
                      f_desc.text.strip(), f_date.text.strip() or today_str())
            dlg[0].dismiss()
            self.refresh()

        title = "Nova Entrada" if type_ == "income" else "Nova Despesa"
        dlg[0] = MDDialog(
            title=title, type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                MDRaisedButton(text="Salvar",
                               md_bg_color=GREEN if type_ == "income" else RED,
                               on_release=save)])
        dlg[0].open()

    def _prev(self):
        self.year, self.month = prev_month(self.year, self.month)
        self.refresh()

    def _next(self):
        self.year, self.month = next_month(self.year, self.month)
        self.refresh()

    def _today(self):
        self.year, self.month = current_ym()
        self.refresh()
