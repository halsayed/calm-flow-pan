# Name: Clone quotas from template project
# Task Type: Excute
# Script Type: EScript
# Author: Husain Ebrahim <husain.ebrahim@nutanix.com>
# Date: 01-11-2021
# Description:

import requests

# -------------- General settings ------------------



# -------------- Test Environment ------------------

# -------------- Calm Environment ------------------
authorization = 'Bearer @@{calm_jwt}@@'
url = 'https://127.0.0.1:9440/api/{}'
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

r = requests.post(url.format('nutanix/v3/projects/list'), json=payload, **kwargs)
if r.status_code == 200 and int(r.json()['metadata']['total_matches']):
    print('INFO - Template project found')
    template = r.json()['entities'][0]
    template_uuid = template['metadata']['uuid']
    print('INFO - template project uuid: {}'.format(template_uuid))
else:
    print('ERROR - No template project found, stopping, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)


# get quota of the template project
# ----------------------------------------------
payload = {
    'filter': 'project=={}'.format(template_uuid)
}

r = requests.post(url.format('calm/v3.0/quotas/list'), json=payload, **kwargs)
if r.status_code == 200 and len(r.json()['entities']) == 0:
    print('INFO - template project has no quotas, stopping')
    exit(0)
elif r.status_code != 200:
    print('ERROR - API call failed, staus_code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

quota_spec = r.json()['entities'][0]['status']

# update new project with template quota
# ----------------------------------------------
quota_uuid = str(uuid.uuid4())
quota_spec['resources']['uuid'] = quota_uuid
quota_spec['resources']['entities']['project'] = project_uuid
payload = {
    'spec': quota_spec,
    'metadata': {
        'kind': 'quota',
        'project_reference': {'kind': 'project', 'uuid': project_uuid},
        'uuid': quota_uuid
    } }
r = requests.post(url.format('calm/v3.0/quotas'), json=payload, **kwargs)
if r.status_code == 200:
    print('INFO - quota created sucessfully, enabling quota')
    print('INFO - waiting before state update')
    sleep(3)
    payload = {
        'spec': {
            'resources': {
                'entities': {'project': project_uuid},
                'state': quota_spec['resources']['state']
                }
            }
        }
    r = requests.put(url.format('calm/v3.0/quotas/update/state'), json=payload, **kwargs)
else:
    print('ERROR - Quota set failed, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

