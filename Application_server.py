# Application Server Prototype
# March 2026
# @author: Phiwumusa Ngidi

from socket import *
from UserM import User_management as usm
import json
from datetime import datetime
import threading
import time

class Server:
    """
    Class: Server

    This class represents the application server for the
    prototype system. It is responsible for starting the
    server, accepting client connections, receiving client
    messages, processing protocol requests, and sending
    responses back to clients.
    """

    def __init__(self):
        """
        __init__()

        This constructor initialises the server by creating
        a user management object and then starting the
        server immediately.
        """
        self.user_man = usm()
        self.start_server()

    users_connectionsockets = {}  # identify or map sockets with with username
    users_addr = {}  # port numbers identified or mapped with username, {username: addr = (ip, port)}

    # Function that processes requests and returns responses to the client application
    """
    This server handles the main protocol commands used by
    the client application. These include login, logout,
    register, group creation, group join, group exit, peer
    connection requests, and group text messages.
    """

    def response(self, sender_id, command, data=()):
        """
        response(sender_id, command, data=())

        This method processes a client command and routes it
        to the appropriate user management function. It uses
        the command value to determine which operation must
        be performed, then returns the corresponding server
        acknowledgement or response message.
        """

        requests = {
            1: "LOGIN",
            2: "LOGOUT",
            3: "REGISTER",
            4: "CREATE",
            5: "JOIN",
            6: "EXIT",
            7: "CONNECT_REQUEST",
            8: "GTEXT_MESSAGE",
            9: "FILE_TRANSFER",
            10: "VIEW_ONLINE",
            11: "VIEW_GROUPS",
        }

        # user functions
        login = lambda x, y: self.user_man.login(x, y)
        register = lambda x, y: self.user_man.register(x, y)
        join = lambda user, groupID: self.user_man.join(user, groupID)
        exit = lambda user: self.user_man.exit(user)
        connect_request = lambda user2: self.user_man.connect_client(user2)
        group_message = lambda group_name: self.user_man.group_chat(group_name)
        create = lambda user, name, chat: self.user_man.create(user, name, chat)
        

        if command == requests.get(1):
            x, y = data
            ack_responce = login(x, y)
            return ack_responce


        if command == requests.get(3):
            x, y = data
            ack_responce = register(x, y)
            return ack_responce
        
        if command == requests.get(2):
            return "logout"

        if command == requests.get(4):
            user, name, members = data
            ack_responce = create(user, name, members)
            return ack_responce

        if command == requests.get(5):
            user, groupID = data
            ack_responce = join(user, groupID)
            return ack_responce

        if command == requests.get(6):
            user, groupID = data
            ack_responce = exit(user, groupID)
            return ack_responce

        if command == requests.get(7):
            user2 = data
            user_, ack_responce = connect_request(user2)

            if user_ is None:
                return self.build_control_message(
                    ack_responce,
                    100,
                    1,
                    body={"ERROR": "USER NOT FOUND ON SYSTEM"}
                )

            addr = Server.get_userAddr(user_)
            data = self.build_control_message(
                "ACK",
                100,
                0,
                {"message": addr}
            )
            # print(data)
            connection_socket = Server.users_connectionsockets.get(sender_id)
            target = user2[0]

            print(f"Notifying {target} to start listening")
            self.send_to_client(Server.get_userSocket(target), self.build_control_message("LISTEN", 1,1))
            time.sleep(1)
            print("sent peer address")
            self.send_to_client(connection_socket, data)
            return ack_responce

        if command == requests.get(8):
            user, groupID, msg = data
            names_or_ack = group_message(groupID)
            print("SENDING TO GROUP MEMBERS:", names_or_ack)
            try:
                for name in names_or_ack:
                    print(name)
                    try:
                        conn = Server.get_userSocket(name)
                        msg_j = self.build_control_message("GTEXT_MESSAGE", 0, 0, {"group-name":groupID, "message":msg}, "DATA", user)
                        print("trying to send message '",msg,"' to group :", groupID )
                        self.send_to_client(conn, msg_j)
                        return self.user_man.acks(0)
                    except:
                        print(f"Message not sent to Client {name}, with address {Server.get_userAddr(name)}.")
            except:
                print("error occured") 
                return ack_responce
            

        if command==requests.get(9):
            # group, filename, filetype
            group, filename, filetype, filesize = data
            save_path = f"files/{filetype}/{filename}"
            got = 0
            with open(save_path, "wb") as f:
                while got< filesize:
                    packet = Server.get_userSocket(sender_id).recv(filesize)
                    if not packet:
                        break
                    f.write(packet)
                    got+=len(packet)

            group_members = self.user_man.db.get_group_members(group)
            msg = self.build_control_message("FILE_TRANSFER", 10, 0, {"sender":sender_id,"filename":filename, "filetype":filetype, "filesize":filesize})
            
            for member in group_members:
                self.send_to_client(Server.get_userSocket(member), msg) # alert clients a file is on the way by giving the file details
            
            with open(save_path, "rb") as f:
                data = f.read()

            for member in group_members:
                self.send_to_client(Server.get_userSocket(member), data, True)
            
            return self.user_man.acks(1)

        if command==requests.get(10):
            users= self.user_man.get_online_users()

            if len(users)!=0: 
                print(users)
                return self.build_message("ONLINE_USERS", 0, 0, {"users":users})
            else: 
                return self.build_control_message("ONLINE_USERS", 0, 1)
            
        if command==requests.get(11):
            return self.build_message("VIEW_GROUPS", 1,1,{"groups": self.user_man.db.get_groups()})
        
    def parse_json(self, raw_json):
        """
        parse_json(raw_json)

        This method parses a raw JSON string into its
        protocol components. It extracts the header fields,
        reads the body if present, converts the body values
        into a tuple, and returns all parsed information in
        a structured form.
        """
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

            return (
                sender_id,
                msg_type,
                command,
                timestamp,
                body_length,
                body_tuple,
                body
            )

        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
        except Exception as e:
            raise ValueError(f"Malformed MMMP message: {e}")

    def build_message(
        self,
        msg_type,
        command,
        sender_id,
        body=None,
        seq_no=None,
        status_code=None
    ):
        """
        build_message(msg_type, command, sender_id, body=None,
        seq_no=None, status_code=None)

        This method builds a general protocol message in JSON
        format. It creates the header, calculates the body
        length, includes optional fields where necessary, and
        returns the final message as a JSON string ready to
        be sent over the network.
        """
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

    def build_control_message(self, command, seq_no, status_code, body=None, msgType= "CONTROL", senderID="server"):
        """
        build_control_message(command, seq_no, status_code,
        body)

        This method builds a control message used by the
        server to send acknowledgement or error responses.
        It creates a control header, calculates the body
        length, attaches the body if present, and returns
        the final JSON string.
        """

        if body is None:
            body = {}

        # Compute body length
        body_json = json.dumps(body)
        body_length = len(body_json.encode()) if body else 0

        header = {
            "msgType": msgType,
            "command": command,
            "status_code": status_code,
            "version": "MMMP/1.0",
            "seqNo": seq_no,
            "senderId": senderID,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "bodyLength": body_length
        }

        message = {
            "header": header
        }

        if body_length > 0:
            message["body"] = body

        return json.dumps(message)

    def send_to_client(self, connection_socket, data, files=False):
        """
        send_to_client(connection_socket, data)

        This method sends data to a connected client through
        the given socket. A newline character is appended so
        that message boundaries can be detected correctly on
        the receiving side.
        """
        if files: connection_socket.sendall(data.encode())
        else: connection_socket.send((data + '\n').encode())  # send modified message to the server socket (then back to the current client)

    def receive_client_data(self, connection_socket, num=1, username=""):
        """
        receive_client_data(connection_socket, num=1)

        This method continuously receives incoming data from
        a client socket. It collects chunks into a buffer,
        separates complete messages using newline markers,
        processes each message, and sends back any resulting
        control response.

        When num is 1, the method stays in continuous listen
        mode. When num is not 1, it handles the initial
        client message and returns the username.
        """

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

                    
                        ctrl_msg = self.process_data(raw_message)
                        if ctrl_msg=="logout":
                            break
                        else:
                            self.send_to_client(connection_socket, ctrl_msg)

                except (BrokenPipeError, ConnectionResetError, OSError):
                    addr = Server.users_addr.pop(username)
                    Server.users_connectionsockets.pop(username)
                    print("client with address", addr, "and username:", username, "disconnected")
                    self.user_man.update_online_users(username, 1)
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
                    try:
                        if not raw_message.strip():
                            continue

                        bool, login_msg = self.process_data(raw_message)

                        self.send_to_client(connection_socket, login_msg)

                        client_json = self.parse_json(raw_message)
                        username = client_json[0]
                        return bool, username
                    except ValueError:
                        print("-")
                        return False
                    
        self.user_man.logout(username)
        Server.users_connectionsockets.get(username).close()
        Server.users_connectionsockets.pop(username)
        Server.users_addr.pop(username)
        # self.user_man.update_online_users(username, 1)
        print(f"finished session for client {username}.")

    def process_data(self, raw_data):  # raw_data is a JSON
        """
        process_data(raw_data)

        This method processes a raw JSON message received by
        the server. It parses the message, determines the
        message type, routes it to the correct response
        handler, and then builds the appropriate control
        message to return to the client.
        """

        if not raw_data or not raw_data.strip():
            return None
        else:
            sender_id, msg_type, command, timestamp, body_length, body_tuple, body = self.parse_json(raw_data)

            if command=="LOGIN":
                ack = self.response(sender_id, command, body_tuple)  # (name, password)
                print(body)
                if self.user_man.acks(0) == ack:
                    return True, self.build_control_message(ack, 100, 0, {"": ""})
            
                return False, self.build_control_message(
                    ack,
                    100,
                    1,
                    {"ERROR": "an error occured, error code 1"}
                )

            elif command == "VIEW_ONLINE":
                users= self.user_man.get_online_users()

                if len(users)!=0: 
                    print("*********ONLINE USERS**********")
                    print(self.build_control_message("VIEW_ONLINE", 0, 0, {"users":users}))
                    return self.build_control_message("VIEW_ONLINE", 0, 0, {"users":users})
                else: 
                    return self.build_control_message("VIEW_ONLINE", 0, 1)                

            elif msg_type == "COMMAND" and command != "CONNECT_REQUEST":
                # print(body_tuple)
                ack = self.response(sender_id, command, body_tuple) 

            elif command == "CONNECT_REQUEST":
                ack = self.response(sender_id, command, body_tuple)

            elif command=="VIEW_ONLINE":
                return self.response(sender_id, command, body_tuple)
            
            elif command=="VIEW_GROUPS":
                data = self.response(sender_id, command, body_tuple) 
                return data
            
            elif msg_type == "DATA":
                # add a handler here for possible errors in version2
                ack = self.response(sender_id, command, body_tuple)

            if self.user_man.acks(0) == ack:
                return self.build_control_message(ack, 100, 0, {"": ""})
            elif ack=="logout":
                return "logout"
            return self.build_control_message(
                ack,
                100,
                1,
                {"ERROR": "an error occured, error code 1"}
            )

    def get_userSocket(username):
        """
        get_userSocket(username)

        This method returns the stored connection socket for
        a given username from the shared server mapping.
        """
        return Server.users_connectionsockets.get(username)

    def get_userAddr(username):
        """
        get_userAddr(username)

        This method returns the stored network address for a
        given username from the shared server mapping.
        """
        return Server.users_addr.get(username)

    def establish_connection(self):
        """
        establish_connection()

        This method continuously accepts new client
        connections. For each connected client, it receives
        the initial message, stores the client's username,
        address, and socket, and then starts a separate
        thread to continue listening for that client's data.
        """
        while True:
            connection_socket, addr = self.server_socket.accept()  # accepts clients establishing connections
            print("Connected to client")
            bool, username = self.receive_client_data(connection_socket, 0)
            print(bool)
            if bool:
                Server.users_addr[username] = addr
                Server.users_connectionsockets[username] = connection_socket
                print(Server.users_addr)
                threading.Thread(
                    target=self.receive_client_data,
                    args=(connection_socket, 1, username),
                    daemon=True
                ).start()
            else:
                pass

    def terminate(self):  # server closes
        """
        terminate()

        This method closes the main server socket and
        terminates the server.
        """
        self.server_socket.close()

    def start_server(self):
        """
        start_server()

        This method creates the main server socket, binds it
        to the chosen port, starts listening for incoming
        client connections, and then calls the connection
        establishment loop.
        """
        server_port = 12000
        self.server_socket = socket(AF_INET, SOCK_STREAM)  # SOCK_STREAM: TCP
        self.server_socket.bind(('', server_port))  # Binds or locks the port number to be 'server_port' instead of the assigning it to the OS
        self.server_socket.listen(50)  # waits for a client connection
        print("Server listening on port", server_port)
        self.establish_connection()


if __name__ == "__main__":
    print("Starting server...")
    server = Server()