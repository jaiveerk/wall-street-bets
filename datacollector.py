from os.path import isfile
import praw
import pandas as pd
from time import sleep
from datetime import date, datetime
import yfinance as yf


# date strings specified with Python datetime format, YYYY-MM-DD, like 2021-01-01

def getPosts(ticker, startDateString, endDateString, lim=900, mode="w"): # gonna want to turn this into something that uses dates    
    # process parameters
    startDate = date.fromisoformat(startDateString)
    endDate = date.fromisoformat(endDateString)
    # might not actually pick up anything, but worth a shot? For instance, unlikely that "Microsoft Corporation" will be in a post
    # but between short name and ticker I think we should get just about everything... no way to isolate the common name right? Hard to make a general solution that would work for both
    # "Microsoft Corporation" and "Papa John's Pizza"
    equityName = yf.Ticker(ticker.upper()).info['shortName'] 


    sub_dict = {
        'selftext': [], 'title': [], 'id': [], 'sorted_by': [],
        'num_comments': [], 'score': [], 'upvote_ratio': [], 'ups': [], 'downs': [], 'is_saved': [], 'is_distinguished': [], 'link_flair_text': [], 'is_locked': [], 'is_self': [], 'is_dd': [], 'date_created': []}
    
    # gonna need to toString the date arguments?
    csv = f'data/{ticker}_{startDate}_{endDate}_posts.csv'

    # Specify a sorting method - new
    subreddit = reddit.subreddit("wsb").new(limit=lim)

    # Set csv_loaded to True if csv exists (can't evaluate truth on a dataframe)
    df, csv_loaded = (pd.read_csv(csv), 1) if isfile(csv) else ('', 0)

    print(f'csv = {csv}')
    print(f'csv_loaded = {csv_loaded}')

    print(f'Collecting information from r/wsb with ticker {ticker} from {startDate} to {endDate}.')

    for post in subreddit:

        postDate = date.fromtimestamp(post.created_utc)

        begunScraping = False
        # If we're older than the start date, we're done collecting
        if postDate < startDate:
            print(f"Oldest posts had dates {sub_dict['date_created'][-2:]} ")
            break
        # If we're newer than the end date, we don't need anything from here
        elif postDate > endDate:
            continue

        if not begunScraping:
            begunScraping = True
            print(f'Newest post has date {postDate.isoformat()}')

        # Check if post.id is in df and set to True if df is empty
        isUnique = post.id not in set(df['id']) if csv_loaded else True

        # check title and post body for mention of specified ticker or company name, else ignore
        contentString = post.selftext.lower() + post.title.lower()
   

        if ((ticker.lower() in contentString) or (equityName in contentString)) and isUnique:
            flairText = post.link_flair_text
            isDD = 1 if flairText.lower() == 'dd' else 0


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
            sub_dict['is_dd'].append(isDD)
            sub_dict['date_created'].append(postDate.isoformat())
        sleep(0.1) # temporary solution for prototype - eventually use refresh tokens
    
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



"""
TODO:
- Add functionality to filter only necessary dates
- Add functionality to filter only posts for relevant ticker -- make argument a list of strings to look for? Also make sure to lower everything
"""