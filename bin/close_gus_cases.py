#!/usr/bin/env python
'''
        Script for closing cases in Gus
'''
from base import Auth
from base import Gus
from common import Common 
import pprint
from optparse import OptionParser
import base64
import logging
import ConfigParser
import getpass
import re
import json
import sys
from datetime import datetime, date, time, timedelta

config = ConfigParser.ConfigParser()
config.readfp(open('creds.config'))


def getImplPlanDetails(caseId,session):
    gusObj = Gus()
    impl_plan_ids = []
    query = "select Id,Case__c from SM_Change_Implementation__c where Case__c='" + caseId +"'"
    case_details = gusObj.run_query(query,session)
    if case_details['records']:
        for r in case_details['records']:
            impl_plan_ids.append(r['Id'])
    return impl_plan_ids

def closeImplPlan(impl_plan_ids,caseId,session):
    gusObj = Gus()
    now = datetime.now()
    end = now.isoformat()
    for id in impl_plan_ids:
        dict = { 'Case__c': caseId, 'End_Time__c': end, 'Status__c': 'Implemented - per plan' }
        details = gusObj.updateImplPlan(id,dict,session)
        logging.debug(details)

def closeCase(caseId, session):
    gusObj = Gus()
    Dict = {    
                'Status': 'Closed',
                'SM_Change_Outcome__c': 'Successful',
            }
    details = gusObj.update_case_details(caseId, Dict, session)
    logging.debug(details)
    
def getCaseId(caseNum,session):
    gusObj = Gus()
    case_details = gusObj.get_case_details_caseNum(caseNum,session)
    return case_details.rstrip()

def getCaseSub(caseId,session):
    gusObj = Gus()
    case_subject = gusObj.get_case_subject_caseNum(caseId,session)
    return case_subject.rstrip()
    
if __name__ == '__main__':
    
    usage = """
    Code to send pm ends for all parts of the implementation plan and close the case
    
    %prog -c 00000000 [-v]
    
    Example closing two cases:
    %prog -c 00081381,00081382
    
    """
    parser = OptionParser(usage)
    parser.add_option("-c", "--case", dest="caseNum",
                            help="The case number(s) of the case to attach the file ")
    parser.add_option("-v", action="store_true", dest="verbose", default=False, help="verbosity") # will set to False later
    (options, args) = parser.parse_args()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    # set username and details of case

    try:
        gpass = config.get('GUS', 'guspassword')
    except ConfigParser.NoOptionError,e:
        gpass = getpass.getpass("Please enter your GUS password: ")
    try:
        username = config.get('GUS', 'username')
        client_id = config.get('GUS', 'client_id')
        client_secret = config.get('GUS', 'client_secret')
    except:
        print('Problem getting username, client_id or client_secret')
        sys.exit()
    # instantiate auth object and generate session dict
    authObj = Auth(username,gpass,client_id,client_secret)
    session = authObj.login()
    
    if options.caseNum:
        caseDetails = { }
        casenums = options.caseNum.split(',')
        print "Closing the following below cases..\n"
        for case in casenums:
            caseId = getCaseId(case, session)
            logging.debug(caseId)
            caseSub = getCaseSub(caseId, session)
            caseDetails[caseId] = case + " - " +caseSub
        for subject in caseDetails.itervalues():
            print subject
        response = raw_input('\nDo you wish to continue? (y|n) ')
        if response.lower() != "y":
            print "Exiting....."
            sys.exit(1)
        for id in caseDetails.iterkeys():
            impl_plan_ids = getImplPlanDetails(id,session)
            logging.debug(impl_plan_ids)
            closeImplPlan(impl_plan_ids,id,session)
            closeCase(caseId, session)
