# Application Server
from socket import *
from UserM import User_management as usm
import json
from datetime import datetime
import threading

class Server:

    def __init__(self):
        self.user_man = usm()
        self.start_server()

    users_connectionsockets = {} # identify or map sockets with with username
    users_addr = {} # port numbers identified or mapped with username, username: addr = (ip, port)
        
    # Function that processes requests and returns responses to the client application
    """
      LOGIN > Initiates a client session.
    • LOGOUT > Terminates a client session.
    • REGISTER > Registers a new client identity.
    • JOIN > Adds a client to a group communication room.
    • EXIT > Removes a client from a group communication room.
    • CONNECT_REQUEST > client asks the server for another clients IP/port
    
    """

    def response(self, sender_id, command, data = ()):

        requests = {1:"LOGIN", 2:"LOGOUT", 3:"REGISTER", 4:"CREATE", 5:"JOIN" , 6:"EXIT", 7:"CONNECT_REQUEST", 8:"GTEXT_MESSAGE"}

        # user functions
        login = lambda x, y:self.user_man.login(x, y)
        register = lambda x, y: self.user_man.register(x, y)
        logout = lambda user:self.user_man.logout(user) 
        join = lambda user, groupID:self.user_man.join(user, groupID)
        exit = lambda user:self.user_man.exit(user)
        connect_request = lambda user2 :self.user_man.connect_client(user2)
        group_message = lambda user1, text :self.user_man.group_chat(user1, text)
        create = lambda user, name, chat:self.user_man.create(user, name, chat)


        if command==requests.get(1): 
            x, y = data
            ack_responce = login(x, y)
            return ack_responce
        
        if command==requests.get(2): 
            user,  = data
            ack_responce = logout(user, sender_id)
            return ack_responce
        
        if command==requests.get(3): 
            x, y = data
            ack_responce = register(x, y)
            return ack_responce
        
        if command==requests.get(4): 
            user, name, members = data
            ack_responce = create(user, name, members)
            return ack_responce
        
        if command==requests.get(5): 
            user, groupID = data
            ack_responce = join(user, groupID)
            return ack_responce        

        if command==requests.get(6): 
            user, groupID = data
            ack_responce = exit(user, groupID)
            return ack_responce 
        
        if command==requests.get(7): 
            user2 = data
            user_ , ack_responce = connect_request(user2)

            if user_ is None:
                return self.build_control_message(ack_responce, 100, 1, body={"ERROR":"USER NOT FOUND ON SYSTEM"})
            
            addr = Server.get_user(user_)
            data = self.build_control_message("ACK", 100,0, {"messsage": addr})
            connection_socket = Server.users_addr.get(user_)

            print("sent peer address")
            self.send_to_client(connection_socket, data)
            return ack_responce
        
        if command==requests.get(8): 
            user, groupID, msg = data
            ack_responce = group_message(user, groupID, msg)
            return ack_responce 
        


    def parse_json(self, raw_json):
        try:
            # Convert JSON string Python dict
            message = json.loads(raw_json)

            header = message.get("header", {})
            body = message.get("body", {})

            # Extract required header fields
            sender_id = header.get("senderId")
            msg_type = header.get("msgType")
            command = header.get("command")
            timestamp = header.get("timestamp")
            body_length = header.get("bodyLength", 0)

            # Convert body dictionary tuple of values
            # If bodyLength = 0, return empty tuple
            if body_length == 0 or not body:
                body_tuple = ()
            else:
                body_tuple = tuple(body.values())

            return (sender_id, msg_type, command, timestamp, body_length, body_tuple, body)

        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
        except Exception as e:
            raise ValueError(f"Malformed MMMP message: {e}")
        


    def build_message(self, msg_type, command, sender_id, body=None, seq_no=None, status_code=None):
        # Default empty body
        if body is None:
            body = {}

        # Convert body to JSON string to calculate byte length
        body_json = json.dumps(body)
        body_length = len(body_json.encode()) if body else 0

        header = {
            "msgType": msg_type,
            "command": command,
            "version": "MMMP/1.0",
            "senderId": sender_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "bodyLength": body_length
        }

        # Optional fields
        if seq_no is not None:
            header["seqNo"] = seq_no

        if status_code is not None:
            header["status_code"] = status_code

        message = {
            "header": header
        }

        # Only include body if it exists
        if body_length > 0:
            message["body"] = body

        # Convert dict JSON string bytes (ready for TCP send)
        return json.dumps(message)


    def build_control_message(self, command, seq_no, status_code, body=None):
        """
        command: "ACK" or "ERROR"
        seq_no: sequence number of the original request
        status_code: protocol status code (e.g., 2 = success, 5 = error)
        body: optional dict (only used for ERROR typically)
        """

        if body is None:
            body = {}

        # Compute body length
        body_json = json.dumps(body)
        body_length = len(body_json.encode()) if body else 0

        header = {
            "msgType": "CONTROL",
            "command": command,
            "status_code": status_code,
            "version": "MMMP/1.0",
            "seqNo": seq_no,
            "senderId": "server",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "bodyLength": body_length
        }

        message = {
            "header": header
        }

        if body_length > 0:
            message["body"] = body

        return json.dumps(message)
    

    def send_to_client(self, connection_socket, data):
        connection_socket.send((data + '\n').encode())# send modified message to the server socket (then back to the current client)

    def receive_client_data(self, connection_socket, num=1):

        
        buffer = ''

        if num == 1:
            while True:
                try:
                    chunk = connection_socket.recv(1024).decode()

                    if not chunk:
                        print("client disconnected")
                        break

                    buffer += chunk

                    while '\n' in buffer:
                        raw_message, buffer = buffer.split('\n', 1)

                        if not raw_message.strip():
                            continue

                        print("connected, everything good")
                        ctrl_msg = self.process_data(raw_message)

                        if ctrl_msg:
                            self.send_to_client(connection_socket, ctrl_msg)

                except (BrokenPipeError, ConnectionResetError, OSError):
                    print("disconnected")
                    break
                except ValueError as e:
                    print(f"Bad message received: {e}")
        else:
            buffer = ''
            while True:
                chunk = connection_socket.recv(1024).decode()

                if not chunk:
                    return None

                buffer += chunk

                while '\n' in buffer:
                    raw_message, buffer = buffer.split('\n', 1)

                    if not raw_message.strip():
                        continue

                    login_msg = self.process_data(raw_message)
                    self.send_to_client(connection_socket, login_msg)

                    client_json = self.parse_json(raw_message)
                    username = client_json[0]
                    return username
            

        
    def process_data(self, raw_data): # raw_data is a JSON
        
        if not raw_data or not raw_data.strip():
            return None
        else :
            sender_id, msg_type, command, timestamp, body_length, body_tuple, body = self.parse_json(raw_data)

            if msg_type =="COMMAND" and command!="CONNECT_REQUEST":
                print(body_tuple)
                ack= self.response(sender_id, command, body_tuple) # (name, password)

            if command=="CONNECT_REQUEST":
                ack = self.response(sender_id, command, body_tuple)
                    

            # can only be a group message on the server side
            if msg_type =="DATA":
                # add a handler here for possible errors in version2 
                ack  = self.response(sender_id, command, body_tuple)

            if self.user_man.acks(0) == ack: return self.build_control_message(ack, 100, 0, {"":""})
            return self.build_control_message(ack, 100, 1, {"ERROR":"an error occured, error code 1"})

    def listen_for_data(self, connection_socket):
        client_threads = threading.Thread(target=self.receive_client_data, args=(connection_socket,))
        client_threads.start()

    def get_user(username):
        return Server.users_addr.get(username)
    
    def establish_connection(self):
        while True:
            connection_socket, addr = self.server_socket.accept() #accepts clients establishing connections
            print("Connected to client")
            username = self.receive_client_data(connection_socket, 0)
            Server.users_addr[username] = addr
            Server.users_connectionsockets[username] = connection_socket
            print(Server.users_addr)
            threading.Thread(target=self.receive_client_data, args=(connection_socket,1), daemon=True).start()


    def terminate(self): # server closes
        self.server_socket.close()


    def start_server(self):
        server_port = 12000
        self.server_socket = socket(AF_INET, SOCK_STREAM) # SOCK_STREAM: TCP 
        self.server_socket.bind(('', server_port)) # Binds or locks the port number to be 'server_port' instead of the assigning it to the OS
        self.server_socket.listen(50) # waits for a client connection
        print("Server listening on port", server_port)
        self.establish_connection()


if __name__ == "__main__":
    print("Starting server...")
    server = Server()

"""

1. command message: 
{
  "header": {
    "msgType": "COMMAND",
    "command": "CREATE",
    "version": "MMMP/1.0",
    "seqNo": 2001,
    "senderId": "client_23",
    "timestamp": "2026-02-27T10:02:15Z",
    "bodyLength": 32
  },
  "body": {
    "group-name": "csc3002f",
    "members":["client_232", "client_222"]
  }
}

2. control message example

{
  "header": {
    "msgType": "CONTROL",
    "command": "ACK",
    "status_code":2,
    "version": "MMMP/1.0",
    "seqNo": 2001,
    "senderId": "server",
    "timestamp": "2026-02-27T10:02:15Z",
    "bodyLength": 0
  }
}


3. Data message

{
  "header": {
    "msgType": "DATA",
    "command": "GTEXT_MESSAGE",
    "version": "MMMP/1.0",
    "seqNo": 2002,
    "senderId": "client_23"
    "timestamp": "2026-02-27T10:02:15Z",
    "bodyLength": 32
  },
  "body": {
    "group-name": "csc3002f",
    "message":"Hello everyone."
  }
}


"""