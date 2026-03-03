# client 
from socket import *
import datetime


class client:
    def __init__(self, username, ip_addr):
        #self.server_ip = server_ip
        #self.server_port = server_port
        self.username = username
        self.ip_addr = ip_addr
        self.client_socket = None
        pass

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
            pass
        
        elif header["msgType"] == "ERROR":
            print("Received ERROR message:", body)
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
            return pong_message
    
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
    

    '''
    function to send via the TCP_connection and also fuction for the UDP connection
    and a main function to run mend everything
    or the send via TCP/UDP can be done in the main function 
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
    "senderId": self.username,
    "timestamp": "2026-02-27T10:02:15Z",
    "bodyLength": 32
  },
  "body": {
    "group-name": "csc3002f",
    "message":"Hello everyone."
  }
}
"""
