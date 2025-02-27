#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: insights_register
short_description: This module registers the insights client
description: >
  This module will check the current registration status, unregister if needed,
  and then register the insights client (and update the display_name if needed)

options:
  state:
    description: >
      Determines whether to register or unregister insights-client
    choices: [ present, absent ]
    default: present
    type: str
  insights_name:
    description: >
      For now, this is just 'insights-client', but it could change in the future
      so having it as a variable is just preparing for that
    default: 'insights-client'
    required: false
    type: str
  display_name:
    description: >
      This option is here to enable registering with a display_name outside of using
      a configuration file. Some may be used to doing it this way so I left this in as
      an optional parameter.
    required: false
    type: str
  force_reregister:
    description: >
      This option should be set to true if you wish to force a reregister of the insights-client.
      Note that this will remove the existing machine-id and create a new one. Only use this option
      if you are okay with creating a new machine-id.
    default: false
    required: false
    type: bool

author:
    - Jason Stephens (@Jason-RH)
'''

EXAMPLES = '''
# Normal registration
- name: Register the insights client
  insights_register:
    state: present
  become: true

# Force a registration (for config changes, etc)
- name: Re-register the insights client
  insights_register:
    state: present
    force_reregister: true
  become: true

# Unregistration
- name: Unregister the insights client
  insights_register:
    state: absent
  become: true
'''

RETURN = '''
original_message:
    description: Just a sentence declaring that there is a registration attempt
    type: str
    returned: always
message:
    description: The output message that the module generates
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
from subprocess import PIPE, Popen


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        insights_name=dict(type='str', required=False, default='insights-client'),
        display_name=dict(type='str', required=False, default=None),
        force_reregister=dict(type='bool', required=False, default=False)
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    state = module.params['state']
    insights_name = module.params['insights_name']
    display_name = module.params['display_name']
    force_reregister = module.params['force_reregister']

    command = [insights_name, '--status']

    result_command = Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout = result_command.communicate()[0]
    reg_status = result_command.returncode
    register_args = [insights_name]

    if state == 'present':
        result['original_message'] = 'Attempting to register ' + insights_name
        if reg_status == 0 and 'unregistered' not in stdout:
            if force_reregister:
                subprocess.call(register_args, '--unregister')
            else:
                result['changed'] = False
                result['message'] = 'The Insights API has determined that this machine is already registered'
                module.exit_json(**result)
        if display_name:
            register_args.extend(['--display-name', display_name])
        register_args.extend('--register')
        subprocess.call(register_args)
        result['changed'] = True
        if force_reregister:
            result['message'] = 'New machine-id created - ' + insights_name + ' has been registered'
        else:
            result['message'] = insights_name + ' has been registered'
        module.exit_json(**result)

    if state == 'absent':
        result['original_message'] = 'Attempting to unregister ' + insights_name
        if reg_status != 0:
            result['changed'] = False
            result['message'] = insights_name + ' is already unregistered'
            module.exit_json(**result)
        else:
            register_args.extend(['--unregister'])
            subprocess.call(register_args)
            result['changed'] = True
            result['message'] = insights_name + ' has been unregistered'
            module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
