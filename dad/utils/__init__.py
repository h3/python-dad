# -*- coding: utf-8 -*-
import os, sys, yaml


def get_config(path):
    f = os.path.join(path, 'project.yml') 
    try:
        return yaml.load(file(f, 'r'))
    except IOError, e:
        return False
    except yaml.YAMLError, e:
        print "Error: Could not parse configuration file:", e


def yes_no_prompt(message, default=False):

    if default:
        yn = "[Y/n]"
    else:
        yn = "[y/N]"

    rs = raw_input('%s %s: ' % (message, yn))

    if rs == '':
        return default

    elif rs not in ['y','yes','n', 'no']:
        return yes_no_prompt(message, default)

    else:
        return rs in ['y', 'yes']


def get_server_type():
    if files.exists('/etc/'):
        out = 'linux'
        if files.exists('/etc/lsb-release'):
            out = 'ubuntu'
        elif files.exists('/etc/redhat-release'):
            out = 'redhat'
            if files.exists('/usr/local/psa/admin/sbin/websrvmng'):
                out = 'redhat+plesk'
    else:
        out = 'unknown'
    return out 


from fabric.state import env
def get_stage(stage, conf=False):
#   if not conf:
#       conf = get_config()
    if conf:
        for role in conf['roles']:
            if role['name'] == stage:
                return role

    return False
