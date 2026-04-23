from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.app import MDApp

Builder.load_string("""
<ProfileScreen>:
    name: "tab_profile"
    md_bg_color: 0.06, 0.07, 0.09, 1
    ScrollView:
        do_scroll_x: False
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(16)
            padding: dp(24), dp(32), dp(24), dp(24)
            MDLabel:
                text: "Perfil"
                font_style: "H5"
                theme_text_color: "Custom"
                text_color: 0.89, 0.91, 0.94, 1
                halign: "center"
                size_hint_y: None
                height: dp(48)
            MDCard:
                orientation: "vertical"
                md_bg_color: 0.10, 0.11, 0.15, 1
                radius: [dp(12)]
                padding: dp(20), dp(16)
                spacing: dp(8)
                size_hint_y: None
                height: dp(100)
                MDLabel:
                    text: "Usuario logado"
                    font_style: "Overline"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(18)
                MDLabel:
                    id: username_lbl
                    text: ""
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 0.89, 0.91, 0.94, 1
                    size_hint_y: None
                    height: dp(36)
            MDRaisedButton:
                text: "Alterar Senha"
                size_hint: 1, None
                height: dp(48)
                md_bg_color: 0.39, 0.40, 0.95, 1
                on_release: root.change_password()
            MDCard:
                orientation: "vertical"
                md_bg_color: 0.10, 0.11, 0.15, 1
                radius: [dp(12)]
                padding: dp(20), dp(16)
                spacing: dp(4)
                size_hint_y: None
                height: dp(80)
                MDLabel:
                    text: "Financas Pessoais"
                    font_style: "Subtitle1"
                    theme_text_color: "Custom"
                    text_color: 0.89, 0.91, 0.94, 1
                    size_hint_y: None
                    height: dp(28)
                MDLabel:
                    text: "Versao 1.0  |  Dados armazenados localmente"
                    font_style: "Caption"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(20)
            MDLabel:
                size_hint_y: None
                height: dp(16)
            MDRaisedButton:
                text: "Sair da Conta (Logoff)"
                size_hint: 1, None
                height: dp(52)
                md_bg_color: 0.94, 0.27, 0.27, 1
                on_release: root.do_logout()
""")


class ProfileScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)

    def refresh(self):
        app = MDApp.get_running_app()
        if hasattr(app, 'current_user') and app.current_user:
            self.ids.username_lbl.text = app.current_user.get("username", "—")

    def do_logout(self):
        app = MDApp.get_running_app()
        app.current_user = None
        app.root.current = "login"

    def change_password(self):
        app = MDApp.get_running_app()
        if not hasattr(app, 'current_user') or not app.current_user:
            return
        uid = app.current_user["id"]
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(170), padding=[0, dp(8), 0, 0])
        f_old = MDTextField(hint_text="Senha atual", mode="rectangle",
                            password=True, size_hint_y=None, height=dp(52))
        f_new = MDTextField(hint_text="Nova senha", mode="rectangle",
                            password=True, size_hint_y=None, height=dp(52))
        f_new2 = MDTextField(hint_text="Confirmar nova senha", mode="rectangle",
                             password=True, size_hint_y=None, height=dp(52))
        for w in [f_old, f_new, f_new2]: content.add_widget(w)
        dlg = [None]
        msg = [None]

        def save(*a):
            from models.user import UserModel, _verify, _hash
            from database.schema import get_connection
            user = app.current_user
            if not _verify(f_old.text, user["password_hash"]):
                if msg[0]: msg[0].text = "Senha atual incorreta."
                return
            if f_new.text != f_new2.text:
                if msg[0]: msg[0].text = "Senhas nao coincidem."
                return
            if len(f_new.text) < 4:
                if msg[0]: msg[0].text = "Minimo 4 caracteres."
                return
            new_hash = _hash(f_new.text)
            conn = get_connection()
            conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, uid))
            conn.commit()
            conn.close()
            app.current_user["password_hash"] = new_hash
            dlg[0].dismiss()

        lbl_msg = MDLabel(text="", font_style="Caption", theme_text_color="Error",
                          size_hint_y=None, height=dp(20))
        msg[0] = lbl_msg
        content.add_widget(lbl_msg)

        dlg[0] = MDDialog(
            title="Alterar Senha", type="custom", content_cls=content,
            buttons=[MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                     MDRaisedButton(text="Salvar", md_bg_color=(0.39,0.40,0.95,1), on_release=save)])
        dlg[0].open()
