# -*- coding: utf-8 -*-
#http://www.foxhop.net/django-virtualenv-apache-mod_wsgi

import os, sys


from fabric.api import settings
from dad.utils import get_config, get_stage, yes_no_prompt
from dad.fabfile import _setup_env, _get_stage_conf, manage, env

from fabric.contrib import console


DEBUG = True

class Project():

    def __init__(self, projectname=False):

        self.base_path       = os.getcwd()
        self.dadconf_path    = os.path.join(self.base_path, 'dad/')
        self.conf            = get_config(self.dadconf_path)
        self.project_name    = self._get_project_name(projectname)

        if self.project_name:
            self.project_path = os.path.join(self.base_path, self.project_name)

            if not os.path.exists(self.project_path):
                sys.stderr.write("Error: %s doesn't exist in %s.\n" % (self.project_name, self.base_path))
                sys.exit(0)


    def update(self, to='dev'):
        """
        Update pip requirements on a given stage

        >>> dad-admin.py -u dev
        """
        self._fab('update_requirements -R %s' % to)

    
    def freeze(self, to='dev'):
        """
        Freeze the requirements for a given stage

        >>> dad-admin.py -f dev
        """
        self._fab('freeze_requirements -R %s' % to)
    

    def clear(self, to='dev'):
        """
        Clear the virtualenv on a given stage

        >>> dad-admin.py -c dev
        """
        self._fab('clear_virtualenv -R %s' % to)

    
    def push(self, to='demo'):
        """
        Deploy the project on a given stage

        >>> dad-admin.py -p dev
        """
        self._fab('push -R %s' % to)
   

    def move_data(self, src='dev', dest='demo'):
        """
        Move database data from one stage to another
        """
        fn = '/tmp/%s.json' % env.project_name
        cmd = []
        cmd.append(self._fab('dump_data:%(file)s -R %(src)s' % { 
            'file': fn, 'src': src }, roles='', hosts='', user=False, run=False))

        cmd.append(self._fab('upload_file:%(file)s,%(dest)s -R %(src)s' % { 
            'file': fn, 'src': src, 'dest': dest }, roles='', hosts='', user=False, run=False))

        cmd.append(self._fab('load_data:%(file)s -R %(dest)s' % { 
            'file': fn, 'dest': dest}, roles='', hosts='', user=False, run=False))

        os.system(' && '.join(cmd))
    
    
    def _fab(self, tasks, roles='', hosts='', user=False, run=True):
        if isinstance(tasks, list):
            tasks = ' '.join(tasks)

        if isinstance(roles, list):
            roles = ' -R %s' % ','.join(roles)

        if isinstance(hosts, list):
            hosts = ' -H %s' % ','.join(hosts)
        if user:
            user = '-u %s' % user

        cmd = "fab%(fabfile)s%(tasks)s%(roles)s%(hosts)s%(user)s" % {
            'fabfile': ' -f %s ' % os.path.join(os.path.dirname(__file__), 'fabfile.py'), 
            'tasks': tasks,
            'roles': roles,
            'hosts': hosts,
            'user': hosts,
        }

        if run:
            os.system(cmd)
        else:
            return cmd


    def setupdev(self):
        """
        Setup development environment. Copies template files and create dad/ directory.
        
        >>> dad-admin.py -i projectname/
        """

        if not self.project_name:
            sys.stderr.write("Error: please provide a project name.\n")
            sys.exit(0)

        self._fab('setupdev:%s' % self.project_name)

    
    def create_local_templates(self):
        """ 
        create local templates which override default templates
        
        >>> dad-admin.py -t
        """
        tpl_path = os.path.join(os.path.dirname(__file__), 'templates/')
        if not os.path.exists(os.path.expanduser('~/.python-dad/templates/')) or console.confirm("Local template already exists, do you want to overrite ?", False):
            os.system('cp -rf %s ~/.python-dad/' % tpl_path)


    def dev(self):
        """
        Enter development environment, creates virtualenv if it doesn't exists
        
        >>> dad-admin.py -d
        """
        
        self._fab('activate_dev -R dev')

        # This wont work from within favbric
        os.system('/bin/bash --rcfile dad/dev.sh')


    def apache(self, role, cmd):
        self._fab('apache_%s -R %s' % (cmd, role))


    def manage(self, role, args):
        """
        Execute the python.manage.py command on a remote host.

        Argument prefix must be replaced with "+"

        >>> dad-admin.py -m syncdb ++settings=settings_dev
        """
        _setup_env()
        
        for host in _get_stage_conf(role)['hosts']:
            with settings(host_string=host):
                manage(role, arguments=args)
        
#   Requires a newer version of fabric .. because it uses "open_shell"
#   def ssh_keyless_auth(self, to='demo'):
#       """
#       Setup SSH key based authentication on a stage
#       """
#       self._fab('setup_keyless_ssh -R %s' % to)

    
    def _get_project_name(self, projectname=False):
        if projectname:
            return projectname
        else:
            try:
                return self.conf['project']['name']
            except:
                return False
