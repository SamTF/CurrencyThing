### IMPORTS
import hashlib
import pandas as pd
from os import path

import users as Users

# Constants
DIFFICULTY = 4                          # the amount of characters in a hash that need to match a user's hex to mine successfully
BLOCKCHAIN = 'block.chain'              # the name of the local blockchain file stored on disk
CREATOR_ID = 840976021687762955         # The User that sends rewards to miners
HASH_TRUNC = 8                          # Block hashes will be 8 characters long to be short but avoid collisions
EMOTES     = 'emote_codes.csv'
# FORMAT   = [Transaction ID, Sender, Amount, Receiver, previous plock Hash]
FORMAT     = ['ID', 'INPUT', 'SIZE', 'OUTPUT', 'PREV_HASH']

# >>> COLLISION DETECTED <<<
# It took 166.5872585773468 seconds and 132773 hashes to find a collision

emotes = pd.read_csv(EMOTES)



### THE BLOCKCHAIN CLASS
class Blockchain:
    def __init__(self, chain: pd.DataFrame):
        self.chain          = chain
        # self.current_data   = []
    

    # Adds a new row to the blockchain
    def append(self, data: list):
        id = len(self.chain.index)                                                      # the id# of this transactions
        self.chain.loc[id] = data                                                       # appends it to the blockchain
        self.chain.to_csv(BLOCKCHAIN)                                                   # saves the updated blockchain



    # Checks if the miner was correct
    # Checks that the proof submitted matches hash he generated, and that the hash matches the user's hex ID
    @staticmethod
    def verify(data: str, key: bytes, hash: str, user: Users.User) -> bool:
        # print('[Blockchain] >>> Verifying hash...')
        # print(f'user: {user}\nuser hex: {user.hex}')
        verification = hashlib.blake2s(data.encode(), key=key).hexdigest()

        # checks if the hash was generated correctly
        if (verification != hash):
            print('[Blockchain] >>> INCORRECT HASH')
            return False
        
        # checks if the hash matches the appropriate user's hex ID
        hash_first = verification[:DIFFICULTY]
        if (not user.hex.startswith(hash_first)):
            print('[Blockchain] >>> USER HEX DOES NOT MATCH')
            return False
        
        # if all these checks pass, the miner was correct!
        # if not... l dunno, the block gets rejected?
        print('[Blockchain] >>> HASH OK')
        return True


    def create_block(self, input, size, output):
        # FOUR(?) CHECKS before approving a transaction/block
        # 1. input and output must be different users
        # 2. size must be integer greater than zero
        # 3. check if the mine is the input, and if so ignore rule 4
        # 4. [NON-MINE] check if input has enough coins to fulfill the transaction
        # 5. check if blockchain is empty - if so, don't get the previous block hash because it won't exist - TEMPORARY CHECK ONLY NEEDED FOR FIRST TRANSACTION - REMOVE LATER
        # 6. check that the blockchain bot is not the ouput - maybe?
        # !!! only proceed if all these checks pass !!!

        # Check 1. input and output must be different users
        if (input == output): return ValueError, 'you cant send coins to yourself, stupid :)'

        # Check 2. size must be integer greater than zero
        try:                amount = int(size)
        except:             return ValueError, 'the size must be a whole number'
        if amount <= 0:     return ValueError, 'the size must be larger than 0'

        # Check 3. Mine is input
        if (input != CREATOR_ID):
            # Check 4. must have enough balance to trade
            if self.get_balance(input) < int(size):
                return ValueError, 'not enough coins :('
        
        # Check 5. Empty Blockchain
        prev_hash = 0
        if not self.chain.empty:
            # Hash the previous block
            prev_hash = self.hash_prev_block()[:HASH_TRUNC]                             # gets the hash of the previous block, shortened to only the first X characters
            prev_hash = self.get_emote()
        
        # Check 6. Can't send coins to blockchain bot
        if output == CREATOR_ID: return ValueError, 'you cant send coins to the currency itself :o'

        id = len(self.chain.index)




        # FORMAT = [Transaction ID, Sender, Amount, Receiver, previous plock Hash]
        block_id = len(self.chain.index)                                                # the transaction ID is the current length of the blockchain

        sender = f'<@{input}>'                                                          # using discord @ formating
        receiver = f'<@{output}>'
        # prev_hash = self.hash_prev_block()[:HASH_TRUNC]                                 # hashes the contents of the previous message

        block = [sender, amount, receiver, prev_hash]                                   # formats the block
        self.chain.loc[block_id] = block                                                # appens the block to the blockchain dataframe
        self.chain.to_csv(BLOCKCHAIN)

        block.insert(0, block_id)                                                       # inserts the block_id for the #blockchain channel to know the order of blocks
        block_content = '   '.join(map(str, block))                                     # displays the block as a single string, instead of an array, seperated by spaces

        return block_content, 'block processed successfully :)'



    # Hashes the contents of the previous message with SHA256
    def hash_prev_block(self, index=-1) -> str:
        prev_block = self.chain.iloc[index].tolist()                                       # gets the last row in the dataframe as a list
        block_content = ' '.join(map(str, prev_block))                                  # converts it into a byte string seperated by spaces
        print(f'HASHING PREV BLOCK: {block_content}')
        
        return hashlib.sha256(block_content.encode()).hexdigest()                       # returns the hash of the block's content
    

    # Gets the current balance of a user's wallet -> put this on some kind of wallet script when I have the block stored on disk
    def get_balance(self, user: int) -> int:
        balance = 0
        user = f'<@{user}>'

        for index, row in self.chain.iterrows():                                    # loops through every single row (transaction) in the dataframe (blockchain)
            # ['INPUT', 'SIZE', 'OUTPUT', 'PREV_HASH']
            block = row.tolist()                                                    # converts the pandas row to an array to make this easier
            # print(block)
            if (user in block):                                                     # checks if the user ID is in the transaction
                size    = int(block[1])                                             # the value of the transaction - must convert from str to int
                position    = block.index(user)                                     # the position of the user in the block : 0 = sender, 2 = receiver

                type = -1 if (position==0) else 1                                   # user was the sender(input) if their position in the transaction is 0, therefore making it a negative transaction (spent currency)
                balance += size * type                                              # negative quantity if sender, positive quantity if receiver

        print(f'[{user}] >>> balance: {balance}')
        return balance
    

    # Gets an emote to use as hash for a block
    # Returns an emote, whose contains contains the first 3 or 2 characters in the block hash
    def get_emote(self):
        prev_block = self.chain.iloc[-1].tolist()                                   # gets the last row in the dataframe as a list
        block_content = ' '.join(map(str, prev_block))                              # converts the row into a string seperated by spaces
        h = hashlib.sha256(block_content.encode()).hexdigest()                      # returns the hash of the block's content

        for index, row in emotes.iterrows():
            if h[:3] in row['hash']:
                return row['code']
        
        for index, row in emotes.iterrows():
            if h[:2] in row['hash']:
                return row['code']
        
        for index, row in emotes.iterrows():
            if h[:1] in row['hash']:
                return row['code']
        

