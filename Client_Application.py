# client 
from socket import *
import datetime
import time
import json
import threading
import queue


class client_application:
    def __init__(self, username, ip_addr="localhost", peer_port=8000):
        self.server_ip = None
        self.server_port = None
        self.username = username
        self.ip_addr = ip_addr
        self.peer_port = peer_port
        self.client_socket = None
        self.udp_socket = None
        self.peer_socket = None
        self.peer_listener_socket = None
        self.message_queue = queue.Queue()
        self.waiting_for_response = False

    def tcp_connect(self, server_ip, server_port):
        # establish TCP connection with the server
        self.server_ip = server_ip
        self.server_port = server_port
        client_socket = socket(AF_INET, SOCK_STREAM) 
        client_socket.connect((server_ip,server_port)) # establish the TCP Connection 
        self.client_socket = client_socket
        print("connected to server")
        # START BACKGROUND LISTENER
        threading.Thread(target=self.tcp_receive_thread,daemon=True).start()

    def tcp_connect_peer(self, peer_ip, peer_port):
        # establish TCP connection with the target client for 1-on-1 chat
        peer_socket = socket(AF_INET, SOCK_STREAM) 
        peer_socket.connect((peer_ip, peer_port)) # establish the TCP Connection 
        self.peer_socket = peer_socket
        print("connected to target client")

        # Start receiver thread
        threading.Thread(target=self.peer_receive_thread,daemon=True).start()
    
    def start_peer_listener(self):
        listener = socket(AF_INET, SOCK_STREAM)
        listener.bind((self.ip_addr, self.peer_port))
        listener.listen(1)
        print("\nWaiting for peer connection...")
        while True:
            self.peer_socket, addr = listener.accept()
            print("Peer connected") 

            # Start thread to handle incoming messages
            threading.Thread(
                target=self.peer_receive_thread,
                daemon=True
            ).start()
    
    def peer_receive_thread(self):
        buffer = ''
        while True:
            try:
                msg = self.peer_socket.recv(2048).decode()
                if not msg:
                    break
                buffer += msg
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    self.receive_message(message)
            except:
                print("Peer disconnected.")
                self.peer_socket = None
                break
    


    def udp_connect(self, server_ip, server_port):
        # establish UDP connection with the server
        self.server_ip = server_ip
        self.server_port = server_port
        self.udp_socket = socket(AF_INET, SOCK_DGRAM) 
        self.udp_socket.bind((self.ip_addr, 0))
        print("connected to server via udp")

    def send_command(self, command, body):
        # send command message to the server
        header  = {
            "msgType": "COMMAND",
            "command": command,
            "senderId": self.username,
            "timestamp": datetime.datetime.now().isoformat(),
            "bodyLength": len((json.dumps(body)).encode())
             }
        
        message = {
            "header": header,
            "body": body
        }
        return message
    
    def send_data(self, command, body):
        # send data message to the server
        header  ={
            "msgType": "DATA",
            "command": command,
            "senderId": self.username,
            "timestamp": datetime.datetime.now().isoformat(),
            "bodyLength": len((json.dumps(body)).encode())
            }
        message = {
            "header": header,
            "body": body
        }
        return message  

    def receive_message(self, message):
        # receive message from the server and process it
        #Still need to disect the message to get the request
        message_dict = json.loads(message)
        header = message_dict["header"]
        body = message_dict["body"]
        
        if header["command"] == 'ACK':
            # process control message
            print('Continue with the next step')
        
        elif header["command"] == "ERROR":
            print("Received ERROR message: ", body)
            # handle error message, you will be given a chance to re-do or terminate

        elif header["command"] == "PING":
            # respond with a PONG message to maintain the connection
            # send a PONG message back to the server automatically

            pong_message = self.send_command("PONG", "")
            #return pong_message
            self.send_message_udp(pong_message)
        
        elif header["command"] == "SEND_TEXT":
            display_message = body['message']
            print(f"{header['senderId']}: ", display_message)

        elif header["command"] == "GTEXT_MESSAGE":
            display_message = body['message']
            print(f"{body['group_name']}-{header['senderId']}: ", display_message)

        elif header["command"] == "VIEW_ONLINE":
            online_users = body['online_users']
            print("Online users: ", online_users)

        elif header["command"] == "EXIT_CHAT":
            print("The chat has ended by the other party.")
            if self.peer_socket:
                self.peer_socket.close()
                self.peer_socket = None

    def send_message_tcp(self, message):
        # send message to the server
        self.client_socket.send((json.dumps(message)+ '\n').encode())

    def send_message_peer(self, message):
        self.peer_socket.send((json.dumps(message)+ '\n').encode())

    def get_connect_message_for_peer(self, timeout=10):
        self.waiting_for_response = True
        try:
            message = self.message_queue.get(timeout=timeout)
            message_dict = json.loads(message)
            header = message_dict["header"]
            body = message_dict["body"]

            if header['command'] == "ACK":
                client_ip, client_port = body['message']
                self.tcp_connect_peer(client_ip, client_port)
                print("connected to target client")
                return True
            else:
                self.receive_message(message)
                return False
        except queue.Empty:
            print("Timeout waiting for connection grant")
            return False
        # self.receive_message(message)

    def get_message_tcp(self):
        # receive message from the server
        message = self.client_socket.recv(2048).decode()
        #return message
        self.receive_message(message)

    def tcp_receive_thread(self):
        buffer = ''
        while True:
            try:
                msg = self.client_socket.recv(2048).decode()
                if not msg:
                    break

                buffer += msg
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)

                    if self.waiting_for_response:
                        self.message_queue.put(message)
                        self.waiting_for_response = False
                    else:
                        self.receive_message(message)

            except:
                print("Server disconnected.")
                break

    def send_message_udp(self, message):
        # send message to the server
        self.udp_socket.sendto((json.dumps(message)).encode(), (self.server_ip, self.server_port))
    
    def get_message_udp(self):
        # receive message from the server
        message, serverAddress = self.udp_socket.recvfrom(2048)
        #return message.decode()
        self.receive_message(message.decode())
    
    def close_connection(self):
        # close the connection with the server
        if self.client_socket:
            self.client_socket.close()
        print("Connection is closed")
    
def main():
    client = None
    server_ip = input("Enter server IP address: ")
    server_port = 12000    #int(input("Enter server port number: ")) 
    
    #client.tcp_connect(server_ip, server_port)
    #client.udp_connect(server_ip, server_port)

    def main_menu1():
        print("Main Menu:\n")
        print("1. REGISTER\n2. LOGIN\n")
    def register():
        print("Welcome")
        nonlocal client
        username = input("Enter your username: ")
        password = input("Enter your password: ")

        client = client_application(username)
        client.tcp_connect(server_ip, server_port)
        client.udp_connect(server_ip, server_port)

        register_message = client.send_command("REGISTER", {"username": client.username, "password": password})
        client.send_message_tcp(register_message)
        time.sleep(1)
        # wait for ACK or ERROR message from the server and process it in receive_message function
    

    def login():
        print("Welcome back")
        nonlocal client 
        username = input("Enter your username: ")
        password = input("Enter your password: ")

        client = client_application(username)
        client.tcp_connect(server_ip, server_port)
        client.udp_connect(server_ip, server_port)
        login_message = client.send_command("LOGIN", {"username": client.username, "password": password})
        client.send_message_tcp(login_message)
        #main_menu2()
        # wait for ACK or ERROR message from the server and process it in receive_message function
        # I'm waiting for the server to check if the login is successful and then send an ACK message, if the login is unsuccessful, it will send an ERROR message and I will handle it in the receive_message function
        #If the login is successful, I will proceed to the main menu 2, if the login is unsuccessful, I will give the user a chance to re-do or terminate
    
    def main_menu2():
        print("Main Menu:\n")
        print("1. 1-on-1 chat\n2. Create Group\n3. View Online Users\n4. LOGOUT\n")
    
    def one_on_one_chat():
        nonlocal client
        # Start listening in background for peer connections
        threading.Thread(target=client.start_peer_listener,daemon=True).start()
        # get the list of users from the server and display them for client to choose which one to chat with
        # when the client chooses, the server obtains the targets ip_adrees and port number so that we can connect
        user = input("Enter the username of the person you want to chat with: ")
        connect_request_message = client.send_command("CONNECT_REQUEST", {"target_user": user})
        client.send_message_tcp(connect_request_message)
        client.get_connect_message_for_peer()
        #client.get_message_tcp()
        while client.peer_socket is not None:
            '''
            message = input("You: ")
            data_message = client.send_data("SEND_TEXT", {"message": message})
            client.send_message_peer(data_message)
            # wait for the other party to send a message and display it, also need to handle if the other party ends the chat by sending an EXIT_CHAT message
            client.get_message_peer()
            if message == 'EXIT_CHAT':
                break
            '''
            message = input("You: ")
            data_message = client.send_data("SEND_TEXT", {"message": message})
            client.send_message_peer(data_message)
            if message == "EXIT_CHAT":
                client.peer_socket.close()
                client.peer_socket = None
                break

        main_menu2()
    
    def create_group():
        group_name = input("Enter the group name: ")
        members = []
        while True:
            member = input("Enter the username of the member you want to add to the group (or type 'done' to finish): ")
            if member == 'done':
                break
            members.append(member)
        create_group_message = client.send_command("CREATE_GROUP", {"group_name": group_name, "members": members})
        client.send_message_tcp(create_group_message)
        
        # wait for ACK or ERROR message from the server and process it
        #client.get_message_tcp()
        message = input("Enter the message to the group ('done' to finish): ")
        gmessage = client.send_data("GTEXT_MESSAGE", {"group_name": group_name, "message": message})
        client.send_message_tcp(gmessage)

        while True:
            #client.get_message_tcp()
            message = input("You: ")
            gmessage = client.send_data("GTEXT_MESSAGE", {"group_name": group_name, "message": message})
            client.send_message_tcp(gmessage)
            if message == 'done':
                break
        main_menu2()

    def view_online_users():
        # send a command message to the server to request the list of online users
        request_message = client.send_command("VIEW_ONLINE", "")
        client.send_message_tcp(request_message)
        # wait for ACK or ERROR message from the server and process it in receive_message function, if ACK, the body will contain the list of online users, if ERROR, handle it in receive_message function
        #client.get_message_tcp()


    def logout():
        logout_message = client.send_command("LOGOUT", "")
        client.send_message_tcp(logout_message)
        # wait for ACK or ERROR message from the server and process it in receive_message function
        #client.get_message_tcp()
        client.close_connection()
        main_menu1()
    #will need to do a while loop when we are still connected to the server
    main_menu1()
    choice = input("Enter your choice: ")
    if choice == '1':
        register()
        login()
    elif choice == '2':
        login()
    while True:
        main_menu2()
        choice2 = input("Enter your choice: ")
        if choice2 == '1':
            one_on_one_chat()
        elif choice2 == '2':
            create_group()
        elif choice2 == '3':
            view_online_users()
        elif choice2 == '4':
            logout()
            break            
        else:
            print("Invalid choice. Please try again.")
    print("Disconnected from server.")

if __name__ == "__main__":
    main()


#196.47.246.187
