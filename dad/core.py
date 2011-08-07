# -*- coding: utf-8 -*-
#http://www.foxhop.net/django-virtualenv-apache-mod_wsgi

import os, sys

from dad.utils import get_config, get_stage, yes_no_prompt

DEBUG = True

class Project():

    def __init__(self, projectname=False):
        from fabric.state import env

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
        Update project requirements
        """
        print "Updating requirements for %s" % self.project_name
        self._fab('update_requirements -R %s' % to)

    
    def deploy(self, to='demo'):
        """
        Deploy a site to a remote server
        """
        self._fab('deploy -R %s' % to)
   

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
        """

        if not self.project_name:
            sys.stderr.write("Error: please provide a project name.\n")
            sys.exit(0)

        self._fab('setupdev:%s' % self.project_name)


    def dev(self):
        """
        Enter development environment, creates virtualenv if it doesn't exists
        """
        
        self._fab('activate_dev -R dev')

        # This wont work from within favbric
        os.system('/bin/bash --rcfile dad/dev.sh')


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
