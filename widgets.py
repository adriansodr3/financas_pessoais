"""Widgets comuns usados em todas as telas."""
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from utils.helpers import fmt_currency, month_label, prev_month, next_month

BG       = (0.06, 0.07, 0.09, 1)
CARD_BG  = (0.10, 0.11, 0.15, 1)
PURPLE   = (0.39, 0.40, 0.95, 1)
GREEN    = (0.13, 0.77, 0.37, 1)
RED      = (0.94, 0.27, 0.27, 1)
ORANGE   = (0.98, 0.60, 0.22, 1)
MUTED    = (0.58, 0.64, 0.72, 1)
WHITE    = (0.89, 0.91, 0.94, 1)


def summary_card(title, value, color):
    card = MDCard(orientation="vertical", padding=12, spacing=4,
                  size_hint=(1, None), height=dp(80),
                  md_bg_color=CARD_BG, radius=[12])
    card.add_widget(MDLabel(text=title, font_style="Overline",
                            theme_text_color="Custom", text_color=MUTED,
                            size_hint_y=None, height=dp(18)))
    lbl = MDLabel(text=fmt_currency(value), font_style="H6",
                  theme_text_color="Custom", text_color=color,
                  size_hint_y=None, height=dp(34))
    card.add_widget(lbl)
    card._value_lbl = lbl
    return card


def update_card(card, value, color=None):
    card._value_lbl.text = fmt_currency(value)
    if color:
        card._value_lbl.text_color = color


def month_nav_bar(on_prev, on_next, on_today=None):
    """Retorna (bar_widget, label_ref)"""
    bar = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48),
                      padding=[8, 0], spacing=4,
                      md_bg_color=CARD_BG)
    btn_p = MDIconButton(icon="chevron-left", on_release=lambda *a: on_prev())
    lbl = MDLabel(text="", halign="center", font_style="Subtitle1",
                  theme_text_color="Custom", text_color=WHITE)
    btn_n = MDIconButton(icon="chevron-right", on_release=lambda *a: on_next())
    bar.add_widget(btn_p)
    bar.add_widget(lbl)
    bar.add_widget(btn_n)
    if on_today:
        btn_t = MDIconButton(icon="calendar-today", on_release=lambda *a: on_today())
        bar.add_widget(btn_t)
    return bar, lbl


def confirm_dialog(title, text, on_confirm, confirm_text="Confirmar", danger=False):
    dialog = MDDialog(
        title=title,
        text=text,
        buttons=[
            MDFlatButton(text="Cancelar", on_release=lambda x: dialog.dismiss()),
            MDRaisedButton(
                text=confirm_text,
                md_bg_color=RED if danger else PURPLE,
                on_release=lambda x: (dialog.dismiss(), on_confirm()))
        ])
    dialog.open()
