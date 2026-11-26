"""Independent Python implementations inspired by established GitHub utilities.

No upstream implementation code is embedded.
"""
import base64
import collections
import difflib
import gzip
import json
import math
from lib.constants import resolve_input_path
from pathlib import Path
import re
import tomllib
from urllib.parse import urlsplit
import zlib

LIMIT=1_000_000

def text(value):
    if not value.strip():raise ValueError('Entrée requise / Input required')
    if len(value)>200000:raise ValueError('Entrée trop longue / Input too long')
    return value


def base32_encode(value):return base64.b32encode(text(value).encode()).decode()
def base32_decode(value):
    raw=''.join(text(value).split()).upper()
    return base64.b32decode(raw+'='*(-len(raw)%8),casefold=True).decode('utf-8')
def gzip_encode(value):return base64.b64encode(gzip.compress(text(value).encode(),mtime=0)).decode()
def gzip_decode(value):
    raw=base64.b64decode(''.join(text(value).split()),validate=True)
    decoder=zlib.decompressobj(16+zlib.MAX_WBITS)
    data=decoder.decompress(raw,LIMIT+1)
    if len(data)>LIMIT or decoder.unconsumed_tail:raise ValueError('Sortie limitée à 1 Mo / Output limit: 1 MB')
    if not decoder.eof or decoder.unused_data:raise ValueError('Flux gzip incomplet ou multiple / Incomplete or multiple gzip streams')
    return data.decode('utf-8')

def json_query(value):
    path,separator,document=text(value).partition('\n')
    if not separator:raise ValueError('Première ligne : chemin. Lignes suivantes : JSON. / First line: path, then JSON.')
    result=json.loads(document)
    # RFC 6901 JSON Pointer, a focused alternative to full jq expressions.
    if path and not path.startswith('/'):raise ValueError('Chemin JSON Pointer requis : /users/0/name')
    for component in path.split('/')[1:] if path else []:
        component=component.replace('~1','/').replace('~0','~')
        if isinstance(result,list):
            if not re.fullmatch(r'0|[1-9][0-9]*',component):raise ValueError('Index de liste invalide / Invalid array index')
            result=result[int(component)]
        elif isinstance(result,dict):result=result[component]
        else:raise ValueError('Chemin absent / Path does not exist')
    return {'path':path,'value':result}

def split_pair(value):
    parts=re.split(r'^---[ \t]*\r?$',text(value),maxsplit=1,flags=re.M)
    if len(parts)!=2:raise ValueError('Séparer les deux documents par une ligne --- / Separate documents with a line ---')
    a,b=parts
    a=a[:-2] if a.endswith('\r\n') else a.removesuffix('\n')
    b=b[2:] if b.startswith('\r\n') else b.removeprefix('\n')
    return a,b

def json_diff(value):
    a,b=[json.loads(v) for v in split_pair(value)]
    changes=[]
    def walk(left,right,path=''):
        if len(changes)>=200:return
        if type(left)!=type(right):changes.append({'path':path,'change':'changed','before':left,'after':right})
        elif isinstance(left,dict):
            for key in sorted(set(left)|set(right)):
                child=path+'/'+key.replace('~','~0').replace('/','~1')
                if key not in left:changes.append({'path':child,'change':'added','after':right[key]})
                elif key not in right:changes.append({'path':child,'change':'removed','before':left[key]})
                else:walk(left[key],right[key],child)
                if len(changes)>=200:break
        elif isinstance(left,list):
            for index in range(max(len(left),len(right))):
                child=path+'/'+str(index)
                if index>=len(left):changes.append({'path':child,'change':'added','after':right[index]})
                elif index>=len(right):changes.append({'path':child,'change':'removed','before':left[index]})
                else:walk(left[index],right[index],child)
                if len(changes)>=200:break
        elif left!=right:changes.append({'path':path,'change':'changed','before':left,'after':right})
    walk(a,b)
    return {'identical':not changes,'changes':changes,'display_limit':200,'limit_reached':len(changes)>=200}

def toml_json(value):return json.dumps(tomllib.loads(text(value)),indent=2,ensure_ascii=False,default=str)
def text_diff(value):
    a,b=split_pair(value)
    if max(len(a.splitlines()),len(b.splitlines()))>2000:raise ValueError('Maximum 2 000 lignes par document / 2,000-line limit per document')
    return {'identical':a==b,'diff':'\n'.join(difflib.unified_diff(a.splitlines(),b.splitlines(),fromfile='before',tofile='after',lineterm=''))}


def defang(value):
    raw=text(value).strip()
    return raw.replace('https://','hxxps://').replace('http://','hxxp://').replace('.','[.]').replace('@','[@]')
def refang(value):
    return text(value).strip().replace('hxxps://','https://').replace('hxxp://','http://').replace('[.]','.').replace('[@]','@')


def register(add):
    entries=[
        ('Data & Encoding','Base32 Encode','Encoder en Base32','Encode Base32','Texte / Text',base32_encode),
        ('Data & Encoding','Base32 Decode','Décoder le Base32','Decode Base32','JBSWY3DP',base32_decode),
        ('Data & Encoding','Gzip Encode','Compresser le texte en gzip Base64','Compress text to gzip Base64','Texte / Text',gzip_encode),
        ('Data & Encoding','Gzip Decode','Décompresser le gzip Base64','Decompress gzip Base64','Base64 gzip',gzip_decode),
        ('Data & Encoding','JSON Pointer','Extraire une valeur JSON','Extract a JSON value','/users/0/name puis JSON à la ligne suivante',json_query),
        ('Data & Encoding','JSON Diff','Comparer deux documents JSON','Compare two JSON documents','JSON avant / ligne --- / JSON après',json_diff),
        ('Data & Encoding','TOML to JSON','Convertir TOML vers JSON','Convert TOML to JSON','name = "SyraLine"',toml_json),
        ('Utilities','Text Diff','Comparer deux textes ligne par ligne','Compare text line by line','Texte avant / ligne --- / texte après',text_diff),
        ('Utilities','URL Defang','Neutraliser un lien pour partage','Defang a link for sharing','https://example.com',defang),
        ('Utilities','URL Refang','Restaurer un lien neutralisé','Restore a defanged link','hxxps://example[.]com',refang),
    ]
    for entry in entries:add(*entry)
