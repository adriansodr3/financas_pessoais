from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.app import MDApp
from screens.widgets import BG, CARD_BG, GREEN, RED, MUTED, WHITE, fmt_currency
from utils.helpers import month_label, prev_month, next_month, current_ym
from models.transaction import TransactionModel

Builder.load_string("""
<ReportsScreen>:
    name: "tab_reports"
    md_bg_color: 0.06, 0.07, 0.09, 1
    BoxLayout:
        orientation: "vertical"
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(52)
            md_bg_color: 0.10, 0.11, 0.15, 1
            MDIconButton:
                icon: "chevron-left"
                on_release: root.prev_month()
            MDLabel:
                id: month_lbl
                text: ""
                halign: "center"
                font_style: "Subtitle1"
                theme_text_color: "Custom"
                text_color: 0.89, 0.91, 0.94, 1
            MDIconButton:
                icon: "chevron-right"
                on_release: root.next_month()
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(48)
            padding: dp(8), dp(4)
            spacing: dp(8)
            md_bg_color: 0.10, 0.11, 0.15, 1
            MDRaisedButton:
                id: btn_exp
                text: "Despesas"
                md_bg_color: 0.94, 0.27, 0.27, 1
                size_hint: 1, None
                height: dp(38)
                on_release: root.set_type("expense")
            MDRaisedButton:
                id: btn_inc
                text: "Entradas"
                md_bg_color: 0.10, 0.11, 0.15, 1
                size_hint: 1, None
                height: dp(38)
                on_release: root.set_type("income")
        ScrollView:
            do_scroll_x: False
            MDBoxLayout:
                id: content
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
                padding: dp(12), dp(12), dp(12), dp(12)
""")


class BarWidget(BoxLayout):
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
            Color(0.15, 0.16, 0.22, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(*self._color)
            Rectangle(pos=self.pos, size=(max(4, self.width * self._pct / 100), self.height))


class ReportsScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.year, self.month = current_ym()
        self._show_type = "expense"

    def set_type(self, t):
        self._show_type = t
        self.ids.btn_exp.md_bg_color = RED   if t == "expense" else CARD_BG
        self.ids.btn_inc.md_bg_color = GREEN if t == "income"  else CARD_BG
        self.refresh()

    def refresh(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        self.ids.month_lbl.text = month_label(self.year, self.month)
        content = self.ids.content
        content.clear_widgets()
        summary = TransactionModel.get_summary_by_category(uid, self.year, self.month)
        items = [s for s in summary if s["type"] == self._show_type]
        total = sum(s["total"] for s in items) if items else 0
        color = RED if self._show_type == "expense" else GREEN
        if not items:
            content.add_widget(MDLabel(text="Sem dados neste mes.", halign="center",
                                       theme_text_color="Secondary", size_hint_y=None, height=dp(80)))
            return
        tc = MDCard(md_bg_color=CARD_BG, radius=[dp(10)], padding=[dp(12), dp(10)],
                    size_hint_y=None, height=dp(60))
        tc.add_widget(MDLabel(
            text="{}: {}".format("Total Despesas" if self._show_type=="expense" else "Total Entradas",
                                 fmt_currency(total)),
            font_style="Subtitle1", theme_text_color="Custom", text_color=color))
        content.add_widget(tc)
        for s in items:
            pct = (s["total"] / total * 100) if total > 0 else 0
            row = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(54), spacing=dp(4))
            top = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
            top.add_widget(MDLabel(text="{} {}".format(s.get("icon") or "", s.get("name") or "—"),
                                   font_style="Body2", theme_text_color="Custom", text_color=WHITE))
            top.add_widget(MDLabel(text="{:.1f}%  {}".format(pct, fmt_currency(s["total"])),
                                   font_style="Body2", theme_text_color="Custom",
                                   text_color=color, halign="right"))
            row.add_widget(top)
            row.add_widget(BarWidget(pct=pct, color_tuple=color))
            content.add_widget(row)

    def prev_month(self):
        self.year, self.month = prev_month(self.year, self.month); self.refresh()
    def next_month(self):
        self.year, self.month = next_month(self.year, self.month); self.refresh()
