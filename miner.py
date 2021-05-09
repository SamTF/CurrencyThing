###### IMPORTS ############
# my scripts
import blockchain
import users as Users

# other imports
import threading
import numpy
import hashlib

users = Users.create_users()

###### FUNCTIONS ############
# While loop that keeps on mining until a verified hash winner is found
def mine(data: str) -> Users.User:
    mining = True
    while mining:
        i = numpy.random.bytes(32)                                                                      # generates a random bytes value for the hash-guessing
        h = hashlib.blake2s(data.encode(), key=i)                                                       # hashes the current message and random bytes
        hash_first = h.hexdigest()[:blockchain.DIFFICULTY]                                              # gets the first X characters of the hex - depending on the current block difficulty
        # print(h.hexdigest())

        if(hash_first in users.hexes(blockchain.DIFFICULTY)):                                           # checks if the hash matches the hex code of any users
            winner = users.find_hex(hash_first)                                                         # gets the winner's user object
            # key = i.hex()                                                                               # converts the bytes key into hex
            # bytes.fromhex(key)                                                                          # converting it back into bytes
            
            ### debug prints
            print(f'[MINER] >>> {h.hexdigest()}')                                                       # the random bytes key used, for verification purposes
            print(f'[MINER] >>> {winner.name} mined a coin!')                                           # the winner who "mined it" first

            verified = blockchain.Blockchain.verify(data, i, h.hexdigest(), winner)                     # sends the info to the blockchain so that it may verify it, and add it

            if verified:                                                                                # if so, stops mining this message and moves on
                mining = False
                return winner




# the thing
if (__name__ == "__main__"):
    print ("Executed when invoked directly")
else:
    print ("MINER IMPORTED")