from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from models.user import UserModel

Builder.load_string("""
<LoginScreen>:
    name: "login"
    md_bg_color: 0.06, 0.07, 0.09, 1
    ScrollView:
        do_scroll_x: False
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            padding: dp(28), dp(48), dp(28), dp(28)
            spacing: dp(14)
            MDLabel:
                text: "Financas Pessoais"
                halign: "center"
                font_style: "H5"
                theme_text_color: "Custom"
                text_color: 0.89, 0.91, 0.94, 1
                size_hint_y: None
                height: dp(48)
            MDLabel:
                text: "Controle financeiro familiar"
                halign: "center"
                font_style: "Caption"
                theme_text_color: "Secondary"
                size_hint_y: None
                height: dp(24)
            MDLabel:
                id: tab_lbl
                text: "ENTRAR"
                halign: "center"
                font_style: "Overline"
                theme_text_color: "Custom"
                text_color: 0.39, 0.40, 0.95, 1
                size_hint_y: None
                height: dp(24)
            MDTextField:
                id: field_user
                hint_text: "Usuario"
                mode: "rectangle"
                size_hint_y: None
                height: dp(56)
            MDTextField:
                id: field_pass
                hint_text: "Senha"
                mode: "rectangle"
                password: True
                size_hint_y: None
                height: dp(56)
            MDTextField:
                id: field_pass2
                hint_text: "Confirmar Senha"
                mode: "rectangle"
                password: True
                size_hint_y: None
                height: dp(56)
                opacity: 0
                disabled: True
            MDLabel:
                id: msg_lbl
                text: ""
                halign: "center"
                font_style: "Caption"
                theme_text_color: "Error"
                size_hint_y: None
                height: dp(24)
            MDRaisedButton:
                id: btn_main
                text: "Entrar"
                size_hint: 1, None
                height: dp(48)
                md_bg_color: 0.39, 0.40, 0.95, 1
                on_release: root.on_main()
            MDRaisedButton:
                id: btn_bio
                text: "Entrar com Digital"
                size_hint: 1, None
                height: dp(48)
                md_bg_color: 0.13, 0.77, 0.37, 1
                opacity: 0
                disabled: True
                on_release: root.on_biometric()
            MDFlatButton:
                id: btn_switch
                text: "Criar nova conta"
                size_hint: 1, None
                height: dp(40)
                on_release: root.toggle_mode()
""")


class LoginScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._register_mode = False

    def on_enter(self):
        self._check_biometric()

    def _check_biometric(self):
        try:
            from utils.biometric import is_available
            if is_available():
                self.ids.btn_bio.opacity = 1
                self.ids.btn_bio.disabled = False
        except Exception:
            pass

    def toggle_mode(self):
        self._register_mode = not self._register_mode
        if self._register_mode:
            self.ids.tab_lbl.text    = "CRIAR CONTA"
            self.ids.btn_main.text   = "Criar Conta"
            self.ids.btn_switch.text = "Ja tenho conta"
            self.ids.field_pass2.opacity = 1
            self.ids.field_pass2.disabled = False
            self.ids.btn_bio.opacity = 0
            self.ids.btn_bio.disabled = True
        else:
            self.ids.tab_lbl.text    = "ENTRAR"
            self.ids.btn_main.text   = "Entrar"
            self.ids.btn_switch.text = "Criar nova conta"
            self.ids.field_pass2.opacity = 0
            self.ids.field_pass2.disabled = True
            self._check_biometric()
        self.ids.msg_lbl.text = ""

    def on_main(self):
        u = self.ids.field_user.text.strip()
        p = self.ids.field_pass.text
        if not u or not p:
            self.ids.msg_lbl.text = "Preencha todos os campos."
            return
        if self._register_mode:
            p2 = self.ids.field_pass2.text
            if p != p2:
                self.ids.msg_lbl.text = "Senhas nao coincidem."
                return
            if len(p) < 4:
                self.ids.msg_lbl.text = "Minimo 4 caracteres."
                return
            try:
                UserModel.create(u, p)
            except Exception as e:
                self.ids.msg_lbl.text = "Usuario ja existe." if "UNIQUE" in str(e) else str(e)
                return
        user = UserModel.authenticate(u, p)
        if not user:
            self.ids.msg_lbl.text = "Usuario ou senha incorretos."
            return
        self._do_login(user)

    def on_biometric(self):
        app = MDApp.get_running_app()
        last = UserModel.load_last_username(app.user_data_dir)
        if not last:
            self.ids.msg_lbl.text = "Faca login manual primeiro para usar a digital."
            return
        self.ids.msg_lbl.text = "Autenticando..."

        def on_success():
            users = UserModel.list_users()
            match = next((u for u in users if u["username"] == last), None)
            if match:
                from database.schema import get_connection
                conn = get_connection()
                row = conn.execute("SELECT * FROM users WHERE username=?", (last,)).fetchone()
                conn.close()
                if row:
                    self._do_login(dict(row))
                    return
            self.ids.msg_lbl.text = "Usuario nao encontrado."

        def on_error(msg):
            self.ids.msg_lbl.text = "Falha: {}".format(msg)

        from utils.biometric import authenticate
        authenticate(on_success, on_error)

    def _do_login(self, user):
        app = MDApp.get_running_app()
        app.current_user = user
        UserModel.save_last_username(user["username"], app.user_data_dir)
        app.root.current = "main"
        app.root.get_screen("main").on_enter_app()

    def on_pre_enter(self):
        self.ids.field_user.text = ""
        self.ids.field_pass.text = ""
        self.ids.field_pass2.text = ""
        self.ids.msg_lbl.text = ""
        self._register_mode = False
        self.ids.tab_lbl.text    = "ENTRAR"
        self.ids.btn_main.text   = "Entrar"
        self.ids.btn_switch.text = "Criar nova conta"
        self.ids.field_pass2.opacity = 0
        self.ids.field_pass2.disabled = True
