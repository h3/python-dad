import os, sys, site, yaml

STAGE = 'demo'

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

new_site_dir = os.path.join(get_stage(STAGE, conf)['virtualenv'], 'py/', '%s-env' % conf['project']['name'], 'lib/python2.6/site-packages/')
old_site_dir = list(sys.path)

site.addsitedir(new_site_dir)

if path not in sys.path:
    sys.path.append(path)
    sys.path.append(os.path.join(path, conf['project']['name']))
    contrib = os.path.join(path, 'contrib/')
    if os.path.exists(contrib):
        sys.path.append(contrib)

# reorder sys.path so new directories from the addsitedir show up first
site_dir = [p for p in sys.path if p not in old_site_dir]
for item in site_dir:
    sys.path.remove(item)
sys.path[:0] = site_dir

import django.core.handlers.wsgi
os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings_%s' % (conf['project']['name'], STAGE)
application = django.core.handlers.wsgi.WSGIHandler()

