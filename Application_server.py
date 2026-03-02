# Application Server
from socket import *
from User_Management import User_management as usm
from User_Management import Database_manager as database
import json

class Server:
    def __init__(self):
        self.user_man = usm()
        server_port = 12000
        
        self.server_socket = socket(AF_INET, SOCK_STREAM) # SOCK_STREAM: TCP 
        self.server_socket.bind(('', server_port)) # Binds or locks the port number to be 'server_port' instead of the assigning it to the OS
        self.server_socket.listen(50) # waits for a client connection
        self.connection_socket, self.addr = self.server_socket.accept() #accepts clients establishing connections
        

    # Function that processes requests and returns responses to the client application
    """
      LOGIN > Initiates a client session.
    • LOGOUT > Terminates a client session.
    • REGISTER > Registers a new client identity.
    • JOIN > Adds a client to a group communication room.
    • EXIT > Removes a client from a group communication room.
    • CONNECT_REQUEST > client asks the server for another clients IP/port
    
    """

    def response(self, command, data = ()):

        requests = {1:"LOGIN", 2:"LOGOUT", 3:"REGISTER", 4:"CREATE", 5:"JOIN" , 6:"EXIT", 7:"CONNECT_REQUEST", 8:"GTEXT_MESSAGE"}

        # user functions
        login = lambda x, y:self.user_man.login(x, y)
        register = lambda x, y: self.user_man.register(x, y)
        logout = lambda user:self.user_man.logout(user) 
        join = lambda user, groupID:self.user_man.join(user, groupID)
        exit = lambda user:self.user_man.exit(user)
        connect_request = lambda user1, user2 :self.user_man.connect_client(user1, user2)
        group_message = lambda user1, text :self.user_man.group_chat(user1, text)
        create = lambda user, name, chat:self.user_man.create(user, name, chat)


        if command==requests.get(1): 
            x, y = data
            ack_responce = login(x, y)
            return ack_responce
        
        if command==requests.get(2): 
            user,  = data
            ack_responce = logout(user)
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
            user1, user2 = data
            ack_responce = connect_request(user1, user2)
            return ack_responce
        
        if command==requests.get(8): 
            user, groupID, msg = data
            ack_responce = group_message(user, groupID, msg)
            return ack_responce 
        


    def parse_json(self, raw_json):
        try:
            # 1Convert JSON string → Python dict
            message = json.loads(raw_json)

            header = message.get("header", {})
            body = message.get("body", {})

            # Extract required header fields
            sender_id = header.get("senderId")
            msg_type = header.get("msgType")
            command = header.get("command")
            timestamp = header.get("timestamp")
            body_length = header.get("bodyLength", 0)

            # Convert body dictionary → tuple of values
            # If bodyLength = 0, return empty tuple
            if body_length == 0 or not body:
                body_tuple = ()
            else:
                body_tuple = tuple(body.values())

            return (sender_id, msg_type, command, timestamp, body_length, body_tuple)

        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")

        except Exception as e:
            raise ValueError(f"Malformed MMMP message: {e}")

    def terminate(self):
        self.connection_socket.close()




'''

'''
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