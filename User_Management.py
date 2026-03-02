# User Management

import pandas as pd
import random

class User_management:
    def __init__(self):
        self.online_users = [] # list of USER OBJECTS (class user [from client app], user:={name: ip address})

    def update_online_users(self, user):
        self.online_users.append(user)

    def login(self, name, password):

        pass

    def logout(self, user):
        
        pass

    def create(self, user, group_name, chat = []):
        # Create a Group chat
        pass

    def register(self, user, password):
        pass

    def join(self, user, groupID):
        pass

    def exit(self, user):
        pass

    def connect_client(self, user1, user2):
        pass

    def group_chat(self, user, text):
        pass


class User:
    def __init__(self, name, ip_adrr):
        self.name = name
        self.ip = ip_adrr

    def get_user(self):
        return (self.name, self.ip)
    

class Database_manager:
    def __init__(self):
        server_data = pd.read_csv()