# User Management

import pandas as pd
import random

class User_management:
    def __init__(self):
        self.online_users = [] # list of USER OBJECTS (class user [from client app], user:={name: ip address})
        self.db = Database_manager()

    def update_online_users(self, user):
        self.online_users.append(user)

    def login(self, name, password):
        if self.db.check_user(name) and self.db.verify_user(name, password)==True: return True # change this to some ack message


    def logout(self, user):
        
        pass

    def create(self, user, group_name, chat = []):
        # Create a Group chat
        pass

    def register(self, user, password):
        pass

    def join(self, user, groupID):
        pass

    def exit(self, user, groupID):
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
        self.file_path = 'database.csv'
        self.server_data = pd.read_csv(self.file_path)


    def check_user(self, name):
        self.refresh()
        names = list(self.server_data['user_name'])
        for n in names:
            if n==name.lower(): return True
        return False
    
    def verify_user(self, name, password):
        self.refresh()
        passwords = list(self.server_data['login_password'])
        names = list(self.server_data['user_name'])

        i = 0 
        for pw in passwords: 
            if pw==password and names[i]==name:
                return True
            i+=1
        return False
    
    def add_user(self, name, password):
        self.refresh()
        df = pd.DataFrame({"user_name":[name], "login_password":[password]})
        df.to_csv(self.file_path, mode="a", header=False, index=False)
        self.refresh()

    def refresh(self):
        self.server_data = pd.read_csv(self.file_path)