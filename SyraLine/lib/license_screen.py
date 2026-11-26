"""Interactive license-activation screen shown before the main SyraLine UI."""
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Input, Static, Select

from . import license as lic
from .localization import LANGUAGES, display_arabic

# Minimal self-contained localization for the gate (falls back to English).
TEXTS = {
    'en': {
        'brand': 'SYRALINE  /  ACTIVATION',
        'enter': 'Enter your license key to activate SyraLine on this machine.',
        'placeholder': 'XXXXX-XXXXX-XXXXX-XXXXX',
        'activate': 'Activate', 'quit': 'Quit', 'working': 'Contacting the license server…',
        'machine': 'Machine ID: ',
        'ok': 'License activated. Launching…',
        'need_key': 'No active license found on this machine.',
        'invalid': 'This license key is not valid.',
        'unknown_key': 'Unknown license key.',
        'revoked': 'This license has been revoked.',
        'expired': 'This license has expired.',
        'bound': 'This key is already used on the maximum number of machines.',
        'offline': 'Cannot reach the license server. Check your connection and retry.',
        'server_error': 'The license server returned an error. Try again later.',
        'empty': 'Please enter a license key.',
    },
    'fr': {
        'brand': 'SYRALINE  /  ACTIVATION',
        'enter': "Entrez votre clé de licence pour activer SyraLine sur cette machine.",
        'placeholder': 'XXXXX-XXXXX-XXXXX-XXXXX',
        'activate': 'Activer', 'quit': 'Quitter', 'working': 'Connexion au serveur de licences…',
        'machine': 'ID machine : ',
        'ok': 'Licence activée. Lancement…',
        'need_key': "Aucune licence active sur cette machine.",
        'invalid': "Cette clé de licence n'est pas valide.",
        'unknown_key': 'Clé de licence inconnue.',
        'revoked': 'Cette licence a été révoquée.',
        'expired': 'Cette licence a expiré.',
        'bound': "Cette clé est déjà utilisée sur le nombre maximum de machines.",
        'offline': "Impossible de joindre le serveur de licences. Vérifiez votre connexion et réessayez.",
        'server_error': 'Le serveur de licences a renvoyé une erreur. Réessayez plus tard.',
        'empty': 'Veuillez entrer une clé de licence.',
    },
}
# Reasons returned by the server/client mapped to a message key.
REASON_KEYS = {
    'need_key': 'need_key', 'empty': 'empty', 'invalid': 'invalid',
    'unknown_key': 'unknown_key', 'bad_signature': 'invalid', 'bad_nonce': 'invalid',
    'wrong_machine': 'invalid', 'revoked': 'revoked', 'expired': 'expired',
    'bound': 'bound', 'max_activations': 'bound', 'offline': 'offline',
    'server_error': 'server_error',
}


class LicenseGate(App[bool]):
    CSS = '''
    Screen { background: #090b10; align: center middle; }
    #card { width: 80; max-width: 96%; height: auto; max-height: 95%;
        border: round #e32636; padding: 1 3; background: #11151e; }
    #brand { color: #e32636; text-style: bold; margin-bottom: 1; }
    #heading { text-style: bold; color: #ffffff; margin-bottom: 1; }
    #key { margin-bottom: 1; }
    #details { color: #d6dbe5; margin-bottom: 1; min-height: 1; }
    Horizontal { height: auto; align: center middle; margin-top: 1; }
    Button { margin: 0 1; min-width: 14; }
    #activate { background: #e32636; color: white; }
    #footnote { color: #8993a6; margin-top: 1; }
    '''
    BINDINGS = [('escape', 'quit', 'Exit')]

    def __init__(self, language=None, reason='need_key', prefill=''):
        super().__init__()
        self.language = language if language in TEXTS else (
            language if language in LANGUAGES else 'en')
        self.reason = reason
        self.prefill = prefill
        self.busy = False

    def tr(self, key):
        table = TEXTS.get(self.language, TEXTS['en'])
        return table.get(key, TEXTS['en'].get(key, key))

    def msg_for(self, reason):
        return self.tr(REASON_KEYS.get(reason, 'invalid'))

    def compose(self) -> ComposeResult:
        with VerticalScroll(id='card'):
            yield Static(self.tr('brand'), id='brand')
            yield Static(self.tr('enter'), id='heading')
            yield Input(value=self.prefill, placeholder=self.tr('placeholder'), id='key')
            yield Static(self.msg_for(self.reason), id='details', markup=False)
            with Horizontal():
                yield Button(self.tr('activate'), id='activate')
                yield Button(self.tr('quit'), id='quit')
            yield Static(self.tr('machine') + lic.machine_id(), id='footnote', markup=False)
            yield Select([(display_arabic(name) if code == 'ar' else name, code)
                          for code, name in LANGUAGES.items()],
                         value=self.language if self.language in LANGUAGES else 'en',
                         allow_blank=False, id='gate-language')

    def on_mount(self):
        self.query_one('#key', Input).focus()

    def on_select_changed(self, event: Select.Changed):
        if event.select.id != 'gate-language' or event.value == self.language:
            return
        self.language = event.value if event.value in TEXTS else 'en'
        self.query_one('#brand', Static).update(self.tr('brand'))
        self.query_one('#heading', Static).update(self.tr('enter'))
        self.query_one('#activate', Button).label = self.tr('activate')
        self.query_one('#quit', Button).label = self.tr('quit')
        self.query_one('#key', Input).placeholder = self.tr('placeholder')

    def on_input_submitted(self, event: Input.Submitted):
        self.start_activation()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == 'quit':
            self.exit(False)
        elif event.button.id == 'activate':
            self.start_activation()

    def start_activation(self):
        if self.busy:
            return
        key = self.query_one('#key', Input).value.strip()
        if not key:
            self.query_one('#details', Static).update(self.tr('empty'))
            return
        self.busy = True
        self.query_one('#activate', Button).disabled = True
        self.query_one('#details', Static).update(self.tr('working'))
        self.run_worker(lambda: self.do_activate(key), thread=True, exclusive=True)

    def do_activate(self, key):
        result = lic.activate(key)
        self.call_from_thread(self.show_result, result)

    def show_result(self, result):
        self.busy = False
        self.query_one('#activate', Button).disabled = False
        if result.get('ok'):
            self.query_one('#details', Static).update(self.tr('ok'))
            self.exit(True)
            return
        # Prefer the backend's own message (e.g. KeyAuth) when it provides one,
        # otherwise fall back to the localized reason text.
        message = (result.get('message') or '').strip()
        self.query_one('#details', Static).update(
            message or self.msg_for(result.get('reason', 'invalid')))

    def action_quit(self):
        self.exit(False)
