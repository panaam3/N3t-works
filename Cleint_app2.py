# client
from socket import *
import datetime
import time
import json
import threading
import queue


class client_application:
    def __init__(self, username, ip_addr="0.0.0.0", peer_port=8000):
        # Server connection details
        self.server_ip = None
        self.server_port = None

        # Client identity / peer settings
        self.username = username
        self.ip_addr = ip_addr
        self.peer_port = peer_port

        # Sockets
        self.client_socket = None
        self.udp_socket = None
        self.peer_socket = None
        self.peer_listener_socket = None

        # Threading / coordination
        self.message_queue = queue.Queue()
        self.waiting_for_response = False
        self.listener_started = False
        self.peer_lock = threading.Lock()

    def tcp_connect(self, server_ip, server_port):
        # establish TCP connection with the server
        self.server_ip = server_ip
        self.server_port = server_port

        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        self.client_socket = client_socket

        print("connected to server")

        # START BACKGROUND LISTENER FOR SERVER MESSAGES
        threading.Thread(target=self.tcp_receive_thread, daemon=True).start()

    def tcp_connect_peer(self, peer_ip, peer_port):
        # establish TCP connection with the target client for 1-on-1 chat
        try:
            peer_socket = socket(AF_INET, SOCK_STREAM)
            peer_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            peer_socket.connect((peer_ip, peer_port))

            with self.peer_lock:
                # close old peer socket if one somehow exists
                if self.peer_socket is not None and self.peer_socket is not peer_socket:
                    try:
                        self.peer_socket.close()
                    except:
                        pass

                self.peer_socket = peer_socket

            print(f"connected to target client at {peer_ip}:{peer_port}")

            # Start receiver thread for peer messages
            threading.Thread(target=self.peer_receive_thread, daemon=True).start()
            return True

        except Exception as e:
            print(f"Could not connect to target client at {peer_ip}:{peer_port}")
            print(f"Reason: {e}")
            return False

    def start_peer_listener(self):
        # start a TCP listener so other clients can connect to me
        if self.listener_started:
            return

        listener = socket(AF_INET, SOCK_STREAM)
        listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # IMPORTANT:
        # Bind to all interfaces so remote machines can reach this listener.
        # Binding to localhost would only allow same-machine connections.
        listener.bind(("", self.peer_port))
        listener.listen(5)

        self.peer_listener_socket = listener
        self.listener_started = True

        print(f"\nWaiting for peer connection on port {self.peer_port}...")

        while True:
            try:
                incoming_peer_socket, addr = listener.accept()

                print(f"Peer connected from {addr[0]}:{addr[1]}")

                with self.peer_lock:
                    # If already in a chat, replace the old peer socket
                    if self.peer_socket is not None:
                        try:
                            self.peer_socket.close()
                        except:
                            pass
                    self.peer_socket = incoming_peer_socket

                # Start thread to handle incoming peer messages
                threading.Thread(target=self.peer_receive_thread, daemon=True).start()

            except Exception as e:
                print(f"Peer listener stopped or failed: {e}")
                break

    def peer_receive_thread(self):
        # receive peer-to-peer messages
        buffer = ''

        while True:
            try:
                with self.peer_lock:
                    current_peer_socket = self.peer_socket

                if current_peer_socket is None:
                    break

                msg = current_peer_socket.recv(2048).decode()

                if not msg:
                    print("Peer disconnected.")
                    with self.peer_lock:
                        try:
                            current_peer_socket.close()
                        except:
                            pass
                        if self.peer_socket is current_peer_socket:
                            self.peer_socket = None
                    break

                buffer += msg

                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)

                    if message.strip():
                        self.receive_message(message)

            except Exception:
                print("Peer disconnected.")
                with self.peer_lock:
                    try:
                        if self.peer_socket is not None:
                            self.peer_socket.close()
                    except:
                        pass
                    self.peer_socket = None
                break

    def udp_connect(self, server_ip, server_port):
        # establish UDP connection with the server
        self.server_ip = server_ip
        self.server_port = server_port

        self.udp_socket = socket(AF_INET, SOCK_DGRAM)

        # bind to any available local port on all interfaces
        self.udp_socket.bind(("", 0))

        print("connected to server via udp")

    def send_command(self, command, body):
        # build a command message to the server
        header = {
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
        # build a data message
        header = {
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
        # receive message from the server or peer and process it
        try:
            message_dict = json.loads(message)
        except json.JSONDecodeError:
            print("Received invalid JSON message.")
            return

        header = message_dict.get("header", {})
        body = message_dict.get("body", {})
        command = header.get("command", "")

        if command == "ACK":
            print("Continue with the next step")

        elif command == "ERROR":
            print("Received ERROR message:", body)

        elif command == "PING":
            # respond automatically
            pong_message = self.send_command("PONG", "")
            self.send_message_udp(pong_message)

        elif command == "SEND_TEXT":
            display_message = body.get("message", "")
            print(f"{header.get('senderId', 'Unknown')}: {display_message}")

        elif command == "GTEXT_MESSAGE":
            display_message = body.get("message", "")
            group_name = body.get("group_name", "GROUP")
            print(f"{group_name}-{header.get('senderId', 'Unknown')}: {display_message}")

        elif command == "VIEW_ONLINE":
            online_users = body.get("online_users", [])
            print("Online users:", online_users)

        elif command == "EXIT_CHAT":
            print("The chat has ended by the other party.")
            with self.peer_lock:
                if self.peer_socket:
                    try:
                        self.peer_socket.close()
                    except:
                        pass
                    self.peer_socket = None

        else:
            # for debugging unknown messages
            print("Received:", message_dict)

    def send_message_tcp(self, message):
        # send message to the server
        self.client_socket.send((json.dumps(message) + '\n').encode())

    def send_message_peer(self, message):
        # send message directly to peer
        with self.peer_lock:
            if self.peer_socket is None:
                print("No peer is connected.")
                return

            try:
                self.peer_socket.send((json.dumps(message) + '\n').encode())
            except Exception as e:
                print(f"Failed to send message to peer: {e}")
                try:
                    self.peer_socket.close()
                except:
                    pass
                self.peer_socket = None

    def get_connect_message_for_peer(self, timeout=10):
        # wait for server response for CONNECT_REQUEST
        self.waiting_for_response = True

        try:
            message = self.message_queue.get(timeout=timeout)
            message_dict = json.loads(message)
            header = message_dict.get("header", {})
            body = message_dict.get("body", {})

            if header.get("command") == "ACK":
                # SERVER RETURNS THE WRONG PORT, SO WE IGNORE IT.
                # We use the returned IP, but force the known peer listening port.
                client_ip, _returned_port = body.get("message", [None, None])

                if client_ip is None:
                    print("Server did not provide a peer IP.")
                    return False

                success = self.tcp_connect_peer(client_ip, self.peer_port)
                return success

            else:
                self.receive_message(message)
                return False

        except queue.Empty:
            print("Timeout waiting for connection grant")
            return False
        except Exception as e:
            print(f"Failed to process connection grant: {e}")
            return False

    def get_message_tcp(self):
        # blocking receive from server, mostly unused because background thread handles it
        message = self.client_socket.recv(2048).decode()
        self.receive_message(message)

    def tcp_receive_thread(self):
        # background receiver for server TCP messages
        buffer = ''

        while True:
            try:
                msg = self.client_socket.recv(2048).decode()

                if not msg:
                    print("Server disconnected.")
                    break

                buffer += msg

                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)

                    if not message.strip():
                        continue

                    if self.waiting_for_response:
                        self.message_queue.put(message)
                        self.waiting_for_response = False
                    else:
                        self.receive_message(message)

            except Exception:
                print("Server disconnected.")
                break

    def send_message_udp(self, message):
        # send UDP message to server
        self.udp_socket.sendto((json.dumps(message)).encode(), (self.server_ip, self.server_port))

    def get_message_udp(self):
        # receive UDP message from server
        message, serverAddress = self.udp_socket.recvfrom(2048)
        self.receive_message(message.decode())

    def close_connection(self):
        # close all sockets
        try:
            if self.peer_socket:
                self.peer_socket.close()
        except:
            pass

        try:
            if self.peer_listener_socket:
                self.peer_listener_socket.close()
        except:
            pass

        try:
            if self.client_socket:
                self.client_socket.close()
        except:
            pass

        try:
            if self.udp_socket:
                self.udp_socket.close()
        except:
            pass

        print("Connection is closed")


def main():
    client = None

    server_ip = input("Enter server IP address: ").strip()
    server_port = 12000

    def main_menu1():
        print("Main Menu:\n")
        print("1. REGISTER\n2. LOGIN\n")

    def register():
        print("Welcome")
        nonlocal client

        username = input("Enter your username: ").strip()
        password = input("Enter your password: ").strip()

        client = client_application(username)
        client.tcp_connect(server_ip, server_port)
        client.udp_connect(server_ip, server_port)

        register_message = client.send_command(
            "REGISTER",
            {"username": client.username, "password": password}
        )
        client.send_message_tcp(register_message)

        time.sleep(1)

    def login():
        print("Welcome back")
        nonlocal client

        username = input("Enter your username: ").strip()
        password = input("Enter your password: ").strip()

        client = client_application(username)
        client.tcp_connect(server_ip, server_port)
        client.udp_connect(server_ip, server_port)

        login_message = client.send_command(
            "LOGIN",
            {"username": client.username, "password": password}
        )
        client.send_message_tcp(login_message)

        time.sleep(1)

    def main_menu2():
        print("Main Menu:\n")
        print("1. 1-on-1 chat\n2. Create Group\n3. View Online Users\n4. LOGOUT\n")

    def one_on_one_chat():
        nonlocal client

        # Start listening in background once
        if not client.listener_started:
            threading.Thread(target=client.start_peer_listener, daemon=True).start()
            time.sleep(0.5)

        user = input("Enter the username of the person you want to chat with: ").strip()

        if not user:
            print("No username entered.")
            return

        connect_request_message = client.send_command(
            "CONNECT_REQUEST",
            {"target_user": user}
        )
        client.send_message_tcp(connect_request_message)

        connected = client.get_connect_message_for_peer()

        if not connected:
            print("Could not establish peer connection.")
            return

        while True:
            with client.peer_lock:
                if client.peer_socket is None:
                    print("Chat ended.")
                    break

            message = input("You: ")

            data_message = client.send_data("SEND_TEXT", {"message": message})
            client.send_message_peer(data_message)

            if message == "EXIT_CHAT":
                with client.peer_lock:
                    try:
                        if client.peer_socket:
                            client.peer_socket.close()
                    except:
                        pass
                    client.peer_socket = None
                break

    def create_group():
        nonlocal client

        group_name = input("Enter the group name: ").strip()
        members = []

        while True:
            member = input("Enter the username of the member you want to add to the group (or type 'done' to finish): ").strip()
            if member == 'done':
                break
            if member:
                members.append(member)

        create_group_message = client.send_command(
            "CREATE_GROUP",
            {"group_name": group_name, "members": members}
        )
        client.send_message_tcp(create_group_message)

        message = input("Enter the message to the group ('done' to finish): ")
        gmessage = client.send_data(
            "GTEXT_MESSAGE",
            {"group_name": group_name, "message": message}
        )
        client.send_message_tcp(gmessage)

        while True:
            message = input("You: ")
            gmessage = client.send_data(
                "GTEXT_MESSAGE",
                {"group_name": group_name, "message": message}
            )
            client.send_message_tcp(gmessage)

            if message == 'done':
                break

    def view_online_users():
        nonlocal client

        request_message = client.send_command("VIEW_ONLINE", "")
        client.send_message_tcp(request_message)

    def logout():
        nonlocal client

        logout_message = client.send_command("LOGOUT", "")
        client.send_message_tcp(logout_message)
        time.sleep(0.5)
        client.close_connection()

    main_menu1()
    choice = input("Enter your choice: ").strip()

    if choice == '1':
        register()
        login()
    elif choice == '2':
        login()
    else:
        print("Invalid choice.")
        return

    while True:
        main_menu2()
        choice2 = input("Enter your choice: ").strip()

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