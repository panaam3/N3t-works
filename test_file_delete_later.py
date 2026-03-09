
from UserM import Database_manager as db


data = db()
data.remove_to_group("Group1","aya")
print(data.get_group_members("Group1"))


d = {1:"hi", 2:"no"}

d.pop(1)

print(d)