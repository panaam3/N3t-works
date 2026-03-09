# User Management Prototype
# March 2026
# author: Phiwumusa Ngidi

import pandas as pd
import numpy as np


class User_management:
    """
    Class: User_management

    This class handles user related operations for the prototype system. 
    It is responsible for managing online users, handling login and logout, 
    registering users, managing group creation and membership updates, returning acknowledgement responses, 
    and attempting peer-to-peer user connection lookup.
    """
    def __init__(self):
        """
        __init__()

        This constructor initialises the user management system. 
        It creates a list for tracking online users and initialises the database manager that is used for reading and writing user and group data.
        """
        self.online_users = []  # list of USER OBJECTS (class user [from client app], user:={name: ip address})
        self.db = Database_manager()

    def update_online_users(self, user, num = 0):
        """
        update_online_users(user)

        This method adds a user to the list of currently online users.

        num = {0, or any number}
        0 - add a client
        any number - remove them 
        """
        if num==0: self.online_users.append(user)
        else: self.online_users.remove(user)

    def login(self, name, password):
        """
        login(name, password)

        This method attempts to log a user into the system by verifying the given username and password against the database. 
        If the credentials are correct, the user is added to the online users list and a success acknowledgement is returned. 
        Otherwise, an error acknowledgement is returned.
        """
        print("logging in")
        
        user = name
    
        print(self.online_users)
        if self.db.verify_user(name, password): 
            self.update_online_users(user)
            return self.acks(0)  # change this to some ack message
        return self.acks(1)

    def logout(self, user):
        """
        logout(user)

        This method removes a user from the list of online users. 
        It searches through the stored online user objects, compares their names with the given user, removes the matching entry, 
        and returns a success acknowledgement.
        """
        for usr in self.online_users:
            name, ip = usr.get_user()
            if user == name:
                self.online_users.remove(usr)
        print("logging out")
        return self.acks(0)
    
    def register(self, user, password):
        """
        register(user, password)

        This method registers a new user by adding their username and password to the database.
         After registration, it returns a success acknowledgement.
        """
        self.db.add_user(user, password)
        print("registering")
        return self.acks(0)

    def create(self, user, group_name, chat_users=[]):
        """
        create(user, group_name, chat_users=[])

        This method creates a new group chat. 
        The creator is added to the beginning of the group member list, and the full group is then stored in the database.
        """
        chat_users = [user] + chat_users
        self.db.add_group(group_name, chat_users)
        return self.acks(0)

    def join(self, group_name, user):
        """
        join(group_name, user)

        This method adds a user to an existing group in the database.
        """
        self.db.add_to_group(group_name, user)
        return self.acks(0)

    def exit(self, group_name, user):
        """
        exit(group_name, user)

        This method removes a user from an existing group in the database.
        """
        self.db.remove_to_group(group_name, user)
        return self.acks(0)

    def connect_client(self, user2):
        """
        connect_client(user2)

        This method attempts to find a requested user in the list of currently online users. 
        If the user is found, the method returns that user together with a success acknowledgement. 
        If the user is not found, it returns None and an error acknowledgement.
        """
        print(f"trying to connect with {user2[0]}")
        print(f"online users: {self.online_users}")

        for user in self.online_users:
            usrr = user2[0]
            print('trying:', usrr)
            if usrr == user:
                print('found', usrr)
                return user, self.acks(0)

        return None, self.acks(1)  # user currently not online, must send an offline message

    def group_chat(self, group_name):
        """
        group_chat(group_name, user, text)

        This method is intended to send a message in a group chat context. In its current prototype form,
        it loops through connected clients and attempts to send the given text to each one. 
        """
        names = self.db.get_group_members(group_name)
        if len(names)!=0: return names
            
        else:
            print(f"Group {names} does not exist or has zero members")
            return self.acks(1)

    def acks(self, numeric):
        """
        acks(numeric)

        This method converts a numeric acknowledgement code into its string equivalent.
        In the current implementation, 0 maps to ACK and 1 maps to ERROR.
        """
        ack_error_codes = {0: "ACK", 1: "ERROR"}
        return ack_error_codes.get(numeric)

    def get_file(self, filepath): # return the file byte size and the data
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            return len(data), data # bytes of the data
        except:
            print("File not found")

    
        

class Database_manager:
    """
    Class: Database_manager

    This class handles persistent storage for the prototype system using comma-separated value files. 
    It is responsible for reading user data, verifying users, adding users, managing group information, and refreshing in-memory data from file.
    """
    def __init__(self):
        """
        __init__()

        This constructor initialises the file paths used for user and group data and loads both files into pandas DataFrames.
        """
        self.file_path = 'database.csv'
        self.groups_path = 'groups_file.csv'

        self.sent_data_path = 'sent_data.csv'
        self.server_data = pd.read_csv(self.file_path)
        self.group_data = pd.read_csv(self.groups_path)

        self.sent_data = pd.read_csv(self.sent_data_path)

    def check_user(self, name):
        """
        check_user(name)

        This method checks whether a given username exists in the user database. It refreshes the data from file, reads the usernames, and returns True if a match is found. Otherwise, it returns False.
        """
        self.refresh()
        names = list(self.server_data['user_name'])
        for n in names:
            if n == name.lower():
                return True
        return False
    
    def verify_user(self, name, password):
        """
        verify_user(name, password)

        This method verifies whether the given username and password match an existing record in the user database. 
        It refreshes the data, compares the username and password entries row by row, and returns True if a valid match is found.
        Otherwise, it returns False.
        """
        self.refresh()
        passwords = list(self.server_data['login_password'])
        names = list(self.server_data['user_name'])
        print("names", names, " passwords", passwords)
        i = 0
        for pw in passwords:
            if pw == password and names[i] == name:
                return True
            i += 1
        return False
    
    def add_user(self, name, password):
        """
        add_user(name, password)

        This method adds a new user to the database. 
        It refreshes the current data, creates a one-row DataFrame for the new user, appends it to the database file, and then refreshes the in-memory data again.
        """
        self.refresh()
        df = pd.DataFrame({"user_name": [name], "login_password": [password]})
        df.to_csv(self.file_path, mode="a", header=False, index=False)
        self.refresh()

    def refresh(self):
        """
        refresh()

        This method reloads both the user data and the group data from their respective files so that the in-memory DataFrames remain up to date.
        """
        self.server_data = pd.read_csv(self.file_path)
        self.group_data = pd.read_csv(self.groups_path)
        self.offline_data = pd.read_csv(self.sent_data_path)
    
    def add_to_group(self, group_name, user):
        self.refresh()

        if group_name not in self.group_data.columns:
            self.group_data[group_name] = pd.Series(dtype="object")
        else:
            self.group_data[group_name] = self.group_data[group_name].astype("object")

        empty_rows = self.group_data[self.group_data[group_name].isna()].index

        if len(empty_rows) > 0:
            insert_index = empty_rows[0]
        else:
            insert_index = len(self.group_data)
            self.group_data = pd.concat(
                [self.group_data, pd.DataFrame(index=[0])],
                ignore_index=True
            )

        self.group_data.loc[insert_index, group_name] = user
        self.group_data.to_csv(self.groups_path, index=False)
        
    def add_group(self, column_name, names=None):
        if names is None:
            names = []

        self.refresh()

        if column_name not in self.group_data.columns:
            self.group_data[column_name] = pd.Series(dtype="object")
        else:
            self.group_data[column_name] = self.group_data[column_name].astype("object")

        # Find first empty row in this group column
        empty_rows = self.group_data[self.group_data[column_name].isna()].index

        if len(empty_rows) > 0:
            start_index = empty_rows[0]
        else:
            start_index = len(self.group_data)

        end_index = start_index + len(names)

        # Expand dataframe if needed
        if end_index > len(self.group_data):
            extra_rows = end_index - len(self.group_data)
            self.group_data = pd.concat(
                [self.group_data, pd.DataFrame(index=range(extra_rows))],
                ignore_index=True
            )

        # Insert new names starting from first free row
        self.group_data.loc[start_index:end_index - 1, column_name] = names

        self.group_data.to_csv(self.groups_path, index=False)

    def remove_to_group(self, group_name, user):
        """
        remove_to_group(group_name, user)

        This method removes a user from a specified group by replacing that user's entry with a missing value. 
        After that, it removes any rows that are entirely empty and saves the updated group data back to file.
        """
        self.refresh()
        self.group_data.loc[self.group_data[group_name] == user, group_name] = np.nan

        # Remove rows that are entirely NaN
        self.group_data = self.group_data.dropna(how="all")

        self.group_data.to_csv(self.groups_path, index=False)

    
    def get_group_members(self, group_name):
        self.refresh()
        try:
            group_members = list(self.group_data[group_name])
            members = []
            for member in group_members:
                if pd.notna(member): members.append(member)
                else: pass
            
            return members if len(members)!=0 else []

        except:
            print(f"Group {group_name} does not exist")
            return
        

    def record_data(self, sender, receiver, datatype, sent_time):
        self.refresh()
        row = {"sender_id": sender,
                "receiver_id": receiver,
                "data_type": datatype,
                "time_stamp": sent_time
               }
        
        new_row = pd.DataFrame([row])
        self.sent_data = pd.concat([self.sent_data, new_row], ignore_index=True)

        self.sent_data.to_csv(self.sent_data_path, index=False)