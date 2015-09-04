'''
cred -- GUS credentials file
'''
import ConfigParser

config = ConfigParser.ConfigParser()
config.readfp(open('creds.config'))

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
    def __init__(self, username, guspasswd=None):
        self.username = username
        self.guspasswd = guspasswd

    def getCredentials(self):
        '''
        Return credentials for an authorized user
        '''
        if self.guspasswd == None:
            self.guspasswd = config.get('GUS', 'guspassword')
        elif self.username == '':
            print 'ERROR: please enter username'
        credDict = { 'username': config.get('GUS', 'username'),
                                'client_secret': config.get('GUS', 'client_secret'),
                                'password': self.guspasswd, 'grant_type': 'password',
                                'client_id': config.get('GUS', 'client_id') }
        return credDict
