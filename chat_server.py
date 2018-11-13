# chat_server.py
import hashlib
import threading
import sys, socket, select
import json
import sha
import time

HOST = '' 
SOCKET_LIST = []
RECV_BUFFER = 4096 
PORT = 9009
threads = []
unsent = {}
block_list = {}
user_sock_dict = {}
sock_user_dict = {}
authenticated = {}
passwd = {}
threads = []
error_messages = {
        404:{'type':'private','sender':'ERROR', 'msg':'User does not exist\n'},
        400:{'type':'private','sender':'ERROR', 'msg':'Username/password incorrect\n'}
        }
broad_mess = []
priv_mess = {}
def chat_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)
 
    print "Chat server started on port " + str(PORT)
 
    while True:

        # get the list sockets which are ready to be read through select
        # 4th arg, time_out  = 0 : poll and never block
        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
        for sock in ready_to_read:
            # a new connection request recieved
            if sock == server_socket: 
                sockfd, addr = server_socket.accept()
                authenticated[str(sockfd.getpeername())] = False
                SOCKET_LIST.append(sockfd)
                print "Client (%s, %s) connected" % addr
                #broadcast(server_socket, sockfd, "(%s,%s) entered our chatting room\n" %addr)
            # a message from a client, not a new connection
            else:
                # process data recieved from client, 
                try:
                    # receiving data from the socket.
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        # there is something in the socket
                        t = threading.Thread(target=parse, args=(data, sock, server_socket))
                        t.start()
                        threads.append(t)
                    else:
                        # remove the socket that's broken    
                        if sock in SOCKET_LIST:
                            SOCKET_LIST.remove(sock)
                        # at this stage, no data means probably the connection has been broken
                        #broadcast(server_socket, sock, "Client (%s, %s) is offline\n" % addr) 

                # exception 
                except:
                    #broadcast(server_socket, sock, "Client (%s, %s) is offline\n" % addr)
                    continue

    server_socket.close()
    
def broadcast(server_socket, sock, message):
    print "f_call"
    for socket in SOCKET_LIST:
        # send the message only to peer
        try:
            if (socket != server_socket and socket != sock and sock_user_dict[str(sock.getpeername())] 
                    not in block_list[sock_user_dict[str(socket.getpeername())]]):
                try :
                    socket.send(message)
                except :
                    socket.close()
                    # broken socket, remove it
                    if socket in SOCKET_LIST:
                        SOCKET_LIST.remove(socket)
        except KeyError:
            pass

def parse(data, sock, server_socket):
    try:
        data_dict = json.loads(data)
    except:
        return
    print data
    try:
        type_msg = str(data_dict['type'])
    except:
        print "type missing"
        return
    if type_msg == 'signup':
        try:
            username =  str(data_dict['username'])
            password = str(data_dict['password'])
        except:
            print "signup format wrong"
            return
        if not passwd.has_key(username):
            passwd[username] = hashlib.sha224(username+password).hexdigest()
            block_list[username] = []
            priv_mess[username] = []
        auth(username, password, sock)
    elif type_msg == 'auth':
        try:
            username =  str(data_dict['username'])
            password = str(data_dict['password'])
        except:
            print "login format wrong"
            return
        auth(username, password, sock)
    elif not authenticated[str(sock.getpeername())]:
        print authenticated
        print "not auth"
        return
    msg_dict = {}
    msg_dict["type"] = type_msg
    if type_msg == "broadcast":
        print "broadcast start"
        msg_dict = {}
        msg_dict["type"] = type_msg
        try:
            msg_dict["msg"] = data_dict["msg"]
        except:
            print "keyerror\n"
            return
        msg_dict["sender"] = sock_user_dict[str(sock.getpeername())]
        message = json.dumps(msg_dict)
        print message
        broad_mess.append(message)
        broadcast(server_socket, sock, message)
    elif type_msg == "private":
        try:
            reciever = data_dict["reciever"]
            msg_dict["msg"] = data_dict["msg"]
        except:
            return
        sender = sock_user_dict[str(sock.getpeername())]
        msg_dict["sender"] = sender
        priv_mess[sender].append(data)
        private(reciever, msg_dict, sock)
    elif type_msg == "block":
        try:
            user = data_dict["user"]
        except:
            return
        block_list[sock_user_dict[str(sock.getpeername())]].append(user)
    elif type_msg == "unblock":
        try:
            user = data_dict["user"]
        except:
            return
        try:
            block_list[sock_user_dict[str(sock.getpeername())]].remove(user)
        except:
            pass

def auth(username, password, sock):
    try:
        print passwd[username], hashlib.sha224(username+password).hexdigest()
        if passwd[username] == hashlib.sha224(username+password).hexdigest():
            user_sock_dict[username] = sock
            sock_user_dict[str(sock.getpeername())] = username
            authenticated[str(sock.getpeername())] = True
            for x in broad_mess:
                time.sleep(0.01)
                msg_dict = json.loads(x)
                if msg_dict['sender'] not in block_list[username]:
                    safe_send(sock, x)
            print priv_mess[username]
            for x in priv_mess[username]:
                time.sleep(0.01)
                safe_send(sock, x)
            print "auth successful - %s" %username
        else:
            print "wrong password"
            try:
                sock.close()
                SOCKET_LIST.remove(sock)
            except:
                pass
    except KeyError:
        print "acc does not exist"
        if sock in SOCKET_LIST:
            SOCKET_LIST.remove(sock)
        safe_send(sock, json.dumps(error_messages[400]))
        time.sleep(1)
        try:
            sock.close()
        except:
            pass

def safe_send(sock, msg):
    try:
        sock.send(msg)
        return 0
    except:
        try:
            SOCKET_LIST.remove(sock)
        except:
            print "sock already removed"
        return 1

def private(reciever, msg_dict, sock):
    print passwd.keys(), reciever
    if reciever not in passwd.keys():
        safe_send(sock, json.dumps(error_messages[404]))
        return
    if sock_user_dict[str(sock.getpeername())] in block_list[reciever]:
        return
    msg = json.dumps(msg_dict)
    priv_mess[reciever].append(msg)
    try:
        status = safe_send(user_sock_dict[reciever], msg)
    except KeyError:
        pass
with open('passwd.json' , 'r') as f:
    passwd = json.load(f)
for x in passwd.keys():
    priv_mess[x] = []
    block_list[x] = []
try:
    chat_server()
except KeyboardInterrupt:
    for t in threads:
        t.join()
    with open('passwd.json', 'w') as f:
        js = json.dumps(passwd)
        f.write(js)
    sys.exit(0)
