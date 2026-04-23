"""
Autenticacao biometrica (digital) para Android.
Usa pyjnius + BiometricPrompt da biblioteca AndroidX.
"""
from kivy.logger import Logger


def is_biometric_available():
    """Retorna True se o dispositivo suporta biometria."""
    try:
        from jnius import autoclass
        BiometricManager = autoclass('androidx.biometric.BiometricManager')
        from android import activity
        ctx = activity.mActivity
        mgr = BiometricManager.from_(ctx)
        result = mgr.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_WEAK)
        return result == BiometricManager.BIOMETRIC_SUCCESS
    except Exception as e:
        Logger.warning("Biometric: nao disponivel - {}".format(e))
        return False


def authenticate(on_success, on_error, on_negative=None,
                 title="Autenticacao", subtitle="Use sua digital para entrar",
                 negative_text="Usar senha"):
    """
    Exibe o prompt de biometria do Android.
    on_success() chamado quando a digital for aceita.
    on_error(msg) chamado em caso de erro.
    on_negative() chamado quando usuario clica 'Usar senha'.
    """
    try:
        from jnius import autoclass, PythonJavaClass, java_method, cast
        from android import activity
        from android.runnable import run_on_ui_thread

        BiometricPrompt = autoclass('androidx.biometric.BiometricPrompt')
        PromptInfo     = autoclass('androidx.biometric.BiometricPrompt$PromptInfo')
        Builder        = autoclass('androidx.biometric.BiometricPrompt$PromptInfo$Builder')
        Executors      = autoclass('java.util.concurrent.Executors')

        class AuthCallback(PythonJavaClass):
            __javainterfaces__ = ['androidx/biometric/BiometricPrompt$AuthenticationCallback']
            __javacontext__    = 'app'

            @java_method('(Landroidx/biometric/BiometricPrompt$AuthenticationResult;)V')
            def onAuthenticationSucceeded(self, result):
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: on_success(), 0)

            @java_method('(ILjava/lang/CharSequence;)V')
            def onAuthenticationError(self, code, msg):
                from kivy.clock import Clock
                msg_str = str(msg)
                if code == 10:  # ERROR_NEGATIVE_BUTTON
                    if on_negative:
                        Clock.schedule_once(lambda dt: on_negative(), 0)
                else:
                    Clock.schedule_once(lambda dt: on_error(msg_str), 0)

            @java_method('()V')
            def onAuthenticationFailed(self):
                pass  # Tentativa falhou mas nao e erro terminal

        @run_on_ui_thread
        def _show():
            frag_activity = cast(
                'androidx.fragment.app.FragmentActivity', activity.mActivity)
            executor = Executors.newSingleThreadExecutor()
            callback = AuthCallback()

            prompt = BiometricPrompt(frag_activity, executor, callback)

            info = (Builder()
                    .setTitle(title)
                    .setSubtitle(subtitle)
                    .setNegativeButtonText(negative_text)
                    .build())
            prompt.authenticate(info)

        _show()

    except Exception as e:
        Logger.exception("Biometric: erro ao exibir prompt")
        on_error("Digital nao disponivel neste dispositivo.")
