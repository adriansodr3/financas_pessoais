from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

from screens.widgets import confirm_dialog, BG, CARD_BG, PURPLE, GREEN, RED, WHITE
from models.category import CategoryModel

EMOJIS = [
    "Casa",    "Carro",  "Comida", "Saude",  "Estudo",
    "Lazer",   "Roupa",  "Viagem", "Pet",    "Trabalho",
    "Conta",   "Outro",  "Invest", "Gym",    "Tech",
    "Musica",  "Cafe",   "Bar",    "Farm",   "Kids",
]

EMOJI_ICONS = {
    "Casa":    "home-outline",
    "Carro":   "car-outline",
    "Comida":  "food-outline",
    "Saude":   "heart-pulse",
    "Estudo":  "book-outline",
    "Lazer":   "gamepad-variant-outline",
    "Roupa":   "tshirt-crew-outline",
    "Viagem":  "airplane-outline",
    "Pet":     "paw-outline",
    "Trabalho":"briefcase-outline",
    "Conta":   "file-document-outline",
    "Outro":   "dots-horizontal",
    "Invest":  "trending-up",
    "Gym":     "dumbbell",
    "Tech":    "laptop",
    "Musica":  "music-note",
    "Cafe":    "coffee-outline",
    "Bar":     "glass-mug-variant",
    "Farm":    "pharmacy",
    "Kids":    "baby-face-outline",
}

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
                MDBoxLayout:
                    id: cat_box
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(8), dp(8), dp(8), dp(80)
                    spacing: dp(4)
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
        self._sel_icon  = "dots-horizontal"
        self._icon_btn  = None

    def refresh(self):
        try:
            app = MDApp.get_running_app()
            if not hasattr(app, 'current_user') or not app.current_user:
                return
            uid = app.current_user["id"]
            box = self.ids.cat_box
            box.clear_widgets()
            cats = CategoryModel.get_all(uid)
            if not cats:
                box.add_widget(MDLabel(
                    text="Nenhuma categoria.", halign="center",
                    theme_text_color="Secondary", size_hint_y=None, height=dp(60)))
                return
            for cat in cats:
                box.add_widget(self._make_card(cat, uid))
        except Exception as e:
            from kivy.logger import Logger
            Logger.exception("FINANCAS: categories refresh: {}".format(e))

    def _make_card(self, cat, uid):
        is_inc = cat["type"] == "income"
        color  = GREEN if is_inc else RED
        # Usar icon do MDI em vez de emoji
        icon_name = cat.get("icon", "dots-horizontal")
        # Se o icon salvo não for um MDI (é texto curto), usar icone generico
        if len(icon_name) <= 2 or icon_name in EMOJI_ICONS:
            icon_name = EMOJI_ICONS.get(icon_name, "dots-horizontal")

        card = MDCard(
            orientation="horizontal",
            size_hint_y=None, height=dp(60),
            md_bg_color=CARD_BG, radius=[dp(8)],
            padding=[dp(12), dp(6)], spacing=dp(8))
        ind = MDBoxLayout(size_hint=(None,1), width=dp(4), md_bg_color=color)

        from kivymd.uix.button import MDIconButton
        ico = MDIconButton(
            icon=icon_name,
            theme_icon_color="Custom",
            icon_color=color,
            size_hint=(None,None), size=(dp(40),dp(40)),
            disabled=True)

        info = MDBoxLayout(orientation="vertical")
        info.add_widget(MDLabel(
            text=cat["name"],
            font_style="Body2", theme_text_color="Custom", text_color=WHITE,
            size_hint_y=None, height=dp(24)))
        info.add_widget(MDLabel(
            text="Entrada" if is_inc else "Despesa",
            font_style="Caption", theme_text_color="Secondary",
            size_hint_y=None, height=dp(18)))

        card.add_widget(ind)
        card.add_widget(ico)
        card.add_widget(info)
        card.bind(on_release=lambda x, c=dict(cat): self._on_item(c, uid))
        return card

    def _on_item(self, cat, uid):
        def do_del():
            CategoryModel.delete(cat["id"], uid)
            self.refresh()
        confirm_dialog(
            "Excluir categoria",
            "{}\nLancamentos existentes nao serao afetados.".format(cat["name"]),
            do_del, "Excluir", danger=True)

    def add_cat(self):
        uid = MDApp.get_running_app().current_user["id"]
        self._sel_type = "expense"
        self._sel_icon = "dots-horizontal"

        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(360), padding=[0, dp(8), 0, 0])

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

        # Icone selecionado
        self._icon_btn = MDRaisedButton(
            text="Icone: Conta (toque para mudar)",
            size_hint=(1,None), height=dp(44), md_bg_color=CARD_BG)

        lbl_pick = MDLabel(
            text="Escolha o icone da categoria:",
            font_style="Caption", theme_text_color="Secondary",
            size_hint_y=None, height=dp(22))

        # Grid de icones usando MDIconButton (renderiza corretamente no Android)
        icon_sv = ScrollView(size_hint=(1,None), height=dp(120), do_scroll_x=False)
        icon_grid = GridLayout(cols=5, spacing=dp(4), padding=dp(4), size_hint_y=None)
        icon_grid.bind(minimum_height=icon_grid.setter("height"))

        def select_icon(label, icon_key):
            self._sel_icon = EMOJI_ICONS[icon_key]
            if self._icon_btn:
                self._icon_btn.text = "Icone: {}".format(icon_key)

        for label in EMOJIS:
            icon_key = EMOJI_ICONS[label]
            row = MDCard(
                orientation="vertical",
                size_hint=(None,None), size=(dp(60), dp(68)),
                md_bg_color=(0.13,0.14,0.20,1), radius=[dp(8)],
                padding=[0, dp(4)])

            from kivymd.uix.button import MDIconButton
            btn_ico = MDIconButton(
                icon=icon_key,
                size_hint=(1,None), height=dp(36))
            lbl_ico = MDLabel(
                text=label, halign="center", font_style="Overline",
                size_hint_y=None, height=dp(20))

            row.add_widget(btn_ico)
            row.add_widget(lbl_ico)
            row.bind(on_release=lambda x, lk=label: select_icon(lk, lk))
            icon_grid.add_widget(row)

        icon_sv.add_widget(icon_grid)

        for w in [f_name, btn_type, lbl_pick, self._icon_btn, icon_sv]:
            content.add_widget(w)

        dlg = [None]
        def save(*a):
            if not f_name.text.strip(): return
            # Salvar o nome do icone MDI
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
