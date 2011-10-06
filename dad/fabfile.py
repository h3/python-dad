import os, sys

from fabric.api import *
from fabric.contrib.project import rsync_project
from fabric.contrib import files, console, django
from fabric.utils import abort, warn
from fabric.decorators import hosts
from fabric.network import interpret_host_string
from fabric.operations import put, get

from dad.utils import get_config, yes_no_prompt
from dad.sysdef import get_sysdef_paths, load_sysdef, get_sysdef_list, get_sysdef

STAGES = ['dev', 'demo', 'beta', 'prod']

RSYNC_EXCLUDE = (
    '.DS_Store',
    '.hg',
    '*.pyc',
    '*.example',
    'Thumbs.db',
    '.svn',
    'media/admin',
    'media/cache',
    'media/uploads',
    'settings_dev.py',
)

output['debug'] = True

env.base_path = os.getcwd()
if os.path.exists(os.path.join(env.base_path, 'manage.py')):
    env.base_path = os.path.abspath(os.path.join(env.base_path, '../'))

env.dadconf_path    = os.path.join(env.base_path, 'dad/')
env.apacheconf_path = os.path.join(env.base_path, 'apache/')
env.dad_path        = os.path.dirname(__file__)
env.tpl_path        = os.path.join(env.dad_path, 'templates/')
env.conf            = get_config(env.dadconf_path)


if env.conf:
    for role in env.conf['roles']:
        env.roledefs[role['name']] = role['hosts']


def clear_virtualenv():
    """ 
    delete any previous install of this virtualenv and start from scratch 
    """
    _setup_env()
    cmd = 'virtualenv --clear %(venv_path)s' % env
    if env.role == 'dev':
        local(cmd)
    else:
        sudo(cmd)


def freeze_requirements():
    """ 
    freeze external dependencies on remote host 
    """
    _setup_env()
    require('requirements', provided_by=STAGES)
    with cd(env.venv_path):
        if console.confirm("Are you sure you want to overrite %(requirements)s ?" % env, default=True):
            cmd = env.venv_activate +' && pip -E %(venv_path)s freeze > %(requirements)s' % env
            if env.is_dev:
                local(cmd)
            else:
                sudo(cmd)


def update_requirements():
    """ 
    update external dependencies on remote host 
    """
    _setup_env()
    require('requirements', provided_by=STAGES)
    requirements_list = [env.role, 'base']
    with cd(env.venv_path):
        for stage in requirements_list:
            if stage in env.requirements:
                cmd =  ['pip install']
                cmd += ['-E %(venv_path)s' % env]
                cmd += ['--requirement %s' % env.requirements[stage]]

                do = sudo
                if env.is_dev:
                    do = local

                do(' '.join(cmd))

    if env.is_dev:
        symlink_virtualenv_src()


def setup_dev():
    """
    Activates the development environment. These actions are performed:

     * Create a virtualenv if it doesn't already exists
     * Create bootstrap script if it doesn't already exists

    """
    _setup_env()
    print "Starting dev environment for %s" % env.project_name
    bootstrap_path = os.path.join(env.dadconf_path, 'dev.sh')
    if not os.path.exists(env.venv_path):
        setup_virtualenv()
    else:
        if not os.path.exists(bootstrap_path):
            if yes_no_prompt("A virtualenv with the same name has been found, \
would you like to use this one ? Otherwise it will be deleted and recreated.", True):
                _create_dev_bootstrap(env.venv_path, env.venv_name)
            else:
                local("rm -rf %s" % os.path.join(env.venv_path, env.venv_name))
                setup_virtualenv()


def install(project_name):
    print "Installing dad for %s" % project_name
    env.project_name = project_name

    # Copy templates
    if os.path.exists(env.apacheconf_path):
        warn("Warning: apache config directory already exists, skipping.\n")
    else:
        local('mkdir %s' % env.apacheconf_path)
        local('cp %s %s' % (_get_template('apache/example.conf'), env.apacheconf_path))
        local('cp %s %s' % (_get_template('apache/prod.conf'), env.apacheconf_path))
        local('cp %s %s' % (_get_template('apache/demo.conf'), env.apacheconf_path))
        local('cp %s %s' % (_get_template('apache/demo.wsgi'), env.apacheconf_path))
        local('cp %s %s' % (_get_template('apache/prod.wsgi'), env.apacheconf_path))

    if os.path.exists(env.dadconf_path):
        warn("Warning: dad config directory already exists, skipping.\n")
    else:
        local('mkdir %s' % env.dadconf_path)
        # requirements.txt
        local('cp %s %s' % (_get_template('requirements.txt'), env.dadconf_path))
        for stage in STAGES:
            req = _get_template('requirements_%s.txt' % stage)
            if files.exists(req):
                local('cp %s %s' % (req, env.dadconf_path))

        _template(_get_template('project.yml'), os.path.join(env.dadconf_path, 'project.yml'), {
            'project_name': project_name,
        })
    
    for stage in STAGES:
        dest = os.path.join(os.path.join(env.base_path, project_name), 'settings_%s.py' % stage)
        src  = _get_template_path('settings_%s.py' % stage)
        if not os.path.exists(dest):
            _template(src, dest, { 'project_name': project_name })


def configure_site():
    require('role', provided_by=STAGES)
    _setup_env()
    set_permissions()

    use_sudo = env.is_dev and False or True

    if not files.exists(env.venv_path, use_sudo=use_sudo):
        setup_virtualenv()

    update_requirements()
    django_symlink_media()
    django_collect_static()
    django_syncdb()
    apache_configure()
    apache_graceful()


def save_state():
    """
    Saves the state of a remote stage for rollback
    """
    #require('role', provided_by=STAGES)
    _setup_env()

    if env.role == 'dev':
        abort('This command only works on remote stages (%s)' % ', '.join(STAGES[1:]))

    # copy vhost src
    sudo("tar -pczf /tmp/rollback.tar.gz --exclude='rollback.tar.gz' %s" % env.stage['path'])
    sudo('mv /tmp/rollback.tar.gz %s' % env.stage['path'])

   
def rollback():
    require('role', provided_by=STAGES)
    _setup_env()

    if env.is_dev:
        abort('This comman only works on remote stages (%s)' % ', '.join(STAGES))
    
    rb_path = '%srollback.tar.gz %s' % env.stage['path']
    if not files.exists(rb_path):
        abort('Rollback file not found (%s)' % rb_path)

    sudo('mv %s %s' % (rb_path, env.stage['path']))

    configure_site()


def push_uploads(dest):
    _setup_env()
    require('venv_root', provided_by=('demo', 'prod'))
    extra_opts = ['--omit-dir-times']

    if env.is_dev:
        use_sudo = False
        do = run
    else:
        use_sudo = True
        do = sudo

    if env.role == 'prod':
        if not console.confirm('Are you sure you want to move %s uploads from %s to production?' % (env.project_name, env.role), default=False):
            abort('Production deployment aborted.')

    src_path = os.path.join(env.base_path.endswith('/') and env.base_path or '%s/' % env.base_path, env.project_name, 'media/uploads/')
    dest_path = os.path.join(env.stage['path'], env.project_name, 'media/')

    # Set permission so we can upload

    sudo('chown -R %s %s' % (env.user, env.stage['path']))

    do('chmod 777 -R %s' % dest_path)

    if not files.exists(os.path.join(dest_path, 'uploads')):
        do('mkdir -p %s' % os.path.join(dest_path, 'uploads'))
    
    do('chown -R %s %s' % (env.user, os.path.join(dest_path)))

    if console.confirm('Delete out of sync files ? (WARNING: permanent !)', default=False):
        delete = True
    else:
        delete = False

    rsync_project(os.path.join(dest_path, 'uploads'),
        local_dir   = src_path,
        exclude     = ('.DS_Store', '.hg', '*.pyc', '*.example', 'Thumbs.db', '.svn',),
        delete      = delete,
        extra_opts  = " ".join(extra_opts),
    )
    do('chown -R %s %s' % (env.user, os.path.join(dest_path)))
    do('chmod 777 -R %s' % os.path.join(dest_path))


def push():
    """ 
    deploy project to remote host 
    750     rwxr-x---       "u=rwx,g=rx,a="
    755     -rwxr-xr-x      "u=rwx,g=rx,o=rx" ?
    777     -rwxrwxrwx      "u=rwx,g=rwx,o=rwx"
    """
    _setup_env()
    require('venv_root', provided_by=('demo', 'prod'))
    extra_opts = ['--omit-dir-times']

    if env.is_dev:
        use_sudo = False
        do = run
    else:
        use_sudo = True
        do = sudo

    if env.role == 'prod':
        if not console.confirm('Are you sure you want to deploy %s to production?' % env.project_name, default=False):
            abort('Production deployment aborted.')

    dest_path = env.base_path.endswith('/') and env.base_path or '%s/' % env.base_path

    if not files.exists(env.stage['path']):
        sudo('mkdir -p %s' % env.stage['path'])
    
    # Set permission so we can upload
    sudo('chmod 777 -R %s' % env.stage['path'])
    sudo('chown -R %s %s' % (env.user, env.stage['path']))

    rsync_project(
        env.stage['path'],
        local_dir=dest_path,
        exclude=RSYNC_EXCLUDE,
        delete=True,
        extra_opts=" ".join(extra_opts),
    )

    configure_site()


def set_permissions():
    _setup_env()
    do = env.is_dev and run or sudo
    
    sudo('chmod %s -R %s' % ('chmod' in env.stage and env.stage['chmod'] or '755', env.stage['path']))
    if 'user' in env.stage and 'group' in env.stage:
        do("chown -R %s:%s %s" % (env.stage['user'], env.stage['group'], env.stage['path']))
    elif 'user' in env.stage:
        do("chown -R %s %s" % (env.stage['user'], env.stage['path']))
        
    do("chmod -R 777 %s" % os.path.join(env.stage['path'], env.project_name, 'media'))


def django_syncdb():
    """ 
    Synchronize/create database on remote host 
    """
    _setup_env()
    sys.path.append(env.base_path)
    django.settings_module('%(project_name)s.settings_%(role)s' % env)
    settings = __import__('%(project_name)s.settings_%(role)s' % env)
    
    # Not sure what's going on here .. but it fixes a problem..
    if getattr(settings, 'settings_%(role)s' % env, False):
        settings = getattr(settings, 'settings_%(role)s' % env, False)

    dbconf = settings.DATABASES['default']

    if dbconf['ENGINE'].endswith('mysql'):
        _create_mysqldb(dbconf)
    # Give apache write permission to the project directory
    elif dbconf['ENGINE'].endswith('sqlite3') and env.role != 'dev':
        user = 'user' in env.stage and env.stage['user'] or 'www-data'
        sudo('chown -R %s %s' % (user, os.path.dirname(dbconf['NAME'])))
        sudo('chmod 777 %s' % dbconf['NAME'])
        

    if env.role in ['prod', 'demo']:
        path = env.stage['path']
        do = run
    else:
        path = env.base_path
        do = local

    if (yes_no_prompt("Do you want to syncdb ?")):
        with(cd(os.path.join(path, env.project_name))):
            do(env.venv_activate +' && %s manage.py syncdb --noinput --settings=settings_%s' % (env.venv_python, env.role))


def symlink_virtualenv_src():
    """
    Creates a symlink that points to the src directory of the virtualenv
    for development purpose. This commands should only be issued for the dev stage.
    """
    _setup_env()
    src  = "%(venv_path)s/src" % env
    dest = os.path.join(env.base_path, 'src')
    if env.is_dev and not os.path.exists(dest) and os.path.exists(src):
        local("ln -s %s %s" % (src, dest))


def setup_virtualenv():
    """ 
    Setup virtualenv on remote host 
    """
    _setup_env()
    if env.is_dev:
        do = local
        _create_dev_bootstrap(env.venv_path, env.venv_name)
    else:
        do = sudo 

    do("mkdir -p %(venv_path)s && chown -R %(user)s %(venv_path)s" % env)

    with cd(env.venv_root):
        do("cd %(venv_root)s && virtualenv %(venv_no_site_packages)s %(venv_distribute)s %(venv_name)s" % env)

    update_requirements()
    
    if 'user' in env.stage and not env.is_dev:
        sudo("chown -R %s %s" % (env.stage['user'], env.venv_root))


def django_symlink_media():
    """ 
    create symbolic link so Apache can serve django admin media 
    """
    _setup_env()
    if not env.is_dev:
        path = os.path.join(env.stage['path'], env.project_name, 'media/')
        if not files.exists(os.path.join(env.stage['path'], 'media/'), use_sudo=True):
            sudo('ln -sf %s %s' % (path, env.stage['path']))


def django_collect_static():
    """ 
    create symbolic link so Apache can serve django admin media 
    """
    _setup_env()
    if env.is_dev:
        path = env.base_path
        do = local
    else:
        path = env.stage['path']
        do = sudo
    with(cd(os.path.join(path, env.project_name))):
        sudo(env.venv_activate +' && python manage.py collectstatic --link --noinput')

def apache_graceful():
    """ 
    Perform a Apache graceful restart 
    """
    _setup_env()
    sudo(env.sysdef['graceful'] % {'servername': env.stage['servername']})


def apache_configure():
    """
    Configure a remote apache server
    """
    _setup_env()
    servername = env.stage['servername']
    tpl = 'apache/%(role)s.conf' % env
    src = os.path.join(env.stage['path'], tpl)
    if env.role == 'dev':
        use_sudo = False
    else:
        use_sudo = True

    if files.exists(src, use_sudo=use_sudo):
        ctx = {}
        dest_path = env.sysdef['vhosts'] % {'servername': servername}

        if 'error_logs' in env.sysdef:
            ctx['error_logs'] = env.sysdef['error_logs'] % {'servername': servername}
        
        if 'access_logs' in env.sysdef:
            ctx['access_logs'] = env.sysdef['access_logs'] % {'servername': servername}

        if 'user' in env.stage:
            ctx['user'] = env.stage['user']
        else:
            ctx['user'] = env.user

        if 'group' in env.stage:
            ctx['group'] = env.stage['group']
        else:
            ctx['group'] = 'www-data'

        ctx['media_path']    = os.path.join(env.stage['path'], 'media/')
        ctx['static_path']   = os.path.join(env.stage['path'], 'static/')
        ctx['project_name']  = env.project_name
        ctx['project_path']  = env.project_path
        ctx['server_name']   = servername
        ctx['server_admin']  = env.stage['serveradmin']
        ctx['document_root'] = env.stage['path']

        get(os.path.join(env.stage['path'], tpl), '/tmp/test')
        files.upload_template(tpl, dest_path, context=ctx, use_sudo=use_sudo, backup=False)
    
    else:
        warn("Warning %s not found." % src)

# Special case because it is run as library
def manage(role, **kwargs):
    _setup_env()
    if env.is_dev:
        path = env.project_path
        do = local
    else:
        path = os.path.join(_get_stage_conf(role)['path'], env.conf['project']['name'])
        do = sudo

    with(cd(path)):
        print do(env.venv_activate +' && %s manage.py %s' % (env.venv_python, kwargs['arguments']))


def move_data(src, dest, data=''):
    """ 
    move database data with dumpdata & loaddata
    """
    _setup_env()
    filename = '%s_%s_%s.json' % (os.path.join('/tmp/', env.project_name), data, env.role)
    dump_data(data, filename)

    dest_file = os.path.join('/tmp/', os.path.basename(filename))
    if not env.is_dev:
        get(os.path.join(env.stage['path'], tpl), dest_file)

        upload_file(dest_file, dest)
        # 'file': fn, 'src': src, 'dest': dest }, roles='', hosts='', user=False, run=False))

   #load_data(fn) 
        # 'file': fn, 'dest': dest}, roles='', hosts='', user=False, run=False))


def dump_data(data='', filename=False):
    """ 
    dumps database data with dumpdata
    """
    # TODO: use concurrency safe temp file
    print "DUMPING: %s to %s" % (data, filename)
    if env.is_dev:
        path = env.base_path
        do = local
    else:
        path = env.stage['path']
        do = sudo

    do('cd %s && %s && python manage.py dumpdata %s --settings=settings_%s > %s ' % (
        os.path.join(path, env.project_name), env.venv_activate, data, env.role, filename))

   #if env.is_dev:
   #    do('cd %s' % path)


def load_data(filename):
    """ 
    loads databse data with loaddata
    """
    _setup_env()
    if env.role in ['prod', 'demo']:
        path = env.stage['path']
        do = sudo
    else:
        path = env.base_path
        do = local
    with(cd(os.path.join(path, env.project_name))):
        do('cd %s && %s && python manage.py loaddata %s' % (
            os.path.join(path, env.project_name),
            env.venv_activate,
            filename,
        ))


def upload_file(filename, dest):
    """ 
    Upload a file to a given destination stage
    """
    _setup_env()
    dest_stage = _get_stage_conf(dest)
    # From dev to prod or demo
    if env.is_dev:
        src = filename
        with(cd('/tmp/')):
            put(src, os.path.join(dest_stage['path'], env.project_name))

# Private methods ---

def _setup_env():
    """
    Setup envorinment variables
    """
    for roledef in env.roledefs:
        if env.host_string in env.roledefs[roledef]:
            env.role = roledef
            setattr(env, 'is_%s' % roledef, True)
        else:
            setattr(env, 'is_%s' % roledef, False)

    if not hasattr(env, 'role'):
        env.role  = 'dev'

    env.stage           = _get_stage_conf(env.role)
    env.project_name    = _get_project_name()
    env.project_path    = os.path.join(env.base_path, env.project_name)
    env.venv_name       = '%s-env' % env.project_name
    env.venv_root       = os.path.join(os.path.expanduser(env.stage['virtualenv']), 'py/')
    env.venv_path       = os.path.join(env.venv_root, env.venv_name)
    env.venv_activate   = '. %s' % os.path.join(env.venv_path, 'bin/activate')
    env.venv_python     = os.path.join(env.venv_path, 'bin/python')
    env.requirements    = {}
    
    if env.is_dev:
        env.requirements_base_path = os.path.join(env.dadconf_path)
    else:
        env.requirements_base_path = os.path.join(env.stage['path'], 'dad/')
        
    env.requirements['base'] = os.path.join(env.requirements_base_path, 'requirements.txt')
   #for stage in STAGES:
   #    rp = os.path.join(env.dadconf_path, 'requirements_%s.txt' % stage)
   #    if os.path.exists(rp):
   #        env.requirements[stage] = rp

    if not env.project_name:
        abort("Cannot determine project name.. does dad/project.yml exists ?")

    if env.role != 'dev':
        if 'sysdef' in env.stage:
            osname, version, t = env.stage['sysdef']
            env.sysdef = get_sysdef(osname, version, t)
        else:
            # TODO: NOT FUNCTIONAL YET !
            env.sysdef = discover_system(True)   

    if 'no_site_packages' in env.stage and env.stage['no_site_packages'] == 'false':
        env.venv_no_site_packages = ''
    else:
        print "USING: --no-site-packages"
        env.venv_no_site_packages = '--no-site-packages'

    if 'setuptools' in env.stage and env.stage['setuptools'] == 'true':
        env.venv_distribute = ''
    else:
        env.venv_distribute = '--distribute'


def _get_template(tpl):
    local_path = os.path.join(os.path.expanduser('~/.python-dad/templates/'), tpl)
    global_path = os.path.join(env.tpl_path, tpl)
    if os.path.exists(local_path):
        return local_path
    else:
        return global_path
    

def _get_project_name():
    """
    Returns the curren project name
    """
    try:
        return env.conf['project']['name']
    except:
        return False


def _get_stage_conf(stage):
    """
    Get configurations for a given stage
    """
    if env.conf:
        for role in env.conf['roles']:
            if role['name'] == stage:
                return role
    return False


def _create_mysqldb(dbconf):
    """
    Create the database if it doesn't exists
    """
    _setup_env()
    cmd = ['mysql']
    if not 'plesk' in env.sysdef['type']:
        if 'USER' in dbconf:
            cmd.append('-u %s' % dbconf['USER'])
        if 'PASSWORD' in dbconf:
            cmd.append('--password=%s' % dbconf['PASSWORD'])
        if 'HOST' in dbconf:
            cmd.append('-h %s' % dbconf['HOST'])
        cmd.append("-e 'CREATE DATABASE IF NOT EXISTS %s;'" % dbconf['NAME'])

        if env.role == 'dev':
            local(" ".join(cmd))
        else:
            run(" ".join(cmd))
    else:
        print "Skipping database creation since this is a plesk managed server."


def _create_dev_bootstrap(env_path, env_name):
    """
    Create the bootstrap bash script that wraps
    virtualenv activate
    """
    _template(_get_template('dev.sh'), os.path.join(env.dadconf_path, 'dev.sh'), {
        'env_path': env.venv_path,
        'activate_path': env.venv_activate,
        'project_name': env.project_name,
    })


def _template(src, dest, variables):
    """
    Opens src file, read its content, inject variables in it and
    write the output to destination. Works only with local files!
    """
    fs = open(src, 'r')
    fd = open(dest, 'w+')
    buff = fs.read()
    fd.write(buff % variables)
    fd.close()
    fs.close()


def _get_template_path(path):
    return os.path.join(env.tpl_path, path)


import commands, re

def _tests_match(tests):
    if len(tests) > 2:
        for test in tests:
            rs = _test_version(test)
            if rs: 
                return rs
    else:
        _setup_env()
        if env.role == 'dev':
            output = commands.getoutput(tests[0])
        else:
            output = run(tests[0])
        rs = re.match(re.compile(tests[1]), output)
        if rs:
            return rs
    return False

def _test_servers(servers):
    for server in servers:
        if _tests_match(server['discover']):
            return server
    return False


def _test_versions(versions):
    for version in versions:
        if _test_servers(version['servers']):
            return version
    return False


def _test_os(sysdef):
# if _tests_match(discover..)
    v = _test_versions(sysdef['versions'])
    print v


def discover_system(output_obj=False):
    for path in get_sysdef_paths():
        sysdefs = get_sysdef_list(path)
        for sysdef in sysdefs:
            sd = load_sysdef(sysdef['path'])
            rs = _test_os(sd)
            if rs:
                if output_obj:
                    return '%s %s (%s)' % (sysdef['name'], rs['version'])
                else:
                    return rs
    return False

# Future fabric version ..
#from fabric.operations import open_shell
#
#def setup_keyless_ssh():
#    _setup_env()
#    open_shell(command='ssh-keygen -t dsa')
#    put('~/.ssh/id_dsa.pub', '~')
#    if files.exists('~/.ssh/authorized_keys2'):
#        run('cat ~/id_dsa.pub >> ~/.ssh/authorized_keys2')
#        run('chmod 600 ~/.ssh/authorized_keys2')
#    elif files.exists('~/.ssh2/authorized_keys2'):
#        run('cat ~/id_dsa.pub >> ~/.ssh2/authorized_keys2')
#        run('chmod 600 ~/.ssh2/authorized_keys2')
#    elif files.exists('~/.ssh/authorized_keys'):
#        run('cat ~/id_dsa.pub >> ~/.ssh/authorized_keys')
#        run('chmod 600 ~/.ssh/authorized_keys')
#    else: 
#        abort('Error: authorized_keys not found on remote server.')
#    run('rm -f ~/id_dsa.pub')
        


# References ..

#
#def staging():
#    """ use staging environment on remote host"""
#    env.user = 'caktus'
#    env.environment = 'staging'
#    env.hosts = ['173.203.208.254']
#    _setup_path()
#
#
#def update_apache_conf():
#    """ upload apache configuration to remote host """
#    require('root', provided_by=('staging', 'production'))
#    source = os.path.join('apache', '%(environment)s.conf' % env)
#    dest = os.path.join(env.home, 'apache.conf.d')
#    put(source, dest, mode=0755)
#    apache_reload()
#
#
#def configtest():    
#    """ test Apache configuration """
#    require('root', provided_by=('staging', 'production'))
#    run('apache2ctl configtest')
#
#
#def apache_reload():    
#    """ reload Apache on remote host """
#    require('root', provided_by=('staging', 'production'))
#    run('sudo /etc/init.d/apache2 reload')
#
#
#def reset_local_media():
#    """ Reset local media from remote host """
#    require('root', provided_by=('staging', 'production'))
#    media = os.path.join(env.code_root, 'media', 'upload')
#    local('rsync -rvaz %s@%s:%s media/' % (env.user, env.hosts[0], media))
