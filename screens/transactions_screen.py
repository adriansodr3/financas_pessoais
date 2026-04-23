from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.list import MDList, TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.button import MDFloatingActionButton
from kivymd.app import MDApp

from screens.widgets import (month_nav_bar, confirm_dialog, BG, CARD_BG,
                              PURPLE, GREEN, RED, ORANGE, MUTED, WHITE, fmt_currency)
from utils.helpers import month_label, prev_month, next_month, current_ym, fmt_date, today_str
from models.transaction import TransactionModel, FixedExpenseModel
from models.category import CategoryModel


class TransactionsScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "tab_transactions"
        self.year, self.month = current_ym()
        self._built = False

    def on_enter(self):
        if not self._built:
            self._build()
            self._built = True
        self.refresh()

    def _build(self):
        root = FloatLayout(md_bg_color=BG)

        col = MDBoxLayout(orientation="vertical", md_bg_color=BG,
                          size_hint=(1, 1), pos_hint={"top": 1})

        nav, self._month_lbl = month_nav_bar(self._prev, self._next, self._today)
        col.add_widget(nav)

        sv = ScrollView()
        self._list = MDList()
        sv.add_widget(self._list)
        col.add_widget(sv)

        root.add_widget(col)

        # FAB
        fab_row = MDBoxLayout(orientation="horizontal", size_hint=(None, None),
                               height=dp(140), width=dp(180),
                               spacing=8, padding=16,
                               pos_hint={"right": 1, "y": 0})
        fab_income = MDFloatingActionButton(
            icon="plus", md_bg_color=GREEN,
            on_release=lambda *a: self._open_form("income"))
        fab_expense = MDFloatingActionButton(
            icon="minus", md_bg_color=RED,
            on_release=lambda *a: self._open_form("expense"))
        fab_row.add_widget(fab_income)
        fab_row.add_widget(fab_expense)
        root.add_widget(fab_row)

        self.add_widget(root)

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self._month_lbl.text = month_label(self.year, self.month)
        FixedExpenseModel.materialize_for_month(uid, self.year, self.month)
        txs = TransactionModel.get_by_period(uid, self.year, self.month)
        self._list.clear_widgets()
        for t in txs:
            is_inc = t["type"] == "income"
            icon = "arrow-up-circle-outline" if is_inc else "arrow-down-circle-outline"
            badge = ""
            if t.get("is_fixed"):
                badge = " 📌"
            elif t.get("installment_id"):
                badge = f" 🗂{t.get('installment_number','?')}x"
            item = TwoLineIconListItem(
                text=f"{t.get('description') or '—'}{badge}",
                secondary_text=f"{fmt_date(t['date'])}  {t.get('category_name') or '—'}  {fmt_currency(t['amount'])}",
                on_release=lambda x, tid=t["id"], td=dict(t): self._on_item(tid, td)
            )
            ico = IconLeftWidget(icon=icon, theme_icon_color="Custom",
                                 icon_color=GREEN if is_inc else RED)
            item.add_widget(ico)
            self._list.add_widget(item)

    def _on_item(self, tid, t):
        app = MDApp.get_running_app()
        uid = app.current_user["id"]
        type_lbl = "Entrada" if t["type"] == "income" else "Despesa"
        info = f"{type_lbl}: {fmt_currency(t['amount'])}\n{t.get('description','')}\n{fmt_date(t['date'])}"

        def do_delete():
            TransactionModel.delete(tid, uid)
            self.refresh()
            MDApp.get_running_app().root.get_screen("main").refresh_dashboard()

        is_fixed = bool(t.get("is_fixed"))
        is_inst = t.get("installment_id") is not None

        if is_inst:
            txt = info + "\n\nEste e um lancamento de parcelamento.\nExcluir so esta parcela?"
        elif is_fixed:
            txt = info + "\n\nEste e um lancamento fixo.\nExcluir so este mes?"
        else:
            txt = info + "\n\nConfirmar exclusao?"

        confirm_dialog("Excluir", txt, do_delete, "Excluir", danger=True)

    def _open_form(self, type_):
        app = MDApp.get_running_app()
        uid = app.current_user["id"]
        cats = CategoryModel.get_all(uid, type_)

        content = MDBoxLayout(orientation="vertical", spacing=8,
                              size_hint_y=None, height=dp(220), padding=[0, 8, 0, 0])
        f_amount = MDTextField(hint_text="Valor (ex: 150.00)", mode="rectangle",
                               input_filter="float", size_hint_y=None, height=dp(48))
        f_desc = MDTextField(hint_text="Descricao", mode="rectangle",
                             size_hint_y=None, height=dp(48))
        f_date = MDTextField(hint_text="Data (AAAA-MM-DD)", mode="rectangle",
                             text=f"{self.year:04d}-{self.month:02d}-01",
                             size_hint_y=None, height=dp(48))

        cat_options = [(c["id"], f"{c.get('icon','')} {c['name']}") for c in cats]
        self._sel_cat = cat_options[0][0] if cat_options else None

        btn_cat = MDRaisedButton(
            text=cat_options[0][1] if cat_options else "Categoria",
            size_hint=(1, None), height=dp(40), md_bg_color=CARD_BG)

        def open_menu(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda n=nm, cid=cid: (
                          setattr(self, '_sel_cat', cid),
                          btn.__setattr__('text', n),
                          menu.dismiss()
                      )} for cid, nm in cat_options]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()

        btn_cat.bind(on_release=open_menu)

        for w in [f_amount, f_desc, f_date, btn_cat]:
            content.add_widget(w)

        def save(*a):
            try:
                amt = float(f_amount.text.replace(",", "."))
            except Exception:
                return
            date_s = f_date.text.strip() or today_str()
            TransactionModel.create(uid, self._sel_cat, type_, amt,
                                    f_desc.text.strip(), date_s)
            dlg.dismiss()
            self.refresh()
            MDApp.get_running_app().root.get_screen("main").refresh_dashboard()

        title = "Nova Entrada" if type_ == "income" else "Nova Despesa"
        dlg = MDDialog(title=title, type="custom", content_cls=content,
                       buttons=[
                           MDFlatButton(text="Cancelar", on_release=lambda x: dlg.dismiss()),
                           MDRaisedButton(text="Salvar",
                                          md_bg_color=GREEN if type_ == "income" else RED,
                                          on_release=save)])
        dlg.open()

    def _prev(self):
        self.year, self.month = prev_month(self.year, self.month)
        self.refresh()

    def _next(self):
        self.year, self.month = next_month(self.year, self.month)
        self.refresh()

    def _today(self):
        self.year, self.month = current_ym()
        self.refresh()
