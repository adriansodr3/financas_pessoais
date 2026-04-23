from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.list import MDList, TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

from screens.widgets import BG, CARD_BG, GREEN, RED, ORANGE, PURPLE, MUTED, WHITE, fmt_currency
from utils.helpers import month_label, prev_month, next_month, current_ym, fmt_date, today_str
from models.transaction import TransactionModel, FixedExpenseModel


Builder.load_string("""
<DashboardScreen>:
    name: "tab_dashboard"
    md_bg_color: 0.06, 0.07, 0.09, 1
    BoxLayout:
        orientation: "vertical"
        # Barra de navegacao de mes
        MDBoxLayout:
            id: nav_bar
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
        # Conteudo principal
        ScrollView:
            do_scroll_x: False
            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(10), dp(10), dp(10), dp(10)
                spacing: dp(8)
                # Cards linha 1
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(76)
                    spacing: dp(8)
                    MDCard:
                        id: card_income
                        md_bg_color: 0.10, 0.11, 0.15, 1
                        radius: [dp(10)]
                        padding: dp(10), dp(8)
                        orientation: "vertical"
                        MDLabel:
                            text: "ENTRADAS+SALDO"
                            font_style: "Overline"
                            theme_text_color: "Custom"
                            text_color: 0.58, 0.64, 0.72, 1
                            size_hint_y: None
                            height: dp(20)
                            halign: "left"
                        MDLabel:
                            id: lbl_income
                            text: "R$ 0,00"
                            font_style: "H6"
                            theme_text_color: "Custom"
                            text_color: 0.13, 0.77, 0.37, 1
                            halign: "left"
                    MDCard:
                        id: card_expense
                        md_bg_color: 0.10, 0.11, 0.15, 1
                        radius: [dp(10)]
                        padding: dp(10), dp(8)
                        orientation: "vertical"
                        MDLabel:
                            text: "SAIDAS"
                            font_style: "Overline"
                            theme_text_color: "Custom"
                            text_color: 0.58, 0.64, 0.72, 1
                            size_hint_y: None
                            height: dp(20)
                            halign: "left"
                        MDLabel:
                            id: lbl_expense
                            text: "R$ 0,00"
                            font_style: "H6"
                            theme_text_color: "Custom"
                            text_color: 0.94, 0.27, 0.27, 1
                            halign: "left"
                # Cards linha 2
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(76)
                    spacing: dp(8)
                    MDCard:
                        md_bg_color: 0.10, 0.11, 0.15, 1
                        radius: [dp(10)]
                        padding: dp(10), dp(8)
                        orientation: "vertical"
                        MDLabel:
                            text: "SALDO"
                            font_style: "Overline"
                            theme_text_color: "Custom"
                            text_color: 0.58, 0.64, 0.72, 1
                            size_hint_y: None
                            height: dp(20)
                            halign: "left"
                        MDLabel:
                            id: lbl_balance
                            text: "R$ 0,00"
                            font_style: "H6"
                            theme_text_color: "Custom"
                            text_color: 0.39, 0.40, 0.95, 1
                            halign: "left"
                    MDCard:
                        md_bg_color: 0.10, 0.11, 0.15, 1
                        radius: [dp(10)]
                        padding: dp(10), dp(8)
                        orientation: "vertical"
                        MDLabel:
                            text: "FIXOS"
                            font_style: "Overline"
                            theme_text_color: "Custom"
                            text_color: 0.58, 0.64, 0.72, 1
                            size_hint_y: None
                            height: dp(20)
                            halign: "left"
                        MDLabel:
                            id: lbl_fixed
                            text: "R$ 0,00"
                            font_style: "H6"
                            theme_text_color: "Custom"
                            text_color: 0.94, 0.27, 0.27, 1
                            halign: "left"
                    MDCard:
                        md_bg_color: 0.10, 0.11, 0.15, 1
                        radius: [dp(10)]
                        padding: dp(10), dp(8)
                        orientation: "vertical"
                        MDLabel:
                            text: "FALTA PAGAR"
                            font_style: "Overline"
                            theme_text_color: "Custom"
                            text_color: 0.58, 0.64, 0.72, 1
                            size_hint_y: None
                            height: dp(20)
                            halign: "left"
                        MDLabel:
                            id: lbl_pending
                            text: "R$ 0,00"
                            font_style: "H6"
                            theme_text_color: "Custom"
                            text_color: 0.98, 0.60, 0.22, 1
                            halign: "left"
                # Botoes
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(52)
                    spacing: dp(8)
                    MDRaisedButton:
                        text: "+ Entrada"
                        md_bg_color: 0.13, 0.77, 0.37, 1
                        size_hint: 1, None
                        height: dp(44)
                        on_release: root.open_form("income")
                    MDRaisedButton:
                        text: "- Despesa"
                        md_bg_color: 0.94, 0.27, 0.27, 1
                        size_hint: 1, None
                        height: dp(44)
                        on_release: root.open_form("expense")
                # Label
                MDLabel:
                    text: "Lancamentos"
                    font_style: "Overline"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(28)
                    halign: "left"
                # Lista
                MDList:
                    id: tx_list
                    size_hint_y: None
                    height: self.minimum_height
""")


class DashboardScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.year, self.month = current_ym()
        self._built = False

    def on_enter(self):
        self.refresh()

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self.ids.month_lbl.text = month_label(self.year, self.month)

        FixedExpenseModel.materialize_for_month(uid, self.year, self.month)
        txs     = TransactionModel.get_by_period(uid, self.year, self.month)
        income  = sum(t["amount"] for t in txs if t["type"] == "income")
        expense = sum(t["amount"] for t in txs if t["type"] == "expense")
        balance = income - expense
        prev    = TransactionModel.get_balance_before_month(uid, self.year, self.month)
        fixed_l = FixedExpenseModel.get_for_month(uid, self.year, self.month)
        fixed   = sum(f["amount"] for f in fixed_l if f["type"] == "expense")
        pending = TransactionModel.get_pending_expenses_from(uid, self.year, self.month)

        self.ids.lbl_income.text  = fmt_currency(income + max(prev, 0))
        self.ids.lbl_expense.text = fmt_currency(expense)
        self.ids.lbl_balance.text = fmt_currency(balance)
        self.ids.lbl_balance.text_color = GREEN if balance >= 0 else RED
        self.ids.lbl_fixed.text   = fmt_currency(fixed)
        self.ids.lbl_pending.text = fmt_currency(pending)

        self.ids.tx_list.clear_widgets()
        for t in txs[:20]:
            is_inc = t["type"] == "income"
            badge  = " Fix" if t.get("is_fixed") else (
                " P{}x".format(t.get("installment_number", "?")) if t.get("installment_id") else "")
            item = TwoLineIconListItem(
                text="{}{}".format(t.get("description") or "—", badge),
                secondary_text="{} | {}".format(
                    fmt_date(t["date"]), fmt_currency(t["amount"])),
                on_release=lambda x, td=dict(t): self._on_tx(td))
            ico = IconLeftWidget(
                icon="arrow-up-circle-outline" if is_inc else "arrow-down-circle-outline",
                theme_icon_color="Custom",
                icon_color=GREEN if is_inc else RED)
            item.add_widget(ico)
            self.ids.tx_list.add_widget(item)

    def _on_tx(self, t):
        uid = MDApp.get_running_app().current_user["id"]
        def do_del():
            TransactionModel.delete(t["id"], uid)
            self.refresh()
        from screens.widgets import confirm_dialog
        confirm_dialog(
            "Excluir",
            "{}: {}\n{}".format(
                "Entrada" if t["type"]=="income" else "Despesa",
                fmt_currency(t["amount"]),
                t.get("description", "")),
            do_del, "Excluir", danger=True)

    def open_form(self, type_):
        uid  = MDApp.get_running_app().current_user["id"]
        from models.category import CategoryModel
        cats = CategoryModel.get_all(uid, type_)
        opts = [(c["id"], "{} {}".format(c.get("icon",""), c["name"])) for c in cats]
        self._sel_cat = opts[0][0] if opts else None

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
            text=opts[0][1] if opts else "Categoria",
            size_hint=(1, None), height=dp(44), md_bg_color=CARD_BG)

        def open_menu(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda cid=cid, n=nm: (
                          setattr(self, "_sel_cat", cid),
                          btn.__setattr__("text", n),
                          menu.dismiss())} for cid, nm in opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()
        btn_cat.bind(on_release=open_menu)

        for w in [f_amt, f_desc, f_date, btn_cat]:
            content.add_widget(w)
        dlg = [None]

        def save(*a):
            try: amt = float(f_amt.text.replace(",", "."))
            except: return
            TransactionModel.create(uid, self._sel_cat, type_, amt,
                                    f_desc.text.strip(),
                                    f_date.text.strip() or today_str())
            dlg[0].dismiss()
            self.refresh()

        dlg[0] = MDDialog(
            title="Nova Entrada" if type_=="income" else "Nova Despesa",
            type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                MDRaisedButton(text="Salvar",
                               md_bg_color=GREEN if type_=="income" else RED,
                               on_release=save)])
        dlg[0].open()

    def prev_month(self):
        self.year, self.month = prev_month(self.year, self.month); self.refresh()
    def next_month(self):
        self.year, self.month = next_month(self.year, self.month); self.refresh()
    def go_today(self):
        self.year, self.month = current_ym(); self.refresh()
