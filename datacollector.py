from os.path import isfile
import praw
import pandas as pd
from time import sleep
from datetime import date, datetime, timedelta
import yfinance as yf
from ftplib import FTP
from tqdm import tqdm
import string
from psaw import PushshiftAPI




def getTickers():
    tickers = []

    def processTicker(ticker):

        if(ticker[:6] == 'Symbol'):
            return
        else:
            stringSplit = ticker.split('|')
            tickerName = stringSplit[0]
            if tickerName == 'EDIT' or tickerName == 'HA' or tickerName == 'PSA' or tickerName == 'DD': # we're gonna ignore tickers that look like words
                return
            
            tickers.append(tickerName)


    with FTP('ftp.nasdaqtrader.com') as ftp:
        ftp.login()
        ftp.cwd('SymbolDirectory')
        # ftp.retrlines('LIST')
        test = ftp.retrlines('RETR nasdaqlisted.txt', processTicker)
    
    return tickers[:-1] # remove performance description

def getPosts(lim=900, mode="w"):  
    
    nasdaqTickers = getTickers()

    # might not actually pick up anything, but worth a shot? For instance, unlikely that "Microsoft Corporation" will be in a post
    # but between short name and ticker I think we should get just about everything... no way to isolate the common name right? Hard to make a general solution that would work for both
    # "Microsoft Corporation" and "Papa John's Pizza"

    sub_dict = {
        'ticker': [], 'selftext': [], 'title': [], 'id': [],
        'num_comments': [], 'score': [], 'upvote_ratio': [], 'ups': [], 'downs': [], 'is_distinguished': [], 'link_flair_text': [], 'is_locked': [], 'is_self': [], 'signal': []}
    
    # gonna need to toString the date arguments?
    csv = 'data/posts.csv'


    # ---------------------- USING PSAW ------------------------------ #
    desiredAttributes = ['selftext','title', 'title', 'id', 'num_comments', 'score', 'upvote_ratio', 'ups', 'downs', 'distinguished', 'link_flair_text', 'locked', 'is_self']
    twentyDaysAgo = date.today() + timedelta(days=-20)
    end_epoch=int(datetime.combine(twentyDaysAgo, datetime.min.time()).timestamp())
    subreddit = list(api.search_submissions(before=end_epoch,
                            subreddit='wallstreetbets',
                            filter=desiredAttributes,
                            limit=1000))

    # ----------------------------------------------------------------- #

    # Set csv_loaded to True if csv exists (can't evaluate truth on a dataframe)
    df, csv_loaded = (pd.read_csv(csv), 1) if isfile(csv) else ('', 0)

    print(f'csv = {csv}')
    print(f'csv_loaded = {csv_loaded}')

    print(f'Collecting information from r/wallstreetbets...')

    postCounter = 0
    for i in tqdm(range(len(subreddit))):
        post = subreddit[i]
        postCounter += 1
        # Check if post.id is in df and set to True if df is empty
        isUnique = post.id not in set(df['id']) if csv_loaded else True
        postCreatedDate = date.fromtimestamp(post.created_utc)

        if not isUnique or not post.link_flair_text: # ignore if we've processed already or if no flair
            continue


        # check title and post body for mention of ticker or company name
        contentString = post.title + " " + post.selftext
        contentString = contentString.translate(str.maketrans('', '', string.punctuation))

        contentStringSplit = contentString.split(" ")
        if contentStringSplit[-1] == 'removed' or contentStringSplit[-1] == 'deleted':
            contentStringSplit = contentStringSplit[:-1]

        for tickerName in nasdaqTickers:
            if tickerName in contentStringSplit: # if a ticker we know of is in this post, let's add a row for it to our CSV
                
                print(f'Processing post: {contentString}')
                print(f'Found ticker: {tickerName}')

                sub_dict['ticker'].append(tickerName)
                sub_dict['selftext'].append(post.selftext)
                sub_dict['title'].append(post.title)
                sub_dict['id'].append(post.id)
                sub_dict['num_comments'].append(post.num_comments)
                sub_dict['score'].append(post.score)
                sub_dict['upvote_ratio'].append(post.upvote_ratio)
                sub_dict['ups'].append(post.ups)
                sub_dict['downs'].append(post.downs)
                sub_dict['is_distinguished'].append(post.distinguished)
                sub_dict['link_flair_text'].append(post.link_flair_text)
                sub_dict['is_locked'].append(post.locked)
                sub_dict['is_self'].append(post.is_self) # whether or not the post is just text (ie if no, then contains some media)

                # now, let's figure out the signal
                dateWindow = 20
                ticker = yf.Ticker(tickerName)

                # get differences in prices
                tenDaysPrior = postCreatedDate + timedelta(days=-10)
                tenDaysLater = postCreatedDate + timedelta(days=10)

                tenDaysPriorString = tenDaysPrior.isoformat()
                tenDaysLaterString = tenDaysLater.isoformat()

                maxHist = ticker.history(period='max')
                isPriorDate = maxHist.index==tenDaysPriorString
                isLaterDate = maxHist.index==tenDaysLaterString

                histPriorDate = maxHist[isPriorDate]

                while histPriorDate.empty: # if 10 days prior is a weekend, keep subtracting 2 days until we reach a non empty day
                    tenDaysPrior = tenDaysPrior + timedelta(days=-2)
                    tenDaysPriorString = tenDaysPrior.isoformat()
                    isPriorDate = maxHist.index==tenDaysPriorString
                    histPriorDate = maxHist[isPriorDate]
                    dateWindow += 2
                
                priorOpeningPrice = histPriorDate['Open'].array[0]
                
                histLaterDate = maxHist[isLaterDate]

                while histLaterDate.empty: # if 10 days after is a weekend, keep adding 2 days until we reach a non empty day
                    tenDaysLater = tenDaysLater + timedelta(days=2)
                    tenDaysLaterString = tenDaysLater.isoformat()
                    isLaterDate = maxHist.index==tenDaysLaterString
                    histLaterDate = maxHist[isLaterDate]
                    dateWindow += 2
                
                priorOpeningPrice = histPriorDate['Open'].array[0]
                laterClosingPrice = histLaterDate['Close'].array[0]


                priceDifference = laterClosingPrice - priorOpeningPrice
                percentageChange = priceDifference / priorOpeningPrice

                print(f"Prior price was {priorOpeningPrice}, later price was {laterClosingPrice}, delta was {percentageChange}")




                # calculate growth rate
                snpGrowthRate = (1.1 ** (dateWindow/365)) - 1 # based on snp generally giving 10% annualized returns, this is how much growth we should expect in dateWindow days

                if percentageChange >= snpGrowthRate:
                    sub_dict['signal'].append(1)
                elif percentageChange > 0 and percentageChange < snpGrowthRate:
                    sub_dict['signal'].append(0)
                else:
                    sub_dict['signal'].append(-1)

    
    new_df = pd.DataFrame(sub_dict)

    # Add new_df to df if df exists then save it to a csv.
    if 'DataFrame' in str(type(df)) and mode == 'w':
        pd.concat([df, new_df], axis=0, sort=0).to_csv(csv, index=False)
        print(
            f'{len(new_df)} new posts collected and added to {csv}')
    elif mode == 'w':
        new_df.to_csv(csv, index=False)
        print(f'{len(new_df)} posts collected and saved to {csv}')
    else:
        print(
            f'{len(new_df)} posts were collected but they were not '
            f'added to {csv} because mode was set to "{mode}" instead of w')

    print(f'postCounter was {postCounter}')

if __name__ == "__main__":
    # ---------------- USING PSAW --------------------
    r = praw.Reddit()
    api = PushshiftAPI(r)

    getPosts(lim=10000)
