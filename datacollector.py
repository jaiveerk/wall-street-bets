from os.path import isfile
import praw
import pandas as pd
from time import sleep
from datetime import date, time, datetime, timedelta
from interruptingcow import timeout
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
            invalidTickers = ['EDIT', 'HA', 'PSA', 'DD', 'YOLO', 'HUGE', 'LMAO', 'CEO', 'CFO', 'MIND', 'GO', 'ON', 'LOL', 'UK', 'USA', 'SHIP', 'MOON', 'CAN', 'STAY', 'WISH', 'LIVE', 'TRUE', 'EYES', 'GAIN', 'MOVE', 'TIL', 'LOVE', 'LIVE', 'GOOD', 'EM', 'APPS', 'PLS']
            invalidTickers = set(invalidTickers)
            if tickerName in invalidTickers: # we're gonna ignore tickers that look like words
                return
            
            tickers.append(tickerName)


    with FTP('ftp.nasdaqtrader.com') as ftp:
        ftp.login()
        ftp.cwd('SymbolDirectory')
        # ftp.retrlines('LIST')
        test = ftp.retrlines('RETR nasdaqlisted.txt', processTicker)
    
    return tickers[:-1] # remove performance description

def getPosts():  
    
    nasdaqTickers = getTickers()

    blank_sub_dict = {
        'date': [], 'ticker': [], 'selftext': [], 'title': [], 'id': [],
        'num_comments': [], 'score': [], 'upvote_ratio': [], 'ups': [], 'downs': [], 'is_distinguished': [], 'link_flair_text': [], 'is_locked': [], 'is_self': [], 'signal': []}
    
    csv = 'data/bigOne.csv'

    # ---------------------- USING PSAW ------------------------------ #
    desiredAttributes = ['selftext','title', 'title', 'id', 'num_comments', 'score', 'upvote_ratio', 'ups', 'downs', 'distinguished', 'link_flair_text', 'locked', 'is_self']
    twentyDaysAgo = date.today() + timedelta(days=-20)
    end_epoch=int(datetime.combine(twentyDaysAgo, datetime.min.time()).timestamp())

    postCounter = 0

    for j in tqdm(range(15)):
        print(F'GETTING 10 THOUSAND MORE... CURRENTLY ON {j}TH ITERATION')

        sub_dict = blank_sub_dict # reset the sub_dict once the sub_dict from previous iteration got written to csv

        df, csv_loaded = (pd.read_csv(csv), 1) if isfile(csv) else ('', 0)

        if 'DataFrame' in str(type(df)): # if it already exists
            end_epoch = int(df['date'].min())
            print(f'Latest post date for current iteration: {date.fromtimestamp(end_epoch).isoformat()}')


        print(f'csv = {csv}')
        print(f'csv_loaded = {csv_loaded}')

        subreddit = list(api.search_submissions(before=end_epoch,
                                subreddit='wallstreetbets',
                                filter=desiredAttributes,
                                limit=10000))

        # ----------------------------------------------------------------- #
        print(f'Collecting information from r/wallstreetbets...')
        
        for i in tqdm(range(len(subreddit))):
            post = subreddit[i]
            postCounter += 1
            # Check if post.id is in df and set to True if df is empty
            isUnique = post.id not in set(df['id']) if csv_loaded else True
            postCreatedDate = date.fromtimestamp(post.created_utc)

            if not post.link_flair_text: # ignore if we've processed already or if no flair
                continue


            # check title and post body for mention of ticker or company name
            contentString = post.title + " " + post.selftext
            contentString = contentString.translate(str.maketrans('', '', string.punctuation))

            contentStringSplit = contentString.split(" ")
            if contentStringSplit[-1] == 'removed' or contentStringSplit[-1] == 'deleted':
                contentStringSplit = contentStringSplit[:-1]

            for tickerName in nasdaqTickers:
                if tickerName in contentStringSplit: # if a ticker we know of is in this post, let's add a row for it to our CSV

                    # let's figure out the signal, no point in adding it unless we know we can find it
                    try:
                        gotInfo = False
                        with timeout(60*4, exception=RuntimeError): # if it takes more than 2 min it's probably just hanging, so leave it alone
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
                                if dateWindow > 50:
                                    raise Exception("Date window got too large, aborting attempt")
                            
                            priorOpeningPrice = histPriorDate['Open'].array[0]
                            
                            histLaterDate = maxHist[isLaterDate]

                            while histLaterDate.empty: # if 10 days after is a weekend, keep adding 2 days until we reach a non empty day
                                tenDaysLater = tenDaysLater + timedelta(days=2)
                                tenDaysLaterString = tenDaysLater.isoformat()
                                isLaterDate = maxHist.index==tenDaysLaterString
                                histLaterDate = maxHist[isLaterDate]
                                dateWindow += 2
                                if dateWindow > 50:
                                    raise Exception("Date window got too large, aborting attempt")
                            
                            priorOpeningPrice = histPriorDate['Open'].array[0]
                            laterClosingPrice = histLaterDate['Close'].array[0]


                            priceDifference = laterClosingPrice - priorOpeningPrice
                            percentageChange = priceDifference / priorOpeningPrice
                            gotInfo = True # set flag to true

                            # print(f"Prior price was {priorOpeningPrice}, later price was {laterClosingPrice}, delta was {percentageChange}")

                        # if it doesn't time out while getting info about the ticker, then we can just add the info to the dictionary
                        if gotInfo: # if it actually worked and we executed everything, then add info about post to csv
                            snpGrowthRate = (1.1 ** (dateWindow/365)) - 1 # based on snp generally giving 10% annualized returns, this is how much growth we should expect in dateWindow days

                            if percentageChange >= snpGrowthRate:
                                sub_dict['signal'].append(1)
                            elif percentageChange > 0 and percentageChange < snpGrowthRate:
                                sub_dict['signal'].append(0)
                            else:
                                sub_dict['signal'].append(-1)
                            
                            # now that we've found signal, add everything else that we need
                            sub_dict['date'].append(post.created_utc)
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

                    except:
                        print(f'Error fetching signal for post about ticker {tickerName}, moving on...')

        # write everything to the csv at each iteration to save progress -- will overwrite the file at each iteration
        new_df = pd.DataFrame(sub_dict)
        pd.concat([df, new_df], axis=0, sort=0).to_csv(csv, index=False)
        print(f'{len(new_df)} new posts collected and and written to {csv}')

            

    print(f'postCounter was {postCounter}')

if __name__ == "__main__":
    # ---------------- USING PSAW --------------------
    r = praw.Reddit()
    api = PushshiftAPI(r)

    getPosts()
