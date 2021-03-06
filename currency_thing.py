### IMPORTS
# The discord bot commands
from os import name
import discord                                                              # the main discord module
from discord.ext import commands, tasks                                     # commands are obvious, tasks are background loops run every X seconds

# The Slash Commands module - NEW NEW NEW !!
from discord_slash import SlashCommand, SlashContext                        # used to create slash commands /
from discord_slash.utils.manage_commands import create_option               # used to specify the type of argument required

# stores a copy of the blockchain as a dataframe to easily iterate thru it and manipulated it
import pandas as pd

# my own scipts
import users as Users                                                       # stores class objects of all users registered to mine
import blockchain                                                           # stores the dataframe, adds and verifies blocks, calculates user balance
import miner                                                                # mines messages
import explorer                                                             # gets cool statistics and achievements from the blockchain without interfering with it


print("_____________Currency Thing INITIALISED_____________")

#### Constants
TOKEN_FILE = '.currency_thing.token'                                        # Name of the text file storing the unique Discord bot token (very dangerous, do not share)
BLOCKCHAIN  = 840988631044456488

### Variables
Blockchain = None                                                           # the Blockchain object that stores the blockchain as df and does the verifying operations
# tmp_winners_df = pd.DataFrame(columns=['miner', 'count'])                   # tmp dataframe containing all the IDs of users who successfully mined a message
                                                                            # used to sum rewards owed to the same person, to optimise the amount of trades required and to not clog the blockchain
tmp_winners_df = pd.read_csv('tmp_miner_rewards.csv', index_col=0)

###### DISCORD STUFF ############################################################
### Creating the bot!
bot = commands.Bot(command_prefix='coin emoji')

###### EVENTS ######
# Runs this when the bot becomes online
@bot.event
async def on_ready():
    print('what is this, some kinda {}?'.format(bot.user.name))             # just a print in the console to confirm the bot is running
    await bot.change_presence(activity=discord.Game('Status'))              # custom status! (has a new syntax)
    print(bot)                                                              # debug print

    # initiates the blockchain
    global Blockchain
    block_df = await get_blockchain(None)
    Blockchain = blockchain.Blockchain(block_df)
    print(Blockchain)

    # starts the reward-giving task - MUST be after blockchain
    give_mining_rewards.start()

    await update_status()                                                   # updates amount of coins in circulation


## POINT I - LISTEN TO ALL MESSAGES ON GENERAL CHAT
@bot.event
async def on_message(message):
    # This allows the bot to also process comands and analyse every message. WOW! -> https://stackoverflow.com/questions/62076257/discord-py-bot-event
    # await bot.process_commands(message)                                 # not all needed now that we're using slash / commands


    # Any message on not on #Blockchain that is not by this bot
    if (message.channel.id != BLOCKCHAIN) and (message.author.id != bot.user.id):
        id = message.id
        server = message.guild.id
        channel = message.channel.id

        # creates a permalink to the message - for now not used
        link = f'https://discord.com/channels/{server}/{channel}/{id}'
        # print(link)

        ### POINT II - MINE EACH MESSAGE
        # threeading literally not needed because this is an async func! WOW!!! (could need to re-implement the queue if spamming attacks somehow break thru the checks?)
        msg = [message.content, message.author.name, message.created_at]            # gets all the relevant info from the message, and dumps it into an array
        print(msg)
        
        winner = miner.mine(str(msg))                                               # uses the miner.py script to mine it
        await add_tmp_winner(winner.id)                                             # adds user to tmp dataframe




###### FUNCTIONS ######
### POINT III - ANTI-TAMPER MEASURES & POINT IV - ADD TRANSACTION DATA TO THE #BLOCKCHAIN CHANNEL
# Uses the blockchain to create a block for this transaction by adding an ID and hashing the previous block
async def create_block(input, size, output):
    # block = blockchain.create_block(input, size, output)                          # gets the properly formatted and verified block from the blockchain
    block, msg = Blockchain.create_block(input, size, output)                       # gets the properly formatted and verified block from the blockchain

    # check if block is an array and not a ValueError
    if block == ValueError:
        print(f'[VALUE ERROR] >>> {msg}')
        return block, msg

    ### POINT IV - ADD TRANSACTION DATA TO THE #BLOCKCHAIN CHANNEL
    channel = bot.get_channel(BLOCKCHAIN)                                           # gets the #blockchain channel
    await channel.send(block)                                                       # writes the block into the #blockchain channel

    return block, msg                                                               # sends a successful transaction confirmation


# Adds users to the temporary dataframe of miner rewards
async def add_tmp_winner(winner: int):
    global tmp_winners_df

    i = len(tmp_winners_df.index)
    tmp_winners_df.loc[i] = [winner, 1]

    tmp_winners_df.to_csv('tmp_miner_rewards.csv')                                  # saves a backup copy in case the bot crashes


# Custom status tracking amount of currency things in circulation
async def update_status():
    print('[CURRENCY THING] >>> Updating Status')
    # circulation = Blockchain.get_balance(bot.user.id) * -1                          # coins in circulation = the balance of the bot user, but positive
    circulation = Blockchain.get_supply(bot.user.id)
    await bot.change_presence(activity=discord.Game(f'{circulation} things ????????'))



###### COMMANDS ############################################################
# Reads all the messages (transactions) in the blockchain (text channel) and returns that as a dataframe
@bot.command()
async def get_blockchain(ctx):
    df = pd.DataFrame(columns=blockchain.FORMAT)                                    # creates an empty dataframe in the correct format
    df.set_index('ID', inplace=True)                                                # sets the block ID column as the dataframe index
    channel = bot.get_channel(BLOCKCHAIN)                                           # gets the #blockchain text channel

    async for msg in channel.history(limit=None):                                   # loops through every single message in the blockchain
        if msg.author != bot.user: continue                                         # only counts messages by the approved bot (the blockchain manager essentially)

        data = msg.content.split()                                                  # splits the message (by whitespaces) into an array

        if len(data) != 5:  continue                                                # blocks have exactly 5 values, anything else is formatted incorrectly

        i = data.pop(0)                                                             # gets the first item in the array as the transaction ID
        data.append(msg.created_at)                                                 # !! ADDITION - Also saving the trade timestamp
        df.loc[i] = data                                                            # appens the rest of the array to the dataframe

    
    df = df.iloc[::-1]                                                              # reverses the row order, because the discord history starts with the most recent message https://stackoverflow.com/questions/20444087/right-way-to-reverse-a-pandas-dataframe
    df.to_csv('block.chain')                                                        # saves the blockchain to disk
    print(df)

    # await ctx.send(df)
    return df




###### SLASH COMMANDS //// #################################################
slash = SlashCommand(bot, sync_commands=True)                                                                           # Initialises the @slash dectorator - NEEDS THE SYNC COMMANDS to be true
guild_ids = [349267379991347200]                                                                                        # The Server ID - not sure why did this needed

### CURRENCY INTERACTIONS ###
# Gets how many coins a user owns
@slash.slash(name='balance',                                                                                            # Name of the Slash command / not the function itself
            guild_ids=guild_ids,                                                                                        # For some reason, this is needed here, but not on the test command?
            description='Displays a user\'s amount of currency things',                                                 # The command's description in the discord UI
            options=[                                                                                                   # Creating specific types of arguments (refer to the getting started docs linked above)
               create_option(
                 name="user",                                                                                           # MUST HAVE the SAME NAME as the argument in the function
                 description="????????",                                                                                     # coin emojis
                 option_type=6,                                                                                         # 6 = Discord User
                 required=False
               )
            ])
async def balance(ctx, user=None):
    # getting the balance of ALL users
    if user == None:
        # user = ctx.author
        print('[CURRENCY THING] >>> Getting all user balance')

        users = Blockchain.chain.groupby(['OUTPUT']).sum().index.to_list()                                              # getting a list of all the users that own currency things
        msg = "**--- Balance Of All Users ---**\n"                                                                      # string to store the output messages, to send them all at once

        for user in users:
            id = user[2:20]                                                                                             # extracts the user ID, removing the mention syntax ("<@000>")
            b = Blockchain.get_balance(id)                                                                              # gets the balance of that user with the Blockchain.py script
            msg += (f'{user} owns **{b}** currency things ????\n')                                                        # appens the user's balance to the discord channel using @mentions instead of username to the string

        await ctx.send(msg)                                                                                             # sends message with all users' balance
        return                                                                                                          # ends the function right here

    # otherwise gets balance of specific user
    print(f'[CURRENCY THING] >>> Getting balance of user: {user}')
    
    b = Blockchain.get_balance(str(user.id))                                                                            # gets the balance of that user with the Blockchain.py script
    await ctx.send(f'{user} owns **{b}** currency things ????')




# SEND COINS! :D much wow such cool
@slash.slash(name='send',                                                                                               # Name of the Slash command / not the function itself
            guild_ids=guild_ids,                                                                                        # For some reason, this is needed here
            description='Send currency things to other people!',                                                        # The command's description in the discord UI
            options=[                                                                                                   # Creating specific types of arguments (refer to the getting started docs linked above)
               create_option(
                 name="size",                                                                                           # MUST HAVE the SAME NAME as the argument in the function
                 description="how many currency things to send?",                                                       # coin emojis
                 option_type=4,                                                                                         # 4 = Integer
                 required=True
               ),
               create_option(
                   name='output',
                   description='who do you want to send currency things to? ????',
                   option_type=6,
                   required=True                                                                                        # 6 = Discord User
               )
            ])
async def send(ctx, size, output):
    print(f'{ctx.author} sending {size} coins to {output}')
    block, msg = await create_block(ctx.author.id, size, output.id)                                                     # Gives the Blockchain the signal to process the transaction, returning an error message if any
    
    if block == ValueError:                                                                                             # Displays error message if there was an error
        await ctx.send(msg)
        return
    
    await ctx.send(f'*Successfuly sent {size} currency things to {output}! ????*')                                          # Otherwise, display Success message


### MILESTONES & ACHIEVEMENTS ###
@slash.slash(name='milestones',
            guild_ids=guild_ids,
            description='???? Who mined the milestone Currency Things? ????')
async def milestones(ctx):
    msg = explorer.get_mining_milestones(Blockchain.blockchain)

    await ctx.send(msg)


###### TASKS #################################################
@tasks.loop(hours=24)
async def give_mining_rewards():
    print('[CURRENCY THING] >>> Giving miners their rewards')
    global tmp_winners_df

    if tmp_winners_df.empty:   return                                                                                   # does nothing if the dataframe is empty
    
    count = tmp_winners_df.groupby(['miner']).sum()                                                                     # sums all rows with the same miner
    print(count)

    for user, row in count.iterrows():                                                                                  # loops thru all the rows in the counted df
        await create_block(bot.user.id, row[0], user)                                                                   # creates a new block for each winner
    

    tmp_winners_df = tmp_winners_df[0:0]                                                                                # resets the dataframe
    tmp_winners_df.to_csv('tmp_miner_rewards.csv')                                                                      # saves a backup copy in case the bot crashes

    await update_status()                                                                                               # updates amount of coins in circulation


##################################################################################




###### RUNNING THE BOT #################################################
if (__name__ == "__main__"):
    with open(TOKEN_FILE, 'r') as f:
        token = f.read()
    bot.run(token)

else:
    print ("DISCORD BOT IMPORTED")