"""Complete menu registry shared by the dashboard and per-tool launchers."""
import re
import unicodedata
from .tools import legacy
from .localization import EN
from tools.core import TOOLS as EXTRA_TOOLS
from tools.catalog_policy import RETIRED_TOOLS

CATEGORIES=[category for category in legacy.MENU if category!='Settings']
CAT_LABELS={'all':'HOME','IP & Network':'RÉSEAU & IP','Domains & Infrastructure':'DOMAINES & DNS','Utilities':'BOÎTE À OUTILS'}
CAT_ICONS={'all':'◈','IP & Network':'◎','Domains & Infrastructure':'◇','Utilities':'⌘'}
SHORT={
 'Web Lookup':('WEB LOOKUP','DNS, HTTP et réseau'),
 'IP Localisation':('IP LOCALISATION','Coordonnées & région'),
 'IP Opérateur':('IP OPÉRATEUR','FAI & infrastructure'),
 'Open Ports':('OPEN PORTS','Services TCP accessibles'),
 'IP Pinger':('IP PINGER','Connectivité & latence'),
 'IP Generator':('IP GENERATOR','Adresses IPv4 aléatoires'),
 'WHOIS Lookup':('WHOIS LOOKUP','Identité du domaine'),
 'DNS Records':('DNS RECORDS','Cartographie des enregistrements'),
 'Subdomain Finder':('SUBDOMAIN FINDER','Explorer les sous-domaines'),
 'SSL Certificate Info':('SSL CERTIFICATE','Certificats & expiration'),
 'Hash Tools':('HASH TOOLS','Empreintes & intégrité'),
 'Password Generator':('PASSWORD GENERATOR','Aléatoire cryptographique'),
 'QR Code':('QR CODE','Texte vers code matriciel'),
 'Text Encoder':('TEXT ENCODER','URL · HTML · ROT13 · HEX'),
 'Base64 Tools':('BASE64 TOOLS','Encodage & décodage'),
}
CAT_ART={'IP & Network':'NETWORK','Domains & Infrastructure':'DOMAIN','Utilities':'UTILITY'}
TOOLS=[(cat,num,name) for cat in CATEGORIES for num,name in legacy.MENU[cat] if name not in RETIRED_TOOLS]
CAT_LABELS.update({'Website':'WEB & SITES','OSINT':'OSINT & RECHERCHE','Files & Media':'FICHIERS & MÉDIAS','Data & Encoding':'DONNÉES & FORMATS','Discord':'DISCORD','Roblox':'ROBLOX'})
EN.update({'RÉSEAU & IP':'NETWORK & IP','DOMAINES & DNS':'DOMAINS & DNS','BOÎTE À OUTILS':'TOOLBOX','WEB & SITES':'WEB & SITES','OSINT & RECHERCHE':'OSINT & RESEARCH','FICHIERS & MÉDIAS':'FILES & MEDIA','DONNÉES & FORMATS':'DATA & FORMATS'})
for tool in EXTRA_TOOLS:
    if tool.category not in CATEGORIES:CATEGORIES.append(tool.category)
    number=1+sum(1 for category,_,_ in TOOLS if category==tool.category)
    TOOLS.append((tool.category,f'{number:02}',tool.name))
    SHORT[tool.name]=(tool.name.upper(),tool.fr)
    legacy.TOOL_DESCRIPTIONS[tool.name]=tool.fr
    EN[tool.fr]=tool.en

# Renommage LÉGER du titre AFFICHÉ de chaque outil (la clé interne `name` ne
# change pas : identifiants, écrans et logique restent intacts). Seul l'intitulé
# montré à l'utilisateur change, tout en restant explicite. Le sous-titre
# (description, déjà traduit) est conservé.
TOOL_RENAMES={
    'Web Lookup':'WEB RECON','IP Localisation':'IP GEO','IP Opérateur':'IP CARRIER',
    'Open Ports':'PORT SCAN','IP Pinger':'PING TEST','IP Generator':'RANDOM IP',
    'IP Inspector':'IP PROFILE','Subnet Calculator':'SUBNET CALC','Reverse DNS':'RDNS LOOKUP',
    'CIDR Overlap':'CIDR CHECK','IPv6 Expander':'IPv6 EXPAND',
    'WHOIS Lookup':'WHOIS INFO','DNS Records':'DNS LOOKUP','Subdomain Finder':'SUBDOMAIN SCAN',
    'SSL Certificate Info':'SSL CERT','Domain RDAP':'RDAP INFO','Email Domain Audit':'EMAIL DNS AUDIT',
    'Hash Tools':'HASH & SUMS','Password Generator':'PASSWORD MAKER','QR Code':'QR MAKER',
    'Text Encoder':'TEXT ENCODE','Base64 Tools':'BASE64 KIT','UUID Generator':'UUID MAKER',
    'Timestamp':'TIME CONVERT','Color Converter':'COLOR CONVERT','Calculator':'QUICK CALC',
    'Line Deduplicator':'DEDUPE LINES','Line Sorter':'SORT LINES','Number Statistics':'NUMBER STATS',
    'Random Token':'TOKEN MAKER','Slug Generator':'SLUG MAKER','Text Case Converter':'TEXT CASE',
    'Text Diff':'TEXT COMPARE','Tracking URL Cleaner':'URL CLEANER','URL Defang':'URL DEFANG',
    'URL Refang':'URL REFANG','Unicode Inspector':'UNICODE PEEK',
    'Website Info':'SITE INFO','URL Scanner':'URL SCAN','HTTP Headers':'HTTP HEADERS',
    'Robots Reader':'ROBOTS.TXT','Sitemap Reader':'SITEMAP','URL Inspector':'URL PROFILE',
    'HTTP Response':'HTTP RESPONSE',
    'Email Info':'EMAIL RECON','GitHub Repository':'GITHUB REPO','GitHub User':'GITHUB PROFILE',
    'Phone Number Inspector':'PHONE RECON','Public Username Search':'USERNAME SEARCH',
    'Email Header Analyzer':'EMAIL HEADERS',
    'EXIF Forensic':'EXIF DATA','Image Info':'IMAGE INFO','File SHA256':'FILE HASH',
    'ZIP Inspector':'ZIP PEEK','File Details':'FILE INFO','File Compare':'FILE COMPARE',
    'Encoding Detector':'ENCODING DETECT','File Hexdump':'HEX DUMP','File Entropy':'FILE ENTROPY',
    'Local Secret Audit':'SECRET SCAN','PDF Inspector':'PDF PEEK','QR Barcode Reader':'QR READER',
    'Similar Image Finder':'SIMILAR IMAGES','Duplicate File Finder':'DUPLICATE FINDER',
    'JSON Format':'JSON PRETTY','JSON Minify':'JSON MINIFY','JWT Inspector':'JWT DECODE',
    'URL Decode':'URL DECODE','Hex Encode':'HEX ENCODE','Hex Decode':'HEX DECODE',
    'Text Statistics':'TEXT STATS','JSON Pointer':'JSON QUERY','TOML to JSON':'TOML → JSON',
    'CSV to JSON':'CSV → JSON','JSON to CSV':'JSON → CSV','JSON Diff':'JSON COMPARE',
    'XML Format':'XML PRETTY','HTML Escape':'HTML ESCAPE','HTML Unescape':'HTML UNESCAPE',
    'Base64 URL Encode':'BASE64URL','URL Encode':'URL ENCODE','Base32 Encode':'BASE32 ENCODE',
    'Base32 Decode':'BASE32 DECODE','Gzip Encode':'GZIP ENCODE','Gzip Decode':'GZIP DECODE',
    'Number Base Converter':'BASE CONVERT',
    'Invite Resolver':'INVITE INFO','Snowflake Decoder':'SNOWFLAKE DECODE',
    'Username Lookup':'USER LOOKUP','Account Age':'ACCOUNT AGE','Friends Count':'FRIENDS COUNT',
    'Followers Count':'FOLLOWERS','Following Count':'FOLLOWING','Group Lookup':'GROUP INFO',
    'Game Lookup':'GAME INFO','Place to Universe':'PLACE → UNIVERSE','Avatar Info':'AVATAR INFO',
}
for _tool_name,_new_title in TOOL_RENAMES.items():
    if _tool_name in SHORT:
        SHORT[_tool_name]=(_new_title,SHORT[_tool_name][1])


# Nouvelle disposition de l'UX : l'ordre des catégories est complètement repensé.
# Les utilitaires et le travail sur les données arrivent en premier, tandis que
# les diagnostics réseau / domaines (les plus techniques) sont renvoyés à la fin.
# Toutes les catégories restent présentes ; seul leur ordre d'affichage change.
# Les catégories en accès libre d'abord, puis les catégories VIP (premium)
# toutes regroupées à la fin de la liste de navigation.
DISPLAY_ORDER=[
    'Data & Encoding','IP & Network','Domains & Infrastructure','Utilities',  # accès libre
    'Website','OSINT','Files & Media','Discord','Roblox',                     # VIP (fin de liste)
]
_category_rank={name:index for index,name in enumerate(DISPLAY_ORDER)}
_rank=lambda name:_category_rank.get(name,len(DISPLAY_ORDER))
CATEGORIES.sort(key=_rank)
TOOLS.sort(key=lambda entry:_rank(entry[0]))  # tri stable : l'ordre interne des outils est conservé


def tool_slug(name):
    return re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower()).strip('-')

TOOL_IDS={tool_slug(name):(cat,name) for cat,_,name in TOOLS}
if len(TOOL_IDS)!=len(TOOLS):raise RuntimeError('Duplicate tool IDs')
