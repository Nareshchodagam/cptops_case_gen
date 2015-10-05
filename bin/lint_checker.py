#!/usr/bin/python
#
#
valid_cmd = ('-product',
              '-superpod',
              '-cluster',
              '-host',
              '-bigipstatus',
              '-forced_host',
              '-cluster',
              '-i',
              '-c',
              '-n',
              '-threads',
              '-auto2',
              '-u',
              '-user',
              '-t',
              '-s',
              '-d',
              '-invdb_mode',
              '-m',
              '-force_update_bootstrap',
              '-device_role',
              '-property',
              '-g',
              '-stopall')

default_cmd = {"-superpod": "v_SUPERPOD",
               "-cluster": "v_CLUSTER",
               "-host": "v_HOSTS",
               "-bigipstatus": "AVAILABILITY_STATUS_GREEN",
               "-forced_host": "v_HOSTS",
               "-device_role": "v_ROLE"}