#!/usr/bin/python

"""A wrapper to generate umps implementation plan and to create cases"""

import argparse
import getpass
import shlex
import json
from subprocess import check_call

data = {
    "chatter5": "na10,cs7",
    "chatter7": "cs8",
    "chatter1c3": "",
    "chatter1c4": "na9,cs14",
    "chatter6": "na7,cs9",
    "chatter8": "cs10",
    "chatter1w3": "na11,cs11",
    "chatter1w4": "n12,na14",
    "chatter2c1": "cs15",
    "chatter2c2": "na2",
    "chatter2c3": "na13,cs19",
    "chatter2c4": "na15,cs16",
    "chatter2w1": "na4,cs17",
    "chatter2w2": "cs20",
    "chatter2w3": "eu0",
    "chatter2w4": "na16,cs18",
    "chatter3c1": "cs23,cs24,cs25,cs27,cs28",
    "chatter3c2": "",
    "chatter3c3": "na5,na19,na20,",
    "chatter3c4": "",
    "chatter3w1": "na17,na18,na22,na23,na41,cs21,cs22,cs26",
    "chatter3w2": "",
    "chatter3w3": "",
    "chatter3w4": "",
    "chatter4c1": "na6,cs42",
    "chatter4c2": "na27,na29,cs40,cs45,cs46",
    "chatter4c3": "na25,na28",
    "chatter4c4": "",
    "chatter4w1": "na24,na26,cs41",
    "chatter4w2": "na31,cs43",
    "chatter4w3": "cs44",
    "chatter4w4": "",
    "chatter9": "ap3,cs5,cs31",
    "chatter10": "cs6",
    "chatter1t3": "ap0,ap2",
    "chatter1t4": "ap1",
    "chatter1p1": "",
    "chatter1p2": "na33",
    "chatter1p3": "cs52",
    "chatter1p4": "",
    "chatter2p1": "",
    "chatter2p2": "",
    "chatter2p3": "",
    "chatter2p4": "",
    "chatter1f1": "",
    "chatter1f2": "cs82,cs83,eu6",
    "chatter1f3": "",
    "chatter1f4": "",
    "chatter1d1": "na8,na34,cs51",
    "chatter1d2": "na3,na32",
    "chatter1d3": "cs50",
    "chatter1d4": "",
    "chatter2d1": "",
    "chatter2d2": "",
    "chatter2d3": "",
    "chatter2d4": "",
    "chatter1l1": "eu5,cs80,cs81",
    "chatter1l2": "eu1,eu3,eu4,cs86,cs87",
    "chatter1l3": "eu2,",
    "chatter1l4": "",

}


def run_command(cmd):
    cmd = shlex.split(cmd)
    check_call(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-D", "--datacenter", help="Please enter the DC "
                                                   "Name",required=True)
    parser.add_argument("-C", "--clusters", help="UMPS clusters name",
                        required=True)
    parser.add_argument("-S", "--superpod", help="superpod name")
    args = parser.parse_args()
    dc = args.datacenter
    clusters = args.clusters
    sp = args.superpod

    if dc and clusters and sp:
        insts = ",".join([data[cluster] for cluster in clusters.split(',')
                          if data[cluster]])

        plan_cmd = 'python build_plan.py -c 0000001 -C -G \'{"clusters" : "%s",'\
                   '"datacenter": "%s", "grouping" : "majorset", "maxgroupsize"'\
                   ':50, "templateid" :  "umps.linux"}\'' % (clusters, dc)

        case_cmd = 'python gus_cases.py -T change  -f ' \
                   '../templates/sites-proxy-oct-patch.json  -s "OCT Patch ' \
                   'Bundle: UMPS %s-%s  %s PROD" -k ' \
                   '../templates/6u6-plan.json ' \
                   ' -l output/summarylist.txt -D %s -i ' \
                   'output/plan_implementation.txt' % (dc.upper(), sp.upper(),
                                                          insts, dc)

        #run_command(plan_cmd)
        run_command(case_cmd)

