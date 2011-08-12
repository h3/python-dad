import os, sys, site, yaml

STAGE = 'prod'

def get_config(path):
    f = os.path.join(path, 'project.yml') 
    try:
        return yaml.load(file(f, 'r'))
    except IOError, e:
        return False
    except yaml.YAMLError, e:
        print "Error: Could not parse configuration file:", e

def get_stage(stage, conf=False):
    for role in conf['roles']:
        if role['name'] == stage:
            return role

path = os.path.dirname(os.path.abspath(os.path.join(__file__, '../')))
conf = get_config(os.path.join(path, 'dad/'))

# http://code.google.com/p/modwsgi/wiki/VirtualEnvironments
# Remember original sys.path.
prev_sys_path = list(sys.path) 

# Add site-packages directory.
for version in ['2.5', '2.6', '2.7']:
    new_site_dir = os.path.join(get_stage(STAGE, conf)['virtualenv'], 'py/', '%s-env' % conf['project']['name'], 'lib/python%s/site-packages/' % version)
    if os.path.exists(new_site_dir):
        site.addsitedir(new_site_dir)
        break

# Add project's paths
if path not in sys.path:
    sys.path.append(path)
    sys.path.append(os.path.join(path, conf['project']['name']))
    contrib = os.path.join(path, 'contrib/')
    if os.path.exists(contrib):
        sys.path.append(contrib)

# Reorder sys.path so new directories at the front.
new_sys_path = []  
for item in list(sys.path): 
    if item not in prev_sys_path: 
        new_sys_path.append(item) 
        sys.path.remove(item) 
sys.path[:0] = new_sys_path 

import django.core.handlers.wsgi
os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings_%s' % (conf['project']['name'], STAGE)
application = django.core.handlers.wsgi.WSGIHandler()

