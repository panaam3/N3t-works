
# Text book example of UDP socket programming, server application
# @author: 

from socket import *

server_port = 12000

# description in doc string below  
server_socket = socket(AF_INET, SOCK_DGRAM) 

'''
socket class/module provides the socket interface for the applicatio-layer of the network application. 
AF_INET indicates that the network is using IPv4, SOCK_DGRAM is the UDP Protocol.
'''

server_socket.bind(('', server_port)) 
# bind function binds the server_port number to the socket of the application-layer of the server, for ID'ing the process



print("The server is ready to receive")
while True:
    msg, client_address = server_socket.recvfrom(2048)
    modified_msg = msg.decode().upper()
    server_socket.sendto(modified_msg, client_address)
