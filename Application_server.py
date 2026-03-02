# Application Server
from socket import *
from User_Management import User_management as usm
from User_Management import Database_manager as database


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

    def response(self, request):

        requests = {1:"LOGIN", 2:"LOGOUT", 3:"REGISTER", 4:"JOIN", 5:"EXIT", 6:"CONNECT_REQUEST"}

        # user functions
        login = lambda x, y:self.user_man.login(x, y)
        logout = lambda user:self.user_man.logout(user)
        register = lambda x, y: self.user_man.register(x, y)
        logout = lambda user:self.user_man.logout(user) 
        join = lambda user:self.user_man.join(user)
        exit = lambda user:self.user_man.exit(user)
        connect_request = lambda user1, user2 :self.user_man.connect_client(user1, user2)


    def terminate(self):
        self.connection_socket.close()