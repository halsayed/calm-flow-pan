# Name: Publish marketplace items based on TEMPLATE project published items
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
    print('INFO - Template project uuid: {}'.format(template_uuid))
else:
    print('ERROR - No template project found, stopping, status code: {}, msg: {}'.format(r.status_code, r.content))
    exit(1)

# get all published items in marketplace
payload = {
    'kind': 'marketplace_item',
    'filter': 'app_state==PUBLISHED'
}

r = requests.post(url.format('calm_marketplace_items/list'), json=payload, **kwargs)
for item in r.json()['entities']:
    r = requests.get(url.format('calm_marketplace_items/'+item['metadata']['uuid']), **kwargs)
    item_details = r.json()
    for project in item_details['spec']['resources']['project_reference_list']:
        if project['uuid'] == template_uuid:
            print('INFO - Publishing item: {}'.format(item['metadata']['uuid']))
            del(item_details['status'])
            item_details['spec']['resources']['project_reference_list'].append({
                'kind': 'project',
                'uuid': project_uuid
            })
            r = requests.put(url.format('calm_marketplace_items/'+item['metadata']['uuid']), json=item_details, **kwargs)

