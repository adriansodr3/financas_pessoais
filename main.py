import os
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem

from database.schema import init_db
from screens.login_screen import LoginScreen
from screens.dashboard_screen import DashboardScreen
from screens.transactions_screen import TransactionsScreen
from screens.fixed_screen import FixedScreen
from screens.installments_screen import InstallmentsScreen
from screens.categories_screen import CategoriesScreen
from screens.reports_screen import ReportsScreen
from utils.helpers import current_ym


class MainScreen(MDScreen):
    """Tela principal com bottom navigation."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "main"
        self._dash = None
        self._build_nav()

    def _build_nav(self):
        nav = MDBottomNavigation(panel_color=(0.10, 0.11, 0.15, 1))

        # (nome_tab, icone, texto, instancia_screen)
        tabs = [
            ("tab_dashboard",    "home-outline",            "Inicio",      DashboardScreen()),
            ("tab_transactions", "format-list-bulleted",    "Lancamentos", TransactionsScreen()),
            ("tab_installments", "credit-card-outline",     "Parcelas",    InstallmentsScreen()),
            ("tab_fixed",        "pin-outline",             "Fixos",       FixedScreen()),
            ("tab_categories",   "tag-outline",             "Categorias",  CategoriesScreen()),
        ]

        for tab_name, icon, text, screen in tabs:
            item = MDBottomNavigationItem(name=tab_name, text=text, icon=icon)
            item.add_widget(screen)
            nav.add_widget(item)
            if tab_name == "tab_dashboard":
                self._dash = screen

        self.add_widget(nav)

    def on_enter_app(self):
        """Chamado apos login bem-sucedido."""
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
        init_db()

        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(LoginScreen())
        sm.add_widget(MainScreen())
        return sm


if __name__ == "__main__":
    FinancasApp().run()
