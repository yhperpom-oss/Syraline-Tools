"""Read-only public lookups and local utilities, integrated into the SyraLine UI.
No credentials, external scripts, shell commands or automatic file writes.
"""
from lib.constants import resolve_input_path
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit, urljoin, parse_qsl, quote, unquote
from html.parser import HTMLParser
import base64, hashlib, ipaddress, json, re, socket, uuid, zipfile
import requests
import dns.resolver
from PIL import Image, ExifTags

@dataclass(frozen=True)
class Tool:
    category: str
    name: str
    fr: str
    en: str
    hint: str
    run: object
    network: bool=False

TOOLS=[]
def add(cat,name,fr,en,hint,fn,network=False):
    TOOLS.append(Tool(cat,name,fr,en,hint,fn,network))

def required(value):
    if not value.strip():raise ValueError('Entrée requise / Input required')
    if len(value)>200000:raise ValueError('Entrée trop longue / Input too long')
    return value.strip()

def domain(value):
    raw=required(value)
    host=urlsplit(raw if '://' in raw else '//'+raw).hostname
    if not host:raise ValueError('Domaine invalide / Invalid domain')
    host=host.encode('idna').decode('ascii').rstrip('.')
    if len(host)>253 or not all(re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?',part) for part in host.split('.')):
        raise ValueError('Domaine invalide / Invalid domain')
    return host

def url(value):
    value=required(value)
    value=value if '://' in value else 'https://'+value
    parsed=urlsplit(value)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('URL HTTP(S) sans identifiants requise / HTTP(S) URL without credentials required')
    return value

def fetch(address,*,json_body=None):
    # Bounded read and explicit timeouts; no cookies or saved credentials.
    with requests.request('POST' if json_body is not None else 'GET',address,json=json_body,
                          headers={'User-Agent':'SyraLine/1.0','Accept':'application/json, text/html;q=0.9, */*;q=0.5'},
                          timeout=(5,12),stream=True) as response:
        response.raise_for_status()
        chunks=[];size=0
        for chunk in response.iter_content(65536):
            size+=len(chunk)
            if size>2_000_000:raise ValueError('Réponse limitée à 2 Mo / Response limit: 2 MB')
            chunks.append(chunk)
        return response.url,dict(response.headers),b''.join(chunks).decode(response.encoding or 'utf-8',errors='replace')

def api(address,body=None):return json.loads(fetch(address,json_body=body)[2])
def numeric(value):
    value=required(value)
    if not re.fullmatch(r'[1-9][0-9]{0,19}',value):raise ValueError('Identifiant numérique requis / Numeric ID required')
    return value

def dns_records(value,kind):
    host=domain(value)
    records=dns.resolver.resolve(host,kind,lifetime=6)
    return {'domain':host,'type':kind,'records':[r.to_text() for r in records]}


def subnet(value):
    n=ipaddress.ip_network(required(value),strict=False)
    if n.version==4 and n.prefixlen<31:first,last=n.network_address+1,n.broadcast_address-1
    else:first,last=n.network_address,n.broadcast_address
    return {'network':str(n),'version':n.version,'netmask':str(n.netmask),'addresses':n.num_addresses,
            'first_host':str(first),'last_host':str(last),'private':n.is_private,'global':n.is_global}

def ip_info(value):
    a=ipaddress.ip_address(required(value))
    return {'ip':str(a),'version':a.version,'expanded':a.exploded,'integer':int(a),'reverse_pointer':a.reverse_pointer,
            'private':a.is_private,'global':a.is_global,'loopback':a.is_loopback,'multicast':a.is_multicast,'reserved':a.is_reserved}

def reverse_dns(value):
    a=ipaddress.ip_address(required(value))
    return {'ip':str(a),'PTR':[r.to_text() for r in dns.resolver.resolve(a.reverse_pointer,'PTR',lifetime=6)]}


def path_file(value,limit=100_000_000):
    p=resolve_input_path(required(value))
    if not p.is_file():raise ValueError('Fichier introuvable / File not found')
    if p.stat().st_size>limit:raise ValueError(f'Fichier trop volumineux / File exceeds {limit} bytes')
    return p


def text_stats(value):
    required(value)
    return {'characters':len(value),'utf8_bytes':len(value.encode()),'words':len(value.split()),'lines':len(value.splitlines()),'unique_words':len(set(value.casefold().split()))}

def json_pretty(value):return json.dumps(json.loads(required(value)),indent=2,ensure_ascii=False)
def json_minify(value):return json.dumps(json.loads(required(value)),separators=(',',':'),ensure_ascii=False)
def jwt_decode(value):
    parts=required(value).split('.')
    if len(parts)!=3:raise ValueError('JWT attendu : header.payload.signature / Expected JWT')
    def decode(x):return json.loads(base64.urlsafe_b64decode(x+'='*(-len(x)%4)))
    return {'header':decode(parts[0]),'payload':decode(parts[1]),'signature_verified':False,'note':'Local decoding only. Claims are untrusted.'}
def timestamp(value):
    value=value.strip()
    if not value:dt=datetime.now(timezone.utc)
    elif re.fullmatch(r'-?\d+(\.\d+)?',value):dt=datetime.fromtimestamp(float(value),timezone.utc)
    else:
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
    return {'utc':dt.astimezone(timezone.utc).isoformat(),'unix_seconds':dt.timestamp()}
def uuid_gen(value):
    count=int(value or '1')
    if not 1<=count<=50:raise ValueError('1–50')
    return [str(uuid.uuid4()) for _ in range(count)]
def color_info(value):
    h=required(value).lstrip('#')
    if not re.fullmatch('[0-9a-fA-F]{6}',h):raise ValueError('#RRGGBB')
    rgb=[int(h[i:i+2],16) for i in (0,2,4)]
    return {'hex':'#'+h.upper(),'rgb':rgb,'css':f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]})'}


add('IP & Network','IP Inspector','Classification IPv4 / IPv6','IPv4 / IPv6 classification','Ex. 192.168.1.1',ip_info)
add('IP & Network','Subnet Calculator','Réseau, masque et plage','Network, mask and range','Ex. 192.168.1.0/24',subnet)
add('IP & Network','Reverse DNS','Résolution DNS inverse','Reverse DNS records','Ex. 1.1.1.1',reverse_dns,True)
for name,kind,fr,en in [('MX Lookup','MX','Serveurs de messagerie','Mail servers'),('TXT Lookup','TXT','Enregistrements texte DNS','DNS text records'),('NS Lookup','NS','Serveurs DNS autoritaires','Authoritative name servers')]:
    add('Domains & Infrastructure',name,fr,en,'Ex. example.com',lambda v,k=kind:dns_records(v,k),True)
add('Data & Encoding','JSON Format','Valider et indenter JSON','Validate and format JSON','Ex. {"hello":"world"}',json_pretty)
add('Data & Encoding','JSON Minify','JSON compact sans espaces','Compact JSON representation','Ex. {"hello":"world"}',json_minify)
add('Data & Encoding','JWT Inspector','Décodage local, sans validation','Local decoding, not verification','header.payload.signature',jwt_decode)
add('Data & Encoding','URL Decode','Décoder les caractères URL','Decode URL escapes','Ex. hello%20world',lambda v:unquote(required(v)))
add('Data & Encoding','Hex Encode','Texte UTF-8 vers hexadécimal','UTF-8 text to hexadecimal','Texte / Text',lambda v:required(v).encode().hex())
add('Data & Encoding','Hex Decode','Hexadécimal vers texte UTF-8','Hexadecimal to UTF-8 text','Ex. 68656c6c6f',lambda v:bytes.fromhex(required(v)).decode('utf-8'))
add('Data & Encoding','Text Statistics','Compter mots et caractères','Count words and characters','Texte / Text',text_stats)
add('Utilities','UUID Generator','Identifiants aléatoires UUID v4','Random UUID v4 identifiers','Nombre / Count : 1–50',uuid_gen)
add('Utilities','Timestamp','Conversion date / Unix UTC','UTC date / Unix conversion','ISO 8601 / Unix seconds (empty = now)',timestamp)
add('Utilities','Color Converter','Couleur HEX vers RGB','HEX to RGB color','Ex. #FF506A',color_info)


from tools.release_options import register as register_release_options
register_release_options(add)

from tools.github_options import register as register_github_options
register_github_options(add)

from tools.final_options import register as register_final_options
register_final_options(add)

from tools.catalog_policy import RETIRED_TOOLS
TOOLS[:]=[tool for tool in TOOLS if tool.name not in RETIRED_TOOLS]
