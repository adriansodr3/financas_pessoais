from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDFloatingActionButton
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

from screens.widgets import (confirm_dialog, BG, CARD_BG, PURPLE,
                              GREEN, RED, MUTED, WHITE)
from models.category import CategoryModel


class CategoriesScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "tab_categories"
        self._built = False

    def on_enter(self):
        if not self._built:
            self._build()
            self._built = True
        self.refresh()

    def _build(self):
        root = FloatLayout(md_bg_color=BG)
        col = MDBoxLayout(orientation="vertical", md_bg_color=BG, size_hint=(1, 1))

        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56),
                             padding=[16, 8], md_bg_color=CARD_BG)
        header.add_widget(MDLabel(text="Categorias", font_style="Subtitle1",
                                  theme_text_color="Custom", text_color=WHITE))
        col.add_widget(header)

        sv = ScrollView()
        self._list = MDList()
        sv.add_widget(self._list)
        col.add_widget(sv)

        root.add_widget(col)

        fab = MDFloatingActionButton(
            icon="plus", md_bg_color=PURPLE,
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
        for cat in CategoryModel.get_all(uid):
            is_inc = cat["type"] == "income"
            icon = "arrow-up-circle-outline" if is_inc else "arrow-down-circle-outline"
            tipo = "Entrada" if is_inc else "Despesa"
            item = OneLineIconListItem(
                text="{} {}  [{}]".format(
                    cat.get("icon", ""), cat["name"], tipo),
                on_release=lambda x, c=dict(cat): self._on_item(c))
            ico = IconLeftWidget(icon=icon, theme_icon_color="Custom",
                                 icon_color=GREEN if is_inc else RED)
            item.add_widget(ico)
            self._list.add_widget(item)

    def _on_item(self, cat):
        app = MDApp.get_running_app()
        uid = app.current_user["id"]

        def do_delete():
            CategoryModel.delete(cat["id"], uid)
            self.refresh()

        confirm_dialog(
            "Excluir categoria",
            "{} {}\n\nExcluir esta categoria?\nLancamentos existentes nao serao afetados.".format(
                cat.get("icon", ""), cat["name"]),
            do_delete, "Excluir", danger=True)

    def _add(self):
        app = MDApp.get_running_app()
        uid = app.current_user["id"]

        content = MDBoxLayout(orientation="vertical", spacing=8,
                              size_hint_y=None, height=dp(196), padding=[0, 8, 0, 0])
        f_name = MDTextField(hint_text="Nome da categoria", mode="rectangle",
                             size_hint_y=None, height=dp(48))
        f_icon = MDTextField(hint_text="Icone emoji (ex: 🏠 🚗 🍕)",
                             mode="rectangle", size_hint_y=None, height=dp(48))

        self._sel_type = "expense"
        type_opts = [("expense", "Despesa"), ("income", "Entrada")]
        btn_type = MDRaisedButton(
            text="Despesa", size_hint=(1, None), height=dp(44), md_bg_color=RED)

        def open_type(btn):
            from kivymd.uix.menu import MDDropdownMenu
            items = [{"text": nm, "viewclass": "OneLineListItem",
                      "on_release": lambda t=tp, n=nm: (
                          setattr(self, '_sel_type', t),
                          btn.__setattr__('text', n),
                          btn.__setattr__('md_bg_color', RED if t == 'expense' else GREEN),
                          menu.dismiss()
                      )} for tp, nm in type_opts]
            menu = MDDropdownMenu(caller=btn, items=items, width_mult=3)
            menu.open()
        btn_type.bind(on_release=open_type)

        for w in [f_name, f_icon, btn_type]:
            content.add_widget(w)

        def save(*a):
            if not f_name.text.strip():
                return
            CategoryModel.create(
                uid, f_name.text.strip(), self._sel_type,
                "#6366f1", f_icon.text.strip() or "💰")
            dlg.dismiss()
            self.refresh()

        dlg = MDDialog(
            title="Nova Categoria", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(text="Salvar", md_bg_color=PURPLE, on_release=save)])
        dlg.open()
