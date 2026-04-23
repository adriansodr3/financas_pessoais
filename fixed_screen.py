from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.list import MDList, TwoLineIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.button import MDFloatingActionButton
from kivymd.app import MDApp

from screens.widgets import (confirm_dialog, BG, CARD_BG, PURPLE, GREEN, RED, MUTED, WHITE, fmt_currency)
from utils.helpers import today_str
from models.transaction import FixedExpenseModel
from models.category import CategoryModel


class FixedScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "tab_fixed"
        self._built = False

    def on_enter(self):
        if not self._built:
            self._build()
            self._built = True
        self.refresh()

    def _build(self):
        root = MDFloatLayout(md_bg_color=BG)

        col = MDBoxLayout(orientation="vertical", md_bg_color=BG, size_hint=(1, 1))

        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56),
                             padding=[16, 8], md_bg_color=CARD_BG)
        header.add_widget(MDLabel(text="Gastos & Receitas Fixos", font_style="Subtitle1",
                                  theme_text_color="Custom", text_color=WHITE))
        col.add_widget(header)

        info = MDLabel(
            text="Alteracoes so valem no mes seguinte.",
            font_style="Caption", theme_text_color="Custom", text_color=MUTED,
            size_hint_y=None, height=dp(28), halign="center")
        col.add_widget(info)

        sv = ScrollView()
        self._list = MDList()
        sv.add_widget(self._list)
        col.add_widget(sv)

        root.add_widget(col)

        fab = MDFloatingActionButton(icon="plus", md_bg_color=PURPLE,
                                     pos_hint={"right": 0.96, "y": 0.04},
                                     on_release=lambda *a: self._add())
        root.add_widget(fab)
        self.add_widget(root)

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self._list.clear_widgets()
        items = FixedExpenseModel.get_active(uid)
        for f in items:
            is_inc = f["type"] == "income"
            icon = "arrow-up-circle-outline" if is_inc else "arrow-down-circle-outline"
            item = TwoLineIconListItem(
                text=f"{f['description']}",
                secondary_text=f"{f.get('category_name','—')}  |  {fmt_currency(f['amount'])} / mes",
                on_release=lambda x, fd=dict(f): self._on_item(fd)
            )
            ico = IconLeftWidget(icon=icon, theme_icon_color="Custom",
                                 icon_color=GREEN if is_inc else RED)
            item.add_widget(ico)
            self._list.add_widget(item)

    def _on_item(self, f):
        app = MDApp.get_running_app()
        uid = app.current_user["id"]
        tp = "Entrada" if f["type"] == "income" else "Despesa"
        info = f"{tp}: {fmt_currency(f['amount'])}/mes\n{f['description']}"

        def do_delete():
            FixedExpenseModel.deactivate(f["id"], uid)
            self.refresh()

        confirm_dialog("Desativar fixo", info + "\n\nDesativar este lancamento fixo?",
                       do_delete, "Desativar", danger=True)

    def _add(self):
        app = MDApp.get_running_app()
        uid = app.current_user["id"]

        content = MDBoxLayout(orientation="vertical", spacing=8,
                              size_hint_y=None, height=dp(260), padding=[0, 8, 0, 0])

        type_options = [("expense", "⬇ Despesa"), ("income", "⬆ Entrada")]
        self._sel_type = "expense"
        self._sel_cat = None

        btn_type = MDRaisedButton(text="⬇ Despesa", size_hint=(1, None),
                                  height=dp(40), md_bg_color=RED)

        def open_type_menu(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda t=tp, n=nm: (
                          setattr(self, '_sel_type', t),
                          btn.__setattr__('text', n),
                          btn.__setattr__('md_bg_color', RED if t == 'expense' else GREEN),
                          reload_cats(),
                          menu.dismiss()
                      )} for tp, nm in type_options]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=3)
            menu.open()
        btn_type.bind(on_release=open_type_menu)

        cats = CategoryModel.get_all(uid, "expense")
        cat_options = [(c["id"], f"{c.get('icon','')} {c['name']}") for c in cats]
        self._sel_cat = cat_options[0][0] if cat_options else None
        btn_cat = MDRaisedButton(
            text=cat_options[0][1] if cat_options else "Categoria",
            size_hint=(1, None), height=dp(40), md_bg_color=CARD_BG)

        def reload_cats():
            cs = CategoryModel.get_all(uid, self._sel_type)
            opts = [(c["id"], f"{c.get('icon','')} {c['name']}") for c in cs]
            self._sel_cat = opts[0][0] if opts else None
            btn_cat.text = opts[0][1] if opts else "Categoria"
            btn_cat._cat_opts = opts

        btn_cat._cat_opts = cat_options

        def open_cat_menu(btn):
            from kivymd.uix.menu import MDDropdownMenu
            opts = getattr(btn, '_cat_opts', cat_options)
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda cid=cid, n=nm: (
                          setattr(self, '_sel_cat', cid),
                          btn.__setattr__('text', n),
                          menu.dismiss()
                      )} for cid, nm in opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()
        btn_cat.bind(on_release=open_cat_menu)

        f_desc = MDTextField(hint_text="Descricao (ex: Aluguel)", mode="rectangle",
                             size_hint_y=None, height=dp(48))
        f_amount = MDTextField(hint_text="Valor (ex: 1200.00)", mode="rectangle",
                               input_filter="float", size_hint_y=None, height=dp(48))

        for w in [btn_type, btn_cat, f_desc, f_amount]:
            content.add_widget(w)

        def save(*a):
            try:
                amt = float(f_amount.text.replace(",", "."))
            except Exception:
                return
            if not f_desc.text.strip():
                return
            FixedExpenseModel.create(uid, self._sel_cat, self._sel_type,
                                     amt, f_desc.text.strip())
            dlg.dismiss()
            self.refresh()

        dlg = MDDialog(title="Novo Fixo", type="custom", content_cls=content,
                       buttons=[
                           MDFlatButton(text="Cancelar", on_release=lambda x: dlg.dismiss()),
                           MDRaisedButton(text="Salvar", md_bg_color=PURPLE, on_release=save)])
        dlg.open()
