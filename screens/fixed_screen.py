from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.list import MDList, TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp
from screens.widgets import confirm_dialog, BG, CARD_BG, PURPLE, GREEN, RED, MUTED, WHITE, fmt_currency
from models.transaction import FixedExpenseModel
from models.category import CategoryModel

Builder.load_string("""
<FixedScreen>:
    name: "tab_fixed"
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
                    text: "Gastos e Receitas Fixos"
                    font_style: "Subtitle1"
                    theme_text_color: "Custom"
                    text_color: 0.89, 0.91, 0.94, 1
                    padding_x: dp(16)
            MDLabel:
                text: "Alteracoes valem a partir do proximo mes"
                font_style: "Caption"
                theme_text_color: "Secondary"
                size_hint_y: None
                height: dp(28)
                halign: "center"
            ScrollView:
                do_scroll_x: False
                MDList:
                    id: fixed_list
                    size_hint_y: None
                    height: self.minimum_height
        MDFloatingActionButton:
            icon: "plus"
            md_bg_color: 0.39, 0.40, 0.95, 1
            pos_hint: {"right": 0.95, "y": 0.02}
            on_release: root.add_fixed()
""")


class FixedScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._sel_type = "expense"
        self._sel_cat = None

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self.ids.fixed_list.clear_widgets()
        for f in FixedExpenseModel.get_active(uid):
            is_inc = f["type"] == "income"
            item = TwoLineIconListItem(
                text=f["description"],
                secondary_text="{} | {} / mes".format(
                    f.get("category_name") or "—", fmt_currency(f["amount"])),
                on_release=lambda x, fd=dict(f): self._on_item(fd))
            ico = IconLeftWidget(
                icon="arrow-up-circle-outline" if is_inc else "arrow-down-circle-outline",
                theme_icon_color="Custom",
                icon_color=GREEN if is_inc else RED)
            item.add_widget(ico)
            self.ids.fixed_list.add_widget(item)

    def _on_item(self, f):
        uid = MDApp.get_running_app().current_user["id"]
        tp = "Entrada" if f["type"] == "income" else "Despesa"
        txt = "{}: {} / mes\n{}\n\nDesativar este fixo?".format(
            tp, fmt_currency(f["amount"]), f["description"])
        def do_del():
            FixedExpenseModel.deactivate(f["id"], uid)
            self.refresh()
        confirm_dialog("Desativar fixo", txt, do_del, "Desativar", danger=True)

    def add_fixed(self):
        uid = MDApp.get_running_app().current_user["id"]
        type_opts = [("expense", "Despesa"), ("income", "Entrada")]
        self._sel_type = "expense"
        cats = CategoryModel.get_all(uid, "expense")
        cat_opts = [(c["id"], "{} {}".format(c.get("icon",""), c["name"])) for c in cats]
        self._sel_cat = cat_opts[0][0] if cat_opts else None

        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(270), padding=[0, dp(8), 0, 0])
        btn_type = MDRaisedButton(text="Despesa", size_hint=(1,None), height=dp(44), md_bg_color=RED)
        btn_cat  = MDRaisedButton(text=cat_opts[0][1] if cat_opts else "Categoria",
                                  size_hint=(1,None), height=dp(44), md_bg_color=CARD_BG)
        f_desc   = MDTextField(hint_text="Descricao (ex: Aluguel)", mode="rectangle",
                               size_hint_y=None, height=dp(52))
        f_amt    = MDTextField(hint_text="Valor (ex: 1200.00)", mode="rectangle",
                               input_filter="float", size_hint_y=None, height=dp(52))

        def open_type(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda t=tp, n=nm: (
                          setattr(self, "_sel_type", t),
                          btn.__setattr__("text", n),
                          btn.__setattr__("md_bg_color", RED if t=="expense" else GREEN),
                          reload_cats(), menu.dismiss()
                      )} for tp, nm in type_opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=3)
            menu.open()

        def reload_cats():
            cs = CategoryModel.get_all(uid, self._sel_type)
            opts = [(c["id"], "{} {}".format(c.get("icon",""), c["name"])) for c in cs]
            self._sel_cat = opts[0][0] if opts else None
            btn_cat.text = opts[0][1] if opts else "Categoria"
            btn_cat._opts = opts

        btn_cat._opts = cat_opts

        def open_cat(btn):
            from kivymd.uix.menu import MDDropdownMenu
            opts = getattr(btn, "_opts", cat_opts)
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda cid=cid, n=nm: (
                          setattr(self, "_sel_cat", cid),
                          btn.__setattr__("text", n),
                          menu.dismiss())} for cid, nm in opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=4)
            menu.open()

        btn_type.bind(on_release=open_type)
        btn_cat.bind(on_release=open_cat)
        for w in [btn_type, btn_cat, f_desc, f_amt]:
            content.add_widget(w)
        dlg = [None]
        def save(*a):
            try: amt = float(f_amt.text.replace(",", "."))
            except: return
            if not f_desc.text.strip(): return
            FixedExpenseModel.create(uid, self._sel_cat, self._sel_type, amt, f_desc.text.strip())
            dlg[0].dismiss()
            self.refresh()
        dlg[0] = MDDialog(title="Novo Fixo", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                                   MDRaisedButton(text="Salvar", md_bg_color=PURPLE, on_release=save)])
        dlg[0].open()
