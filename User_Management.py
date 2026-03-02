# User Management

import pandas as pd


class User_management:
    def __init__(self):
        self.online_users = [] # list of USER OBJECTS (class user [from client app], user:={name: ip address})

    def update_online_users(self, user):
        self.online_users.append(user)

    def login(self, user, password):
        
        pass

    def logout(self, user):
        
        pass

    def create(self, user, password):
        # Create a client-to-client & group chat
        pass

    def register(self, user, password):
        pass

    def join(self, user):
        pass

    def exit(self, user):
        pass

    def connect_client(self, user1, user2):
        pass

class Database_manager:
    def __init__(self):
        server_data = pd.read_csv()