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
        self._screens = {}
        self._build_nav()

    def _build_nav(self):
        try:
            from screens.dashboard_screen     import DashboardScreen
            from screens.transactions_screen  import TransactionsScreen
            from screens.installments_screen  import InstallmentsScreen
            from screens.fixed_screen         import FixedScreen
            from screens.categories_screen    import CategoriesScreen
            from screens.reports_screen       import ReportsScreen
            from screens.profile_screen       import ProfileScreen

            tabs = [
                ("tab_dashboard",    "home-outline",            "Inicio",      DashboardScreen()),
                ("tab_transactions", "format-list-bulleted",    "Lancamentos", TransactionsScreen()),
                ("tab_installments", "credit-card-outline",     "Parcelas",    InstallmentsScreen()),
                ("tab_fixed",        "pin-outline",             "Fixos",       FixedScreen()),
                ("tab_reports",      "chart-bar",               "Relatorios",  ReportsScreen()),
                ("tab_categories",   "tag-outline",             "Categorias",  CategoriesScreen()),
                ("tab_profile",      "account-outline",         "Perfil",      ProfileScreen()),
            ]

            nav = MDBottomNavigation(panel_color=(0.10, 0.11, 0.15, 1))

            for tab_name, icon, text, screen in tabs:
                item = MDBottomNavigationItem(name=tab_name, text=text, icon=icon)
                item.add_widget(screen)
                nav.add_widget(item)
                self._screens[tab_name] = screen

            # CORRECAO PRINCIPAL: bind para chamar refresh ao trocar de aba
            nav.bind(current=self._on_tab_switch)
            self.add_widget(nav)
            Logger.info("FINANCAS: Nav built OK")
        except Exception as e:
            Logger.exception("FINANCAS: Erro nav: {}".format(e))

    def _on_tab_switch(self, nav_widget, tab_name):
        screen = self._screens.get(tab_name)
        if screen and hasattr(screen, 'refresh'):
            try:
                screen.refresh()
            except Exception as e:
                Logger.warning("FINANCAS: refresh {} falhou: {}".format(tab_name, e))

    def on_enter_app(self):
        dash = self._screens.get("tab_dashboard")
        if dash:
            dash.year, dash.month = current_ym()
            dash.refresh()

    def refresh_dashboard(self):
        dash = self._screens.get("tab_dashboard")
        if dash:
            dash.refresh()


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
            Logger.info("FINANCAS: Build OK")
        except Exception as e:
            Logger.exception("FINANCAS: Build error: {}".format(e))
            err = MDScreen(name="error")
            err.add_widget(MDLabel(text="Erro: {}".format(e), halign="center",
                                   theme_text_color="Custom", text_color=(1,0.3,0.3,1)))
            sm.add_widget(err)
        return sm

    def on_start(self):
        try:
            from database.schema import init_db
            init_db()
            Logger.info("FINANCAS: DB OK")
        except Exception as e:
            Logger.exception("FINANCAS: DB error: {}".format(e))


if __name__ == "__main__":
    FinancasApp().run()
