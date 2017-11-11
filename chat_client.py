# chat_client.py
import json
import sys, socket, select
 
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
                    try:
                        msg = json.loads(data)
                    except:
                        continue
                    sys.stdout.write(msg['sender']+' :'+msg['msg'])
                    sys.stdout.write('[Me] '); sys.stdout.flush()     
            
            else :
                # user entered a message
                msg = sys.stdin.readline()
                msg_dict = {}
                msg_dict['type'] = 'broadcast'
                msg_dict['msg'] = msg
                s.send(json.dumps(msg_dict))
                sys.stdout.write('[Me] '); sys.stdout.flush() 

if __name__ == "__main__":

    sys.exit(chat_client())

