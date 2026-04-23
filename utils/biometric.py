"""Autenticação biométrica (digital) — Android only, graceful fallback."""

def is_available() -> bool:
    try:
        from jnius import autoclass
        BiometricManager = autoclass('androidx.biometric.BiometricManager')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        ctx = PythonActivity.mActivity
        manager = BiometricManager.from_(ctx)
        STRONG = BiometricManager.Authenticators.BIOMETRIC_STRONG
        return manager.canAuthenticate(STRONG) == BiometricManager.BIOMETRIC_SUCCESS
    except Exception:
        return False


def authenticate(on_success, on_error):
    """Mostra o prompt de digital do Android."""
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        from android.runnable import run_on_ui_thread
        from kivy.clock import Clock

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        BiometricPromptClass = autoclass('androidx.biometric.BiometricPrompt')
        PromptInfo = autoclass('androidx.biometric.BiometricPrompt$PromptInfo')
        Executors = autoclass('java.util.concurrent.Executors')

        class _Callback(PythonJavaClass):
            __javacontext__ = 'app'
            __javainterfaces__ = ['androidx/biometric/BiometricPrompt$AuthenticationCallback']

            def __init__(self):
                super().__init__()

            @java_method('(Landroidx/biometric/BiometricPrompt$AuthenticationResult;)V')
            def onAuthenticationSucceeded(self, result):
                Clock.schedule_once(lambda dt: on_success(), 0)

            @java_method('(ILjava/lang/CharSequence;)V')
            def onAuthenticationError(self, code, msg):
                Clock.schedule_once(lambda dt: on_error(str(msg)), 0)

            @java_method('()V')
            def onAuthenticationFailed(self):
                pass

        cb = _Callback()

        @run_on_ui_thread
        def _show():
            activity = PythonActivity.mActivity
            executor = Executors.newSingleThreadExecutor()
            prompt = BiometricPromptClass(activity, executor, cb)
            info = (PromptInfo.Builder()
                    .setTitle("Financas Pessoais")
                    .setSubtitle("Use sua digital para entrar")
                    .setNegativeButtonText("Cancelar")
                    .build())
            prompt.authenticate(info)

        _show()

    except Exception as e:
        on_error("Digital nao disponivel: {}".format(e))
