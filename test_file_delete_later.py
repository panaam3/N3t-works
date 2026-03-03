# testing file 

from User_Management import Database_manager as dm


database = dm()

print(database.server_data)

database.add_user("ayabonga", "l259gqt553")
print(database.server_data)