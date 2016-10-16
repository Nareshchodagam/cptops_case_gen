'''
        GUS Python REST base class
'''
import requests
import json
import string
#from cred import Cred
from cred import GusCred 
#from gusparse import GusParse
from gusparse import GusParse
import base64
import re
import ConfigParser
import common
import logging
from ssl_version import SSLAdapter
import ssl
import sys
import os

try:    
    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.expanduser('~') + '/git/cptops_case_gen/config/vaultcreds.config'))
except:
    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.expanduser('~') + '/git/cptops_case_gen/config/creds.config'))


class Gus(object):
    '''
    GUS baseclass
    '''
    _oauthURL = config.get('LOGIN','oauthURL')
    _api_ver = config.get('GUS', 'api_ver')

    def __init__(self):
        pass

    def showVersion(self):
        '''
        Print version information
        '''
        self.version = '0.6'
        self.author = 'cpt@salesforce.com'
        return self.version, self.author

    def generatePostHeader(self, sessionDetails, token):
        '''
        Generate JSON Header for POST requests
        '''
        self.sessionDetails = sessionDetails
        self._token = token
        self._postHeader = {'Authorization': 'Bearer ' + self._token,
                            'Content-Type': 'application/json',
                            'Sforce-Auto-Assign': 'False'}
        return self._postHeader

    def generateGetHeader(self, sessionDetails, token):
        '''
        Generate JSON Header for GET requests
        '''
        self.sessionDetails = sessionDetails
        self._token = token
        self._getHeader = {'Authorization': 'Bearer ' + self._token}
        return self._getHeader

    def generateAuthHeader(self):
        '''
        Generate JSON Header for Auth requests
        '''
        self._authHeader = { 'content-type': 'application/x-www-form-urlencoded' }
        return self._authHeader

    def create(self, recType, recDict, sess):
        self.recordType = recType
        self.recordDict = recDict
        self.session = sess

        # parse dict
        pObj = GusParse()
        self.parsedDict = pObj.parseDict(self.recordDict)

        # Convert Unicode to Strings or else Salesforce rejects
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/Case/'

        # Generate Header
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        # Check RecordType and create case based on this type
        if re.search('RMA', recType, re.IGNORECASE):
            try:
                gusRecord = requests.post(instance, data=json.dumps(self.parsedDict), headers=postHeader)
                rmaId = gusRecord.text.split(':')[1].split('"')[1].encode('ascii', 'ignore')
            except Exception, e:
                print('Unable to create case: ', e)

            try:
                # change record type to RMA
                recTypeId = {'RecordTypeId': '012b0000000Z8e4AAC' }
                updated_rma = requests.patch(instance + rmaId, data=json.dumps(recTypeId), headers=postHeader)

            except Exception, e:
                print('Unable to change recordType to RMA: ', e)

        elif re.search('Incident', recType, re.IGNORECASE):
            try:
                gusRecord = requests.post(instance, data=json.dumps(self.parsedDict), headers=postHeader)
            except Exception, e:
                print('Unable to create case: ', e)

        elif re.search('Change', recType, re.IGNORECASE):
            try:
                gusRecord = requests.post(instance, data=json.dumps(self.parsedDict), headers=postHeader)
                changeId = gusRecord.text.split(':')[1].split('"')[1].encode('ascii', 'ignore')
            except Exception, e:
                print('Unable to create case: ', e)
            try:
                # change record type to Change
                recTypeId = {'RecordTypeId': '012b0000000Z8e2AAC' }
                updated_change = requests.patch(instance + changeId, data=json.dumps(recTypeId), headers=postHeader)

            except Exception, e:
                print('Unable to create case: ', e)

        else:
            print 'ERROR: Invalid RecordType entered. Must be one of RMA, Incident or Change'

        # Return the gusRecord ID if valid
        gusRecordID = gusRecord.json()['id']

        return gusRecordID

    def create_incident_case(self, recType, recDict, sess):
        self.recordType = recType
        self.recordDict = recDict
        self.session = sess

        # parse dict
        pObj = GusParse()
        self.parsedDict = pObj.parseDict(self.recordDict)

        # Convert Unicode to Strings or else Salesforce rejects
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/Case/'

        # Generate Header
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            gusRecord = requests.post(instance, data=json.dumps(self.parsedDict), headers=postHeader)
        except Exception, e:
            print('Unable to create case: ', e)

        gusRecordID = gusRecord.json()['id']

        return gusRecordID

    def create_change_case(self, recDict, sess):
        self.recordDict = recDict
        self.session = sess

        # parse dict
        pObj = GusParse()
        self.parsedDict = pObj.parseDict(self.recordDict)

        # Convert Unicode to Strings or else Salesforce rejects
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/Case/'

        # Generate Header
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            gusRecord = requests.post(instance, data=json.dumps(self.parsedDict), headers=postHeader)
            gusRecordId = gusRecord.json()['id']

        except Exception, e:
            print('Unable to create case: ', e)

        return gusRecordId

    def delete(self):
        pass

    def add_implementation_row(self, caseId, implanDict, session):
        self.caseId = caseId
        self.session = session
        self.implanDict = implanDict
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/v29.0/sobjects/SM_Change_Implementation__c/'

        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            case_details = requests.post(instance, data=json.dumps(self.implanDict), headers=postHeader)
            return case_details.json()
        except Exception, e:
            print('Unable to update case: ', e)
    
    def addLogicalConnectorRow(self, caseId, Dict, session):
        self.caseId = caseId
        self.session = session
        self.Dict = Dict
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/SM_Case_to_LogicalHost_Connector__c/'

        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            case_details = requests.post(instance, data=json.dumps(self.Dict), headers=postHeader)
            return case_details.json()
        except Exception, e:
            print('Unable to add Logical case connector: ', e)

    def update_case_details(self, caseId, recDict, sess):
        self.recordDict = recDict
        #caseId = self.recordDict['ParentId']
        self.session = sess
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/Case/'

        #payload = {'Status': 'Closed', 'ParentId': self.caseId }
        pObj = GusParse()
        self.parsedDict = pObj.parseDict(self.recordDict)
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            case_details = requests.patch(instance + caseId, data=json.dumps(self.parsedDict), headers=postHeader)
            return case_details
        except Exception, e:
            print('Unable to update case: ', e)

    def updateImplPlan(self, Id, Dict, session):
        self.recordDict = Dict
        caseId = self.recordDict['Case__c']
        self.session = session
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/SM_Change_Implementation__c/'
        
        #payload = {'Status': 'Closed', 'ParentId': self.caseId }
        #pObj = GusParse()
        #self.parsedDict = pObj.parseDict(self.recordDict)
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            case_details = requests.patch(instance + Id, data=json.dumps(self.recordDict), headers=postHeader)
            return case_details
        except Exception, e:
            print('Unable to update case: ', e)
            
    def updateLogicalConnector(self, Id, Dict, session):
        self.recordDict = Dict
        self.session = session
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/SM_Case_to_LogicalHost_Connector__c/'
        
        #payload = {'Status': 'Closed', 'ParentId': self.caseId }
        #pObj = GusParse()
        #self.parsedDict = pObj.parseDict(self.recordDict)
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            case_details = requests.patch(instance + Id, data=json.dumps(self.recordDict), headers=postHeader)
            return case_details
        except Exception, e:
            print('Unable to update case: ', e)

    def add_case_comment(self, comment, caseId, sess):
        '''
        adds a comment to a case defined by caseId
        '''
        self.comment = comment
        self.caseId = caseId
        self.session = sess
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/CaseComment/'

        payload = {'CommentBody' : self.comment, 'ParentId': self.caseId }
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            comment_add = requests.post(instance, data=json.dumps(payload), headers=postHeader)
            return comment_add
        except Exception, e:
            print('Unable to add a case comment: ', e)

    def get_case_details(self, caseId, session):
        '''
        get case details from a case number
        '''
        self.caseId = caseId
        self.session = session
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/Case/' + self.caseId

        payload = { 'ParentId': self.caseId }
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            case_details = requests.get(instance, data=json.dumps(payload), headers=postHeader)
            if case_details.status_code != 200:
                return "Case not found"
            else:
                d = case_details.json()
                output = "Case Number: {0} Status: {1} Priority: {2} Subject: {3}".format(d['CaseNumber'],d['Status'],d['Priority'],d['Subject'])
                return case_details.json()
        except Exception, e:
            print('Unable to get case details: ', e)

    def get_case_details_caseNum(self, caseNum, session):
        '''
        get case details from a case number
        '''
        self.caseNum = caseNum
        self.session = session
        query = "Select id from Case where caseNumber='" + self.caseNum + "'"
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/query?q=' + query

        payload = { }
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            case_details = requests.get(instance, data=json.dumps(payload), headers=postHeader)
            if case_details.status_code != 200:
                return "Case not found"
            else:
                d = case_details.json()
                return d['records'][0]['Id']
        except Exception, e:
            print('Unable to get case details: ', e)
            
    def get_case_subject_caseNum(self, caseNum, session):
        '''
        get case subject from a case number
        '''
        self.caseNum = caseNum
        self.session = session
        query = "Select subject from Case where Id ='" + self.caseNum + "'"
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/query?q=' + query

        payload = { }
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            case_details = requests.get(instance, data=json.dumps(payload), headers=postHeader)
            if case_details.status_code != 200:
                return "Case not found"
            else:
                d = case_details.json()
                return d['records'][0]['Subject']
        except Exception, e:
            print('Unable to get the case subject: ', e)

    def getWorkItemDetailsNum(self, workItemNum, session):
        '''
        get work item details from a work item number
        '''
        self.workItemNum = workItemNum
        self.session = session
        query = "Select Id,Bug_Number__c,Name from ADM_Work__c where Name='" + self.workItemNum + "'"
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/query?q=' + query

        payload = { }
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            case_details = requests.get(instance, data=json.dumps(payload), headers=postHeader)
            if case_details.status_code != 200:
                return "Case not found"
            else:
                d = case_details.json()
                return d['records'][0]['Id']
        except Exception, e:
            print('Unable to get case details: ', e)


    def describeObject(self, object, session):
        self.object = object
        self.session = session
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/sobjects/' + object + '/describe/'

        payload = { }
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            object_details = requests.get(instance, data=json.dumps(payload), headers=postHeader)
            d = object_details.json()
            return d
        except Exception, e:
            print('Unable to get object details: ', e)

    def run_query(self, query, session):
        self.query = query
        self.session = session
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/query?q=' + query

        payload = { }
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            query_details = requests.get(instance, data=json.dumps(payload), headers=postHeader)

            d = query_details.json()
            return d
        except Exception, e:
            print('Unable to get query details: ', e)


    def get_recent_cases(self, session):
        '''
        get recent cases
        '''
        self.session = session
        query = "Select CaseNumber, Status, Priority, Subject from Case where Status!='closed' order by CaseNumber desc limit 5 "
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/' + self._api_ver + '/query?q=' + query

        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)

        try:
            #case_details = requests.get(instance, data=json.dumps(payload), headers=postHeader)
            case_details = requests.get(instance, headers=postHeader)
            d = case_details.json()
            return d['records']
        except Exception, e:
            print('Unable to get recent cases: ', e)
            

    def submitCase(self, caseId, session):
        '''
        submit a case for approval post case creation
        '''
        self.caseId = caseId
        self.session = session
        token = str(self.session['token'])
        instance = str(self.session['instance']) + '/services/data/v30.0/process/approvals/'
        gObj = Gus()
        postHeader = gObj.generatePostHeader(self.session, token)
        payload = { "requests": [{"actionType": "Submit", "contextId": self.caseId }] }

        try:
            details = requests.post(instance, data=json.dumps(payload), headers=postHeader)
            d = details.json()
            return d
        except Exception, e:
            print('Unable to submit case for approval: ', e)

    def attach(self, fo, nm, case, sess):
        '''
        attach() attaches a file supplied by the user to the case defined by caseId
        '''
        self.fObj = fo
        self.name = nm
        self.caseId = case
        self.sessionDetails = sess

        # convert file to base64 encoding
        attachment = base64.b64encode(self.fObj.read())
        payload = {'name': self.name, 'body': attachment, 'ParentId': self.caseId }
        token = str(self.sessionDetails['token'])
        attachmentURL = str(self.sessionDetails['instance']) + '/services/data/' + self._api_ver + '/sobjects/Attachment/'

        gusObj = Gus()
        postHeader = gusObj.generatePostHeader(self.sessionDetails, token)

        try:
            attach_item = requests.post(attachmentURL, data=json.dumps(payload), headers=postHeader)
            if attach_item.status_code != 204:
                logging.debug(attach_item.text)
            return attach_item
        except Exception, e:
            print('Unable to add file to case: ', e)
            
    def renameAttach(self, name, Id, session):
        '''
        attach() attaches a file supplied by the user to the case defined by caseId
        '''

        self.name = name
        self.Id = Id
        self.sessionDetails = session

        payload = {'name': self.name }
        token = str(self.sessionDetails['token'])
        attachmentURL = str(self.sessionDetails['instance']) + '/services/data/' + self._api_ver + '/sobjects/Attachment/'

        gusObj = Gus()
        postHeader = gusObj.generatePostHeader(self.sessionDetails, token)

        try:
            attach_item = requests.patch(attachmentURL + Id, data=json.dumps(payload), headers=postHeader)
            if attach_item.status_code != 204:
                logging.debug(attach_item.text,attach_item.status_code,attach_item)
            return attach_item
        except Exception, e:
            print('Unable to add file to case: ', e)
            
    def attachWI(self, fo, nm, workItemId, session):
        '''
        attach() attaches a file supplied by the user to the work item defined by workItemId
        '''
        self.fObj = fo
        self.name = nm
        self.workItemId = workItemId
        self.sessionDetails = session

        # convert file to base64 encoding
        attachment = base64.b64encode(self.fObj.read())
        payload = {'name': self.name, 'body': attachment, 'ParentId': self.workItemId }
        token = str(self.sessionDetails['token'])
        attachmentURL = str(self.sessionDetails['instance']) + '/services/data/' + self._api_ver + '/sobjects/Attachment/'

        gusObj = Gus()
        postHeader = gusObj.generatePostHeader(self.sessionDetails, token)

        try:
            attach_item = requests.post(attachmentURL, data=json.dumps(payload), headers=postHeader)
            if attach_item.status_code != 200:
                print(attach_item.text)
            return attach_item
        except Exception, e:
            print('Unable to add file to case: ', e)




class Auth(Gus):

    '''
    Auth baseclass
    '''
    def __init__(self, username, guspasswd,client_id,client_secret):
        '''
        Initialise Auth class object
        '''
        Gus.__init__(self)
        self.username = username
        self.guspasswd = guspasswd
        self.client_id = client_id
        self.client_secret = client_secret

    def login(self):
        '''
        Login to SFDC application and return JSON
        '''
        credObj = GusCred(self.username,self.guspasswd,self.client_id,self.client_secret)
        credDict = credObj.getCredentials()

        gusObj = Gus()
        authHeader = gusObj.generateAuthHeader()
        s = requests.Session()
        s.mount('https://', SSLAdapter(ssl_version=ssl.PROTOCOL_TLSv1_2))
        logging.debug(self._oauthURL)
        gus_login = requests.post(self._oauthURL, data=credDict, headers=authHeader)


        gus_dict = json.loads(gus_login.text)
        token = gus_dict['access_token']
        instance = gus_dict['instance_url']
        sessionDetails = {'token': token, 'instance': instance}

        return sessionDetails
