from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.app import MDApp
from models.user import UserModel


class LoginScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "login"
        self._register_mode = False
        self._build()

    def _build(self):
        # ScrollView como raiz garante funcionamento em qualquer tamanho de tela
        sv = ScrollView(size_hint=(1, 1))

        root = MDBoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(60), dp(32), dp(32)],
            spacing=dp(16),
            size_hint_y=None,
            md_bg_color=(0.06, 0.07, 0.09, 1)
        )
        root.bind(minimum_height=root.setter("height"))

        # Logo e titulo
        root.add_widget(MDLabel(
            text="[size=48]💰[/size]",
            markup=True, halign="center",
            size_hint_y=None, height=dp(64)))

        root.add_widget(MDLabel(
            text="Financas Pessoais",
            halign="center", font_style="H5",
            theme_text_color="Custom",
            text_color=(0.89, 0.91, 0.94, 1),
            size_hint_y=None, height=dp(40)))

        root.add_widget(MDLabel(
            text="Controle financeiro familiar",
            halign="center", font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None, height=dp(24)))

        root.add_widget(MDLabel(size_hint_y=None, height=dp(16)))

        self.tab_lbl = MDLabel(
            text="ENTRAR",
            halign="center", font_style="Overline",
            theme_text_color="Custom",
            text_color=(0.39, 0.40, 0.95, 1),
            size_hint_y=None, height=dp(24))
        root.add_widget(self.tab_lbl)

        self.field_user = MDTextField(
            hint_text="Usuario", mode="rectangle",
            size_hint_y=None, height=dp(56))
        root.add_widget(self.field_user)

        self.field_pass = MDTextField(
            hint_text="Senha", mode="rectangle",
            password=True, size_hint_y=None, height=dp(56))
        root.add_widget(self.field_pass)

        self.field_pass2 = MDTextField(
            hint_text="Confirmar Senha", mode="rectangle",
            password=True, size_hint_y=None, height=dp(56))
        self.field_pass2.opacity = 0
        self.field_pass2.disabled = True
        root.add_widget(self.field_pass2)

        self.msg = MDLabel(
            text="", halign="center", font_style="Caption",
            theme_text_color="Error",
            size_hint_y=None, height=dp(24))
        root.add_widget(self.msg)

        self.btn_main = MDRaisedButton(
            text="Entrar",
            size_hint=(1, None), height=dp(48),
            md_bg_color=(0.39, 0.40, 0.95, 1),
            on_release=self._on_main)
        root.add_widget(self.btn_main)

        self.btn_switch = MDFlatButton(
            text="Criar nova conta",
            size_hint=(1, None), height=dp(40),
            on_release=self._toggle_mode)
        root.add_widget(self.btn_switch)

        sv.add_widget(root)
        self.add_widget(sv)

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
                self.msg.text = "Senha: minimo 4 caracteres."
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
        if hasattr(self, 'field_pass2'):
            self.field_pass2.text = ""
        self.msg.text = ""
