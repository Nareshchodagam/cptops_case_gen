#!/usr/bin/python
#
"""
Case Gen environment setup script. 
    - Activate idbhost submodule
    - Create necessary symlinks
"""
import subprocess
import os

activate_cmd = "git submodule init"
update_cmd = "git submodule update"

if os.getcwd() != os.environ['HOME'] + "/git/cptops_case_gen":
    print "Current working directory should be " + os.environ['HOME'] + "/git/cptops_case_gen"
    sys.exit(1)
else:
    print "Activating submodule and refreshing...."
    try:
        subprocess.check_call(activate_cmd.split())
        subprocess.check_call(update_cmd.split())
    except subprocess.CalledProcessError:
        print "Submodule update failed."
        sys.exit(1)

if not os.path.exists('includes'):
    os.mkdir('includes')
    os.symlink('../idbhost/includes/idbhost.py', 'includes/idbhost.py')
else:
    os.symlink('../idbhost/includes/idbhost.py', 'includes/idbhost.py')
    