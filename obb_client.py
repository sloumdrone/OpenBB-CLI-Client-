import os.path, json, urllib2, sys
import os, tempfile
import getpass
from subprocess import call

udata = './u.conf.json'
incoming = ''
error_dict = {
    1000: 'oBB ERROR 1000 : Communication error',
    1001: 'oBB ERROR 1001 : Database not found',
    1002: 'oBB ERROR 1002 : Bad username, password, or token',
    1003: 'oBB ERROR 1003 : Database write error, contact server admin',
    1004: 'oBB ERROR 1004 : Bad query/no matches for provided input',
    1005: 'oBB ERROR 1005 : Client request format error',
    1006: 'oBB ERROR 1006 : Invalide command or target',
    1007: 'No data matches your request\nCheck your settings and try again\n'
}


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
    data = {'user': username, 'password': pw}
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
                print error_dict[x]
    except:
        print 'Unable to communicate with server'


def log_off(command,target,flags,value):
    data = {'user': incoming['user'], 'token':incoming['token']}
    try:
        response = make_request('logoff', None, data)
        if response['success']:
            print '\n{} has been logged off...\n'.format(data['user'])
            incoming['user'] = ''
            incoming['board'] = None
            incoming['topic'] = None
            incoming['post'] = None
            incoming['token'] = None
        else:
            for x in response['errors']:
                print error_dict[x]
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
    data = {'user': username,'password': password, 'bio': bio, 'contact': contact,'url': url}
    try:
        response = make_request('join',None,data)
        if response['success']:
            print '\nAn account has been created for {}\nPlease log in...'.format(username)
        else:
            for x in response['errors']:
                print error_dict[x]
    except:
        print 'Unable to communicate with server'

def delete_user(command,target,flags,value):
    username = raw_input('\nTo delete your account from the remote server\nplease enter your username: ')
    password = getpass.getpass('Great. Now enter your password: ')
    repass = getpass.getpass('One more time, just to be safe: ')
    if password == repass:
        verify = raw_input('Are you sure? This cannot be undone (y/n): ')
        if verify.lower() in ['y','yes','yeah','yup','ya']:
            data = {'user': username,'password':password}
            try:
                response = make_request('delete',None,data)
                if response['success']:
                    print '\nThe account for {} has been deleted\n'.format(username)
                else:
                    for x in response['errors']:
                        print error_dict[x]
                    print 'Account not deleted!'
            except:
                print 'Unable to communicate with server'
                print 'Account not deleted!'
    else:
        print 'Passwords did not match!'
        print 'Account not deleted!'
    return False


def add(command,target,flags,value):
    headline = None
    if not value and target == 'board':
        value = raw_input('Please enter the name you would like for the new {}: '.format(target))
    elif not value:
        value = None
    if target == 'topic':
        headline = raw_input('Topic name: ')
    elif target == 'post':
        headline = raw_input('Headline / Title: ')
        while len(headline) > 81 or len(headline) < 5:
            print '\nHeadline must be between 5 and 81 characters!\n'
            headline = raw_input('Headline / Title: ')
    if target == 'reply':
        description = raw_input('Provide the content of the reply: ')
    elif target == 'post':
        EDITOR = os.environ.get('EDITOR', 'vim')
        initial_message = "Delete this text and enter your post text..."

        with tempfile.NamedTemporaryFile(suffix=".tmp") as tmp:
            tmp.write(initial_message)
            tmp.flush()
            call([EDITOR, tmp.name])
            tmp.seek(0)
            description = tmp.read()
    else:
        description = raw_input('{} description: '.format(target))
        while len(description) > 40 or len(description) < 5:
            print '\n{} descriptions must be between 5 and 40 characters long!\n'.format(target)
            description = raw_input('{} description: '.format(target))
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
        if response['success']:
            print 'Your {} has been added!'.format(target)
        else:
            for x in response['errors']:
                print error_dict[x]
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
        response = make_request(command, target, data)
        print 'oBB --- [RESPONSE] >>>>>>\n'
        if response['success']:
            if target != 'board':
                print 'Board: {}\n'.format(incoming['board'])
            elif target == 'post':
                print 'Topic: {}'.format(incoming['topic_hl'])

            for x in response['rows']:
                spaces = u' ' * (20 - len(x['headline']))
                if target == 'board':
                    print x['headline'] + spaces + x['body']
                elif target == 'topic':
                    print 'ID: ' + str(x['id']) + ' // ' + x['headline'] + ' // ' + x['body']
                else:
                    print 'ID: ' + str(x['id']) + ' // ' + x['headline'] + ' // By: ' + x['creator']
            print '\n'
        else:
            for x in response['errors']:
                print error_dict[x]
    except:
        print 'Unable to communicate with server'

def view(command, target, flags, value):
    if not incoming['board']:
        print 'No board is set for the current user'
        return False
    if target == 'post' and not incoming['topic']:
        print 'No topic is set for the current user'
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
        print 'oBB --- [{}] >>>>>>\n'.format(incoming['board'])
        response = make_request(command, target, data)
        if response['success']:
            print '{}:\n'.format(target)
            print '{}\nby {} - {}\n\n{}'.format(
                response['headline'],
                response['creator'],
                response['time'],
                response['body']
            )
            if target == 'post':
                print '\n\nreplies:\n'
                for x in response['rows']:
                    if x['time'] and x['creator']:
                        print '{} - {}'.format(x['creator'], x['time'])
                    print x['body']
                    print '\n---\n'
        else:
            for x in response['errors']:
                print error_dict[x]
    except:
        print 'Unable to communicate with server'




def set_api(command, target, flags, value):
    if not target:
        print "No target supplied. Nothing set."
        return False

    if not value:
        value = raw_input("Enter {} ID: ".format(target))

    incoming[target] = value

    print "\nCurrent {}: {}\n".format(target,value)


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
        'target': ['board','topic','post','reply','admin'],
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
    },
    'view': {
        'target': ['topic','post'],
        'caller': view,
        'flags': ['-h']
    }
}



if __name__ == '__main__':
    if not os.path.isfile(udata):
        with open(udata,'w') as f:
            data = {
                'remote_root': 'http://localhost:8080',
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

