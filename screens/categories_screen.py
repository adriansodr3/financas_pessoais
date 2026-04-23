import os
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.text import LabelBase
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

# Tentar registrar font com suporte a emoji do sistema Android
_EMOJI_FONT = "Roboto"
for _path in [
    "/system/fonts/NotoColorEmoji.ttf",
    "/system/fonts/NotoEmoji-Regular.ttf",
    "/system/fonts/AndroidEmoji.ttf",
]:
    if os.path.exists(_path):
        try:
            LabelBase.register(name="EmojiFont", fn_regular=_path)
            _EMOJI_FONT = "EmojiFont"
        except Exception:
            pass
        break

# Categorias pre-definidas: (label exibido, icone salvo no banco)
CATEGORIAS = [
    ("Casa",       "🏠"), ("Mercado",    "🛒"), ("Carro",      "🚗"),
    ("Saude",      "❤"), ("Educacao",   "📚"), ("Lazer",      "🎉"),
    ("Contas",     "📋"), ("Trabalho",   "💼"), ("Comida",     "🍕"),
    ("Celular",    "📱"), ("Musica",     "🎵"), ("Academia",   "🏋"),
    ("Viagem",     "✈"), ("Roupas",     "👕"), ("Farmacia",   "💊"),
    ("Salario",    "💰"), ("Freelance",  "💻"), ("Investim.",  "📈"),
    ("Presente",   "🎁"), ("Combustivel","⛽"), ("Transporte", "🚌"),
    ("Cafe",       "☕"), ("Cerveja",    "🍺"), ("Streaming",  "🎬"),
    ("Pet",        "🐾"), ("Planta",     "🌿"), ("Ferram.",    "🔧"),
    ("Estrela",    "⭐"), ("Outros",     "💸"), ("+",          "+"),
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
        self._sel_icon  = "💸"

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self.ids.cat_list.clear_widgets()
        for cat in CategoryModel.get_all(uid):
            is_inc = cat["type"] == "income"
            icon_txt = cat.get("icon") or ""
            item = OneLineIconListItem(
                text="{}  {}  [{}]".format(
                    icon_txt, cat["name"],
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
            "{}  {}\nLancamentos existentes nao serao afetados.".format(
                cat.get("icon",""), cat["name"]),
            do_del, "Excluir", danger=True)

    def add_cat(self):
        uid = MDApp.get_running_app().current_user["id"]
        self._sel_type = "expense"
        self._sel_icon = CATEGORIAS[0][1]
        self._icon_btn = None  # referencia ao botao de icone selecionado

        # Altura: nome + tipo + grid (4 linhas * 52dp) + icone selecionado + padding
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(380), padding=[0, dp(8), 0, 0])

        f_name = MDTextField(hint_text="Nome da categoria", mode="rectangle",
                             size_hint_y=None, height=dp(52))

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

        # Label icone selecionado
        selected_lbl = MDLabel(
            text="Icone selecionado: {}".format(self._sel_icon),
            font_style="Caption", theme_text_color="Custom",
            text_color=(0.39,0.40,0.95,1),
            size_hint_y=None, height=dp(22))

        # Grid de icones — usa texto curto sem emoji para garantir renderizacao
        grid_lbl = MDLabel(text="Escolher icone:", font_style="Overline",
                           theme_text_color="Secondary",
                           size_hint_y=None, height=dp(20))

        icon_sv = ScrollView(size_hint=(1,None), height=dp(180), do_scroll_x=False)
        icon_grid = GridLayout(cols=5, spacing=dp(4), size_hint_y=None, padding=dp(2))
        icon_grid.bind(minimum_height=icon_grid.setter("height"))

        def pick_icon(label, icon, lbl_ref):
            self._sel_icon = icon
            lbl_ref.text = "Icone selecionado: {}  {}".format(label, icon)

        for label, icon in CATEGORIAS:
            from kivy.uix.button import Button
            btn_i = Button(
                text="{}\n{}".format(icon, label),
                font_size=dp(11),
                size_hint=(1, None),
                height=dp(52),
                background_color=(0.12, 0.13, 0.18, 1),
                background_normal="",
                halign="center")
            btn_i.bind(on_release=lambda x, l=label, ic=icon: pick_icon(l, ic, selected_lbl))
            icon_grid.add_widget(btn_i)

        icon_sv.add_widget(icon_grid)

        for w in [f_name, btn_type, selected_lbl, grid_lbl, icon_sv]:
            content.add_widget(w)

        dlg = [None]
        def save(*a):
            if not f_name.text.strip(): return
            CategoryModel.create(uid, f_name.text.strip(), self._sel_type,
                                 "#6366f1", self._sel_icon)
            dlg[0].dismiss()
            self.refresh()

        dlg[0] = MDDialog(
            title="Nova Categoria", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                MDRaisedButton(text="Salvar", md_bg_color=PURPLE, on_release=save)])
        dlg[0].open()
