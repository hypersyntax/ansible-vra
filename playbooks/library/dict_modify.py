#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: dict_modify

short_description: Modifies a key/value within a nested dictionary

version_added: "2.4"

description:
    - "Given a JSON, this finds a key in a parent and updates the value"

options:
    parent:
        description:
            - This is where you can find the key inside the JSON
        required: true
    key:
        description:
            - This is the key you are looking to change the value of
        required: true
    value:
        description:
            - This is the value of the key you are looking to change
        required: true
    json:
        description:
            - This is the JSON you want to modify
        required: true

author:
    - @dellEMC
'''

EXAMPLES = '''
- dict_modify:
    parent: haystack
    key: needle
    value: my_value
    json: "{{ farm_house }}"
    register: output
'''

RETURN = '''
json:
    description: This can be either the original JSON if no key was found or the new JSON with the new value if it was found
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
import json

# Start of Helper Functions
def find_in_obj(obj, condition, path=None):
    ''' generator finds full path to nested dict key when key is at an unknown level
        borrowed from http://stackoverflow.com/a/31625583/5456148'''
    if path is None:
        path = []

    # In case this is a list
    if isinstance(obj, list):
        for index, value in enumerate(obj):
            new_path = list(path)
            new_path.append(index)
            for result in find_in_obj(value, condition, path=new_path):
                yield result

    # In case this is a dictionary
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = list(path)
            new_path.append(key)
            for result in find_in_obj(value, condition, path=new_path):
                yield result

            if condition == key:
                new_path = list(path)
                new_path.append(key)
                yield new_path


def set_nested_value(nested_dict, path_list, key, value):
    ''' add or update a value in a nested dict using passed list as path
        borrowed from http://stackoverflow.com/a/11918901/5456148'''
    cur = nested_dict
    path_list.append(key)
    for path_item in path_list[:-1]:
        try:
            cur = cur[path_item]
        except KeyError:
            cur = cur[path_item] = {}

    cur[path_list[-1]] = value
    return nested_dict


def update_nested_dict(nested_dict, findkey, updatekey, updateval):
    ''' finds and updates values in nested dicts with find_in_dict(), set_nested_value()'''
    return set_nested_value(
        nested_dict,
        list(find_in_obj(nested_dict, findkey))[0],
        updatekey,
        updateval
    )

def recursive_lookup(k, d):
    if k in d:
        return d[k]
    for v in d.values():
        if isinstance(v, dict):
            return recursive_lookup(k, v)
    return None

# End of Helper Functions

def run_module():
    module_args = dict(
        json        =   dict(type='dict', required=True),
        parent      =   dict(type='str',  required=True),
        key         =   dict(type='str',  required=True),
        value       =   dict(type='str',  required=True)
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        verify = recursive_lookup( module.params['key'], module.params['json'])
        if verify:
            result['msg'] = "value would have been modified"

        result['json'] = module.params['json']

    verify = recursive_lookup( module.params['key'], module.params['json'])
    if verify:
        json_dict = update_nested_dict(
            module.params['json'],
            module.params['parent'],
            module.params['key'],
            module.params['value']
        )
        result['changed'] = True
        result['json'] = json_dict
        result['verify'] = verify
    else:
        result['json'] = module.params['json']

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()