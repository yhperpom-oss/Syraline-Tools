"""Secret area presentation: confirmation and a construction placeholder."""
import webbrowser
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input

DISCORD_URL = 'https://discord.gg/TSCFZHPGaX'


class DarkConfirmation(ModalScreen[bool]):
    BINDINGS=[Binding('escape','cancel',show=False)]

    def compose(self):
        with Vertical(id='dark-confirm'):
            yield Static('◈',classes='dark-emblem')
            yield Static(self.app.tr('ZONE VIP'),classes='dark-kicker')
            yield Static(self.app.tr('Vous êtes sur le point d’entrer dans la zone VIP. Souhaitez-vous continuer ?'),id='dark-question')
            with Horizontal(id='dark-actions'):
                yield Button(self.app.tr('Non, revenir'),id='dark-cancel')
                yield Button(self.app.tr('Oui, entrer'),id='dark-accept')

    def on_mount(self):
        self.query_one('#dark-cancel').focus()

    def on_button_pressed(self,event):
        event.stop()
        self.dismiss(event.button.id=='dark-accept')

    def action_cancel(self):
        self.dismiss(False)


class DarkAccess(ModalScreen[bool]):
    BINDINGS=[Binding('escape','cancel',show=False),Binding('ctrl+v','paste',show=False)]

    def compose(self):
        with Vertical(id='dark-access'):
            yield Static('◇  VIP ZONE',classes='dark-kicker')
            yield Static(self.app.tr('Entrez votre clé de licence.'),id='dark-code-label')
            yield Input(password=False,placeholder=self.app.tr('Clé de licence'),id='dark-code')
            yield Static('',id='dark-code-error')
            yield Static(self.app.tr('Entrez une clé valide pour activer le mode VIP et débloquer toutes les features.'),id='dark-key-help')
            yield Static(self.app.tr('Pas de clé ? Rejoins le Discord pour l’obtenir.'),id='dark-key-links-label')
            with Horizontal(id='dark-key-links'):
                yield Button('Discord  ↗',id='dark-discord')
            with Horizontal(id='dark-actions'):
                yield Button(self.app.tr('Annuler'),id='dark-code-cancel')
                yield Button(self.app.tr('Coller'),id='dark-paste')
                yield Button(self.app.tr('Déverrouiller'),id='dark-unlock')

    def on_mount(self):
        self.query_one('#dark-code',Input).focus()

    def unlock(self):
        field=self.query_one('#dark-code',Input)
        key=field.value.strip()
        if not key:
            self.query_one('#dark-code-error',Static).update(self.app.tr('Entrez votre clé de licence.'))
            field.focus();return
        self.query_one('#dark-unlock',Button).disabled=True
        self.query_one('#dark-code-error',Static).update(self.app.tr('Vérification…'))
        self.run_worker(lambda:self._verify(key),thread=True,exclusive=True)

    def _verify(self,key):
        from .license import activate
        result=activate(key)
        self.app.call_from_thread(self._show_result,result)

    def _show_result(self,result):
        self.query_one('#dark-unlock',Button).disabled=False
        field=self.query_one('#dark-code',Input)
        if result.get('ok'):
            field.value=''
            self.dismiss(True)
            return
        message=(result.get('message') or '').strip() or self.app.tr('Code incorrect. Réessayez.')
        self.query_one('#dark-code-error',Static).update(message)
        field.value='';field.focus()

    def action_paste(self):
        from .clipboard import read_clipboard
        text=read_clipboard().strip()
        if text:
            field=self.query_one('#dark-code',Input)
            field.value=text
            field.focus()

    def on_input_submitted(self,event):
        event.stop()
        self.unlock()

    def on_button_pressed(self,event):
        event.stop()
        if event.button.id=='dark-paste':self.action_paste()
        elif event.button.id=='dark-unlock':self.unlock()
        elif event.button.id=='dark-discord':
            try:webbrowser.open(DISCORD_URL)
            except Exception:pass
        else:self.action_cancel()

    def action_cancel(self):
        self.query_one('#dark-code',Input).value=''
        self.dismiss(False)


class DarkConstruction(ModalScreen):
    BINDINGS=[Binding('escape','back',show=False)]

    def compose(self):
        with Vertical(id='dark-chamber'):
            yield Static('◈',classes='dark-emblem')
            yield Static(self.app.tr('ZONE VIP'),classes='dark-kicker')
            yield Static('━━━━━━━━━━━━━━━━',id='dark-divider')
            yield Static(self.app.tr('En construction'),id='dark-title')
            yield Button(self.app.tr('← RETOUR'),id='dark-back')

    def on_mount(self):
        self.query_one('#dark-back').focus()
        if self.app.motion:
            chamber=self.query_one('#dark-chamber')
            chamber.styles.opacity=0
            chamber.styles.animate('opacity',1.,duration=.35)

    def on_button_pressed(self,event):
        event.stop()
        self.action_back()

    def action_back(self):
        self.dismiss()
