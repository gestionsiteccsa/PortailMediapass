"""Script autonome de diagnostic PMB.

Initialise Django, charge le certificat client, puis effectue des appels
HTTP directs (sans passer par ``call_pmb``) pour tester la connectivité
brute avec le serveur PMB.

Utilisation :
    python debug_pmb.py
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
import django

django.setup()

import requests

from home.services.pmb_client import _get_cert_path

cert_path = _get_cert_path()
print(f'Cert path: {cert_path}')
print(f'Cert exists: {os.path.exists(cert_path)}')
print(f'Cert size: {os.path.getsize(cert_path)}')

# Test direct
url = 'https://fourmies.pmbpro.net/ws/connector_out.php?source_id=4'
payload = {'method': 'pmbesOPACEmpr_login', 'params': ['test', 'test'], 'id': 1}
resp = requests.post(url, json=payload, cert=cert_path, verify=True, timeout=30)
print(f'Status: {resp.status_code}')
print(f'Body: {resp.text[:500]}')

# Compare with search function
payload2 = {'method': 'pmbesSearch_simpleSearch', 'params': [0, 'harry'], 'id': 1}
resp2 = requests.post(url, json=payload2, cert=cert_path, verify=True, timeout=30)
print(f'Search Status: {resp2.status_code}')
print(f'Search Body: {resp2.text[:200]}')
