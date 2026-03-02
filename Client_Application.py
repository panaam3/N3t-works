# client 
from socket import *
import json
import datetime


class client:
    def __init__(self):
        #self.server_ip = server_ip
        #self.server_port = server_port
        #self.username = username
        #self.ip_addr = ip_addr
        pass

    def tcp_connect(self, server_ip, server_port):
        # establish TCP connection with the server
        self.server_ip = server_ip
        self.server_port = server_port

        client_socket = socket(AF_INET, SOCK_STREAM) 
        client_socket.connect((server_ip,server_port)) # establish the TCP Connection 
        #self.client_socket = client_socket

    def send_command(self, command, body):
        # send command message to the server
        header  = {
            "msgType": "COMMAND",
            "command": command,
            "version": "MMMP/1.0",
            "seqNo": 2001,
            "senderId": self.username,
            "timestamp": datetime.datetime.now().isoformat(),
            "bodyLength": len(json.dumps(body))
             }
        
        message = {
            "header": header,
            "body": body
        }
        return message
    
    def send_data(self, command, body):
        # send data message to the server
        pass

    def receive_message(self, message):
        # receive message from the server and process it
        #Still need to disect the message to get the request
        pass


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
