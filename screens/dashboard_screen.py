from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.list import MDList, TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

from screens.widgets import (summary_card, update_card, month_nav_bar,
                              confirm_dialog, BG, CARD_BG, PURPLE, GREEN,
                              RED, ORANGE, MUTED, WHITE, fmt_currency)
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

        # Navegacao de mes
        nav, self._month_lbl = month_nav_bar(self._prev, self._next, self._today)
        root.add_widget(nav)

        sv = ScrollView()
        content = MDBoxLayout(orientation="vertical", spacing=12,
                              padding=[12, 12, 12, 12],
                              size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # Cards linha 1
        row1 = GridLayout(cols=2, spacing=8, size_hint_y=None, height=dp(88))
        self.c_income = summary_card("ENTRADAS+SALDO ANT.", 0, GREEN)
        self.c_expense = summary_card("SAIDAS DO MES", 0, RED)
        row1.add_widget(self.c_income)
        row1.add_widget(self.c_expense)
        content.add_widget(row1)

        # Cards linha 2
        row2 = GridLayout(cols=3, spacing=8, size_hint_y=None, height=dp(88))
        self.c_balance = summary_card("SALDO", 0, PURPLE)
        self.c_fixed = summary_card("FIXOS", 0, RED)
        self.c_pending = summary_card("FALTA PAGAR", 0, ORANGE)
        row2.add_widget(self.c_balance)
        row2.add_widget(self.c_fixed)
        row2.add_widget(self.c_pending)
        content.add_widget(row2)

        # Botoes de acao
        btn_row = MDBoxLayout(orientation="horizontal", spacing=8,
                              size_hint_y=None, height=dp(48))
        btn_inc = MDRaisedButton(text="+ Entrada", md_bg_color=GREEN,
                                 on_release=lambda *a: self._open_form("income"))
        btn_exp = MDRaisedButton(text="- Despesa", md_bg_color=RED,
                                 on_release=lambda *a: self._open_form("expense"))
        btn_row.add_widget(btn_inc)
        btn_row.add_widget(btn_exp)
        content.add_widget(btn_row)

        # Lista de lancamentos
        lbl_tx = MDLabel(text="Lancamentos do mes", font_style="Subtitle2",
                         theme_text_color="Custom", text_color=MUTED,
                         size_hint_y=None, height=dp(28))
        content.add_widget(lbl_tx)

        self._tx_list = MDList()
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
        income = sum(t["amount"] for t in txs if t["type"] == "income")
        expense = sum(t["amount"] for t in txs if t["type"] == "expense")
        balance = income - expense

        prev_bal = TransactionModel.get_balance_before_month(uid, self.year, self.month)
        income_w = income + max(prev_bal, 0)

        fixed = FixedExpenseModel.get_for_month(uid, self.year, self.month)
        fixed_total = sum(f["amount"] for f in fixed if f["type"] == "expense")
        pending = TransactionModel.get_pending_expenses_from(uid, self.year, self.month)

        update_card(self.c_income, income_w, GREEN)
        update_card(self.c_expense, expense, RED)
        update_card(self.c_balance, balance, GREEN if balance >= 0 else RED)
        update_card(self.c_fixed, fixed_total, RED)
        update_card(self.c_pending, pending, ORANGE)

        # Preencher lista
        self._tx_list.clear_widgets()
        self._transactions = txs
        for t in txs[:30]:
            is_inc = t["type"] == "income"
            icon = "arrow-up-circle" if is_inc else "arrow-down-circle"
            color = "[color=22c55e]" if is_inc else "[color=ef4444]"
            amt = f"{color}{fmt_currency(t['amount'])}[/color]"
            badge = ""
            if t.get("is_fixed"):
                badge = " 📌"
            elif t.get("installment_id"):
                badge = f" 🗂{t.get('installment_number','?')}x"

            item = TwoLineIconListItem(
                text=f"{t.get('description') or '—'}{badge}",
                secondary_text=f"{fmt_date(t['date'])}  |  {t.get('category_name') or '—'}  |  {fmt_currency(t['amount'])}",
                on_release=lambda x, tid=t["id"], td=dict(t): self._edit_tx(tid, td)
            )
            ico = IconLeftWidget(icon=icon,
                                 theme_icon_color="Custom",
                                 icon_color=GREEN if is_inc else RED)
            item.add_widget(ico)
            self._tx_list.add_widget(item)

    def _open_form(self, type_):
        app = MDApp.get_running_app()
        uid = app.current_user["id"]
        from models.category import CategoryModel
        cats = CategoryModel.get_all(uid, type_)

        content = MDBoxLayout(orientation="vertical", spacing=8,
                              size_hint_y=None, height=dp(260),
                              padding=[0, 8, 0, 0])
        f_amount = MDTextField(hint_text="Valor (ex: 150.00)", mode="rectangle",
                               input_filter="float", size_hint_y=None, height=dp(48))
        f_desc = MDTextField(hint_text="Descricao", mode="rectangle",
                             size_hint_y=None, height=dp(48))
        f_date = MDTextField(hint_text="Data (AAAA-MM-DD)", mode="rectangle",
                             text=__import__('utils.helpers', fromlist=['today_str']).today_str(),
                             size_hint_y=None, height=dp(48))

        from kivymd.uix.menu import MDDropdownMenu
        cat_options = [(c["id"], f"{c.get('icon','')} {c['name']}") for c in cats]
        self._sel_cat_id = cat_options[0][0] if cat_options else None

        btn_cat = MDRaisedButton(
            text=cat_options[0][1] if cat_options else "Categoria",
            size_hint_y=None, height=dp(40),
            md_bg_color=CARD_BG)

        def open_cat_menu(btn):
            items = [{"text": name, "viewclass": "OneLineListItem",
                      "on_release": lambda n=name, cid=cid: (
                          setattr(self, '_sel_cat_id', cid),
                          btn.__setattr__('text', n),
                          menu.dismiss()
                      )} for cid, name in cat_options]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()

        btn_cat.bind(on_release=open_cat_menu)

        for w in [f_amount, f_desc, f_date, btn_cat]:
            content.add_widget(w)

        title = "Nova Entrada" if type_ == "income" else "Nova Despesa"

        def save(*a):
            try:
                amt = float(f_amount.text.replace(",", "."))
            except Exception:
                return
            desc = f_desc.text.strip()
            date_s = f_date.text.strip() or __import__('utils.helpers', fromlist=['today_str']).today_str()
            TransactionModel.create(uid, self._sel_cat_id, type_, amt, desc, date_s)
            dlg.dismiss()
            self.refresh()

        dlg = MDDialog(title=title, type="custom", content_cls=content,
                       buttons=[
                           MDFlatButton(text="Cancelar", on_release=lambda x: dlg.dismiss()),
                           MDRaisedButton(text="Salvar", md_bg_color=GREEN if type_ == "income" else RED,
                                          on_release=save)])
        dlg.open()

    def _edit_tx(self, tid, t):
        def do_delete():
            TransactionModel.delete(tid, MDApp.get_running_app().current_user["id"])
            self.refresh()

        is_fixed = bool(t.get("is_fixed"))
        is_inst = t.get("installment_id") is not None
        type_lbl = "Entrada" if t["type"] == "income" else "Despesa"
        info = f"{type_lbl}: {fmt_currency(t['amount'])}\n{t.get('description','')}\n{fmt_date(t['date'])}"

        if is_inst:
            confirm_dialog("Excluir parcela", info + "\n\nExcluir so esta parcela?",
                           do_delete, "Excluir", danger=True)
        elif is_fixed:
            confirm_dialog("Excluir lancamento fixo", info + "\n\nExcluir so este mes?",
                           do_delete, "So este mes", danger=True)
        else:
            confirm_dialog("Excluir lancamento", info, do_delete, "Excluir", danger=True)

    def _prev(self):
        self.year, self.month = prev_month(self.year, self.month)
        self.refresh()

    def _next(self):
        self.year, self.month = next_month(self.year, self.month)
        self.refresh()

    def _today(self):
        self.year, self.month = current_ym()
        self.refresh()
