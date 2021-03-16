from os.path import isfile
import praw
import pandas as pd
from time import sleep


def getPosts(ticker, startDate, endDate, sort="new", lim=900, mode="w"): # gonna want to turn this into something that uses dates

    sub_dict = {
        'selftext': [], 'title': [], 'id': [], 'sorted_by': [],
        'num_comments': [], 'score': [], 'upvote_ratio': [], 'ups': [], 'downs': [], 'is_saved': [], 'is_distinguished': [], 'link_flair_text': [], 'is_locked': [], 'is_self': []}
    
    # gonna need to toString the date arguments?
    csv = f'{ticker}_{startDate}_{endDate}_posts.csv'

    # Specify a sorting method.
    subreddit = reddit.subreddit("wsb").top(limit=lim)

    # Set csv_loaded to True if csv exists (can't evaluate truth on a dataframe)
    df, csv_loaded = (pd.read_csv(csv), 1) if isfile(csv) else ('', 0)

    print(f'csv = {csv}')
    print(f'After set_sort(), sort = {sort}')
    print(f'csv_loaded = {csv_loaded}')

    print(f'Collecting information from r/wsb with ticker {ticker} from {startDate} to {endDate}.')

    for post in subreddit:

        # Check if post.id is in df and set to True if df is empty
        unique_id = post.id not in set(df['id']) if csv_loaded else True

        # Save any unique posts to sub_dict.
        if unique_id: # date of post is unix date in post.created_utc
            sub_dict['selftext'].append(post.selftext)
            sub_dict['title'].append(post.title)
            sub_dict['id'].append(post.id)
            sub_dict['sorted_by'].append(sort)
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