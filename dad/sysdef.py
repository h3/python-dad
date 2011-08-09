import os, yaml

DAD_PATH = os.path.dirname(__file__)

def load_sysdef(path):
    f = os.path.join(path) 
    try:
        return yaml.load(file(f, 'r'))
    except IOError, e:
        return False
    except yaml.YAMLError, e:
        print "Error: Could not parse sysdef file:", e


def get_sysdef_paths():
    paths = []
    local_path = os.path.join(os.getcwd(), 'dad/sysdefs/')
    # local path takes precedence on default path
    if os.path.exists(local_path):
        paths.append(local_path)
    paths.append(os.path.join(DAD_PATH, 'sysdefs/'))
    return paths


def get_sysdef_list(path):
    dirs = os.listdir(path)
    out = []
    for fname in dirs:
        if fname.endswith('.yml'):
            out.append({
                'name': fname.replace('.yml',''),
                'path': os.path.join(path, fname),
            })
    return out


def get_sysdef(osname, version, t):
    paths = get_sysdef_paths()
    server = False
    for path in paths:
        p = os.path.join(path, '%s.yml' % osname.lower())
        if os.path.exists(p):
            sysdef = load_sysdef(p)
            break
    if sysdef:
        for v in sysdef['versions']:
            if version in v['versions']:
                sysdefversion = v
                break
    if sysdefversion:
        for server in sysdefversion['servers']:
            if t == server['type']:
                out = server
    if out:
        return out
    else:
        return False

