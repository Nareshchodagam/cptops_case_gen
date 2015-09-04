'''
        gusparse -- converts user friendly dictionary to GUS friendly dictionary
'''
class GusParse(object):
    '''
    parse
    '''

    def __init__(self):
        self._gusDict = {}

    def parseDict(self, userDict):
        '''
        Parse dictionary depending on the values entered
        '''
        for k, v in userDict.iteritems():
            if k == 'Category':
                self._gusDict['SM_Category__c'] = v
            elif k == 'SubCategory':
                self._gusDict['SM_Sub_Category__c'] = v
            elif k == 'Subject':
                self._gusDict['Subject'] = v
            elif k == 'Description':
                self._gusDict['Description'] = v
            elif k == 'DC':
                self._gusDict['SM_Data_Center_Facility__c'] = v
            elif k == 'Status':
                self._gusDict['Status'] = v
            elif k == 'Priority':
                self._gusDict['Priority'] = v
            elif k == 'Change-Type':
                self._gusDict['SM_Change__c'] = v
            elif k == 'SRO-Resource':
                self._gusDict['SM_OSC_Resource_Req_d__c'] = v
            elif k == 'StartTime':
                self._gusDict['SM_Target_Execution_Date_Time__c'] = v
            elif k == 'EndTime':
                self._gusDict['SM_Target_Execution_End_Date_Time__c'] = v
            elif k == 'Environment':
                self._gusDict['SM_Target_Execution_Date_Time__c'] = v
            elif k == 'DC':
                self._gusDict['SM_Data_Center_Facility__c'] = v
            elif k == 'Implementation':
                self._gusDict['SM_Implementation_Plan__c'] = v
            elif k == 'Verification':
                self._gusDict['SM_Verification_Plan__c'] = v
            elif k == 'Backout':
                self._gusDict['SM_Backout_Plan__c'] = v
            elif k == 'Shared-Infrastructure':
                self._gusDict['SM_Shared_Infrastructure__c'] = v
            elif k == 'Tested-Change':
                self._gusDict['SM_Tested_Change__c'] = v
            elif k == 'Risk-Level':
                self._gusDict['SM_Risk_Level__c'] = v
            elif k == 'Risk-Summary':
                self._gusDict['SM_Risk_Summary__c'] = v
            elif k == 'Impact-Severity':
                self._gusDict['SM_Impact_Severity__c'] = v
            elif k == 'Impact-Scope':
                self._gusDict['SM_Impact_Scope__c'] = v
            elif k == 'Impact-Summary':
                self._gusDict['SM_Impact_Summary__c'] = v
            elif k == 'RecordTypeId':
                self._gusDict['RecordTypeId'] = v
            elif k == 'Change-Area':
                self._gusDict['SM_Change_Area__c'] = v
            elif k == 'Business-Justification':
                self._gusDict['SM_Next_Action__c'] = v
            elif k == 'Patch-Desc':
                self._gusDict['SM_Patch_Description__c'] = v
            elif k == 'Patch-Vendor':
                self._gusDict['SM_Patch_Vendor__c'] = v
            elif k == 'Business-Reason':
                self._gusDict['SM_Business_Reason__c'] = v
            elif k == 'Case-Owner':
                self._gusDict['OwnerId'] = v
            elif k == 'Cloud-Team':
                self._gusDict['SM_Cloud_Team__c'] = v
            elif k == 'Functional-System-Area':
                self._gusDict['SM_Functional_System_Area__c'] = v
            elif k == 'Infrastructure-Type':
                self._gusDict['SM_Infrastructure_Type__c'] = v
            elif k == 'Test-Evidence':
                self._gusDict['SM_Test_Evidence__c'] = v
            elif k == 'Vendor-Case-Number':
                self._gusDict['SM_Vendor_Case_Number_s__c'] = v
            elif k == 'SM_Change_Outcome__c':
                self._gusDict['SM_Change_Outcome__c'] = v
            elif k == 'Source-Control':
                self._gusDict['SM_Source_Control_Tool__c'] = v
            else:
                pass


        return self._gusDict
