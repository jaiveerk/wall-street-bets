from os.path import isfile
import praw
import pandas as pd
from time import sleep
from datetime import date, datetime, timedelta
import yfinance as yf
from ftplib import FTP



def getTickers():
    tickers = []

    def processTicker(ticker):
        if(ticker[:6] == 'Symbol'):
            return
        else:
            tickers.append(ticker.split('|')[0])


    with FTP('ftp.nasdaqtrader.com') as ftp:
        ftp.login()
        ftp.cwd('SymbolDirectory')
        # ftp.retrlines('LIST')
        test = ftp.retrlines('RETR nasdaqlisted.txt', processTicker)
    
    return tickers

def getPosts(lim=900, mode="w"):  
    
    nasdaqTickers = getTickers()

    # might not actually pick up anything, but worth a shot? For instance, unlikely that "Microsoft Corporation" will be in a post
    # but between short name and ticker I think we should get just about everything... no way to isolate the common name right? Hard to make a general solution that would work for both
    # "Microsoft Corporation" and "Papa John's Pizza"
    nasdaqTickers = [(ticker, yf.Ticker(ticker.upper()).info['shortName']) for ticker in nasdaqTickers] # make (ticker, name) tuples

    print("Ticker information processed")


    sub_dict = {
        'ticker': [], 'selftext': [], 'title': [], 'id': [], 'sorted_by': [],
        'num_comments': [], 'score': [], 'upvote_ratio': [], 'ups': [], 'downs': [], 'is_saved': [], 'is_distinguished': [], 'link_flair_text': [], 'is_locked': [], 'is_self': [], 'signal': []}
    
    # gonna need to toString the date arguments?
    csv = 'data/posts.csv'

    # Specify a sorting method - new
    subreddit = reddit.subreddit("wallstreetbets").new(limit=lim)

    # Set csv_loaded to True if csv exists (can't evaluate truth on a dataframe)
    df, csv_loaded = (pd.read_csv(csv), 1) if isfile(csv) else ('', 0)

    print(f'csv = {csv}')
    print(f'csv_loaded = {csv_loaded}')

    print(f'Collecting information from r/wallstreetbets...')

    for post in subreddit:
        # Check if post.id is in df and set to True if df is empty
        isUnique = post.id not in set(df['id']) if csv_loaded else True

        if not isUnique or not post.link_flair_text: # ignore if we've processed already or if no flair 
            continue


        # check title and post body for mention of ticker or company name
        contentString = post.selftext.lower() + post.title.lower()
   

        for tuple in nasdaqTickers:
            if tuple[0] in contentString or tuple[1] in contentString: # if a ticker we know of is in this post, let's add a row for it to our CSV
                sub_dict['ticker'].append(tuple[0])
                sub_dict['selftext'].append(post.selftext.lower())
                sub_dict['title'].append(post.title.lower())
                sub_dict['id'].append(post.id)
                sub_dict['num_comments'].append(post.num_comments)
                sub_dict['score'].append(post.score)
                sub_dict['upvote_ratio'].append(post.upvote_ratio)
                sub_dict['ups'].append(post.ups)
                sub_dict['downs'].append(post.downs)
                sub_dict['is_saved'].append(post.saved)
                sub_dict['is_distinguished'].append(post.distinguished)
                sub_dict['link_flair_text'].append(post.link_flair_text)
                sub_dict['is_locked'].append(post.locked)
                sub_dict['is_self'].append(post.is_self) # whether or not the post is just text (ie if no, then contains some media)

                # now, let's figure out the signal
                dateWindow = 20
                ticker = yf.Ticker(tuple[0])

                # get differences in prices
                postCreatedDate = date.fromtimestamp(post.created_utc)

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


if __name__ == "__main__":
    # creates Reddit API instance
    reddit = praw.Reddit()
    getPosts()
