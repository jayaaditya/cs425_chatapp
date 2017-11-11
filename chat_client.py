# chat_client.py
import json
import sys, socket, select

window_state = {'type':'broadcast','sender':'Server'}
chat_log = {'Server':[]}

def print_msg(msg):
    sys.stdout.write('\r'+msg['sender']+' :'+msg['msg'])
    sys.stdout.write('Me: '); sys.stdout.flush()

def chat_client():
    if(len(sys.argv) < 3) :
        print 'Usage : python chat_client.py hostname port'
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    # connect to remote host
    username = raw_input("Enter username :")
    password = raw_input("Enter password :")
    msg_dict = {}
    msg_dict['username'] = username
    msg_dict['password'] = password
    msg_dict['type'] = 'auth'
    try :
        s.connect((host, port))
    except :
        print 'Unable to connect'
        sys.exit()
    s.send(json.dumps(msg_dict))
    print 'Connected to remote host. You can start sending messages'
    sys.stdout.write('[Me] '); sys.stdout.flush()
    while 1:
        socket_list = [sys.stdin, s]
        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
        for sock in read_sockets:            
            if sock == s:
                # incoming message from remote server, s
                data = sock.recv(4096)
                if not data :
                    print '\nDisconnected from chat server'
                    sys.exit()
                else :
                    #print data
                    msg = json.loads(data)
                    if msg['type'] == 'broadcast':
                        chat_log['Server'].append(msg)
                    if msg['type'] == 'private':
                        if chat_log.has_key(msg['sender']):
                            chat_log[msg['sender']].append(msg)
                        else:      
                            chat_log[msg['sender']] = [msg]
                    if window_state['type'] == 'private' and window_state['sender'] == msg['sender']:
                        print_msg(msg)
                    if window_state['type'] == 'broadcast' and msg['type'] == 'broadcast':
                        print_msg(msg)
            else :
                # user entered a message
                msg = sys.stdin.readline()
                if msg.strip() == '/private':
                    window_state['type'] = 'private'
                    window_state['sender'] = 'none'
                    for x in chat_log.keys():
                        if x != 'Server':
                            print x
                    sys.stdout.write('Enter Username: '); sys.stdout.flush()
                elif msg.strip() == '/broadcast':
                    window_state['type'] = 'broadcast'
                    window_state['sender'] = 'Server'
                    for x in chat_log['Server']:
                        print_msg(x)
                    sys.stdout.write('\rMe: '); sys.stdout.flush()
                elif window_state['type'] == 'private' and window_state['sender'] == 'none':
                    user = msg.strip()
                    window_state['sender'] = user
                    if chat_log.has_key(user):
                        for x in chat_log[user]:
                            print_msg(x)
                    else:
                        chat_log[user] = []
                        print "New thread"
                    sys.stdout.write('\rMe: '); sys.stdout.flush()
                else:
                    msg_dict = {}
                    msg_dict['type'] = window_state['type']
                    msg_dict['reciever'] = window_state['sender']
                    msg_dict['msg'] = msg
                    s.send(json.dumps(msg_dict))
                    msg_dict['sender'] = 'Me'
                    chat_log[msg_dict['reciever']].append(msg_dict)
                    sys.stdout.write('Me: '); sys.stdout.flush()
try:
    chat_client()
except KeyboardInterrupt:
    sys.exit(0)
