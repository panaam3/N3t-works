# User Management
import pandas as pd
import numpy as np


class User_management:
    def __init__(self):
        self.online_users = [] # list of USER OBJECTS (class user [from client app], user:={name: ip address})
        self.db = Database_manager()

    def update_online_users(self, user):
        self.online_users.append(user)

    def login(self, name, password, ip_addr):
        print("logging in")
        
        user = User(name, ip_addr)
        self.update_online_users(user)

        print(self.online_users)
        if self.db.check_user(name) and self.db.verify_user(name, password)==True: return self.acks(0) # change this to some ack message


    def logout(self, user, ip_addr):
        for usr in self.online_users:
            name, ip = usr.get_user()
            if user==name and ip==ip_addr:
                self.online_users.remove(usr)
        print("logging out")
        return self.acks(0)
    
    def register(self, user, password):
        self.db.add_user(user, password)
        print("registering")
        return self.acks(0)

    def create(self, user, group_name, chat_users = []):
        chat_users = [user] + chat_users
        self.db.add_group(group_name, chat_users)
        return self.acks(0)

    def join(self, group_name, user):
        self.db.add_to_group(group_name, user)

    def exit(self, group_name, user):
        self.db.remove_to_group(group_name, user)

    def connect_client(self, user2):
        print(f"trying to connect with {user2}")
        for usr in self.online_users:
            nm, ip = usr.get_user()
            print(f"name: {nm}, ip: {ip}")

        for user in self.online_users:
            name, ip = user.get_user()
            user2, = user2
            if name==user2: return user.get_user(), ip, self.acks(0)

        return None, None, self.acks(1) # user currently not online, must send an offline message

    def group_chat(self, group_name, user, text):

        # get group method
        for addr, conn in self.clients.items():
            try:
                conn.send(text.encode())
            except:
                pass

    def acks(self, numeric):
        ack_error_codes = {0:"ACK", 1:"ERROR"}
        return ack_error_codes.get(numeric)


class User:
    def __init__(self, name, ip_adrr):
        self.name = name
        self.ip = ip_adrr

    def get_user(self):
        return (self.name, self.ip)
    
    
class Database_manager:
    def __init__(self):
        self.file_path = 'database.csv'
        self.groups_path = 'groups_file.csv'
        self.server_data = pd.read_csv(self.file_path)
        self.group_data = pd.read_csv(self.groups_path)

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
        self.group_data = pd.read_csv(self.groups_path)
    
    def add_to_group(self, group_name, user):
        self.refresh()
        self.add_group(group_name, [user])
        

    def add_group(self, column_name, names= []):
        self.refresh()
        
        values_length = len(names)
        current_length = len(self.group_data)

        # Add column if it doesn't exist
        if column_name not in self.group_data.columns:
            self.group_data[column_name] = np.nan

        # Expand dataframe if needed
        if values_length > current_length:
            extra_rows = values_length - current_length
            self.group_data = pd.concat(
                [self.group_data, pd.DataFrame(index=range(extra_rows))],
                ignore_index=True
            )

        # Insert values
        self.group_data.loc[:values_length - 1, column_name] = names

        # Save back
        self.group_data.to_csv(self.groups_path, index=False)

    def remove_to_group(self, group_name, user):
        self.refresh()
        self.group_data.loc[self.group_data[group_name] == user, group_name] = np.nan

        # Remove rows that are entirely NaN
        self.group_data = self.group_data.dropna(how="all")

        self.group_data.to_csv(self.groups_path, index=False)