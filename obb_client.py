import os.path, json, urllib2, sys
import getpass

udata = './u.conf.json'
incoming = ''


def make_request(command,target,args):
    if target:
        url = "{}/api/{}/{}".format(incoming['remote_root'],command,target)
    else:
        url = "{}/sys/{}".format(incoming['remote_root'],command)
    data = {'data': args}
    req = urllib2.Request(url)
    req.add_header('Content-Type','application/json')
    response = urllib2.urlopen(req,json.dumps(data))
    response = json.loads(response.read())
    return response


def parse_args():
    args = {'flags':[]}
    try:
        args['command'] = sys.argv[1]
    except:
        print 'Invalid Query. See: help'
        return False

    try:
        args['target'] = sys.argv[2]
    except:
        args['target'] = None

    if len(sys.argv) > 3:
        for x in sys.argv[2:]:
            if x[0] == '-':
                args['flags'].append(x)
            else:
                args['value'] = x
    else:
        args['value'] = None

    return args


def validate_args(arg_list):
    if not arg_list:
        return False
    valid_request = True
    errors = []
    if arg_list['command'] and not arg_list['command'] in opts:
        valid_request = False
        errors.append('Unknown command: {}'.format(arg_list['command']))
    if arg_list['target'] and not arg_list['target'] in opts[arg_list['command']]['target']:
        valid_request = False
        errors.append('Unknown target: {}'.format(arg_list['target']))
    if arg_list['flags']:
        for flag in arg_list['flags']:
            if arg_list['target']:
                if not flag in opts[arg_list['command']][arg_list['target']]:
                    valid_request = False
                    errors.append('Unknown flag: {}'.format(flag))
            else:
                if not flag in opts[arg_list['command']['flags']]:
                    valid_request = False
                    errors.append('Unknown flag: {}'.format(flag))

    if valid_request:
        opts[arg_list['command']]['caller'](
            arg_list['command'],
            arg_list['target'],
            arg_list['flags'],
            arg_list['value']
        )
    else:
        for x in errors:
            print x


def log_on(command,target,flags,value):
    username = raw_input('Enter your username: ')
    pw = getpass.getpass('Enter your password: ')
    data = {'username': username, 'password': pw}
    try:
        response = make_request('logon',None,data)
        if response['success']:
            print '\n{} is now logged on...\n'.format(username)
            update_user_data(
                token=response['token'],
                user=username
            )
        else:
            for x in response['errors']:
                print 'ERROR: {}'.format(x)
    except:
        print 'Unable to communicate with server'


def log_off(command,target,flags,value):
    data = {'username': incoming['user'], 'token':incoming['token']}
    try:
        response = make_request('logoff', None, data)
        if response['success']:
            print '\n{} has been logged off...\n'.format(data['username'])
        else:
            for x in response['errors']:
                print 'ERROR: {}'.format(x)
    except:
        print 'Unable to communicate with server'


def join(command,target,flags,value):
    print '\nWelcome to OpenBB!\nJust a few quick questions and you\'ll be all set\n\n'
    username = raw_input('Enter a username: ')
    password = getpass.getpass('Enter your password: ')
    repassword = getpass.getpass('Re-enter your password: ')
    while password != repassword:
        print '\nPasswords did not match!\n'
        password = getpass.getpass('Enter your password: ')
        repassword = getpass.getpass('Re-enter your password: ')
    bio = raw_input('Enter a short bio (optional): ')
    contact = raw_input('Enter contact information (optional): ')
    url = raw_input('Enter a URL for yourself (optional): ')
    data = {'user': username,'pw': password, 'bio': bio, 'contact': contact,'url': url}
    try:
        response = make_request('join',None,data)
        if response['success']:
            print '\nAn account has been created for {}\nPlease log in...'.format(username)
        else:
            for x in response['errors']:
                print 'ERROR: {}'.format(x)
    except:
        print 'Unable to communicate with server'

def delete_user(command,target,flags,value):
    username = raw_input('\nTo delete your account from the server on file\nplease enter your username: ')
    password = getpass.getpass('Great. Now enter your password: ')
    repass = getpass.getpass('One more time, just to be safe: ')
    if password == repass:
        verify = raw_input('Are you sure? This cannot be undone (y/n): ')
        if verify.lower() in ['y','yes']:
            data = {'user': username,'pw':password}
            try:
                response = make_request('delete',None,data)
                if response['success']:
                    print '\nThe account for {} has been deleted\n'.format(username)
                else:
                    for x in response['errors']:
                        print 'ERROR: {}'.format(x)
            except:
                print 'Unable to communicate with server'
    else:
        print 'Passwords did not match!'
        return False
    print 'Account not deleted!'
    return False


def add(command,target,flags,value):
    headline = None
    if not value and target == 'board':
        value = raw_input('Please enter the name you would like for the new {}: '.format(target))
    elif not value:
        value = None
    if target == 'topic':
        headline = raw_input('Provide the name of the topic: ')
    elif target == 'post':
        headline = raw_input('Provide a headline (optional): ')

    if target == 'reply':
        description = raw_input('Provide the content of the reply: ')
    else:
        description = raw_input('Provide a description of this {} (optional): '.format(target))
    data = {
        'value': value,
        'token': incoming['token'],
        'user': incoming['user'],
        'body': description,
        'headline': headline,
        'board': incoming['board'],
        'topic': incoming['topic'],
        'post': incoming['post']
    }
    try:
        response = make_request(command,target,data)
        for x in response['messages']:
            print x
    except:
        print 'Unable to communicate with server'


def list_api(command,target,flags,value):
    if not value:
        value = 0
    if target == 'post' and not incoming['topic']:
        print 'No topic is set for the current user'
        return False
    elif target == 'topic' and not incoming['board']:
        print 'No board is set for the current user'
        return False
    if not target:
        print 'Incomplete query: no target'
        return False
    data = {
        'value': value,
        'token': incoming['token'],
        'user': incoming['user'],
        'body': None,
        'headline': None,
        'board': incoming['board'],
        'topic': incoming['topic'],
        'post': incoming['post']

    }
    try:
        response = make_request(command,target,data)
        if response['data']['success']:
            print '--- [RESPONSE] >>>>>>\n'
            for x in response['data']['rows']:
                spaces = u' ' * (20 - len(x['headline']))
                if target == 'board':
                    print x['headline'] + spaces + x['body']
                else:
                    print str(x['id']) + ' | ' + x['headline'] + ' | ' + x['body']
            print '\n'
        else:
            for x in response['messages']:
                print x
    except:
        print 'Unable to communicate with server'

def set_api(command,target,flags,value):
    if not target:
        print "No target supplied. Nothing set."
        return False

    if not value:
        value = raw_input("Enter {} ID: ".format(target))

    incoming[target] = value

    print "\nCurrent {}:\n{}\n".format(target,value)


def current(command,target,flags,value):
    for x in incoming:
        if not x == 'token' and incoming[x]:
            print 'Current {}: {}'.format(x,incoming[x])


def update_user_data(remote=None,token=None,user=None):
    global incoming
    if remote:
        incoming['remote_root'] = remote
    if token:
        incoming['token'] = token
    if user:
        incoming['user'] = user
    return False


opts = {
    'logon': {
        'target': [],
        'caller': log_on,
        'flags': ['-h','-u']
    },
    'logoff': {
        'target': [],
        'caller': log_off,
        'flags': ['-h']
    },
    'join': {
        'target': [],
        'caller': join,
        'flags': ['-h']
    },
    'delete': {
        'target': [],
        'caller': delete_user,
        'flags': ['-h']
    },
    'add': {
        'target': ['board','topic','post','reply''admin'],
        'caller': add,
        'flags': ['-h']
    },
    'set': {
        'target': ['board','topic','post','remote_root','user'],
        'caller': set_api,
        'flags': ['-h']
    },
    'current': {
        'target': [],
        'caller': current,
        'flags': ['-h']
    },
    'list': {
        'target': ['board','topic','post'],
        'caller': list_api,
        'flags': ['-h']
    }
}



if __name__ == '__main__':
    if not os.path.isfile(udata):
        with open(udata,'w') as f:
            data = {
                'remote_root': 'localhost:8080',
                'token': '',
                'user': '',
                'board': None,
                'topic': None,
                'post': None
            }
            json.dump(data,f)
    with open(udata,'r') as f:
        conf = f.read()
        incoming = json.loads(conf)
    args = parse_args()
    validate_args(args)
    with open(udata,'w') as f:
        json.dump(incoming,f)

