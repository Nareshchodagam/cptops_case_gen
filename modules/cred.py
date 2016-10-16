'''
cred -- GUS credentials file
'''
import ConfigParser

try:    
    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.expanduser('~') + '/git/cptops_case_gen/config/vaultcreds.config'))
except:
    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.expanduser('~') + '/git/cptops_case_gen/config/creds.config'))


class Cred(object):
    '''
    Credentials base class
    '''
    def __init__(self):
        pass

    def showVersion(self):
        '''
        Latest version
        '''
        self.version = '0.1'

class GusCred(Cred):
    '''
    GUS credentials class
    '''
    def __init__(self, username, guspasswd=None, client_id=None, client_secret=None):
        self.username = username
        self.guspasswd = guspasswd
        self.client_id = client_id
        self.client_secret = client_secret

    def getCredentials(self):
        '''
        Return credentials for an authorized user
        '''
        if self.guspasswd == None:
            self.guspasswd = config.get('GUS', 'guspassword')
        if self.username == None:
                self.username = config.get('GUS', 'username')
        if self.client_id == None:
            self.client_id = config.get('GUS', 'client_id')
        if self.client_secret == None:
            self.client_secret = config.get('GUS', 'client_secret')
        
        credDict = { 'username': self.username,
                    'client_secret': self.client_secret,
                    'password': self.guspasswd, 
                    'grant_type': 'password',
                    'client_id': self.client_id }
        return credDict
