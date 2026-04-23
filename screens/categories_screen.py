from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

from screens.widgets import confirm_dialog, BG, CARD_BG, PURPLE, GREEN, RED, WHITE
from models.category import CategoryModel

EMOJIS = [
    "💰","💸","🏠","🛒","🚗","❤️","📚","🎉","📋","💻",
    "🍕","🎮","👕","💊","✈️","📱","🎵","🐾","🌿","💼",
    "🏋️","🎓","🎬","🍺","☕","🔧","🎸","🌟","🐶","🏖️",
    "💡","🧾","🎁","🏥","⛽","🚌","🍔","🧴","🛡️","💈",
]

Builder.load_string("""
<CategoriesScreen>:
    name: "tab_categories"
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
                    text: "Categorias"
                    font_style: "Subtitle1"
                    theme_text_color: "Custom"
                    text_color: 0.89, 0.91, 0.94, 1
                    padding_x: dp(16)
            ScrollView:
                do_scroll_x: False
                MDList:
                    id: cat_list
                    size_hint_y: None
                    height: self.minimum_height
        MDFloatingActionButton:
            icon: "plus"
            md_bg_color: 0.39, 0.40, 0.95, 1
            pos_hint: {"right": 0.95, "y": 0.02}
            on_release: root.add_cat()
""")


class CategoriesScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._sel_type  = "expense"
        self._sel_emoji = "💰"

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self.ids.cat_list.clear_widgets()
        for cat in CategoryModel.get_all(uid):
            is_inc = cat["type"] == "income"
            item = OneLineIconListItem(
                text="{} {}  [{}]".format(
                    cat.get("icon",""), cat["name"],
                    "Entrada" if is_inc else "Despesa"),
                on_release=lambda x, c=dict(cat): self._on_item(c))
            ico = IconLeftWidget(
                icon="arrow-up-circle-outline" if is_inc else "arrow-down-circle-outline",
                theme_icon_color="Custom", icon_color=GREEN if is_inc else RED)
            item.add_widget(ico)
            self.ids.cat_list.add_widget(item)

    def _on_item(self, cat):
        uid = MDApp.get_running_app().current_user["id"]
        def do_del():
            CategoryModel.delete(cat["id"], uid)
            self.refresh()
        confirm_dialog(
            "Excluir categoria",
            "{} {}\nLancamentos existentes nao serao afetados.".format(
                cat.get("icon",""), cat["name"]),
            do_del, "Excluir", danger=True)

    def add_cat(self):
        uid = MDApp.get_running_app().current_user["id"]
        self._sel_type  = "expense"
        self._sel_emoji = "💰"

        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(330), padding=[0, dp(8), 0, 0])

        # Nome
        f_name = MDTextField(hint_text="Nome da categoria", mode="rectangle",
                             size_hint_y=None, height=dp(52))

        # Tipo
        btn_type = MDRaisedButton(text="Despesa", size_hint=(1,None), height=dp(44), md_bg_color=RED)
        def open_type(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda t=tp, n=nm: (
                          setattr(self,"_sel_type",t),
                          btn.__setattr__("text",n),
                          btn.__setattr__("md_bg_color", RED if t=="expense" else GREEN),
                          menu.dismiss()
                      )} for tp,nm in [("expense","Despesa"),("income","Entrada")]]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=3)
            menu.open()
        btn_type.bind(on_release=open_type)

        # Label emoji selecionado
        lbl_emoji_title = MDLabel(
            text="Icone:", font_style="Overline",
            theme_text_color="Secondary", size_hint_y=None, height=dp(20))

        self._emoji_lbl = MDRaisedButton(
            text=self._sel_emoji + "  (toque para mudar)",
            size_hint=(1,None), height=dp(44), md_bg_color=CARD_BG)

        # Grid de emojis
        emoji_sv = ScrollView(size_hint=(1,None), height=dp(110), do_scroll_y=True, do_scroll_x=False)
        emoji_grid = GridLayout(cols=8, spacing=dp(4), size_hint_y=None, padding=dp(4))
        emoji_grid.bind(minimum_height=emoji_grid.setter("height"))

        def set_emoji(e):
            self._sel_emoji = e
            self._emoji_lbl.text = e + "  (selecionado)"

        for e in EMOJIS:
            btn_e = Button(
                text=e,
                font_size=dp(22),
                size_hint=(None,None),
                size=(dp(40), dp(40)),
                background_color=(0.15, 0.16, 0.22, 1),
                background_normal="")
            btn_e.bind(on_release=lambda x, emoji=e: set_emoji(emoji))
            emoji_grid.add_widget(btn_e)

        emoji_sv.add_widget(emoji_grid)

        for w in [f_name, btn_type, lbl_emoji_title, self._emoji_lbl, emoji_sv]:
            content.add_widget(w)

        dlg = [None]
        def save(*a):
            if not f_name.text.strip(): return
            CategoryModel.create(uid, f_name.text.strip(), self._sel_type,
                                 "#6366f1", self._sel_emoji)
            dlg[0].dismiss()
            self.refresh()

        dlg[0] = MDDialog(
            title="Nova Categoria", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                MDRaisedButton(text="Salvar", md_bg_color=PURPLE, on_release=save)])
        dlg[0].open()
