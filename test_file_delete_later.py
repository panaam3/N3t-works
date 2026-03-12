
from UserM import Database_manager as db


data = db()
data.remove_to_group("Group1","aya")
print(data.get_group_members("Group1"))


d = {1:"hi", 2:"no"}

d.pop(1)

a = [1,2,3,"hi"]
a.remove("hi")
print(list({1:"a", 2:"b"}.items()))