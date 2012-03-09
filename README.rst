Introduction
------------

Python-dad which stands for Django Automated Deployment is a lightweight Python package which harness the power of `Virtualenv <http://pypi.python.org/pypi/virtualenv>`__, `pip <http://pypi.python.org/pypi/pip>`__ and `fabric <http://pypi.python.org/pypi/Fabric/1.0.0>`__ to fully automate the development setup and deployment of django projects.


Goals
=====

 * Be easy to use (little to no knowledge of pip/fabric/virtualenv needed)
 * Streamline django installation on different stages (dev, demo, beta, prod)
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


Notes
=====

Two packages can be problematic to use with PIP, at least with Ubuntu.


PIL
^^^

When using PIL with Ubuntu 64bit you might get a jpeg encoder error. To fix it, simply do this::

    sudo ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/
    sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
    sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/


For more infos about this bug: http://ubuntuforums.org/showthread.php?t=1751455


MySQL-python
^^^^^^^^^^^^

I also had some problem with MySQL-python, which sometimes work and sometimes doesn't work.
I haven't figured out why exactly, but using a tarball solves the problem. So instead of using
MySQL-python in your requirements.txt, use a direct tarball link like this:

http://downloads.sourceforge.net/project/mysql-python/mysql-python/1.2.2/MySQL-python-1.2.2.tar.gz


Credits
=======

This project was created and is sponsored by:

.. figure:: http://motion-m.ca/media/img/logo.png
    :figwidth: image

Motion Média (http://motion-m.ca)

