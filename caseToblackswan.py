#!/usr/bin/env python

import sys
import datetime
from modules.buildplan_helper import *
import json
import os
import ConfigParser
import logging
import requests
#
try:
    from pyczar import pyczar
except Exception as e:
    print('no %s installed : %s' % ('pyczar',e))
    sys.exit(1)
configdir = os.environ['HOME'] + "/.cptops/config"
config = ConfigParser.ConfigParser()
try:
    config.readfp(open(configdir + '/vaultcreds.config'))
except IOError:
    logging.error("No vaultcreds.config file found in %s", configdir)
    sys.exit(1)

os.environ['NO_PROXY'] = "secretservice.dmz.salesforce.com"


def saveApiKey(savedapikey, apikey):
    with open(savedapikey, 'w') as f:
        json.dump(apikey, f)

def getApiKey(savedapikey):
    with open(savedapikey, 'r') as f:
        apikey = json.load(f)
        return apikey

def GetApiKey():
    vault = config.get('BLACKSWAN', 'vault')
    cert = config.get('BLACKSWAN', 'cert')
    key = config.get('BLACKSWAN', 'key')
    server = config.get('VAULT', 'server')
    port = config.get('VAULT', 'port')
    pc = pyczar.Pyczar(server, port)
    apiKey = pc.get_secret_by_subscriber(vault, 'apikey', cert, key)
    return apiKey

def CheckApiKey(apikey):
    url = "https://ops0-cpt1-2-prd.eng.sfdc.net:9876/api/v1/test/apikey"
    headers = {"x-api-key": apikey}
    res = requests.get(url, headers=headers, verify=False)
    try:
        if res.status_code == 200:
            print("Api key is valid.")
            return True
        else:
            print("WARNING: Api key is not valid.")
            return False
    except Exception as e:
        print("Unable to connect to Blackswan API, ", e)
        return False

def writeToFile(data):
    """
    :param data:
    :return:
    """
    json_dir = common.outputdir + "/blackswanUpload.json"
    f = open(json_dir, 'w')
    f.write(json.dumps(data))
    f.close()

def CreateBlackswanJson(inputdict, bundle):
    """

    :param inputdict:
    :param bundle:
    :return:
    """
    user = 'user'
    username = ''
    if os.path.isfile(user):
        username = getApiKey(user)
        print("Found username from saved session: ", username)
        logging.debug("%s" % username)


    if not username:
        try:
            username = config.get('GUS', 'username')
            username = username.split("@")[0]
            saveApiKey(user, username)
            print("Found username from CONFIG file: ", username)
        except Exception as e :
            print("username section not found under GUS in CONFIG file. ", e)
    if not username:
        username = raw_input("\nEnter username(One Time Only): ")
        saveApiKey(user, username)
    roles = inputdict["roles"].split(",")
    patchcases = []
    for role in roles:
        patchcases_part = {"role": role,
                      "dc": inputdict["datacenter"],
                      "superpod": inputdict["superpod"],
                      "pod": inputdict["clusters"]}
        patchcases.append(patchcases_part)
    json_dict = [{"captain": False,
                 "katzmeow": True,
                 "created": datetime.datetime.now().isoformat()+"Z",
                 "createdby": username,
                 "guscase": "",
                 "guscaseid": "",
                 "patchcases": patchcases,
                 "hosts": [],
                 "release": bundle,
                 "test": False},
                 ]
    writeToFile(json_dict)

def readJsonFromFile(file):
    """
    :param file:
    :return:
    """
    with open(file, 'r') as f:
        data = json.load(f)
    return data

def BlackswanJson(caseNum):
    """
    :param caseNum:
    :param username:
    :return:
    """
    hostFile = common.outputdir + "/summarylist.txt"
    jFile = common.outputdir + "/blackswanUpload.json"
    caseId = caseNum['Id']
    caseNumber = caseNum['CaseNumber']
    with open(hostFile, 'r') as h:
        hostlist = h.read().splitlines()
    jsonFile = readJsonFromFile(jFile)
    jsonFile[0]["hosts"] = hostlist
    jsonFile[0]["guscase"] = caseNumber
    jsonFile[0]["guscaseid"] = caseId

    print("writing json file.")
    writeToFile(jsonFile)
    return jsonFile

def UploadDataToBlackswanV1(caseNum):
    """
    :param caseNum:
    :return:
    """
    jsondata = BlackswanJson(caseNum)
    apikey = ''
    valid_api = ''
    savedapikey = "savedapikey"
    if os.path.isfile(savedapikey):
        apikey = getApiKey(savedapikey)
        logging.debug("%s" % apikey)
    try:
        valid_api = CheckApiKey(apikey)
        logging.debug(apikey)
    except Exception as e:
        print('error : %s' % e)
    if valid_api != True:
        apikey, user = GetApiKey()
        print("Savinng ApiKey.")
        saveApiKey(savedapikey, apikey)
    else:
        print("Saved ApiKey is valid.")
    url = "https://ops0-cpt1-2-prd.eng.sfdc.net:9876/api/v1/gus-cases/new"
    headers = {"x-api-key": apikey}
    res = requests.post(url, data=json.dumps(jsondata), headers=headers, verify=False)
    try:
        if res.status_code == 200:
            print("Successfully Posted data to Blackswan.")
        else:
            print("Unable to post data to blackswan")

    except Exception as e:
        print("Unable to connect to blackswan API :: %s", e)