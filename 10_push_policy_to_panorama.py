# Shared between test and calm environments
# --------------------------------------------------
import requests
import json

import urllib3
urllib3.disable_warnings()

# credentials and settings
# --------------------------------------------------

paronama = '10.54.60.50'
username = 'admin'
password = 'nx2Tech526!'
cluster_name = 'CL-ELM-1'
project_category = 'PROJECTS'
project_code = 'XYZ'
device_group = 'NTNX-FlowGroup'
zone_name = 'NTNX-Flow-Zone'
applications_default = 'ping,httport'
applications_user = 'ssh,ms-rdp'
ou_base = 'ou=Projects,dc=elm,dc=poc'

# --------------------------------------------------


# get auth key
# --------------------------------------------------
url = 'https://{}/api/?type=keygen&user={}&password={}'.format(paronama, username, password)
r = requests.get(url, verify=False)
if r.status_code != 200:
    print('ERROR - getting VM details failed, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)
auth_key = r.text.split('<key>')[1].split('</key>')[0]
print('INFO - authenticated successfully')

# create address group for the project
# --------------------------------------------------
group_name = 'Project-{}'.format(project_code)
address_group = {'entry': [
            {
                '@name': group_name,
                '@location': 'device-group',
                '@device-group': device_group,
                '@loc': device_group,
                'dynamic': {
                    'filter': "'ntnx.PC-prism-central.{}.{}.{}'".format(cluster_name, project_category, project_code),
                }
            }]}
url ='https://{}/restapi/v10.2/Objects/AddressGroups?location=device-group&device-group={}&name={}'\
    .format(paronama, device_group, group_name)
r = requests.post(url, json=address_group, verify=False, headers={'X-PAN-KEY': auth_key})
if r.status_code != 200:
    print('ERROR - creating address group failed, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)
print('INFO - address group created successfully')


# policy entry template
# --------------------------------------------------
entry = {
    '@name': '',
    '@location': 'device-group',
    '@device-group': device_group,
    'target': {'negate': 'no'},
    'to': {'member': [zone_name]},
    'from': {'member': [zone_name]},
    'source': {'member': ['any']},
    'destination': {'member': ['any']},
    'source-user': {'member': ['any']},
    'category': {'member': ['any']},
    'application': {'member': ['']},
    'service': {'member': ['application-default']},
    'source-hip': {'member': ['any']},
    'destination-hip': {'member': ['any']},
    'action': 'allow'
}

# default allow entry
# --------------------------------------------------
entry_name = '{}-external-default'.format(project_code)
url = 'https://{}/restapi/v10.2/Policies/SecurityPreRules?location=device-group&device-group={}&name={}'\
    .format(paronama, device_group, entry_name)

entry['@name'] = entry_name
entry['source']['member'] = ['any']
entry['destination']['member'] = [group_name]
entry['application']['member'] = applications_default.split(',')

r = requests.post(url, json={'entry': [entry]}, verify=False, headers={'X-PAN-KEY': auth_key})
if r.status_code == 200:
    print('INFO - default external allow entry created successfully')
else:
    print('ERROR - creating default external allow entry failed, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

# default intra entry
# --------------------------------------------------
entry_name = '{}-intra-default'.format(project_code)
url = 'https://{}/restapi/v10.2/Policies/SecurityPreRules?location=device-group&device-group={}&name={}'\
    .format(paronama, device_group, entry_name)

entry['@name'] = entry_name
entry['source']['member'] = [group_name]
entry['destination']['member'] = [group_name]
entry['application']['member'] = ['any']

r = requests.post(url, json={'entry': [entry]}, verify=False, headers={'X-PAN-KEY': auth_key})
if r.status_code == 200:
    print('INFO - default intra project allow entry created successfully')
else:
    print('ERROR - creating default intra project allow entry failed, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)



# user based entry
# --------------------------------------------------
entry_name = '{}-user-default'.format(project_code)
url = 'https://{}/restapi/v10.2/Policies/SecurityPreRules?location=device-group&device-group={}&name={}'\
    .format(paronama, device_group, entry_name)

entry['@name'] = entry_name
entry['source']['member'] = ['any']
entry['destination']['member'] = [group_name]
entry['source-user']['member'] = ['cn={}-users,{}'.format(project_code, ou_base)]
entry['application']['member'] = applications_user.split(',')

r = requests.post(url, json={'entry': [entry]}, verify=False, headers={'X-PAN-KEY': auth_key})
if r.status_code == 200:
    print('INFO - default user based allow entry created successfully')
else:
    print('ERROR - creating default user based allow entry failed, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

# commit changes
# --------------------------------------------------
url = 'https://{}/api/?key={}&type=commit&action=all&cmd=<commit-all><shared-policy><device-group><entry name="{}"/></device-group></shared-policy></commit-all>'.format(paronama, auth_key, device_group)

r = requests.get(url, verify=False)
if r.status_code == 200:
    print('INFO - changes committed successfully')
else:
    print('ERROR - committing changes failed, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)
