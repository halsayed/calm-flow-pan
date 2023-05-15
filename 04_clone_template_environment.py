# Name: Clone project enivronment from a reference project template
# Task Type: Excute
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
project_template = '@@{PROJECT_TEMPLATE}@@'
project_uuid = '@@{PROJECT_UUID}@@'

kwargs = {
    'verify': False,
    'headers': {'Authorization': authorization}
}

# find the template project to clone the specs
# ----------------------------------------------
payload = {
    'kind': 'project',
    'filter': 'name=={}'.format(project_template)
}

r = requests.post(url.format('projects/list'), json=payload, **kwargs)
if r.status_code == 200 and int(r.json()['metadata']['total_matches']):
    print('INFO - Template project found')
    template = r.json()['entities'][0]
    template_uuid = template['metadata']['uuid']
    account_reference_list = template['spec']['resources']['account_reference_list']
    default_subnet_reference = template['spec']['resources']['default_subnet_reference']
    subnet_reference_list = template['spec']['resources']['subnet_reference_list']
    environment_reference_list = template['spec']['resources']['environment_reference_list']
    default_environment_uuid = template['spec']['resources']['default_environment_reference'].get('uuid')

    print('INFO - template project uuid: {}'.format(template_uuid))
else:
    print('ERROR - No template project found, stopping, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

# get target project details
# -----------------------------------------
print('INFO - updating target project: {}'.format(project_uuid))
r = requests.get(url.format('projects/' + project_uuid), **kwargs)
project_spec = r.json()
del (project_spec['status'])

# create new environments based on the template
target_environment_list = []
target_default_environment = None
for environment in environment_reference_list:
    print('INFO - creating new environment')
    r = requests.get(url.format('environments/' + environment['uuid']), **kwargs)
    env_spec = r.json()
    template_env_uuid = env_spec['metadata']['uuid']
    del (env_spec['status'])
    new_substrate_list = []
    for substrate in env_spec['spec']['resources']['substrate_definition_list']:
        substrate['uuid'] = str(uuid.uuid4())
        new_substrate_list.append(substrate)

    env_spec['spec']['resources']['substrate_definition_list'] = new_substrate_list
    env_spec['metadata'] = {'kind': 'environment', 'name': env_spec['spec']['name'],
                            'project_reference': {'kind': 'project', 'uuid': project_uuid}}
    env_spec['spec']['resources']['credential_definition_list'] = [{
        'name': 'default',
        'type': 'PASSWORD',
        'username': 'admin',
        'secret': {'attrs': {'is_secret_modified': True}, 'value': str(uuid.uuid4())},
        'uuid': str(uuid.uuid4())
    }]

    r = requests.post(url.format('environments'), json=env_spec, **kwargs)
    if r.status_code == 200:
        new_env_uuid = r.json()['metadata']['uuid']
        print('INFO - new environment created with uuid: {}'.format(new_env_uuid))
        target_environment_list.append({'kind': 'environment', 'uuid': new_env_uuid})
        if template_env_uuid == default_environment_uuid:
            target_default_environment = {'kind': 'environment', 'uuid': new_env_uuid}

# append the project spec with new environment list
if len(target_environment_list):
    project_spec['spec']['resources']['environment_reference_list'] = target_environment_list
if target_default_environment:
    project_spec['spec']['resources']['default_environment_reference'] = target_default_environment

sleep(3)
r = requests.put(url.format('projects/' + project_uuid), json=project_spec, **kwargs)

# check if the update worked
if r.status_code == 202:
    result = r.json()
    task_uuid = result['status']['execution_context']['task_uuid']
    task_state = result['status']['state']
    project_uuid = result['metadata']['uuid']
    print('INFO - Project update with status code: {}'.format(r.status_code))
    print('INFO - task: {}, state: {}'.format(task_uuid, task_state))
else:
    print('ERRPR - project update failed, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

# for for the project task to complete
while task_state == 'PENDING':
    print('INFO - waiting for 1 sec')
    sleep(1)
    r = requests.get(url.format('tasks/' + task_uuid), **kwargs)
    task_state = r.json()['status']
    print('INFO - task: {}, state: {}'.format(task_uuid, task_state))



