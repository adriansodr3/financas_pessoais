import os

from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.logger import Logger
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem

from utils.helpers import current_ym


class MainScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "main"
        self._dash = None
        self._nav_built = False

    def build_nav(self):
        if self._nav_built:
            return
        try:
            from screens.login_screen import LoginScreen
            from screens.dashboard_screen import DashboardScreen
            from screens.transactions_screen import TransactionsScreen
            from screens.fixed_screen import FixedScreen
            from screens.installments_screen import InstallmentsScreen
            from screens.categories_screen import CategoriesScreen

            nav = MDBottomNavigation(panel_color=(0.10, 0.11, 0.15, 1))

            tabs = [
                ("tab_dashboard",    "home-outline",         "Inicio",      DashboardScreen()),
                ("tab_transactions", "format-list-bulleted", "Lancamentos", TransactionsScreen()),
                ("tab_installments", "credit-card-outline",  "Parcelas",    InstallmentsScreen()),
                ("tab_fixed",        "pin-outline",          "Fixos",       FixedScreen()),
                ("tab_categories",   "tag-outline",          "Categorias",  CategoriesScreen()),
            ]

            for tab_name, icon, text, screen in tabs:
                item = MDBottomNavigationItem(name=tab_name, text=text, icon=icon)
                item.add_widget(screen)
                nav.add_widget(item)
                if tab_name == "tab_dashboard":
                    self._dash = screen

            self.add_widget(nav)
            self._nav_built = True
            Logger.info("FINANCAS: MainScreen nav built OK")
        except Exception as e:
            Logger.exception(f"FINANCAS: Erro ao criar nav: {e}")

    def on_enter_app(self):
        if not self._nav_built:
            self.build_nav()
        if self._dash:
            self._dash.year, self._dash.month = current_ym()
            self._dash.refresh()

    def refresh_dashboard(self):
        if self._dash:
            self._dash.refresh()


class FinancasApp(MDApp):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.current_user = None
        self.title = "Financas Pessoais"

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.accent_palette = "Green"

        sm = ScreenManager(transition=NoTransition())

        try:
            from screens.login_screen import LoginScreen
            sm.add_widget(LoginScreen())
            sm.add_widget(MainScreen())
            Logger.info("FINANCAS: Screens carregadas OK")
        except Exception as e:
            Logger.exception(f"FINANCAS: Erro ao carregar screens: {e}")
            err = MDScreen(name="error")
            err.add_widget(MDLabel(
                text=f"Erro ao iniciar:\n{e}",
                halign="center",
                theme_text_color="Custom",
                text_color=(1, 0.3, 0.3, 1)))
            sm.add_widget(err)

        return sm

    def on_start(self):
        try:
            from database.schema import init_db
            init_db()
            Logger.info("FINANCAS: Banco inicializado OK")
        except Exception as e:
            Logger.exception(f"FINANCAS: Erro no banco: {e}")


if __name__ == "__main__":
    FinancasApp().run()
