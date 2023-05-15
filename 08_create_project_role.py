# Name: Add the AD user as admin role to the new project
# Task Type: Execute
# Script Type: EScript
# Author: Husain Ebrahim <husain.ebrahim@nutanix.com>
# Date: 21-11-2021
# Description:

import requests

# -------------- General settings ------------------


# -------------- Test Environment ------------------
# region test-environment
# -----------------------------------------------
# from decouple import config
# import requests
# import urllib3
# import json
# import base64
# from time import sleep
# import uuid
#
# urllib3.disable_warnings()
#
# # prism central config
# pc_host = config('PC_HOST')
# pc_port = config('PC_PORT', '9440')
# pc_username = config('PC_USERNAME')
# pc_password = config('PC_PASSWORD')
# pc_authorization = 'Basic ' + base64.b64encode('{}:{}'.format(pc_username, pc_password).encode()).decode()
#
# # test settings
# project_template = 'TEMPLATE'
# project_uuid = '464f93ec-b976-4dc1-b5c0-f15a916899ee'
# project_code = 'TTT'
# ou_base = 'ou=projects,dc=elm,dc=poc'
# domain = 'elm.poc'
# role_name = 'Project Admin'
# endregion

# region calm-environment
# -----------------------------------------------
import requests

# prism central config
pc_host = '127.0.0.1'
pc_port = '9440'
pc_authorization = 'Bearer @@{calm_jwt}@@'

# blueprint settings
project_template = '@@{PROJECT_TEMPLATE}@@'
project_uuid = '@@{PROJECT_UUID}@@'
project_code = '@@{PROJECT_CODE}@@'
ou_base = '@@{PROJECT_OU_BASE}@@'
domain = '@@{DOMAIN_NAME}@@'
role_name = '@@{ROLE_NAME}@@'
# endregion

# region http headers
# -----------------------------------------------
pc_url = 'https://{}:{}/api/nutanix/v3/{}'.format(pc_host, pc_port, '{}')
pc_kwargs = {
    'verify': False,
    'headers': {'Authorization': pc_authorization}
}
# endregion

# find the template project to clone the specs
# ----------------------------------------------
payload = {
    'kind': 'project',
    'filter': 'name=={}'.format(project_template)
}

r = requests.post(pc_url.format('projects/list'), json=payload, **pc_kwargs)
if r.status_code == 200 and int(r.json()['metadata']['total_matches']):
    print('INFO - Template project found')
    template = r.json()['entities'][0]
    template_uuid = template['metadata']['uuid']
    print('INFO - Template project uuid: {}'.format(template_uuid))
else:
    print('ERROR - No template project found, stopping, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

# find directory service uuid on prism
# ----------------------------------------------
payload = {
    'kind': 'directory_service'
}
directory_uuid = ''

r = requests.post(pc_url.format('directory_services/list'), json=payload, **pc_kwargs)
if r.status_code == 200:
    for directory in r.json()['entities']:
        if directory['spec']['resources']['domain_name'] == domain:
            directory_uuid = directory['metadata']['uuid']

    if directory_uuid:
        print('INFO - Direcotry found with uuid: {}'.format(directory_uuid))
    else:
        print('ERROR - no directory uuid found for domain: {}'.format(domain))
        exit(1)
else:
    print('ERROR - No directory service found, stopping, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

# find Prism roles uuid and names
# ----------------------------------------------
payload = {'kind': 'role', 'filter': '', 'length': 1000}
r = requests.post(pc_url.format('roles/list'), json=payload, **pc_kwargs)
prism_roles = {}
if r.status_code == 200:
    for role in r.json().get('entities', []):
        prism_roles[role['metadata']['uuid']] = role['spec']['name']
else:
    print('ERROR - failed to get roles, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)


# get the group uuid
# ----------------------------------------------
group_uuid = str(uuid.uuid4())
# user_group = 'cn={},{}'.format(project_code + '-users', ou_base)
# payload = {
#     'entity_type': 'user_group',
#     'group_sort_attribute': 'group_name',
#     'group_member_attributes': [
#         {'attribute': 'group_name'},
#         {'attribute': 'directory_domain'},
#         {'attribute': 'distinguished_name'}
#     ],
#     'query_name': 'prism:GroupsRequestModel',
#     'filter_criteria': 'distinguished_name=in={}'.format(user_group.replace(',', '%2C').replace('=', '%3D')).lower(),
# }
#
# r = requests.post(pc_url.format('groups'), json=payload, **pc_kwargs)
# if r.status_code == 200:
#     group_uuid = r.json()['group_results'][0]['entity_results'][0]['entity_id']
#     print('INFO - group uuid: {}'.format(group_uuid))
# else:
#     print('ERROR - failed to get group uuid, status code: {}, msg: {}'.format(r.status_code, r.content))
#     exit(1)

# get the template project details
# ----------------------------------------------
r = requests.get(pc_url.format('projects_internal/' + template_uuid), **pc_kwargs)
if r.status_code == 200:
    print('INFO - obtain template details')
    template = r.json()

# get the new project details
r = requests.get(pc_url.format('projects_internal/' + project_uuid), **pc_kwargs)
if r.status_code == 200:
    print('INFO - obtain new project details')
    project = r.json()

# prepare the project details to update with roles
# ----------------------------------------------
del (project['status'])
template_roles = template['spec']['access_control_policy_list']
roles = []

for role in template_roles:
    reference_role = role['acp']['resources']['role_reference']['uuid']
    if prism_roles.get(reference_role) == role_name:
        filter = json.dumps(role['acp']['resources']['filter_list']).replace(template_uuid, project_uuid)
        filter = json.loads(filter)
        roles.append({
            'uuid': group_uuid,
            'name': 'cn={}-users,{}'.format(project_code.lower(), ou_base.lower()),
            'reference_role': reference_role,
            'filter': filter
        })

# update the new project with clone roles
# ----------------------------------------------
acp_list = []
groups_list = []
for role in roles:
    # acp_list payload
    acp_list.append({
        'acp': {
            'name': 'nuCalmAcp-{}'.format(str(uuid.uuid4())),
            'resources': {
                'role_reference': {'uuid': role['reference_role'], 'kind': 'role'},
                'user_group_reference_list': [{
                    'name': role['name'],
                    'kind': 'user_group',
                    'uuid': role['uuid']
                }],
                'filter_list': role['filter']
            }
        },
        'metadata': {'kind': 'access_control_policy'},
        'operation': 'ADD'
    })

    groups_list.append(
        {
            'name': role['name'],
            'kind': 'user_group',
            'uuid': role['uuid']
        }
    )

project['spec']['access_control_policy_list'] = acp_list
project['spec']['project_detail']['resources']['external_user_group_reference_list'] = groups_list
project['spec']['user_group_list'] = [{
    'metadata': {'kind': 'user_group', 'uuid': group_uuid},
    'operation': 'ADD',
    'user_group': {'resources':
                       {'directory_service_user_group':
                                     {'distinguished_name': 'CN={}-users,{}'.format(project_code, ou_base)}
                        }
                   }
}]

r = requests.put(pc_url.format('projects_internal/' + project_uuid), json=project, **pc_kwargs)

if r.status_code == 202:
    print('INFO - new project updated with roles')
else:
    print('ERROR - project role update, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)


