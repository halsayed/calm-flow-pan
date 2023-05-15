# Name: Create flow policy based on project and app name
# Task type: SetVariable
# Script type: Escript
# Author: Husain Ebrahim
# Date: 08-03-2022
# Description:

# Shared between test and calm environments
# --------------------------------------------------
import requests
category_name = 'AppType'
app_type = 'Default'
projects_category = 'PROJECTS'

# -------------- Test Environment ------------------
# import json
# from time import sleep
# import uuid
# import urllib3
# import re
# import json
# from base64 import b64encode
# from decouple import config
# urllib3.disable_warnings()
#
# PRISM_HOST = config('PC_HOST')
# PRISM_PORT = config('PC_PORT', '9440')
# PRISM_USER = config('PC_USERNAME')
# PRISM_PASS = config('PC_PASSWORD')
# authorization = 'Basic {}'.format(b64encode(f'{PRISM_USER}:{PRISM_PASS}'.encode()).decode())
# url = 'https://{}:{}/api/nutanix/v3/'.format(PRISM_HOST, PRISM_PORT)
# project_code = 'TTT'
# description = 'Name of the project'
# default_policy = json.loads('''[
#   {"ip": "0.0.0.0", "prefix": 0, "protocol": "TCP", "port": 22},
#   {"ip": "0.0.0.0", "prefix": 0, "protocol": "TCP", "port": 9090}
# ]''')
# id_based_policy = json.loads('''[{"ip": "0.0.0.0", "prefix": 0, "protocol": "TCP", "port": 5985}''')

# -------------- Calm Environment ------------------
authorization = 'Bearer @@{calm_jwt}@@'
url = 'https://127.0.0.1:9440/api/nutanix/v3/'
project_code = '@@{PROJECT_CODE}@@'
description = 'Flow policy for @@{PROJECT_CODE}@@ - @@{PROJECT_NAME}@@'
default_policy = json.loads('''@@{DEFAULT_POLICY}@@''')
id_based_policy = json.loads('''@@{ID_BASED_POLICY}@@''')

kwargs = {
    'verify': False,
    'headers': {'Authorization': authorization}
}


# --------------- functions ------------------------
# --------------------------------------------------
def generate_ace(ace):
    ip = ace.get('ip')
    prefix = int(ace.get('prefix', 0))
    proto = ace.get('protocol')
    port = int(ace.get('port', 0))
    entry = {
        'peer_specification_type': 'IP_SUBNET',
        'ip_subnet': {
            'ip': ip,
            'prefix_length': prefix
        },
        'protocol': proto,
    }
    if proto == 'TCP':
        entry['tcp_port_range_list'] = [{'start_port': port, 'end_port': port}]
    elif proto == 'UDP':
        entry['udp_port_range_list'] = [{'start_port': port, 'end_port': port}]

    return entry

# ----------------- end of functions ---------------------
# --------------------------------------------------------

# create policy
# ---------------------------------------------
policy_name = '{}-policy'.format(project_code)
target_group = {
    'peer_specification_type': 'FILTER',
    'filter': {
      'type': 'CATEGORIES_MATCH_ALL',
      'kind_list': ['vm'],
      'params': {category_name: [app_type], projects_category: [project_code]}
    }
  }
resources = {
    'allow_ipv6_traffic': False,
    'is_policy_hitlog_enabled': False,
    'app_rule': {
      'target_group': target_group,
      'inbound_allow_list': [],
      'outbound_allow_list': [{'peer_specification_type': 'ALL'}],
      'action': 'APPLY'
    }
  }
acl = []
for ace in default_policy:
    acl.append(generate_ace(ace))

for ace in id_based_policy:
    acl.append(generate_ace(ace))

resources['app_rule']['inbound_allow_list'] = acl
payload = {
    'api_version': '3.1.0',
    'metadata': {'kind': 'network_security_rule'},
    'spec': {
      'name': policy_name,
      'description': description,
      'resources': resources
    }
  }

r = requests.post((url+'network_security_rules'), json=payload, **kwargs)
if r.status_code == 202:
    print('INFO - flow policy created')
    print('POLICY_UUID={}'.format(r.json()['metadata']['uuid']))
    print('CURRENT_POLICY={}'.format(json.dumps(default_policy)))
else:
    print('ERROR - policy creation failed, status code: {}, msg: {}'.format(r.status_code,r.content))
    exit(1)

