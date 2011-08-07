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
parser.add_option('-s', '--setup',      dest='setup', action='store_true')
parser.add_option('-d', '--dev',        dest='dev', action='store_true')
parser.add_option('-u', '--update',     dest='update', action='store_true')
parser.add_option('-D', '--deploy',     dest='deploy', action='store_true')
#parser.add_option('-K', '--ssh-keyless-auth', dest='ssh_keyless_auth', action='store_true')
#parser.add_option('-m', '--move-data',  dest='move_data', action='store_true')

def main():

    (options, args) = parser.parse_args()

    try:
        if options.setup:
            name = len(args) and args[0].replace('/', '') or False
            project = Project(name)
            project.setupdev()

        if options.dev:
            project = Project()
            project.dev()

        if options.update:
            project = Project()
            stage = len(args) and args[0] or 'dev'
            project.update(stage)

        if options.deploy:
            stage = len(args) and args[0] or 'demo'
            project = Project()
            project.deploy(stage)

       #if options.ssh_keyless_auth:
       #    stage = len(args) and args[0] or 'demo'
       #    project = Project()
       #    project.ssh_keyless_auth(stage)
        
       #if options.move_data:
       #    stage = len(args) and args[0] or 'demo'
       #    if len(args) != 2:
       #        print >> sys.stderr, "\nMove data requires two stages names, ex: dad-admin.py -m dev demo."
       #        sys.exit(1)
       #    project = Project()
       #    project.move_data(args[0], args[1])


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
