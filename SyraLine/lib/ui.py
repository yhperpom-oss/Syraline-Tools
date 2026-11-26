"""Présentation exclusivement : aucun execute() de l'application initiale modifié."""
from __future__ import annotations
import json
import zipfile
import math
import os
import colorsys
import webbrowser
from pathlib import Path
import time

# Lien Discord officiel (carte profil + écran VIP SPACE).
DISCORD_URL = 'https://discord.gg/TSCFZHPGaX'
from datetime import datetime

import pyfiglet
import psutil
from rich.text import Text
from textual import events
from textual.color import Color
from textual.content import Content
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll, HorizontalScroll, Grid
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input, Label, ListView, ListItem, TextArea
from .boot import NeonBoot, MatrixBoot
from .dark import DarkConfirmation, DarkAccess, DarkConstruction
from .vip import VipArrival
import zipfile
from types import SimpleNamespace
from .config import PROFILE_PATH, read_profile, write_profile
from .setup import ProfileScreen
from .localization import translate, EN, LANGUAGES
from tools.core import TOOLS as EXTRA_TOOLS
from tools.catalog_policy import RETIRED_TOOLS

from .constants import APP_DIR as ROOT, STYLES_DIR, INPUT_DIR
from .result_export import save_result
from .tools import legacy
from .pages import CATEGORIES, CAT_LABELS, CAT_ICONS, SHORT, CAT_ART, TOOLS

def compact_qr(matrix):
    """Même matrice QR ; deux modules verticaux par cellule terminal."""
    width=len(matrix[0])+6
    padded=[[False]*width for _ in range(3)]
    padded += [[False]*3+list(row)+[False]*3 for row in matrix]
    padded += [[False]*width for _ in range(3)]
    if len(padded)%2:padded.append([False]*width)
    lines=[]
    for y in range(0,len(padded),2):
        lines.append(''.join(' ▀▄█'[int(padded[y][x])+2*int(padded[y+1][x])] for x in range(width)))
    return Text('\n'.join(lines),style='#080808 on #ffffff',no_wrap=True,overflow='crop')

legacy._qr_to_text=compact_qr

from .themes import PALETTES

for key,(_,accent,secondary,bg,surface,line,fg,dim,gold) in PALETTES.items():
    legacy.THEMES[key]={'syraline-bg':bg,'syraline-bg-alt':surface,'syraline-border':line,'syraline-accent':accent,'syraline-accent-2':secondary,'syraline-cyan':gold,'syraline-text':fg,'syraline-text-dim':dim,'syraline-success':'#8bd5ae','syraline-warning':gold,'syraline-error':'#ff6378'}


def color(app,key):
    if app.active_theme=='rainbow' and not app.accent and key in ('syraline-accent','syraline-accent-2'):
        accent=getattr(app,'rainbow_accent','#ff506a')
        return accent if key=='syraline-accent' else blend(accent,'#100d13',.32)
    if getattr(app,'accent','') and key in ('syraline-accent','syraline-accent-2'):
        return app.accent if key=='syraline-accent' else blend(app.accent,'#100d13',.32)
    return legacy.THEMES[app.active_theme][key]
def blend(a,b,t):
    aa=tuple(int(a[i:i+2],16) for i in (1,3,5));bb=tuple(int(b[i:i+2],16) for i in (1,3,5))
    return '#'+''.join(f'{round(x+(y-x)*max(0,min(1,t))):02x}' for x,y in zip(aa,bb))

class NavCats(HorizontalScroll):
    """Barre de catégories horizontale : la molette la fait défiler latéralement
    (utile en petite fenêtre où toutes les catégories ne tiennent pas)."""
    def on_mouse_scroll_down(self,event):
        self.scroll_relative(x=14,animate=False);event.stop()
    def on_mouse_scroll_up(self,event):
        self.scroll_relative(x=-14,animate=False);event.stop()


class VipZoneButton(Button):
    """An animated dark portal drawn cell by cell, with native button controls."""
    def on_mount(self):
        self.styles.line_pad=0
        self.phase=0.;self.engagement=0.;self.last_tick=time.monotonic()
        self.set_interval(1/24,self.aura_frame)

    def aura_frame(self):
        now=time.monotonic();delta=min(.1,now-self.last_tick);self.last_tick=now
        if self.app.screen is not self.screen:return
        target=float(self.is_mouse_over or self.has_focus)
        if self.app.motion:
            self.phase+=delta
            self.engagement+=(target-self.engagement)*.22
        else:self.engagement=target
        self.refresh()

    def render(self):
        width=max(4,self.content_size.width)
        phase=getattr(self,'phase',0.)
        engagement=getattr(self,'engagement',0.)
        pulse=(.5-.5*math.cos(phase*math.tau/4)) if self.app.motion else .35
        vip=bool(self.app.vip_pack)
        violet=blend('#c99a2e' if vip else '#ad8544','#ffd86b' if vip else '#f4d997',engagement)
        head=(phase/3.8%1)*(width*2+2)
        title='◇  VIP ZONE  ↗' if width>=19 else 'VIP ZONE'
        if self.app.vip_pack:title='◆  VIP ON  ◆' if width>=15 else 'VIP ON'
        inner=width-2
        title=title[:inner].center(inner)
        lines=['╭'+'─'*inner+'╮','│'+title+'│','╰'+'─'*inner+'╯']
        out=Text(no_wrap=True,overflow='crop')
        for y,line in enumerate(lines):
            for x,char in enumerate(line):
                edge=y!=1 or x in (0,width-1)
                perimeter=x if y==0 else width+1+(width-1-x)
                distance=min(abs(perimeter-head),width*2+2-abs(perimeter-head))
                flare=max(0,1-distance/5) if self.app.motion else .15
                if edge:
                    ink=blend('#4a3515' if vip else '#49391f',violet,.35+.3*pulse+.35*engagement)
                    ink=blend(ink,'#fff3c8' if vip else '#fff0c5',flare*.9)
                else:
                    ink=blend('#e2c882' if vip else '#dfcc9f','#fff6dc' if vip else '#fff4d9',engagement)
                    if char in '◇↗':ink=blend(violet,'#fff0c5',engagement)
                depth=max(0,1-abs(x-(width-1)/2)/(width/2))
                background=blend('#0e0b05' if vip else '#0c0a07','#5a4414' if vip else '#51401d',depth*(.18+.28*engagement))
                out.append(char,style=('bold ' if not edge else '')+ink+' on '+background)
            if y<2:out.append('\n')
        return Content.from_rich_text(out)

class Wordmark(Static):
    def on_mount(self):
        self.phase=0.;self.logo=pyfiglet.figlet_format('SYRALINE',font='ansi_shadow').rstrip('\n')
        self.set_interval(.12,self.tick)
    def tick(self):
        if self.app.motion and self.app.screen is self.screen:
            self.phase+=.12;self.refresh()
    def render(self):
        accent=color(self.app,'syraline-accent');dim=color(self.app,'syraline-accent-2');fg=color(self.app,'syraline-text')
        if self.size.width<38:
            return Text('S Y R A L I N E  /  T O O L S',style='bold '+accent)
        lines=self.logo.splitlines();width=max(map(len,lines));out=Text()
        for y,line in enumerate(lines):
            for x,ch in enumerate(line):
                gleam=max(0,1-abs((x-self.phase*6)%(width+20)-8)/7)*.65 if self.app.motion else 0
                out.append(ch,style=blend(blend(accent,dim,y/max(1,len(lines)-1)*.5),fg,gleam))
            if y<len(lines)-1:out.append('\n')
        return out

# Police pixel « maison » (demi-blocs), nette et lisible en petite taille.
# Chaque lettre : 8 lignes de pixels sur 6 colonnes.
_PIXEL_GLYPHS=(
    ('011111','111111','110000','111110','011111','000011','111111','111110'),  # S
    ('110011','110011','111111','011110','001100','001100','001100','001100'),  # Y
    ('111110','111111','110011','110011','111110','111100','110110','110011'),  # R
    ('001100','011110','110011','110011','111111','111111','110011','110011'),  # A
    ('110000','110000','110000','110000','110000','110000','111111','111111'),  # L
    ('111111','111111','001100','001100','001100','001100','111111','111111'),  # I
    ('110011','111011','111011','111111','111111','110111','110111','110011'),  # N
    ('111111','111111','110000','111110','111110','110000','111111','111111'),  # E
)

def _pixel_logo(gap=1):
    """Logo SYRALINE en demi-blocs, 4 lignes. gap=1 → ~55 colonnes (net),
    gap=0 → ~48 colonnes (repli pour les fenêtres un peu plus étroites)."""
    sep='0'*gap
    pixels=[sep.join(g[y] for g in _PIXEL_GLYPHS) for y in range(8)]
    return [''.join(' ▀▄█'[int(t)+2*int(b)] for t,b in zip(pixels[y],pixels[y+1])) for y in range(0,8,2)]


class CompactSignature(Static):
    """Wordmark SYRALINE : grande police ansi_shadow en fenêtre large, police
    pixel maison (nette) en fenêtre étroite."""
    LOGO=pyfiglet.figlet_format('SYRALINE',font='ansi_shadow').rstrip('\n').splitlines()
    COMPACT_LOGO=_pixel_logo(1)   # ~55 colonnes, version nette
    COMPACT_TIGHT=_pixel_logo(0)  # ~48 colonnes, repli si moins de place
    BIG_W=max((len(l) for l in LOGO),default=1)
    def on_mount(self):
        self.phase=0.;self.last_tick=time.monotonic()
        self.set_interval(1/24,self.tick)
    def tick(self):
        now=time.monotonic();elapsed=min(.1,now-self.last_tick);self.last_tick=now
        if self.app.motion and self.app.screen is self.screen:
            self.phase+=elapsed;self.refresh()
    def render(self):
        width=max(1,self.content_size.width)
        accent=color(self.app,'syraline-accent');dim=color(self.app,'syraline-accent-2');fg=color(self.app,'syraline-text')
        # Titre pixel (4 lignes) : version large si elle tient dans l'espace
        # central, sinon version étroite, sinon texte.
        lines=self.COMPACT_LOGO if max(len(l) for l in self.COMPACT_LOGO)<=width else self.COMPACT_TIGHT
        logo_width=max((len(l) for l in lines),default=1)
        if logo_width>width:
            return Text('S Y R A L I N E',style='bold '+accent,no_wrap=True,overflow='crop')
        # Centrage MANUEL (mêmes espaces en tête de chaque ligne) : indispensable,
        # sinon le centrage CSS recadre chaque ligne séparément et casse le logo.
        pad=max(0,(width-logo_width)//2)
        text=Text(no_wrap=True,overflow='crop')
        for y,line in enumerate(lines):
            line=line.ljust(logo_width)
            if pad:text.append(' '*pad)
            for x,char in enumerate(line):
                # Un reflet traverse les lettres sans déplacer le logo.
                sweep=(self.phase%4.6)/2.2
                head=-10+sweep*(logo_width+20)
                gleam=max(0,1-abs(x-head)/10)**1.2 if self.app.motion and sweep<1.2 else 0
                base=blend(blend(accent,dim,y/max(1,len(lines)-1)*.5),fg,gleam*.7)
                text.append(char,style=base)
            if y<len(lines)-1:text.append('\n')
        return text

class SignatureRail(Static):
    def on_mount(self):
        self.phase=0.;self.last_tick=time.monotonic();self.set_interval(1/24,self.tick)
    def tick(self):
        now=time.monotonic();elapsed=min(.1,now-self.last_tick);self.last_tick=now
        if self.app.motion and self.app.screen is self.screen:
            self.phase+=elapsed;self.refresh()
    def render(self):
        width=max(1,self.size.width)
        out=Text(no_wrap=True)
        for x in range(width):
            strength=max(0,1-x/max(1,width*.55))**2
            if self.app.motion:
                head=((self.phase%5.2)/3.7)*(width+20)-10
                strength=max(strength,max(0,1-abs(x-head)/11)**1.5)
            out.append('━' if x<3 or strength>.55 else '─',style=blend(color(self.app,'syraline-border'),color(self.app,'syraline-accent'),strength))
        return out

class Orbital(Static):
    """Sculpture de particules braille, purement décorative et calculée localement."""
    def on_mount(self):
        self.phase=0.;self.set_interval(.14,self.tick)
    def tick(self):
        if self.app.motion and self.app.screen is self.screen:
            self.phase+=.045;self.refresh()
    def render(self):
        w=max(8,self.size.width);h=max(3,self.size.height);pw=w*2;ph=h*4
        dots={};brightness={};lut=((1,8),(2,16),(4,32),(64,128))
        def plot(x,y,level):
            x=int(x);y=int(y)
            if 0<=x<pw and 0<=y<ph:
                key=(x//2,y//4);dots[key]=dots.get(key,0)|lut[y%4][x%2];brightness[key]=max(level,brightness.get(key,0))
        for ring in range(3):
            tilt=(-.8,.8,0.05)[ring];r=min(pw*.42,ph*.6)
            for i in range(230):
                t=i/230*math.tau
                xx=math.cos(t)*r;yy=math.sin(t)*r*.4
                x=xx*math.cos(tilt)-yy*math.sin(tilt);y=xx*math.sin(tilt)+yy*math.cos(tilt)
                phase=(t-self.phase-ring*1.7)%math.tau
                plot(pw/2+x,ph/2+y*.65,.3+.7*max(0,1-phase/1.5))
        for k in range(28):
            t=k/28*math.tau+self.phase*.3
            plot(pw/2+math.cos(t)*5,ph/2+math.sin(t)*4,1)
        out=Text();accent=color(self.app,'syraline-accent');line=color(self.app,'syraline-border')
        for y in range(h):
            for x in range(w):
                key=(x,y);out.append(chr(0x2800+dots[key]) if key in dots else ' ',style=blend(line,accent,brightness.get(key,0)))
            if y<h-1:out.append('\n')
        return out

class Topline(Static):
    def on_mount(self):self.set_interval(1,self.refresh)
    def render(self):
        a=color(self.app,'syraline-accent');d=color(self.app,'syraline-text-dim');f=color(self.app,'syraline-text')
        text=Text('  ◈ ',style=a);text.append('SYRALINE',style='bold '+f);text.append(' / TOOLS',style=d)
        suffix=self.app.username+'  /  '+datetime.now().strftime('%H:%M')+'  '
        text.append(' '*max(2,self.size.width-len(text.plain)-len(suffix)));text.append(suffix,style=d)
        return text

class Telemetry(Static):
    def on_mount(self):
        self.cpu=[0.]*16;self.mem=0.;psutil.cpu_percent();self.set_interval(1,self.tick);self.tick()
    def tick(self):
        self.cpu=(self.cpu+[psutil.cpu_percent()])[-16:];self.mem=psutil.virtual_memory().percent;self.refresh()
    def render(self):
        a=color(self.app,'syraline-accent');d=color(self.app,'syraline-text-dim');f=color(self.app,'syraline-text')
        out=Text('SYSTÈME LOCAL\n\n',style=d)
        out.append('CPU  ',style=d);out.append(f'{self.cpu[-1]:5.1f}%\n',style=f)
        out.append(''.join('▁▂▃▄▅▆▇█'[min(7,int(v/100*8))] for v in self.cpu)+'\n\n',style=a)
        out.append('RAM  ',style=d);out.append(f'{self.mem:5.1f}%\n',style=f)
        n=round(self.mem/100*16);out.append('━'*n,style=a);out.append('━'*(16-n),style=color(self.app,'syraline-border'))
        return out

class ModuleCard(Static,can_focus=True):
    BINDINGS=[Binding('enter','open','Ouvrir',show=False),Binding('right','next_card',show=False),Binding('left','previous_card',show=False),Binding('down','down_card',show=False),Binding('up','up_card',show=False)]
    class Picked(Message):
        def __init__(self,card):super().__init__();self.card=card
    def __init__(self,cat,num,name,index):
        super().__init__(id=f'module-{index}',classes='module-card');self.cat=cat;self.num=num;self.tool_name=name;self.index=index;self.hovered=False;self.glow=0.;self.reveal_at=None;self.motion_style=None
        self.tooltip=None
        self.is_premium = '[PREMIUM]' in name or 'PREMIUM' in name.upper() or name in getattr(self.app, 'premium_tools', set())
        if self.is_premium:
            self.add_class('premium-card')
    def on_mount(self):self.tooltip=self.app.tr(self.app.descriptions[self.tool_name])
    def on_focus(self):self.post_message(self.Picked(self));self.scroll_visible(animate=self.app.motion)
    def on_enter(self):self.hovered=True
    def on_leave(self):self.hovered=False
    def motion_frame(self,now,enabled):
        target=1. if self.hovered or self.has_focus else 0.
        self.glow=target if not enabled else self.glow+(target-self.glow)*.27
        if abs(self.glow-target)<.005:self.glow=target
        opacity=1.
        if self.reveal_at is not None and enabled:
            progress=max(0.,min(1.,(now-self.reveal_at)/.22))
            opacity=.25+.75*(1-(1-progress)**3)
            if progress>=1:self.reveal_at=None
        elif not enabled:self.reveal_at=None
        state=(round(self.glow,3),round(opacity,3),self.app.active_theme,color(self.app,'syraline-accent'),getattr(self,'is_premium',False))
        if state==self.motion_style:return
        self.motion_style=state
        if getattr(self, 'is_premium', False):
            self.styles.border=('round',blend('#8a6d1b','#ffd700',self.glow))
            self.styles.background=Color.parse(blend('#130f04','#2b2106',self.glow*.35))
        else:
            self.styles.border=('round',blend(color(self.app,'syraline-border'),color(self.app,'syraline-accent'),self.glow))
            self.styles.background=Color.parse(blend(color(self.app,'syraline-bg-alt'),color(self.app,'syraline-accent'),self.glow*.18))
        self.styles.opacity=state[1]
    def on_click(self):self.focus();self.action_open()
    def action_open(self):self.app.open_tool(self.cat,self.tool_name)
    def action_next_card(self):self.app.move_card(self,1)
    def action_previous_card(self):self.app.move_card(self,-1)
    def action_down_card(self):self.app.move_card(self,self.app.columns)
    def action_up_card(self):self.app.move_card(self,-self.app.columns)
    def render(self):
        a=color(self.app,'syraline-accent');d=color(self.app,'syraline-text-dim');f=color(self.app,'syraline-text')
        title,subtitle=self.app.short[self.tool_name];title=self.app.tr(title);subtitle=self.app.tr(subtitle);width=max(12,self.content_size.width)
        out=Text(no_wrap=True,overflow='ellipsis')
        if getattr(self, 'is_premium', False):
            unlocked=bool(self.app.vip_pack)
            out.append((f'{self.index+1:02}' if self.app.category=='all' else self.num)+' ',style='bold #ffd700')
            clean_title = title.replace('[PREMIUM]', '').strip()
            out.append(clean_title[:max(1,width-10)]+' ',style='bold #ffffff')
            out.append(('★ VIP\n' if unlocked else '◆ VIP\n'),style='bold #ffd700')
            out.append((subtitle[:width-1]+'…' if len(subtitle)>width else subtitle)+'\n',style='#e6c200')
            tail=self.app.tr(' · VIP ACTIF') if unlocked else self.app.tr(' · VERROUILLÉ')
            out.append(self.app.tr(self.app.cat_labels.get(self.cat,self.cat.upper()))+tail,style='bold #ffa500')
            return out
        if self.cat == 'all':
            out.append((f'{self.index+1:02}')+' ',style='bold #ff3452')
            out.append(title[:max(1,width-10)]+' ',style='bold #ffffff')
            out.append('◈ HUB\n',style='bold #ff3452')
            out.append((subtitle[:width-1]+'…' if len(subtitle)>width else subtitle)+'\n',style=d)
            out.append(self.app.tr('HOME · ACCÈS RAPIDE'),style='bold #ffacbb')
            return out
        out.append((f'{self.index+1:02}' if self.app.category=='all' else self.num)+' ',style=a)
        out.append(title[:max(1,width-3)]+'\n',style='bold '+f)
        out.append((subtitle[:width-1]+'…' if len(subtitle)>width else subtitle)+'\n',style=d)
        out.append(self.app.tr(self.app.cat_labels.get(self.cat,self.cat.upper())),style=color(self.app,'syraline-accent-2'))
        return out

class Inspector(Vertical):
    def compose(self):
        yield Static('MODULE / FOCUS',id='inspector-tag')
        yield Orbital(id='detail-orbit')
        yield Static('01',id='detail-number')
        yield Static('WEB LOOKUP',id='detail-name')
        yield Static(self.app.tr(self.app.descriptions[self.app.catalog[0][2]]),id='detail-description')
        yield Static('IP & RÉSEAU',id='detail-meta')
        yield Button('OUVRIR LE MODULE  ↗',id='detail-open')
        yield Static('La précision commence\npar le bon outil.',id='detail-caption')
    def select(self,card):
        is_prem = getattr(card, 'is_premium', False)
        if card.cat == 'all':
            self.query_one('#detail-number',Static).update(Text(f"{card.num} ◈ HUB", style="bold #ffd700" if is_prem else "bold #ff3452"))
            self.query_one('#detail-name',Static).update(Text(self.app.tr(self.app.short[card.tool_name][0]), style="bold #ffffff"))
            self.query_one('#detail-description',Static).update(Text(self.app.tr(self.app.descriptions[card.tool_name]), style="#f6e9ed"))
            self.query_one('#detail-meta',Static).update(Text(self.app.tr("HOME · HUB OFFICIEL"), style="bold #ffacbb"))
            btn = self.query_one('#detail-open',Button)
            if card.tool_name in ('Discord', 'Telegram'):
                btn.label = self.app.tr('REJOINDRE  ↗')
            elif card.tool_name == 'Zone VIP':
                btn.label = self.app.tr('ACTIVER VIP  ★')
            elif is_prem:
                btn.label = 'DÉBLOQUER (PREMIUM) ★'
            elif card.tool_name == 'Mode Standard':
                btn.label = self.app.tr('QUITTER LE VIP  ←')
            else:
                btn.label = self.app.tr('OUVRIR L’OPTION  ↗')
            btn.styles.background = '#8a6d1b' if is_prem else color(self.app, 'syraline-accent-2')
            btn.styles.color = '#ffffff'
            return
        if is_prem:
            self.query_one('#detail-number',Static).update(Text(f"{card.num} ★ PREMIUM", style="bold #ffd700"))
            self.query_one('#detail-name',Static).update(Text(self.app.tr(self.app.short[card.tool_name][0]), style="bold #ffffff"))
            self.query_one('#detail-description',Static).update(Text(self.app.tr(self.app.descriptions[card.tool_name]), style="#e6c200"))
            self.query_one('#detail-meta',Static).update(Text(self.app.tr(self.app.cat_labels.get(card.cat, card.cat.upper())) + " · ACCÈS VIP", style="bold #ffa500"))
            btn = self.query_one('#detail-open',Button)
            btn.label = self.app.tr('OUVRIR LE MODULE  ↗') if self.app.vip_pack else self.app.tr('DÉBLOQUER (VIP)  ★')
            btn.styles.background = '#8a6d1b'
            btn.styles.color = '#ffffff'
        else:
            self.query_one('#detail-number',Static).update(card.num)
            self.query_one('#detail-name',Static).update(self.app.tr(self.app.short[card.tool_name][0]))
            self.query_one('#detail-description',Static).update(self.app.tr(self.app.descriptions[card.tool_name]))
            self.query_one('#detail-meta',Static).update(self.app.tr(self.app.cat_labels.get(card.cat, card.cat.upper())))
            btn = self.query_one('#detail-open',Button)
            btn.label = 'OUVRIR LE MODULE  ↗'
            btn.styles.background = color(self.app, 'syraline-accent-2')
            btn.styles.color = color(self.app, 'syraline-text')

class BootScreen(ModalScreen):
    BINDINGS=[Binding('enter','skip',show=False),Binding('escape','skip',show=False)]
    def compose(self):
        yield MatrixBoot(id='neon-canvas')
        yield Static('ENTRÉE  /  PASSER L’INTRODUCTION',id='boot-skip')
    def on_mount(self):self.done=False;self.app.localize(self)
    def action_skip(self):
        if not self.done:self.done=True;self.dismiss()

class AppearanceScreen(ModalScreen):
    def on_mount(self):self.app.localize(self)
    BINDINGS=[Binding('escape','close',show=False)]
    def compose(self):
        with Vertical(id='appearance-box'):
            yield Static('ATELIER / APPARENCE',classes='eyebrow')
            yield Static('Choisis ton atmosphère.',id='appearance-title')
            for key,(name,*_) in PALETTES.items():yield Button(('●  ' if self.app.active_theme==key else '○  ')+name,id='theme-'+key)
            yield Button('ANIMATIONS  /  '+('ACTIVES' if self.app.motion else 'PAUSE'),id='motion-toggle')
            yield Button('PROFIL / LANGUE / COULEUR',id='edit-profile')
            yield Button('REJOUER L’INTRODUCTION',id='replay-boot')
            yield Button('RETOUR  /  ÉCHAP',id='appearance-close')
    def on_button_pressed(self,event):
        key=event.button.id
        if key.startswith('theme-'):
            self.app.apply_theme(key[6:])
            for k,(name,*_) in PALETTES.items():self.query_one('#theme-'+k,Button).label=('●  ' if k==self.app.active_theme else '○  ')+name
        elif key=='motion-toggle':
            self.app.action_motion();event.button.label=self.app.tr('ANIMATIONS  /  '+('ACTIVES' if self.app.motion else 'PAUSE'))
        elif key=='edit-profile':self.dismiss();self.app.call_after_refresh(self.app.action_profile)
        elif key=='replay-boot':self.dismiss();self.app.call_after_refresh(self.app.action_intro)
        else:self.dismiss()
    def action_close(self):self.dismiss()

class SearchScreen(ModalScreen):
    BINDINGS=[Binding('escape','close',show=False),Binding('down','next',show=False),Binding('up','previous',show=False)]
    def compose(self):
        with Vertical(id='search-box'):
            yield Static('BARRE DE RECHERCHE  /  CTRL F',classes='eyebrow')
            yield Input(placeholder='Un outil, une idée…',id='search-input')
            yield ListView(id='search-results')
            yield Static('↑ ↓  NAVIGUER     ENTRÉE  OUVRIR     ÉCHAP  FERMER',classes='search-hint')
    async def on_mount(self):self.app.localize(self);self.seq=0;await self.populate('');self.query_one(Input).focus()
    async def populate(self,value):
        self.seq+=1;seq=self.seq;lv=self.query_one(ListView);await lv.clear()
        if seq!=self.seq:return
        for cat,num,name in self.app.catalog:
            if value.casefold() in (name+' '+self.app.descriptions[name]+' '+self.app.tr(self.app.descriptions[name])+' '+self.app.cat_labels[cat]+' '+cat).casefold():
                await lv.append(ListItem(Label(Text(f'{num}  {self.app.tr(self.app.short[name][0])}   {self.app.tr(self.app.cat_labels[cat])}')),name=cat+'|'+name))
        if lv.children:lv.index=0
    async def on_input_changed(self,event):
        if hasattr(self,'seq'):await self.populate(event.value)
    def on_input_submitted(self,event):self.choose()
    def on_list_view_selected(self,event):self.choose()
    def action_next(self):
        lv=self.query_one(ListView);lv.index=min(len(lv.children)-1,(lv.index or 0)+1) if lv.children else None
    def action_previous(self):
        lv=self.query_one(ListView);lv.index=max(0,(lv.index or 0)-1) if lv.children else None
    def choose(self):
        lv=self.query_one(ListView)
        if lv.index is not None and lv.children:
            cat,name=lv.children[lv.index].name.split('|',1);self.dismiss();self.app.open_tool(cat,name)
    def action_close(self):self.dismiss()

class ChangelogScreen(ModalScreen):
    BINDINGS = [Binding('escape', 'close', show=False), Binding('enter', 'close', show=False)]
    def __init__(self, vip=False):
        super().__init__()
        self.vip = vip
    def compose(self):
        tr = self.app.tr
        with Vertical(id='appearance-box'):
            yield Static(tr('SYRALINE / CHANGELOG'), classes='eyebrow')
            yield Static(tr('Nouveautés & Historique des versions'), id='appearance-title')
            yield Static(Text(tr('◆ Édition 2.4.1 — 78 outils standards · résultats structurés · copie · sélection de fichiers'), style='bold #ff3452'))
            content = VerticalScroll()
            content.styles.height = "auto"
            content.styles.max_height = 22
            content.styles.margin = (0, 0, 1, 0)
            with content:
                if self.vip:
                    yield Static(Text(tr("◆ SYRALINE VIP (Actif)"), style="bold #ffd700"))
                    yield Static(Text(tr("  • Mode VIP activé par clé de licence (KeyAuth)"), style="#ffffff"))
                    yield Static(Text(tr("  • Toutes les fonctionnalités premium débloquées"), style="#ffffff"))
                    yield Static(Text(tr("  • Catégories VIP : Web, OSINT, Fichiers, Discord, Roblox"), style="#ffffff"))
                    yield Static(Text(tr("  • Support multilingue 6 langues synchro (FR, EN, ES, DE, ZH, AR)"), style="#ffffff"))
                else:
                    yield Static(Text(tr("◆ SYRALINE v1.0.0 — Terminal Edition"), style="bold #ff3452"))
                    yield Static(Text(tr("  • Moteur TUI moderne Textual + Rich haute performance"), style="#ffffff"))
                    yield Static(Text(tr("  • Catalogue de modules (Réseau, Domaines, Utilitaires, Données)"), style="#ffffff"))
                    yield Static(Text(tr("  • Mode VIP débloquant les modules premium par clé de licence"), style="#ffffff"))
                    yield Static(Text(tr("  • Localisation intégrale en 6 langues avec bidi/reshaper"), style="#ffffff"))
                    yield Static(Text(tr("  • Personnalisation complète : thèmes, animations, profils"), style="#ffffff"))
            yield Button(tr('RETOUR  /  ÉCHAP'), id='changelog-close')
    def on_button_pressed(self, event):
        self.dismiss()
    def action_close(self):
        self.dismiss()

class CreditsScreen(ModalScreen):
    BINDINGS = [Binding('escape', 'close', show=False), Binding('enter', 'close', show=False)]
    def compose(self):
        tr = self.app.tr
        with Vertical(id='appearance-box'):
            yield Static(tr('SYRALINE / CRÉDITS'), classes='eyebrow')
            yield Static(tr('Informations & Équipe du projet'), id='appearance-title')
            content = VerticalScroll()
            content.styles.height = "auto"
            content.styles.max_height = 22
            content.styles.margin = (0, 0, 1, 0)
            with content:
                yield Static(Text("SYRALINE — TERMINAL EDITION", style="bold #ff3452"))
                yield Static(Text(tr("Architecture & Réalisation : l’équipe SyraLine"), style="#ffffff"))
                import platform, sys
                yield Static(Text("\n" + tr("Système :"), style="bold #ffacbb"))
                yield Static(Text(f"  • {platform.system()} {platform.release()} · Python {sys.version.split()[0]}", style="#ad8b95"))
                yield Static(Text("\n" + tr("Technologies utilisées :"), style="bold #ffacbb"))
                yield Static(Text("  • Python 3.12+, Textual, Rich, Requests, Pillow", style="#ad8b95"))
            yield Button(tr('RETOUR  /  ÉCHAP'), id='credits-close')
    def on_button_pressed(self, event):
        self.dismiss()
    def action_close(self):
        self.dismiss()

# Catégories réservées au VIP : débloquées par une clé de licence valide.
PREMIUM_CATEGORIES = {'Website', 'OSINT', 'Files & Media', 'Discord', 'Roblox'}

# Accueil repensé : on ouvre directement sur l'exploration du catalogue et la
# personnalisation ; la Zone VIP et les infos système passent en fin de liste.
HOME_TOOLS = [
    ('all', '01', 'Tous les modules'),
    ('all', '02', 'Profil & Thème'),
    ('all', '03', 'Changelog'),
    ('all', '04', 'Crédits & Système'),
    ('all', '05', 'Zone VIP'),
]

HOME_SHORT = {
    'Zone VIP': ('ESPACE VIP', 'Activer avec une clé de licence'),
    'Profil & Thème': ('PROFIL & APPARENCE', 'Personnaliser l’apparence'),
    'Changelog': ('NOUVEAUTÉS', 'Nouveautés SyraLine v1.0'),
    'Crédits & Système': ('À PROPOS', 'Informations & diagnostics'),
    'Tous les modules': ('TOUT LE CATALOGUE', 'Explorer tout le catalogue'),
}

HOME_DESCRIPTIONS = {
    'Zone VIP': 'Entre ta clé de licence pour activer le mode VIP et débloquer toutes les fonctionnalités premium de SyraLine.',
    'Profil & Thème': 'Configure ton pseudonyme, sélectionne ta langue (FR, EN, ES, DE, ZH, AR) et personnalise ta palette de couleurs.',
    'Changelog': 'Historique complet des mises à jour, correctifs et ajouts de SyraLine v1.0 Terminal Edition.',
    'Crédits & Système': 'Crédits officiels SyraLine. Informations système, environnement d’exécution et diagnostics.',
    'Tous les modules': 'Affiche l’intégralité des modules disponibles dans le catalogue sans filtrage.',
}

class ToolPresentation:
    BINDINGS=[Binding('f5','screen.run_analysis',show=False,priority=True)]
    def action_run_analysis(self):self.run_tool()
    COPY_RESULT=True
    _last_plain=""
    _last_structured=False
    _last_saved=None
    """Nouvel habillage ; le moteur d'exécution est hérité sans modification."""
    def compose(self):
        yield Topline(classes='tool-topline')
        with Vertical(id='tool-toolbar'):
            with Horizontal(id='title-row'):
                yield Button('← RETOUR',id='back-btn')
                yield Static(Text(self.app.short.get(self.TITLE_TOOL,(self.TITLE_TOOL.upper(),))[0],style='bold '+color(self.app,'syraline-accent')),id='screen-title')
            yield Static(Text(self.app.tr(self.app.descriptions.get(self.TITLE_TOOL,''))),id='tool-context')
            with Horizontal(id='input-row'):
                yield Input(placeholder=legacy.t(self.PLACEHOLDER,self.app.lang),id='tool-input')
                if not getattr(self, 'MULTILINE', False):
                    yield Button('EXÉCUTER  ↗',id='run-btn')
            if getattr(self, 'MULTILINE', False):
                yield TextArea(id='tool-multiline')
            if getattr(self, 'COPY_RESULT', False) or getattr(self, 'FILE_PICKER', False):
                with Horizontal(id='tool-actions'):
                    if getattr(self, 'MULTILINE', False):
                        yield Button('EXÉCUTER  ↗',id='run-btn')
                    if getattr(self, 'FILE_PICKER', False):
                        yield Button(self.app.tr('CHOISIR UN DOSSIER') if self.TITLE_TOOL in {'Local Secret Audit','Similar Image Finder','Duplicate File Finder'} else 'CHOISIR UN FICHIER', id='browse-file-btn')
                    if getattr(self, 'COPY_RESULT', False):
                        yield Button('COPIER LE RÉSULTAT', id='copy-result-btn', disabled=True)
                    yield Button('ENREGISTRER', id='save-result-btn', disabled=True)
        with VerticalScroll(id='result-scroll') as result:
            result.border_title=self.app.tr(' SORTIE / RÉSULTATS ')
            yield Static(Text('◇\n\n' + self.app.tr('PRÊT POUR VOTRE PROCHAINE EXPLORATION') + '\n\n' + legacy.t(self.PLACEHOLDER,self.app.lang)),id='tool-empty')
        yield Static(self.app.tr('ÉCHAP Retour · F5 Exécuter · ENTRÉE Nouvelle ligne') if getattr(self,'MULTILINE',False) else '  ÉCHAP  Retour au tableau de bord    /    ENTRÉE  Exécuter',classes='tool-footnote')
    def on_mount(self):
        self.app.localize(self)
        self.set_class(self.app.size.height<30,'compact-tool')
        self.query_one('#tool-input',Input).focus()
        if getattr(self, 'MULTILINE', False):
            self.query_one('#input-row').display = False
            self.query_one('#tool-multiline',TextArea).focus()
        if self.app.motion:self.styles.opacity=0.;self.styles.animate('opacity',1.,duration=.18)
    def on_button_pressed(self,event):
        if event.button.id == 'save-result-btn':
            self.save_output()
        elif event.button.id == 'copy-result-btn':
            if self._last_plain:
                self.app.copy_to_clipboard(self._last_plain)
                self.app.notify(self.app.tr('Résultat envoyé au presse-papiers du terminal.'))
        else:super().on_button_pressed(event)
    def save_output(self):
        if not self._last_plain:return
        try:
            self._last_saved=save_result(self.TITLE_TOOL,self._last_plain,structured=self._last_structured)
            if self.TITLE_TOOL == 'QR Code':
                import qrcode
                with self._last_saved.with_suffix('.png').open('xb') as stream:
                    qrcode.make(self.query_one('#tool-input',Input).value).save(stream,format='PNG')
            self.app.notify(f'Output : {self._last_saved}')
        except OSError as exc:
            self.app.notify(f'Export impossible : {exc}',severity='warning')

    def run_tool(self):
        self._last_structured=False
        self._last_saved=None
        if self.query('#save-result-btn'):self.query_one('#save-result-btn',Button).disabled=True
        self._started_at=time.monotonic()
        self._last_plain=''
        if self.query('#copy-result-btn'):self.query_one('#copy-result-btn',Button).disabled=True
        if self.query('#run-btn'):self.query_one('#run-btn',Button).disabled=True
        super().run_tool()
    def _finish(self,spinner,scroll,output,ok):
        if not self.is_mounted:return
        if isinstance(output,str) and output.startswith(('[red]','[yellow]')):ok=False
        from rich.console import Console
        from rich.panel import Panel
        import io
        if not ok:
            message=str(output).replace('[bold red]','').replace('[/bold red]','').replace('[red]','').replace('[/red]','').replace('[yellow]','').replace('[/yellow]','')
            output=Panel(Text(message),title='ERREUR / ERROR',border_style='red',padding=(1,1))
        if ok and not self._last_plain:
            stream=io.StringIO();console=Console(file=stream,width=100,color_system=None)
            console.print(output);self._last_plain=stream.getvalue()
        if ok and self._last_plain:
            self.save_output()
        if self.query('#save-result-btn'):self.query_one('#save-result-btn',Button).disabled=not ok or not self._last_plain
        elapsed=time.monotonic()-getattr(self,'_started_at',time.monotonic())
        scroll.border_subtitle=f"{'✓ OK' if ok else '× ERROR'}  ·  {elapsed:.2f} s"
        super()._finish(spinner,scroll,output,ok)
        if self.query('#run-btn'):self.query_one('#run-btn',Button).disabled=False
        if self.query('#copy-result-btn'):self.query_one('#copy-result-btn',Button).disabled=not ok or not self._last_plain
    def on_resize(self,event):
        self.set_class(event.size.height<30,'compact-tool')

SCREEN_CLASSES={(cat,name):type('Styled'+cls.__name__,(ToolPresentation,cls),{}) for (cat,name),cls in legacy.TOOL_SCREENS.items() if name not in RETIRED_TOOLS}

def make_extra_screen(tool):
    class IntegratedTool(ToolPresentation,legacy.ToolScreen):
        BINDINGS=[Binding('f5','screen.run_analysis',show=False,priority=True)]
        TITLE_TOOL=tool.name
        PLACEHOLDER=tool.hint
        MULTILINE=tool.name in {'CSV to JSON','JSON to CSV','XML Format','Line Deduplicator','Line Sorter','JSON Pointer','JSON Diff','TOML to JSON','Text Diff','Email Header Analyzer'}
        FILE_PICKER=tool.name in {'EXIF Forensic','Image Info','File SHA256','ZIP Inspector','File Details','Encoding Detector','File Hexdump','File Entropy','PDF Inspector','QR Barcode Reader','Local Secret Audit','Similar Image Finder','Duplicate File Finder','File Compare','Email Header Analyzer'}
        COPY_RESULT=True
        _last_plain=''
        def on_button_pressed(self,event):
            if event.button.id == 'browse-file-btn':
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root=tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost',True)
                    try:
                        selected=(filedialog.askdirectory(title=self.TITLE_TOOL,initialdir=str(INPUT_DIR)) if self.TITLE_TOOL in {'Local Secret Audit','Similar Image Finder','Duplicate File Finder'} else filedialog.askopenfilenames(title=self.TITLE_TOOL,initialdir=str(INPUT_DIR)) if self.TITLE_TOOL == 'File Compare' else filedialog.askopenfilename(title=self.TITLE_TOOL,initialdir=str(INPUT_DIR)))
                    finally:
                        root.destroy()
                    if selected:
                        if self.TITLE_TOOL == 'File Compare':
                            if len(selected)!=2:raise ValueError('Sélectionnez exactement deux fichiers')
                            selected=' | '.join(selected)
                        if self.MULTILINE:self.query_one('#tool-multiline',TextArea).load_text(selected)
                        else:self.query_one('#tool-input',Input).value=selected
                except Exception as exc:
                    self.app.notify(f'Sélecteur indisponible : {exc}',severity='warning')
            elif event.button.id == 'copy-result-btn':
                if self._last_plain:
                    self.app.copy_to_clipboard(self._last_plain)
                    self.app.notify(self.app.tr('Résultat envoyé au presse-papiers du terminal.'))
            else:super().on_button_pressed(event)
        def run_tool(self):
            self._last_plain=''
            self.query_one('#copy-result-btn',Button).disabled=True
            if self.MULTILINE:
                self.query_one('#tool-input',Input).value=self.query_one('#tool-multiline',TextArea).text
            super().run_tool()
        def _finish(self,spinner,scroll,output,ok):
            if not self.is_mounted:return
            super()._finish(spinner,scroll,output,ok)
            self.query_one('#copy-result-btn',Button).disabled=not ok or not self._last_plain
        def execute(self,value):
            from .result_view import render_result
            output=tool.run(value)
            self._last_structured=isinstance(output,(dict,list))
            self._last_plain=output if isinstance(output,str) else json.dumps(output,indent=2,ensure_ascii=False,default=str)
            return render_result(output,self.TITLE_TOOL,color(self.app,'syraline-accent'),self.app.tr)
    IntegratedTool.__name__='Integrated'+tool.name.replace(' ','')
    return IntegratedTool

for tool in EXTRA_TOOLS:SCREEN_CLASSES[tool.category,tool.name]=make_extra_screen(tool)


class SyraLineApp(App):
    TITLE='SYRALINE / TERMINAL EDITION'
    SUB_TITLE='Violet'
    CSS=legacy.SyraLineApp.CSS+'\n'+(STYLES_DIR/'compact.tcss').read_text(encoding='utf-8')
    CSS_PATH=None
    BINDINGS=[Binding('ctrl+f','search','Recherche'),Binding('f4','appearance','Apparence'),Binding('f7','motion','Animations'),Binding('f1','intro','Introduction'),Binding('ctrl+c','quit','Quitter'),Binding('escape','home','Accueil'),Binding('pagedown','page(1)',show=False),Binding('pageup','page(-1)',show=False),Binding('1','category(0)',show=False),Binding('2','category(1)',show=False),Binding('3','category(2)',show=False),Binding('4','category(3)',show=False)]
    BINDINGS += [Binding(str(i+1) if i<9 else '0',f'category({i})',show=False) for i in range(4,min(10,len(CATEGORIES)+1))]
    def __init__(self,boot=True,profile_path=None,initial_tool=None,language=None,welcome_links=False):
        self.vip_pack=None
        self.catalog=list(HOME_TOOLS)+list(TOOLS);self.categories=list(CATEGORIES);self.cat_labels=dict(CAT_LABELS);self.cat_labels['all']='HOME';self.short=dict(SHORT);self.short.update(HOME_SHORT);self.descriptions=dict(legacy.TOOL_DESCRIPTIONS);self.descriptions.update(HOME_DESCRIPTIONS);self.tool_screens=dict(SCREEN_CLASSES)
        # VIP = débloquer les catégories premium. Pas de pack externe à charger.
        self.premium_tools={name for cat,num,name in TOOLS if cat in PREMIUM_CATEGORIES}
        self.active_theme='violet';self.motion=True;self.boot=boot;self.lang='en';self.config=dict(legacy.DEFAULT_CONFIG,configured=True,sound=False,language='en');self.category='all';self.selected=self.catalog[0];self.columns=2;self.start=time.monotonic()
        try:
            cfg=json.loads((ROOT/'config'/'appearance.json').read_text(encoding='utf-8'))
            if cfg.get('theme') in PALETTES:self.active_theme=cfg['theme']
            self.motion=cfg.get('motion',True) is True
        except (OSError,ValueError,AttributeError):pass
        self.profile_path=Path(profile_path) if profile_path else PROFILE_PATH
        self.welcome_links=welcome_links
        # Réactive le VIP si une clé de licence valide est déjà mémorisée.
        try:
            from .license_state import load_state, within_grace, key_expired, clear_state, same_machine
            _st=load_state()
            if _st.get('key') and key_expired(_st):
                clear_state()  # clé expirée : on la retire pour de bon
            elif _st.get('key') and within_grace(_st) and same_machine(_st):
                self.vip_pack={'name':'SYRALINE VIP'}
        except Exception:
            pass
        self.profile=read_profile(self.profile_path);self.username='Invité';self.accent=''
        self.load_preferences()
        self.rainbow_accent='#ff506a';self.rainbow_tick=0.
        self.initial_tool=initial_tool
        if language in LANGUAGES:self.lang=language;self.config['language']=language
        self.page=0;self.page_size=9;self.page_count=1
        super().__init__()
    def get_css_variables(self):
        variables=super().get_css_variables();variables.update(legacy.THEMES[self.active_theme])
        if self.active_theme=='rainbow' and not self.accent:
            variables['syraline-accent']=self.rainbow_accent;variables['syraline-accent-2']=blend(self.rainbow_accent,'#100d13',.32)
        if self.accent:
            variables['syraline-accent']=self.accent;variables['syraline-accent-2']=blend(self.accent,'#100d13',.32)
        return variables
    def compose(self):
        yield Topline(id='topline')
        with Horizontal(id='hero'):
            # Une seule rangée : VIP (gauche) · TITRE centré · profil (droite).
            yield VipZoneButton('VIP ZONE',id='secret-entry',tooltip=self.tr('ZONE VIP'))
            yield CompactSignature(id='dashboard-brand')
            with Vertical(id='hero-right'):
                with Horizontal(id='profile-identity-row'):
                    yield Static(Text(self.username),id='palette-label')
                    yield Button(self.tr('PROFIL  ↗'),id='edit-header-profile')
                yield Static('',id='signature')
                yield Button('DISCORD  ↗',id='community-tagline',classes='community-link')
            yield SignatureRail(id='signature-rail')
        with Horizontal(id='navbar'):
            with NavCats(id='navbar-cats'):
                for idx,key in enumerate(['all']+self.categories):
                    if idx==0:
                        # Le bouton HOME de la barre devient « Back home ».
                        yield Button('«  BACK HOME',id='cat-0',classes='nav-button nav-back chosen')
                    else:
                        cls='nav-button'+(' vip-cat' if key in PREMIUM_CATEGORIES else '')
                        yield Button(f'{idx:02}  '+self.cat_labels.get(key,key.upper()),id=f'cat-{idx}',classes=cls)
            yield Button('← STD',id='exit-vip',classes='nav-button nav-aux',disabled=True)
            yield Button('⌕',id='open-search',classes='nav-button nav-aux')
            yield Button('◐',id='open-appearance',classes='nav-button nav-aux')
            yield Static('',id='sidebar-end')
        with Horizontal(id='workspace'):
            with Vertical(id='catalog'):
                with Horizontal(id='catalog-heading'):
                    yield Static('01 / COLLECTION',id='collection-title')
                    yield Static(f'{len(self.catalog)} MODULES',id='collection-count')
                yield Static('Molette pour explorer · Entrée pour ouvrir',id='collection-subtitle')
                with VerticalScroll(id='cards-scroll'):
                    with Grid(id='cards'):
                        for index,(cat,num,name) in enumerate(self.catalog):yield ModuleCard(cat,num,name,index)
                yield Static('↕  MOLETTE / DÉFILEMENT CONTINU',id='scroll-hint')
                # Visible seulement sur le Home : accès centré à la page catalogue.
                with Horizontal(id='access-row'):
                    yield Button('ACCÉDER À SYRALINE  ↗',id='access-syraline')
            yield Inspector(id='inspector')
        yield Static('',id='footer')
    def on_mount(self):
        self.query_one('#exit-vip').display=False
        if self.welcome_links:
            from .first_launch import open_welcome_links_once
            self.call_after_refresh(open_welcome_links_once, self.profile_path)
        self.screen.add_class('dashboard');self.screen.add_class('home-view');self.resize_layout(self.size.width,self.size.height);self.set_interval(1,self.update_footer);self.update_footer()
        self.set_interval(5,self.check_key_expiry)
        self.query_one(ModuleCard).focus()
        self.localize(self.screen)
        self.set_interval(1/30,self.motion_frame)
        if self.initial_tool:
            self.call_after_refresh(self.open_tool,*self.initial_tool)
        elif self.boot:
            if self.motion:self.push_screen(BootScreen(),lambda _:self.first_run())
            else:self.first_run()
    def on_resize(self,event):
        if self.is_mounted:self.resize_layout(event.size.width,event.size.height)
    def resize_layout(self,width,height):
        dashboard=self.screen_stack[0]
        dashboard.set_class(width<155,'narrow');dashboard.set_class(width<100,'compact');dashboard.set_class(height<34,'short');dashboard.set_class(height<27,'tiny')
        # Plus de barre latérale : seules les marges et l'inspecteur réduisent la largeur.
        available=width-8-(27 if width>=155 else 0)
        self.columns=max(1,min(5,available//29))
        cards=self.query('#cards')
        if cards:
            cards.first().styles.grid_size_columns=self.columns
            self.paginate()

    def paginate(self):
        if self.category=='all':
            cards=[c for c in self.query(ModuleCard) if c.cat=='all']
        elif self.category=='_full_collection':
            cards=[c for c in self.query(ModuleCard) if c.cat!='all']
        else:
            cards=[c for c in self.query(ModuleCard) if c.cat==self.category]
        visible=cards
        for card in self.query(ModuleCard):card.display=card in visible;card.refresh()
        return visible

    def action_page(self,delta):
        if len(self.screen_stack)>1:return
        scroll=self.query_one('#cards-scroll')
        scroll.scroll_relative(y=delta*max(1,scroll.size.height-2),animate=self.motion)
    def check_key_expiry(self):
        """Désactive automatiquement le VIP dès que la clé expire, même app ouverte."""
        if not self.vip_pack:return
        try:
            from .license_state import load_state, key_expired, clear_state
            if key_expired(load_state()):
                clear_state();self.set_vip(False)
                self.notify(self.tr('Clé expirée. Accès VIP désactivé.'),severity='warning')
        except Exception:
            pass
    def update_footer(self):
        if not self.query('#footer'):return
        elapsed=int(time.monotonic()-self.start);a=color(self,'syraline-accent');d=color(self,'syraline-text-dim')
        text=Text('  CTRL F ',style=a);text.append(self.tr('recherche')+'   ',style=d);text.append('F4 ',style=a);text.append(self.tr('apparence')+'   ',style=d);text.append('F7 ',style=a);text.append(self.tr('mouvement')+'   ',style=d);text.append('CTRL C ',style=a);text.append(self.tr('quitter'),style=d)
        if self.size.width<100:
            text=Text(' Ctrl F ',style=a);text.append(self.tr('recherche')+'  ',style=d);text.append('F4 ',style=a);text.append(self.tr('apparence')+'  ',style=d);text.append('Ctrl C ',style=a);text.append(self.tr('quitter'),style=d)
        tail=('◆ VIP ON  /  ' if self.vip_pack else '')+f'{elapsed//60:02}:{elapsed%60:02}  /  '+('LIVE' if self.motion else 'PAUSE')+'  '
        text.append(' '*max(2,self.size.width-len(text.plain)-len(tail)));text.append(tail,style=d);self.query_one('#footer',Static).update(text)
    def on_module_card_picked(self,message):
        if (message.card.cat,message.card.num,message.card.tool_name) not in self.catalog:return
        self.selected=(message.card.cat,message.card.num,message.card.tool_name)
        self.screen_stack[0].query_one(Inspector).select(message.card)
    def move_card(self,card,delta):
        cards=self.paginate()
        if card in cards:
            index=max(0,min(len(cards)-1,cards.index(card)+delta));cards[index].focus()
    async def on_button_pressed(self,event):
        bid=event.button.id or ''
        if bid=='access-syraline':self.action_category(1)
        elif bid.startswith('cat-'):self.action_category(int(bid[4:]))
        elif bid=='open-search':self.action_search()
        elif bid=='open-appearance':self.action_appearance()
        elif bid=='edit-header-profile':self.action_profile()
        elif bid=='secret-entry':await self.action_secret()
        elif bid=='exit-vip':self.set_vip(False)
        elif bid=='community-tagline':
            try:webbrowser.open(DISCORD_URL)
            except Exception:self.notify('Impossible d’ouvrir Discord.',severity='warning')
        elif bid=='detail-open':self.open_tool(self.selected[0],self.selected[2])
    def action_category(self,index):
        if len(self.screen_stack)>1:return
        if not 0<=index<=len(self.categories):return
        key=(['all']+self.categories)[index];self.category=key
        # 'all' = page Home (titre centré, pas de barre de catégories) ;
        # une vraie catégorie = page catalogue (barre visible).
        self.screen_stack[0].set_class(key=='all','home-view')
        for idx in range(len(self.categories)+1):self.query_one(f'#cat-{idx}').set_class(idx==index,'chosen')
        self.page=0;visible=self.paginate()
        if key=='all':
            title_tag=f'{index+1:02} / '+self.tr('HOME VIP' if self.vip_pack else 'HOME')
            self.query_one('#collection-title',Static).update(title_tag)
            self.query_one('#collection-count',Static).update(self.tr(f'{len(visible):02} OPTIONS'))
            self.query_one('#collection-subtitle',Static).update(Text(self.tr('SYRALINE · HOME HUB')))
        else:
            self.query_one('#collection-title',Static).update(f'{index+1:02} / '+self.tr(self.cat_labels.get(key,key.upper())))
            count=sum(1 for c in self.query(ModuleCard) if c.cat==key)
            self.query_one('#collection-count',Static).update(self.tr(f'{count:02} MODULES'))
            self.query_one('#collection-subtitle',Static).update(Text(self.tr('Molette pour explorer · Entrée pour ouvrir')))
        self.query_one('#cards-scroll').scroll_home(animate=False)
        if visible:visible[0].focus()
        now=time.monotonic()
        for i,card in enumerate(visible):card.reveal_at=now+min(i,8)*.018 if self.motion else None
        self.motion_frame()

    def open_home_tool(self,name):
        if name in ('Zone VIP', 'VIP Zone'):
            self.call_after_refresh(self.action_secret)
        elif name in ('Mode Standard',):
            self.set_vip(False)
        elif name in ('Profil & Thème', 'Configuration Profil'):
            self.action_profile()
        elif 'Changelog' in name:
            self.push_screen(ChangelogScreen(vip=bool(self.vip_pack)))
        elif 'Crédits' in name:
            self.push_screen(CreditsScreen())
        elif 'Tous les modules' in name:
            self.action_all_collection()

    def action_all_collection(self):
        self.category = '_full_collection'
        self.screen_stack[0].set_class(False,'home-view')
        for idx in range(len(self.categories)+1):
            self.query_one(f'#cat-{idx}').remove_class('chosen')
        visible = self.paginate()
        self.query_one('#collection-title', Static).update(self.tr('COLLECTION COMPLÈTE'))
        self.query_one('#collection-count', Static).update(self.tr(f'{len(visible):02} MODULES'))
        self.query_one('#collection-subtitle', Static).update(Text(self.tr('Tous les modules sans filtre de catégorie')))
        self.query_one('#cards-scroll').scroll_home(animate=False)
        if visible: visible[0].focus()

    def open_tool(self,cat,name):
        if cat == 'all':
            self.open_home_tool(name)
            return
        # Module premium verrouillé : demander la clé de licence (mode VIP).
        if name in self.premium_tools and not self.vip_pack:
            self.push_screen(DarkAccess(), self.secret_unlocked)
            return
        handler=self.tool_screens.get((cat,name))
        if not handler:return
        from textual.screen import Screen
        if isinstance(handler,type) and issubclass(handler,Screen):
            self.push_screen(handler())
        elif callable(handler):
            try:
                res=handler()
            except Exception as e:
                self.notify(f"Erreur lancement: {e}", severity="error")
                return
            if isinstance(res,Screen):
                self.push_screen(res)
    def action_search(self):
        if len(self.screen_stack)==1:self.push_screen(SearchScreen())
    async def action_secret(self):
        if len(self.screen_stack)!=1:return
        if self.vip_pack:
            # Déjà VIP : revenir à l'affichage standard (la clé reste mémorisée).
            self.set_vip(False)
            self.notify(self.tr('Mode standard rétabli.'),severity='information')
            return
        # Clé valide déjà mémorisée : réactiver le VIP sans redemander la clé.
        # Mais une clé EXPIRÉE est retirée : on redemande une clé valide.
        try:
            from .license_state import load_state, within_grace, key_expired, clear_state, same_machine
            st=load_state()
            if st.get('key') and key_expired(st):
                clear_state()
            elif st.get('key') and within_grace(st) and same_machine(st):
                self.set_vip(True)
                self.push_screen(VipArrival(), lambda _: self._after_vip_arrival())
                return
        except Exception:
            pass
        self.push_screen(DarkAccess(), self.secret_unlocked)
    def secret_unlocked(self,confirmed):
        # DarkAccess a déjà validé et mémorisé la clé via license.activate().
        if confirmed:
            self.set_vip(True)
            # ACCESS GRANTED, puis rechargement pour charger les outils VIP du pack.
            self.push_screen(VipArrival(), lambda _: self._after_vip_arrival())
    def _after_vip_arrival(self):
        # Les outils VIP ne se chargent qu'au démarrage : si le catalogue ne les a
        # pas encore (première activation dans cette session), on relance l'app.
        if not any(cat in PREMIUM_CATEGORIES for cat, _, _ in self.catalog):
            self._needs_reload = True
            self.exit()
    def set_vip(self,active):
        """Affiche/masque le mode VIP. La clé mémorisée n'est pas effacée ici :
        revenir au mode standard garde la licence, Zone VIP la réactive aussitôt."""
        self.vip_pack={'name':'SYRALINE VIP'} if active else None
        dashboard=self.screen_stack[0]
        dashboard.set_class(active,'vip-active')
        self.refresh_css()
        back=self.query_one('#exit-vip',Button);back._source_label='← MODE STANDARD';back.label=self.tr('← MODE STANDARD');back.display=active;back.disabled=not active
        self.query_one('#sidebar-end',Static).update('SYRALINE\n'+('VIP ZONE' if active else 'TERMINAL EDITION'))
        portal=self.query_one('#secret-entry',Button)
        portal.tooltip=self.tr('VIP ACTIF · toutes les features débloquées') if active else self.tr('ZONE VIP')
        portal.refresh();self.query_one('#signature-rail').refresh()
        for card in self.query(ModuleCard):card.refresh()
        if self.query(Inspector) and self.query(ModuleCard):
            self.query_one(Inspector).select(self.query_one(ModuleCard))
        self.update_footer()

    def action_appearance(self):
        if len(self.screen_stack)==1:self.push_screen(AppearanceScreen())
    def action_intro(self):
        if len(self.screen_stack)==1:self.push_screen(BootScreen())
    def action_home(self):
        if len(self.screen_stack)==1:self.action_category(0)
    def motion_frame(self):
        now=time.monotonic()
        if self.active_theme=='rainbow' and self.motion and not self.accent and now-self.rainbow_tick>.35:
            self.rainbow_tick=now
            self.rainbow_accent='#'+''.join(f'{round(c*255):02x}' for c in colorsys.hsv_to_rgb(((now-self.start)/16)%1,.62,1.))
            self.refresh_css()
        if len(self.screen_stack)!=1:return
        for card in self.query(ModuleCard):
            if card.display:card.motion_frame(now,self.motion)
    def action_motion(self):
        self.motion=not self.motion;self.save_appearance();self.update_footer();self.motion_frame()
        for widget in self.query('CompactSignature, SignatureRail'):widget.refresh()
    def apply_theme(self,key):
        self.active_theme=key;self.accent='';self.refresh_css();self.save_appearance();self.query_one('#signature',Static).update('')
        for widget in self.query(Static):widget.refresh()
    def save_appearance(self):
        if self.profile:
            self.profile.update(theme=self.active_theme,motion=self.motion,accent=self.accent)
            try:write_profile(self.profile_path,self.profile)
            except OSError:self.notify(self.tr('Sauvegarde impossible.'),severity='warning')
            return
        try:write_profile(self.profile_path,{'theme':self.active_theme,'motion':self.motion,'accent':self.accent,'language':self.lang})
        except OSError:self.notify('Impossible de sauvegarder l’apparence.',severity='warning')

    def tr(self,text):return translate(text,self.lang)
    def load_preferences(self):
        if self.profile:
            self.username=self.profile['username'];self.lang=self.profile['language']
            self.active_theme=self.profile['theme'];self.accent=self.profile.get('accent','')
            self.motion=self.profile.get('motion',True) is True
            self.config.update(language=self.lang,username=self.username)
    def first_run(self):
        if not self.profile:self.push_screen(ProfileScreen(first=True))
    def action_profile(self):
        if len(self.screen_stack)==1:self.push_screen(ProfileScreen())
    def profile_updated(self):
        self.refresh_css()
        self.query_one('#palette-label',Static).update(Text(self.username))
        self.localize(self.screen_stack[0])
        self.action_category((['all']+self.categories).index(self.category))
        for widget in self.query(Static):widget.refresh()
        self.update_footer()
    def localize(self,root,language=None):
        tr=lambda text:translate(text,language or self.lang)
        for widget in root.query('Static, Button, Input'):
            if isinstance(widget,ModuleCard):
                widget.tooltip=tr(self.descriptions[widget.tool_name]);widget.refresh()
            elif isinstance(widget,Button):
                if widget.id=='secret-entry':widget.tooltip=tr('ZONE VIP')
                source=getattr(widget,'_source_label',str(widget.label));widget._source_label=source
                widget.label=tr(source)
            elif isinstance(widget,Input):
                source=getattr(widget,'_source_placeholder',widget.placeholder);widget._source_placeholder=source;widget.placeholder=tr(source)
            elif type(widget) is Static and widget.id not in ('palette-label','footer'):
                source=getattr(widget,'_source_text',widget.content)
                if isinstance(source,Text):source=source.plain
                if isinstance(source,str):widget._source_text=source;widget.update(tr(source))
