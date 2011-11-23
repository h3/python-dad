#!/usr/bin/env python

import sys, os 

from optparse import OptionParser

#from fabric.network import disconnect_all
from dad.core import Project

"""

Directory structure

 + website.com
   + apache
     - prod.wsgi
     - demo.wsgi
     - apache.conf
   + contrib
   + dad
     - project.yml
     - requirements.txt
     - dev.sh
   + project

"""

usage = """usage: %prog [options]"""
parser = OptionParser(usage=usage)
#parser.add_option("-c", "--clear", dest="clear", action="store_true",
#                  )
# Working
parser.add_option('-a', '--apache',     type="string", dest='apache', action='store')
parser.add_option('-c', '--clear',      type="string", dest='clear', action='store')
parser.add_option('-d', '--dev',        dest='dev', action='store_true')
parser.add_option('-f', '--freeze',     type="string", dest='freeze', action='store')
parser.add_option('-F', '--fetch-uploads', type="string", dest='fetch_uploads', action='store')
parser.add_option('-i', '--install',    dest='install', action='store_true')
parser.add_option('-s', '--syncdb',     dest='syncdb', action='store_true')
parser.add_option('-S', '--save-state', type="string", dest='save_state', action='store')
parser.add_option('-m', '--manage',     type="string", dest='manage', action='store')
parser.add_option('-M', '--move-data',  dest='move_data', action='store')
parser.add_option('-p', '--push',       type="string", dest='push', action='store')
parser.add_option('-P', '--push-uploads', type="string", dest='push_uploads', action='store')
parser.add_option('-r', '--rollback',   type="string", dest='rollback', action='store')
parser.add_option('-t', '--create-local-templates', dest='create_local_templates', action='store_true')
parser.add_option('-u', '--update',     type="string", dest='update', action='store')
#parser.add_option('-q', '--quiet',      dest='quiet', action='store_true')
#parser.add_option('-K', '--ssh-keyless-auth', dest='ssh_keyless_auth', action='store_true')

def main():

    (options, args) = parser.parse_args()

    try:
        if options.install:
            name = len(args) and args[0].replace('/', '') or False
            project = Project(name)
            project.install()

        if options.dev:
            project = Project()
            project.dev()
        
        if options.manage:
            project = Project()
            project.manage(options.manage, ' '.join(args).replace('+', '-').replace('++', '--'))

        if options.create_local_templates:
            project = Project()
            project.create_local_templates()
        
        if options.freeze:
            stage = options.freeze or 'dev'
            project = Project()
            project.freeze(stage)
        
        if options.clear:
            stage = options.clear or 'dev'
            project = Project()
            project.clear(stage)

        if options.update:
            project = Project()
            stage = options.update or 'dev'
            project.update(stage)

        if options.push:
            stage = options.push or 'demo'
            project = Project()
            project.push(stage)

        if options.push_uploads:
            stage = options.push_uploads or 'demo'
            project = Project()
            project.push_uploads(stage)

        if options.fetch_uploads:
            stage = options.fetch_uploads or 'demo'
            project = Project()
            project.fetch_uploads(stage)
        
        if options.apache:
            stage = options.apache or 'demo'
            cmd   = args[0]
            project = Project()
            project.apache(cmd, stage)
        
        if options.save_state:
            stage = options.save_state or 'demo'
            project = Project()
            project.save_state(stage)
        
        if options.rollback:
            stage = options.rollback or 'demo'
            project = Project()
            project.rollback(stage)
        
        if options.move_data:
            data = options.move_data or 'demo'
            if len(args) == 2:
                src  = args[0]
                dest = args[1]
            elif len(args) == 1:
                src  = 'dev'
                dest = args[0]
                print (src, dest)
            else:
                print >> sys.stderr, "\nMove data requires a module.model, a destination and optionally a source (defaults to dev) as arguments"
                sys.exit(1)
            project = Project()
            project.move_data(data, dest, src)

       #if options.ssh_keyless_auth:
       #    stage = len(args) and args[0] or 'demo'
       #    project = Project()
       #    project.ssh_keyless_auth(stage)


    except SystemExit:
        # a number of internal functions might raise this one.
        raise
    except KeyboardInterrupt:
        if state.output.status:
            print >> sys.stderr, "\nStopped."
        sys.exit(1)
    except:
        sys.excepthook(*sys.exc_info())
        # we might leave stale threads if we don't explicitly exit()
        sys.exit(1)
    finally:
        pass
        #disconnect_all()


if __name__ == "__main__":
    main()
    sys.exit(0)
