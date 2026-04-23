from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.app import MDApp

from screens.widgets import (month_nav_bar, BG, CARD_BG, PURPLE,
                              GREEN, RED, MUTED, WHITE, fmt_currency)
from utils.helpers import month_label, prev_month, next_month, current_ym
from models.transaction import TransactionModel


class BarWidget(BoxLayout):
    """Barra de progresso simples sem dependencia de MDProgressBar."""
    def __init__(self, pct, color_tuple, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height = dp(8)
        self._pct = pct
        self._color = color_tuple
        self.bind(size=self._draw, pos=self._draw)

    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            # Fundo
            Color(0.15, 0.16, 0.22, 1)
            Rectangle(pos=self.pos, size=self.size)
            # Barra preenchida
            Color(*self._color)
            w = max(4, self.width * self._pct / 100)
            Rectangle(pos=self.pos, size=(w, self.height))


class ReportsScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "tab_reports"
        self.year, self.month = current_ym()
        self._show_type = "expense"
        self._built = False

    def on_enter(self):
        if not self._built:
            self._build()
            self._built = True
        self.refresh()

    def _build(self):
        root = MDBoxLayout(orientation="vertical", md_bg_color=BG)
        nav, self._month_lbl = month_nav_bar(self._prev, self._next)
        root.add_widget(nav)

        btn_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48),
                              padding=[8, 4], spacing=8, md_bg_color=CARD_BG)
        self._btn_exp = MDRaisedButton(
            text="Despesas", md_bg_color=RED, size_hint=(1, None), height=dp(38),
            on_release=lambda *a: self._set_type("expense"))
        self._btn_inc = MDRaisedButton(
            text="Entradas", md_bg_color=CARD_BG, size_hint=(1, None), height=dp(38),
            on_release=lambda *a: self._set_type("income"))
        btn_row.add_widget(self._btn_exp)
        btn_row.add_widget(self._btn_inc)
        root.add_widget(btn_row)

        sv = ScrollView()
        self._content = MDBoxLayout(orientation="vertical", spacing=10,
                                    padding=[12, 12, 12, 12], size_hint_y=None)
        self._content.bind(minimum_height=self._content.setter("height"))
        sv.add_widget(self._content)
        root.add_widget(sv)
        self.add_widget(root)

    def _set_type(self, t):
        self._show_type = t
        self._btn_exp.md_bg_color = RED   if t == "expense" else CARD_BG
        self._btn_inc.md_bg_color = GREEN if t == "income"  else CARD_BG
        self.refresh()

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self._month_lbl.text = month_label(self.year, self.month)
        self._content.clear_widgets()

        summary = TransactionModel.get_summary_by_category(uid, self.year, self.month)
        items = [s for s in summary if s["type"] == self._show_type]
        total = sum(s["total"] for s in items) if items else 0
        color = RED if self._show_type == "expense" else GREEN

        if not items:
            self._content.add_widget(
                MDLabel(text="Sem dados neste mes.", halign="center",
                        theme_text_color="Secondary",
                        size_hint_y=None, height=dp(80)))
            return

        # Card total
        tc = MDCard(md_bg_color=CARD_BG, radius=[10], padding=[12, 10],
                    size_hint_y=None, height=dp(60))
        tipo = "Total Despesas" if self._show_type == "expense" else "Total Entradas"
        tc.add_widget(MDLabel(
            text="{}: {}".format(tipo, fmt_currency(total)),
            font_style="Subtitle1", theme_text_color="Custom", text_color=color))
        self._content.add_widget(tc)

        for s in items:
            pct = (s["total"] / total * 100) if total > 0 else 0
            nome = "{} {}".format(s.get("icon") or "", s.get("name") or "—")

            row = MDBoxLayout(orientation="vertical", size_hint_y=None,
                              height=dp(56), spacing=4)

            top = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
            top.add_widget(MDLabel(text=nome, font_style="Body2",
                                   theme_text_color="Custom", text_color=WHITE))
            top.add_widget(MDLabel(
                text="{:.1f}%  {}".format(pct, fmt_currency(s["total"])),
                font_style="Body2", theme_text_color="Custom",
                text_color=color, halign="right"))
            row.add_widget(top)
            row.add_widget(BarWidget(pct=pct, color_tuple=color))
            self._content.add_widget(row)

    def _prev(self):
        self.year, self.month = prev_month(self.year, self.month)
        self.refresh()

    def _next(self):
        self.year, self.month = next_month(self.year, self.month)
        self.refresh()
