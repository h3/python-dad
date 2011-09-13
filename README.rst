Introduction
------------

Python-dad which stands for Django Automated Deployment is a lightweight Python package which harness the power of `Virtualenv <http://pypi.python.org/pypi/virtualenv>`__, `pip <http://pypi.python.org/pypi/pip>`__ and `fabric <http://pypi.python.org/pypi/Fabric/1.0.0>`__ to fully automate the development setup and deployment of django projects.


Goals
=====

 * Be easy to use (little to no knowledge of pip/fabric/virtualenv needed)
 * Streamline django installation on different stages (dev, demo, prod)
 * Spread some pony love 


Features
========

 * Works on existing projects
 * Works with any VCS (svn, hg, git, etc..)
 * Total encapsulation of project dependencies and versions (thanks to pip/virtualenv)
 * Deploy project to demo or production stage from a single command 


Usage example
=============

This show the process of configuring and using python-dad on a Django project::

    $: cd myproject.com
    $: ls
    myproject

    # Create necessary hooks
    $: dad-admin.py -i myproject/
    $: ls
    myproject/ dad/ apache/

    # Configure project
    $: vim dad/project.yml

    # Start developing !
    $: dad-admin.py -d

    # Deploy to demo server
    $: dad-admin.py -p demo

    # Deploy to production server
    $: dad-admin.py -p prod

That's it !

For more detailed information about installing and using python-dad please read the Getting Started Guide


Credits
=======

This project was created and is sponsored by:

.. |MotionMedia| image:: http://motion-m.ca/media/img/logo.png
.. _MotionMedia: http://motion-m.ca/

