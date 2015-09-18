#!/usr/bin/python
###############################################################################
#
# Purpose: Common library to establish global functions and includes
#
###############################################################################

import sys
import os
from os.path import expanduser

# Set the default sys.path
sys.path.append(os.getcwd() +'/../includes/')
sys.path.append('/opt/compute_deploy/includes/')

class Common:
    """Help on module common:

    NAME
        Common

    DESCRIPTION
        This is a common library used hold commonly used methods and properties.

    Instructions

    How to import -
        from common import Common
        common=Common()

    Access common properties
        outputdir=common.outputdir


    """
    def __init__(self):

        # Filesystem paths.
        self.home=expanduser("~")
        self.logdir='../log'
        self.outputdir='../output'
        self.etcdir='../etc'
        self.bindir='.'
        self.includedir='../includes'
        self.tmpdir='../tmp'
        self.templatedir='../templates'
        self.cidb_jar_path = os.getcwd() + '/../lib/auth'