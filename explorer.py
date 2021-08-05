### BLOCK CHAIN EXPLORER
### This script gets interestings statistics and achievements from the blockchain. It doesn't not modify the blockchain in any way, only reads data from it.

### IMPORTS
import pandas as pd

pd.options.mode.chained_assignment = None


###### CONSTANTS        ##############################################################################################################
CREATOR_ID = 840976021687762955         # The User that sends rewards to miners
BLOCKCHAIN = 'block.chain'              # the name of the local blockchain file stored on disk

###### HELPER FUNCTIONS ##############################################################################################################
def get_blockchain():
    '''
    Reads the blockchain from disk.
    '''
    chain = pd.read_csv(BLOCKCHAIN)
    chain['SIZE'] = pd.to_numeric(chain['SIZE'])                                # Converts the SIZE column into INT type; otherwise it assumes STRING type
    chain['TIME'] = pd.to_datetime(chain['TIME'])                               # Converts the TIME column into datetime format

    return chain


def get_thousands(supply) -> int:
    '''
    Rounds down the thing supply to the nearest thousand.
    '''
    i = str(supply)[:-3]                                                        # removes the last 3 characters
    thousands = int(i) * 1000                                                   # multiplies the thousandth figures by 1000

    return thousands


def user_list(blockchain: pd.DataFrame) -> list:
    '''
    Returns a list of all users to ever received a currency thing.
    '''
    return blockchain.groupby(['OUTPUT']).sum().index.to_list()                 # getting a list of all the users that own currency things as discord @mentions



###### GENERAL BLOCKCHAIN ##############################################################################################################
def get_supply(blockchain: pd.DataFrame) -> int:
    '''
    Gets the total amount of currency things in circulation / the amount mined
    '''
    INPUT = blockchain.groupby(['INPUT']).sum()                                     # INPUT  Dataframe - sums all currency things SENT BY each user - where the user is on the INPUT  side of the trade
    supply = INPUT.loc[f'<@{CREATOR_ID}>']['SIZE']                                  # Sums all currency things sent by the discord bot - aka total supply
    print(f'[EXPLORER] >>> Current supply: {supply}')

    return supply


def supply_over_tx(blockchain: pd.DataFrame) -> int:
    '''
    Returns the total amount of currency things in circulation at each transaction ID.
    '''
    INPUT = blockchain.loc[blockchain['INPUT'] == f'<@{CREATOR_ID}>']           # All currency things sent by the Currency Thing bot (mined)
    INPUT.drop(['INPUT', 'OUTPUT', 'PREV_HASH', 'TIME'], axis=1, inplace=True)# Removes unnecessary columns

    print('[EXPLORER] >>> SUPPLY OVER TX')

    return INPUT.cumsum() 


###### USER ACHIEVEMENTS ##############################################################################################################
def who_mined_xth_thing(thing: int, blockchain: pd.DataFrame, cum_supply: pd.DataFrame):
    '''
    Finds the user who mined the Nth currency thing. Returns the trade ID.

    thing: the Nth thing.
    cum_supply: the cumulative supply of the blockchain over TX. Passed a variable so that we don't needlessly re-calculate it every time.
    '''
    print(f'[EXPLORER] >>> Checking who mined currency thing #{thing}')

    df = blockchain.loc[blockchain['INPUT'] == f'<@{CREATOR_ID}>']              # All currency things sent by the Currency Thing bot (mined)
    df['SUPPLY'] = supply_over_tx(blockchain)['SIZE']                           # Adds the total supply at each point as a column to the dataframe

    filter = df.loc[df['SUPPLY'] <= thing]                                      # Getting all trades where the supply is less than the amount we're looking for (anything after that is after the nth thing was mined, so the last trade before then was the miner)
    winner = filter.tail(1)[['OUTPUT', 'TIME']]                                 # Gets the last row before the limit - the winner - only the Output and Time columns

    # Getting the direct values
    user = winner.iloc[0]['OUTPUT']
    date = winner.iloc[0]['TIME'].date()
    trade_id = winner.index.tolist()[0]

    # print('[EXPLORER] >>> Winner DataFrame')
    # print(winner)

    return thing, user, trade_id, date


def get_mining_milestones(blockchain: pd.DataFrame):
    print('[EXPLORER] >>> Getting Mining Milestones')

    # getting the latest thousandth thing milestone
    latest_thousand = get_thousands(get_supply(blockchain))
    milestones      = range(1000, latest_thousand + 1000, 1000)

    # loading the milestones dataframe from disk
    milestones_df           = pd.read_csv('milestones.csv', index_col=0)
    milestones_df['DATE']   = pd.to_datetime(milestones_df['DATE'])

    # Checks if the Milestones DF on disk is up to date. If not, updates it and overwrites it.
    if not latest_thousand in milestones_df.index:
        print('[EXPLORER] >>> Updating Milestones.CSV')
        # A list of tuples containing the Milestone reached, and the Trade ID where it was reached, for each milestone specified above
        achievements = [(who_mined_xth_thing(x, blockchain, supply_over_tx(blockchain))) for x in milestones]
        
        # Converting the list of tuples into a dataframe and saving it to disk
        milestones_df = pd.DataFrame(achievements, columns=['MILESTONE', 'USER', 'ID', 'DATE']).set_index('MILESTONE')
        milestones_df.to_csv('milestones.csv')


    # string to store the output messages, to send them all at once
    msg = "**--- 🥳 Currency Thing Milestones 🎉 ---**\n\n"

    # Getting the relevant info of each miltestone
    for index, row in milestones_df.iterrows():
        thing   = index
        user    = row['USER']
        trade   = row['ID']
        date    = row['DATE'].strftime('%d/%m')

        # formatting this into a string and appending it to the main string
        msg += (f'**{thing}th** currency thing: ➤  {user} ({date} @ trade #{trade})\n')
    
    return msg


def test(blockchain: pd.DataFrame):
    print('\n\n\n[EXPLORER] >>> TEST')
    print(blockchain)










###### IF NAME == MAIN ##############################################################################################################
if (__name__ == "__main__"):
    print('beep beep badaboop, I was run directly')
else:
    print ("BLOCKCHAIN EXPLORER IMPORTED")


