from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
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
                    text: "—"
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
                    text: "Versao 1.0  |  Dados locais no celular"
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

        content = MDBoxLayout(orientation="vertical", spacing=dp(10),
                              size_hint_y=None, height=dp(210), padding=[0, dp(8), 0, 0])
        f_old  = MDTextField(hint_text="Senha atual",       mode="rectangle", password=True, size_hint_y=None, height=dp(56))
        f_new  = MDTextField(hint_text="Nova senha",        mode="rectangle", password=True, size_hint_y=None, height=dp(56))
        f_new2 = MDTextField(hint_text="Confirmar nova",    mode="rectangle", password=True, size_hint_y=None, height=dp(56))
        msg_lbl = MDLabel(text="", font_style="Caption", theme_text_color="Error",
                          size_hint_y=None, height=dp(24), halign="center")
        for w in [f_old, f_new, f_new2, msg_lbl]:
            content.add_widget(w)

        dlg = [None]

        def save(*a):
            old  = f_old.text
            new  = f_new.text
            new2 = f_new2.text
            if not old or not new:
                msg_lbl.text = "Preencha todos os campos."
                return
            if new != new2:
                msg_lbl.text = "Novas senhas nao coincidem."
                return
            if len(new) < 4:
                msg_lbl.text = "Minimo 4 caracteres."
                return
            from models.user import UserModel
            ok = UserModel.change_password(uid, old, new)
            if not ok:
                msg_lbl.text = "Senha atual incorreta."
                return
            # Atualiza hash no cache
            from database.schema import get_connection
            conn = get_connection()
            row = conn.execute("SELECT password_hash FROM users WHERE id=?", (uid,)).fetchone()
            conn.close()
            if row:
                app.current_user["password_hash"] = row["password_hash"]
            dlg[0].dismiss()

        dlg[0] = MDDialog(
            title="Alterar Senha", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda x: dlg[0].dismiss()),
                MDRaisedButton(text="Salvar", md_bg_color=(0.39,0.40,0.95,1), on_release=save)])
        dlg[0].open()
