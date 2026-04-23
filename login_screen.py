from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.app import MDApp
from models.user import UserModel


class LoginScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "login"
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation="vertical", padding=24, spacing=16,
                           md_bg_color=(0.06, 0.07, 0.09, 1))
        root.add_widget(MDLabel(size_hint_y=None, height=40))

        card = MDCard(orientation="vertical", padding=28, spacing=16,
                      size_hint=(1, None), height=480,
                      md_bg_color=(0.10, 0.11, 0.15, 1),
                      radius=[16])

        icon_lbl = MDLabel(text="💰  Financas Pessoais",
                           halign="center", font_style="H5",
                           theme_text_color="Custom",
                           text_color=(0.89, 0.91, 0.94, 1),
                           size_hint_y=None, height=56)

        sub = MDLabel(text="Controle financeiro familiar",
                      halign="center", font_style="Caption",
                      theme_text_color="Secondary",
                      size_hint_y=None, height=28)

        self.tab_lbl = MDLabel(text="ENTRAR",
                               halign="center", font_style="Overline",
                               theme_text_color="Custom",
                               text_color=(0.39, 0.40, 0.95, 1),
                               size_hint_y=None, height=24)

        self.field_user = MDTextField(hint_text="Usuario", mode="rectangle",
                                      size_hint_y=None, height=48)
        self.field_pass = MDTextField(hint_text="Senha", mode="rectangle",
                                      password=True, size_hint_y=None, height=48)
        self.field_pass2 = MDTextField(hint_text="Confirmar Senha", mode="rectangle",
                                       password=True, size_hint_y=None, height=48)
        self.field_pass2.opacity = 0
        self.field_pass2.disabled = True

        self.msg = MDLabel(text="", halign="center", font_style="Caption",
                           theme_text_color="Error",
                           size_hint_y=None, height=24)

        self.btn_main = MDRaisedButton(text="Entrar", size_hint_x=1,
                                       md_bg_color=(0.39, 0.40, 0.95, 1),
                                       on_release=self._on_main)
        self.btn_switch = MDFlatButton(text="Criar nova conta", size_hint_x=1,
                                       on_release=self._toggle_mode)

        self._register_mode = False

        for w in [icon_lbl, sub, self.tab_lbl, self.field_user,
                  self.field_pass, self.field_pass2, self.msg,
                  self.btn_main, self.btn_switch]:
            card.add_widget(w)

        root.add_widget(card)
        root.add_widget(MDLabel(size_hint_y=1))
        self.add_widget(root)

    def _toggle_mode(self, *a):
        self._register_mode = not self._register_mode
        if self._register_mode:
            self.tab_lbl.text = "CRIAR CONTA"
            self.btn_main.text = "Criar Conta"
            self.btn_switch.text = "Ja tenho conta"
            self.field_pass2.opacity = 1
            self.field_pass2.disabled = False
        else:
            self.tab_lbl.text = "ENTRAR"
            self.btn_main.text = "Entrar"
            self.btn_switch.text = "Criar nova conta"
            self.field_pass2.opacity = 0
            self.field_pass2.disabled = True
        self.msg.text = ""

    def _on_main(self, *a):
        u = self.field_user.text.strip()
        p = self.field_pass.text
        if not u or not p:
            self.msg.text = "Preencha todos os campos."
            return
        if self._register_mode:
            p2 = self.field_pass2.text
            if p != p2:
                self.msg.text = "Senhas nao coincidem."
                return
            if len(p) < 4:
                self.msg.text = "Senha deve ter ao menos 4 caracteres."
                return
            try:
                UserModel.create(u, p)
            except Exception as e:
                self.msg.text = "Usuario ja existe." if "UNIQUE" in str(e) else str(e)
                return
        user = UserModel.authenticate(u, p)
        if not user:
            self.msg.text = "Usuario ou senha incorretos."
            return
        app = MDApp.get_running_app()
        app.current_user = user
        app.root.current = "main"
        app.root.get_screen("main").on_enter_app()

    def on_pre_enter(self):
        self.field_user.text = ""
        self.field_pass.text = ""
        self.field_pass2.text = ""
        self.msg.text = ""
