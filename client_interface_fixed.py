
# client_interface_fixed.py

import os
from socket import *
import datetime
import time
import json
import threading
import queue
import csv
from app import socketio


class client_application:

    def __init__(self, ip_addr="0.0.0.0", peer_port=8000):

        self.server_ip = "196.42.96.83"
        self.server_port = 12000

        self.username = None

        self.ip_addr = ip_addr
        self.peer_port = peer_port

        self.client_socket = None
        self.udp_socket = None

        self.peer_socket = None
        self.peer_listener_socket = None

        self.listener_started = False

        self.peer_lock = threading.Lock()
        self.peer_connected_event = threading.Event()

        self.message_queue = queue.Queue()
        self.waiting_for_response = False

        self.login_event = threading.Event()
        self.login_success = False
        self.login_error_message = ""

    # -------------------------------
    # TCP CONNECTION
    # -------------------------------

    def tcp_connect(self, server_ip=None, server_port=None):

        if server_ip:
            self.server_ip = server_ip

        if server_port:
            self.server_port = server_port

        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.connect((self.server_ip, self.server_port))

        self.client_socket = sock

        print("Connected to server")

        threading.Thread(
            target=self.tcp_receive_thread,
            daemon=True
        ).start()

    # -------------------------------
    # UDP CONNECTION
    # -------------------------------

    def udp_connect(self, server_ip, server_port):

        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.bind(("", 0))

        self.server_ip = server_ip
        self.server_port = server_port

    # -------------------------------
    # PEER CONNECT
    # -------------------------------

    def tcp_connect_peer(self, peer_ip, peer_port):

        try:

            sock = socket(AF_INET, SOCK_STREAM)
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

            sock.connect((peer_ip, peer_port))

            with self.peer_lock:

                if self.peer_socket:
                    try:
                        self.peer_socket.close()
                    except:
                        pass

                self.peer_socket = sock

            self.peer_connected_event.set()

            print(f"Connected to peer {peer_ip}:{peer_port}")

            threading.Thread(
                target=self.peer_receive_thread,
                daemon=True
            ).start()

            return True

        except Exception as e:

            print("Peer connection failed:", e)
            return False

    # -------------------------------
    # PEER LISTENER
    # -------------------------------

    def start_peer_listener(self):

        if self.listener_started:
            return

        self.listener_started = True

        threading.Thread(
            target=self._listener_loop,
            daemon=True
        ).start()

    def _listener_loop(self):

        listener = socket(AF_INET, SOCK_STREAM)
        listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        listener.bind(("", self.peer_port))
        listener.listen(5)

        self.peer_listener_socket = listener

        print(f"Listening for peers on {self.peer_port}")

        while True:

            try:

                sock, addr = listener.accept()

                print("Incoming peer:", addr)

                with self.peer_lock:

                    if self.peer_socket:
                        try:
                            self.peer_socket.close()
                        except:
                            pass

                    self.peer_socket = sock

                self.peer_connected_event.set()

                threading.Thread(
                    target=self.peer_receive_thread,
                    daemon=True
                ).start()

            except Exception as e:
                print("Listener stopped:", e)
                break

    # -------------------------------
    # MESSAGE BUILDERS
    # -------------------------------

    def send_command(self, command, body):

        header = {
            "msgType": "COMMAND",
            "command": command,
            "senderId": self.username,
            "timestamp": datetime.datetime.now().isoformat(),
            "bodyLength": len(json.dumps(body).encode())
        }

        return {"header": header, "body": body}

    def send_data(self, command, body):

        header = {
            "msgType": "DATA",
            "command": command,
            "senderId": self.username,
            "timestamp": datetime.datetime.now().isoformat(),
            "bodyLength": len(json.dumps(body).encode())
        }

        return {"header": header, "body": body}

    # -------------------------------
    # SEND SOCKET MESSAGES
    # -------------------------------

    def send_message_tcp(self, message):

        if self.client_socket:
            self.client_socket.sendall((json.dumps(message) + "\n").encode())

    def send_message_udp(self, message):

        if self.udp_socket:
            self.udp_socket.sendto(
                json.dumps(message).encode(),
                (self.server_ip, self.server_port)
            )

    def send_message_peer(self, message):

        with self.peer_lock:
            sock = self.peer_socket

        if sock is None:
            print("No peer connected")
            return False

        try:

            sock.sendall((json.dumps(message) + "\n").encode())
            return True

        except Exception as e:

            print("Peer send error:", e)

            with self.peer_lock:

                try:
                    sock.close()
                except:
                    pass

                self.peer_socket = None

            self.peer_connected_event.clear()

            return False

    # -------------------------------
    # RECEIVE THREADS
    # -------------------------------

    def tcp_receive_thread(self):

        buffer = ""

        while True:

            try:

                data = self.client_socket.recv(4096)

                if not data:
                    print("Server disconnected")
                    break

                buffer += data.decode()

                while "\n" in buffer:

                    message, buffer = buffer.split("\n", 1)

                    if not message.strip():
                        continue

                    if self.waiting_for_response:
                        self.message_queue.put(message)
                    else:
                        self.receive_message(message)

            except Exception as e:

                print("TCP receive error:", e)
                break

    def peer_receive_thread(self):

        buffer = ""

        while True:

            try:

                with self.peer_lock:
                    sock = self.peer_socket

                if sock is None:
                    break

                data = sock.recv(4096)

                if not data:
                    print("Peer disconnected")
                    break

                buffer += data.decode(errors="ignore")

                while "\n" in buffer:

                    message, buffer = buffer.split("\n", 1)

                    if message.strip():
                        self.receive_message(message)

            except Exception as e:
                print("Peer receive error:", e)
                break

        with self.peer_lock:

            if self.peer_socket:
                try:
                    self.peer_socket.close()
                except:
                    pass

            self.peer_socket = None

        self.peer_connected_event.clear()

    # -------------------------------
    # RECEIVE MESSAGE HANDLER
    # -------------------------------

    def receive_message(self, message):

        try:
            message_dict = json.loads(message)
        except:
            print("Invalid JSON")
            return

        header = message_dict.get("header", {})
        body = message_dict.get("body", {})

        command = header.get("command")

        if command == "SEND_TEXT":

            sender = header.get("senderId", "Unknown")
            text = body.get("message", "")

            print(f"{sender}: {text}")

            socketio.emit(
                "new_message",
                {
                    "chat_name": sender,
                    "message": text
                },
                room=self.username
            )

            self.offline_data_rec(message_dict)

        elif command == "FILE_TRANSFER":

            filename = body.get("fileName")
            filesize = body.get("fileSize")
            sender = header.get("senderId")

            with self.peer_lock:
                sock = self.peer_socket

            if sock:
                self.receive_file(sock, filename, filesize, sender)

    # -------------------------------
    # FILE TRANSFER
    # -------------------------------

    def send_file(self, filepath, target):

        threading.Thread(
            target=self._send_file_worker,
            args=(filepath, target),
            daemon=True
        ).start()

    def _send_file_worker(self, filepath, target):

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        body = {
            "target": target,
            "fileName": filename,
            "fileSize": filesize
        }

        message = self.send_data("FILE_TRANSFER", body)

        with self.peer_lock:
            sock = self.peer_socket

        if sock is None:
            print("Peer disconnected")
            return

        sock.sendall((json.dumps(message) + "\n").encode())

        with open(filepath, "rb") as f:

            while True:

                chunk = f.read(4096)

                if not chunk:
                    break

                sock.sendall(chunk)

        print("File sent")

    def receive_file(self, sock, filename, filesize, sender):

        os.makedirs("app/static/uploads/received", exist_ok=True)

        filepath = os.path.join(
            "app/static/uploads/received",
            os.path.basename(filename)
        )

        received = 0

        with open(filepath, "wb") as f:

            while received < filesize:

                chunk = sock.recv(min(4096, filesize - received))

                if not chunk:
                    break

                f.write(chunk)
                received += len(chunk)

        socketio.emit(
            "uploaded_files",
            {
                "chat_name": sender,
                "name": os.path.basename(filename),
                "url": filepath
            },
            room=self.username
        )

        print("File received:", filename)

    # -------------------------------
    # OFFLINE STORAGE
    # -------------------------------

    def offline_data_rec(self, message):

        filename = "chat_history.csv"

        if not os.path.exists(filename):

            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "sender_id",
                    "receiver_id",
                    "offline_data",
                    "time_stamp"
                ])

        header = message["header"]
        body = message["body"]

        row = [
            header.get("senderId"),
            self.username,
            body.get("message"),
            header.get("timestamp")
        ]

        with open(filename, "a", newline="") as f:

            writer = csv.writer(f)
            writer.writerow(row)

    # -------------------------------
    # CLEANUP
    # -------------------------------

    def close_connection(self):

        sockets = [
            self.peer_socket,
            self.peer_listener_socket,
            self.client_socket,
            self.udp_socket
        ]

        for sock in sockets:
            try:
                if sock:
                    sock.close()
            except:
                pass

        self.peer_socket = None
        self.client_socket = None
        self.udp_socket = None

        self.peer_connected_event.clear()

        print("Connections closed")
