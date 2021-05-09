import pandas

USERS_FILE = 'users.csv'
user_df = pandas.read_csv(USERS_FILE, index_col=0)
print(user_df)
print('\n\n\n')


# This class stores user information in an easily accessible object, and generates their hex
class User:
    def __init__(self, id, name):
        self.id     = int(id)
        self.name   = str(name)
        self.hex    = hex(id)[2:]
    
    def __repr__(self):                                                                     # this is what gets output in the console when you print the object. cool! -> https://www.pythontutorial.net/python-oop/python-__repr__/
        return f'User: {self.id} | {self.name} | {self.hex}'


# This class stores a list of all users, and some useful finder functions
class Users:
    def __init__(self, users):                                                              # initialised Users given a list of User objects
        self.users = users
    
    def add_user(self, id, name):
        new_user = User(id, name)                                                           # creating the new User object
        self.users.append(user_df)                                                          # adding it to the list currently in memory
        
        user_df.loc[id] = [name]                                                            # adding it to the .csv file on disk
        user_df.to_csv(USERS_FILE)                                                          # saves the file with the new users to disk


    @property
    def names(self):
        for user in self.users:
            yield (user.name)
    
    def hexes(self, length=None):
        for user in self.users:
            yield user.hex[:length]
    
    def find(self, id):
        for user in self.users:
            if(user.id == id):
                return user
    
    def find_hex(self, h):
        for user in self.users:
            if(user.hex.startswith(h)):
                return user
    
    def find_name(self, n):
        for user in self.users:
            if(user.name == n):
                return user
    

# Reads the data in USERS_FILE and stores that as User objects into a Users list
def create_users():
    users = []
    for index, row in user_df.iterrows():
        users.append(User(index, row['Username']))
    
    users = Users(users)
    return users


# users = create_users()
# # testing if adding more users works - it does!
# users.add_user(0000000000000, "God")
# for user_df in users.users: print(user_df)



# the thing
if (__name__ == "__main__"):
    print ("Executed when invoked directly")
    # testing if adding more users works - it does!
    users = create_users()
    users.add_user(0000000000000, "God")
    for user_df in users.users: print(user_df)
else:
    print ("USERS IMPORTED")


