import os.path
import sys
import re


def check_config_exists(config):
    if os.path.exists(config):
        overwrite = raw_input('Config already exists, overwrite? (y|n): ')
        if overwrite == 'y':
            try:
                os.remove(config)
                print('Config file removed')
            except Exception,e:
                print('Unable to remove config file')
        else:
            print('exiting')
            sys.exit(0)

def get_username():
    username = raw_input('Enter your GUS username without @gus.com: ')
    if re.search(r'@gus.com', username):
        print('@gus.com included in input. Stripping it')
        username = username.replace('@gus.com', '')
    return username

def gen_config(config,username=None):
    try:
        f = open(config,'w')

        f.write("[GUS]\n")
        f.write("username = " + username + "@gus.com")
        f.write('''
client_secret = 516830729068743801
client_id = 3MVG92.uWdyphVj6UxPnhEXcGWJ0S1x3YjODc6tr26PrGYmtAtX8xXFxSGkMqF2H9cF6xfv6AZe9MDfzd1BF9
api_ver = v29.0

[LOGIN]
oauthURL = https://gus.salesforce.com/services/oauth2/token
''')
        f.close()
        print("Config file %s written with username %s " % (config, username))
    except Exception,e:
        print('Unable to create config file',e)

if __name__ == "__main__":
    config = 'creds.config'
    check_config_exists(config)
    username = get_username()
    gen_config(config,username)