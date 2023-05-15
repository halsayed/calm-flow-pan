# Name: Create tenant project and return project uuid
# Task Type: set variable
# Script Type: EScript
# Author: Husain Ebrahim <husain.ebrahim@nutanix.com>
# Date: 25-09-2021
# Description:

import requests

# -------------- General settings ------------------



# -------------- Test Environment ------------------

# -------------- Calm Environment ------------------
authorization = 'Bearer @@{calm_jwt}@@'
url = 'https://127.0.0.1:9440/api/nutanix/v3/{}'
project_name = '@@{PROJECT_NAME}@@'
project_code = '@@{PROJECT_CODE}@@'
project_category = '@@{PROJECT_CATEGORY}@@'

kwargs = {
    'verify': False,
    'headers': {'Authorization': authorization}
}

payload = {
    'spec': {
        'name': '{}-{}'.format(project_code, project_name),
        'resources': {
            'subnet_reference_list': [],
            'external_user_group_reference_list': [],
            'user_reference_list': []
        },
        'description': 'Project for tenant: {}, using code: {}'.format(project_name, project_code)
    },
    'api_version': '3.1.0',
    'metadata': {
        'kind': 'project',
        'spec_version': 0,
        'owner_reference': {
            'kind': 'user',
            'name': 'admin',
            'uuid': '00000000-0000-0000-0000-000000000000'
        },
        'categories': {
            project_category: project_code
        }
    }
}

r = requests.post(url.format('projects'), json=payload, **kwargs)

if r.status_code == 202:
    result = r.json()
    task_uuid = result['status']['execution_context']['task_uuid']
    task_state = result['status']['state']
    project_uuid = result['metadata']['uuid']
    print('INFO - Project created with status code: {}'.format(r.status_code))
    print('INFO - Project uuid: {}'.format(project_uuid))
    print('INFO - task: {}, state: {}'.format(task_uuid, task_state))
else:
    print('ERRPR - project creation failed, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

# for for the project task to complete
while task_state == 'PENDING':
    print('INFO - waiting for 1 sec')
    sleep(1)
    r = requests.get(url.format('tasks/'+task_uuid), **kwargs)
    task_state = r.json()['status']
    print('INFO - task: {}, state: {}'.format(task_uuid, task_state))

print('PROJECT_UUID={}'.format(project_uuid))