# client 
from socket import *
import datetime


class client_application:
    def __init__(self, username, ip_addr='localhost'):
        self.server_ip = None
        self.server_port = None
        self.username = username
        self.ip_addr = ip_addr
        self.client_socket = None

    def tcp_connect(self, server_ip, server_port):
        # establish TCP connection with the server
        self.server_ip = server_ip
        self.server_port = server_port
        client_socket = socket(AF_INET, SOCK_STREAM) 
        client_socket.connect((server_ip,server_port)) # establish the TCP Connection 
        self.client_socket = client_socket
        print("connected to server")
       
    def udp_connect(self, server_ip, server_port):
        # establish UDP connection with the server
        self.server_ip = server_ip
        self.server_port = server_port
        client_socket = socket(AF_INET, SOCK_DGRAM) 
        print("connected to server")

    def send_command(self, command, body):
        # send command message to the server
        header  = {
            "msgType": "COMMAND",
            "command": command,
            "version": "MMMP/1.0",
            "seqNo": 2001,
            "senderId": self.username,
            "timestamp": datetime.datetime.now().isoformat(),
            "bodyLength": len(body)
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
            "version": "MMMP/1.0",
            "seqNo": 2002,
            "senderId": self.username,
            "timestamp": datetime.datetime.now().isoformat(),
            "bodyLength": len(body)
            }
        message = {
            "header": header,
            "body": body
        }
        return message  

    def receive_message(self, message):
        # receive message from the server and process it
        #Still need to disect the message to get the request
        message_dict = message
        header = message_dict["header"]
        body = message_dict["body"]
        
        if header["msgType"] == 'ACK':
            # process control message
            print('Continue with the next step')
        
        elif header["msgType"] == "ERROR":
            print("Received ERROR message: ", body)
            # handle error message, you will be given a chance to re-do or terminate

        
        elif header["msgType"] == "CONNECT_GRANT":
            # provides the target client's IP address and port number
            #assumption that the body will only contain the tuple (ip_adres, port_number)
            cLient_ip, client_port = body['message']
            self.tcp_connect(cLient_ip, client_port)
            print("connected to target client")
            
        
        elif header["msgType"] == "PING":
            # respond with a PONG message to maintain the connection
            # send a PONG message back to the server automatically
            pong_message = self.send_command("PONG", "")
            #return pong_message
            self.send_message_udp(pong_message)
        
        elif header["msgType"] == "SEND_TEXT":
            display_message = body['message']
            print("Them: ", display_message)

        elif header["msgType"] == "GTEXT_MESSAGE":
            display_message = body['message']
            print(f"{body['group_name']}-{header['senderId']}: ", display_message)

        elif header["msgType"] == "VIEW_ONLINE":
            online_users = body['online_users']
            print("Online users: ", online_users)

        elif header["msgType"] == "EXIT_CHAT":
            print("The chat has ended by the other party.")
            self.close_connection()  # Still need to revisit this maybe it will also end the connection with the server too


    def send_message_tcp(self, message):
        # send message to the server
        self.client_socket.send(str(message).encode())

    def get_message_tcp(self):
        # receive message from the server
        message = self.client_socket.recv(2048).decode()
        #return message
        self.receive_message(message)

    def send_message_udp(self, message):
        # send message to the server
        self.client_socket.sendto(str(message).encode(), (self.server_ip, self.server_port))
    
    def get_message_udp(self):
        # receive message from the server
        message, serverAddress = self.client_socket.recvfrom(2048)
        #return message.decode()
        self.receive_message(message.decode())
    
    def close_connection(self):
        # close the connection with the server
        if self.client_socket:
            self.client_socket.close()
        print("Connection is closed")
    
def main():
    username = input("Enter your username: ")
    client = client_application(username)

    server_ip = input("Enter server IP address: ")
    server_port = int(input("Enter server port number: ")) 
    
    client.tcp_connect(server_ip, server_port)

    def main_menu1():
        print("Main Menu:\n")
        print("1. REGISTER\n2. LOGIN")
    def register():
        password = input("Enter your password: ")
        register_message = client.send_command("REGISTER", {"username": client.username, "password": password})
        client.send_message_tcp(register_message)
        # wait for ACK or ERROR message from the server and process it in receive_message function
        login()

    def login():
        print("Welcome back, ", client.username)
        password = input("Enter your password: ")
        login_message = client.send_command("LOGIN", {"username": client.username, "password": password})
        client.send_message_tcp(login_message)
        #main_menu2()
        # wait for ACK or ERROR message from the server and process it in receive_message function
        # I'm waiting for the server to check if the login is successful and then send an ACK message, if the login is unsuccessful, it will send an ERROR message and I will handle it in the receive_message function
        #If the login is successful, I will proceed to the main menu 2, if the login is unsuccessful, I will give the user a chance to re-do or terminate
    
    def main_menu2():
        print("Main Menu:\n")
        print("1. 1-on-1 chat\n2. Create Group\n3. View Online Users\n4. LOGOUT")
    
    def one_on_one_chat():
        # get the list of users from the server and display them for client to choose which one to chat with
        # when the client chooses, the server obtains the targets ip_adrees and port number so that we can connect
        user = input("Enter the username of the person you want to chat with: ")
        connect_request_message = client.send_command("CONNECT_REQUEST", {"target_user": user})
        client.send_message_tcp(connect_request_message)
        client.receive_message(client.get_message_tcp())
        while True:
            message = input("You: ")
            data_message = client.send_data("SEND_TEXT", {"message": message})
            client.send_message_tcp(data_message)
            # wait for the other party to send a message and display it, also need to handle if the other party ends the chat by sending an EXIT_CHAT message
            client.get_message_tcp()
            if message == 'EXIT_CHAT':
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
        client.receive_message(client.get_message_tcp())
        message = input("Enter the message to the group ('done' to finish): ")
        gmessage = client.send_data("GTEXT_MESSAGE", {"group_name": group_name, "message": message})
        client.send_message_tcp(gmessage)

        while True:
            client.get_message_tcp()
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
        client.receive_message(client.get_message_tcp())


    def logout():
        logout_message = client.send_command("LOGOUT", "")
        client.send_message_tcp(logout_message)
        # wait for ACK or ERROR message from the server and process it in receive_message function
        client.receive_message(client.get_message_tcp())
        client.close_connection()
        main_menu1()

    main_menu1()
    choice = input("Enter your choice: ")
    if choice == '1':
        register()
    elif choice == '2':
        login()
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
        else:
            print("Invalid choice. Please try again.")
    else:
        print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

#196.47.246.187