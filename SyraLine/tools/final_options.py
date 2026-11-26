"""The final eleven public-information and local-analysis options."""
from lib.constants import resolve_input_path
import collections
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email import policy
from email.parser import BytesParser, Parser
import hashlib
import ipaddress
import os
from pathlib import Path
import re
import threading
from urllib.parse import quote, unquote_plus, urlsplit, urlunsplit

FILE_LIMIT=20_000_000
SKIP_DIRS={'.git','.venv','venv','node_modules','__pycache__','packages'}
_secret_lock=threading.Lock()

def required(value):
    if not value.strip():raise ValueError('Entrée requise / Input required')
    if len(value)>200000:raise ValueError('Entrée trop longue / Input too long')
    return value.strip()


def rdap(value):
    from tools.core import api,domain
    host=domain(value)
    tld=host.rsplit('.',1)[-1]
    bootstrap=api('https://data.iana.org/rdap/dns.json')
    endpoints=next((urls for tlds,urls in bootstrap.get('services',[]) if tld in tlds),[])
    if not endpoints:raise ValueError('RDAP indisponible pour ce TLD / No RDAP service for this TLD')
    address=next((u for u in endpoints if u.startswith('https://')),None)
    if not address:raise ValueError('Aucun service RDAP HTTPS / No HTTPS RDAP endpoint')
    source=address.rstrip('/')+'/domain/'+quote(host,safe='')
    data=api(source)
    contacts=[]
    for entity in data.get('entities',[]):
        card=entity.get('vcardArray',[])
        fields=card[1] if len(card)>1 and isinstance(card[1],list) else []
        name=next((v[3] for v in fields if len(v)>3 and v[0]=='fn'),None)
        contacts.append({'name':name,'roles':entity.get('roles',[]),'handle':entity.get('handle')})
    return {'domain':data.get('ldhName',host),'source':source,'handle':data.get('handle'),
            'status':data.get('status',[]),'events':data.get('events',[]),'nameservers':[d.get('ldhName') for d in data.get('nameservers',[])],
            'dnssec':data.get('secureDNS',{}),'entities':contacts,
            'note':'Informations publiques disponibles ; champs parfois masqués / Public registration data; some fields may be redacted'}


def email_audit(value):
    from tools.core import domain
    import dns.resolver
    host=domain(value)
    def txt(name):
        try:
            answer=dns.resolver.resolve(name,'TXT',lifetime=5)
            return [''.join(part.decode('utf-8',errors='replace') for part in row.strings) for row in answer],None
        except (dns.resolver.NXDOMAIN,dns.resolver.NoAnswer):return [],'absent'
        except Exception as exc:return [],type(exc).__name__
    records,spf_error=txt(host)
    spf=[v for v in records if v.lower().startswith('v=spf1')]
    records,dmarc_error=txt('_dmarc.'+host)
    dmarc=[v for v in records if v.lower().startswith('v=dmarc1')]
    findings=[]
    if len(spf)!=1:findings.append('SPF absent ou multiple / SPF missing or multiple')
    if len(dmarc)!=1:findings.append('DMARC absent ou multiple / DMARC missing or multiple')
    policy_values={}
    if len(dmarc)==1:
        tags=[v.strip().split('=',1) for v in dmarc[0].split(';') if v.strip()]
        if any(len(v)!=2 for v in tags):findings.append('Balise DMARC invalide / Invalid DMARC tag')
        for item in tags:
            if len(item)==2:
                key,content=item
                if key.lower() in policy_values:findings.append('Balise DMARC dupliquée / Duplicate DMARC tag: '+key)
                policy_values[key.lower()]=content
        if policy_values.get('p') not in ('none','quarantine','reject'):findings.append('Politique DMARC absente ou invalide / Missing or invalid DMARC policy')
    return {'domain':host,'spf_records':spf,'spf_dns_status':spf_error or 'OK','dmarc_records':dmarc,
            'dmarc_dns_status':dmarc_error or 'OK','dmarc_tags':policy_values,'findings':findings,
            'note':'Audit des enregistrements publiés ; pas de simulation complète SPF ni vérification DKIM / Published-record audit, not full SPF or DKIM verification'}


def clean_url(value):
    from tools.core import url
    original=url(value)
    parts=urlsplit(original)
    fragments=parts.query.split('&') if parts.query else []
    keys=[unquote_plus(v.split('=',1)[0]).casefold() for v in fragments]
    signed=any(k in {'sig','signature','token','x-amz-signature','x-goog-signature'} for k in keys)
    removed=[];kept=[]
    for segment,key in zip(fragments,keys):
        if not signed and (key.startswith('utm_') or key in {'fbclid','gclid','dclid','msclkid','mc_cid','mc_eid'}):removed.append(key)
        else:kept.append(segment)
    cleaned=urlunsplit((parts.scheme,parts.netloc,parts.path,'&'.join(kept),parts.fragment))
    return {'original':original,'cleaned':cleaned,'removed_parameters':removed,'signed_link_preserved':signed,
            'note':'Règles conservatrices ; paramètres inconnus conservés / Conservative rules; unknown parameters preserved'}

def register(add):
    options=[
        ('Domains & Infrastructure','Domain RDAP','Données publiques du registre de domaine','Public domain registration data','example.com',rdap,True),
        ('Domains & Infrastructure','Email Domain Audit','Examiner SPF et DMARC publiés','Inspect published SPF and DMARC','example.com',email_audit,True),
        ('Utilities','Tracking URL Cleaner','Retirer les paramètres de suivi connus','Remove known tracking parameters','https://example.com/?utm_source=test',clean_url),
    ]
    for option in options:add(*option)
