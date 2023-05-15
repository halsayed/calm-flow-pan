# Name: Check if project code exists and create it if not
# Task Type: set variable
# Script Type: EScript
# Author: Husain Ebrahim <husain.ebrahim@nutanix.com>
# Date: 10-05-2023
# Description:
# region general settings
# -----------------------------------------------

# endregion

# region test-environment
# -----------------------------------------------
from decouple import config
import requests
import urllib3
import json
import base64
from time import sleep
import uuid

urllib3.disable_warnings()

# prism central config
pc_host = config('PC_HOST')
pc_port = config('PC_PORT', '9440')
pc_username = config('PC_USERNAME')
pc_password = config('PC_PASSWORD')
pc_authorization = 'Basic ' + base64.b64encode('{}:{}'.format(pc_username, pc_password).encode()).decode()

# test settings
project_code = 'AAB'
project_category = 'PROJECTS'
# endregion


# region calm-environment
# -----------------------------------------------
# import requests
#
# # prism central config
# pc_host = '127.0.0.1'
# pc_port = '9440'
# pc_authorization = 'Bearer @@{calm_jwt}@@'
#
# # blueprint settings
# project_code = '@@{PROJECT_CODE}@@'
# project_category = '@@{PROJECT_CATEGORY}@@'
# endregion


# region http headers
# -----------------------------------------------
pc_url = 'https://{}:{}/api/nutanix/v3/{}'.format(pc_host, pc_port, '{}')
pc_kwargs = {
    'verify': False,
    'headers': {'Authorization': pc_authorization}
}
# endregion


# region main function
# -----------------------------------------------

# check if the category exists and if the code is already in the category
payload = {'kind': 'category'}
r = requests.post(pc_url.format('categories/'+project_category+'/list'), json=payload, **pc_kwargs)
if r .status_code == 200:
    current_count = int(r.json()['metadata']['total_matches'])
    print('INFO - current project code count: {}'.format(current_count))

if current_count > 0:
    codes = []
    for entity in r.json()['entities']:
        codes.append(entity['value'])
    if project_code in codes:
        print('ERROR - project code already exists')
        exit(1)

# if the category key doesn't exist then create it
if current_count == 0:
    payload = {'name': project_category}
    print('INFO - category key is not available, creating it')
    r = requests.put(pc_url.format('categories/'+project_category), json=payload, **pc_kwargs)
    print('INFO - creating category status code: {}'.format(r.status_code))

# adding the new project code to the category
payload = {'value': project_code}
r = requests.put(pc_url.format('categories/'+project_category+'/'+project_code), json=payload, **pc_kwargs)

print('PROJECT_CODE={}'.format(project_code))
# endregion