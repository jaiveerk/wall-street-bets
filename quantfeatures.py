from logging import error
import pandas as pd
import numpy as np
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import emoji
from sklearn import preprocessing


# we probably just care about compound sentiment -- other options are neg, neu, pos
def getCompoundSentiment(row, sia):
    title = row['title']
    selftext = row['selftext']

    if not isinstance(title, str):
        title = ""
    
    if not isinstance(selftext, str):
        selftext = ""

    contentString = title + selftext

    sentimentDict = sia.polarity_scores(contentString)
    return sentimentDict['compound']




def getLength(s):
    if not isinstance(s, str):
        return 0
    else:
        return len(s)

def getNumEmojis(row, specificEmoji=""):
    title = row['title']
    selftext = row['selftext']

    if not isinstance(title, str):
        title = ""
    
    if not isinstance(selftext, str):
        selftext = ""
    
    contentString = title + selftext

    if specificEmoji == "":
        emojiSet = set(emoji.UNICODE_EMOJI['en'].keys())

        return len([letter for letter in contentString if letter in emojiSet])
    else:
        uniqueEmoji = emoji.emojize(f":{specificEmoji}:")
        if uniqueEmoji == f":{specificEmoji}:": # if emojizing had no effect, error with the argument
             raise NameError('Invalid emoji parameter specified')
        return len([letter for letter in contentString if letter == uniqueEmoji])



def dataToNumpy(df, dfName=""):
    if not dfName == "":
        print(f'processing {dfName}')

    nltk.downloader.download('vader_lexicon')
    sia = SentimentIntensityAnalyzer()


    # engineer additional features, starting with sentiment and lengths of selftext and title
    df['compound_sentiment'] = df.apply(lambda row: getCompoundSentiment(row, sia), axis=1)

    # lengths of title and selftext
    df['selftext_length'] = df.apply(lambda row: getLength(row['selftext']), axis=1)
    df['title_length'] = df.apply(lambda row: getLength(row['title']), axis=1)
    df['num_emojis'] = df.apply(lambda row: getNumEmojis(row), axis=1)
    df['num_rockets'] = df.apply(lambda row: getNumEmojis(row, "rocket"), axis=1)



    uniqueFlairs = ['Discussion', 'DD', 'Chart', 'YOLO', 'Meme', 'News', 'Loss', 'Gain', 'Shitpost']

    for flair in uniqueFlairs:
        df[f"is_{flair}"] = df.apply(lambda row: 1 if row['link_flair_text'] == flair else 0, axis=1)
    
    df = df.drop(columns=['selftext', 'title', 'is_distinguished', 'link_flair_text'])

    data = df.to_numpy()


    data = np.delete(data, [0, 1, 2], 1) # delete columns for ticker, ID on axis 1 


    y = data[:, 7] # signal is 8th column (so index 7)
    X = np.delete(data, 7, 1) # X will be everything else

    scaler = preprocessing.StandardScaler().fit(X)
    X_scaled = scaler.transform(X)

    # So columns are ['num_comments', 'score', 'upvote_ratio', 'ups', 'downs', 'is_locked',
    # 'is_self', 'compound_sentiment', 'selftext_length',
    # 'title_length', 'num_emojis', 'num_rockets', 'is_Gain', 'is_DD',
    # 'is_Discussion', 'is_News', 'is_Technical Analysis', 'is_Meme',
    # 'is_YOLO', 'is_Loss', 'is_Daily Discussion', 'is_Chart', 'is_Shitpost']


    # normalize the y
    y = y+1
    y=y.astype('int')

    # instead of having this write to a CSV, maybe have it input a CSV (aka the regular data) and then it just ouputs the numpy X and Y? That means that we can call log reg from backtester just by
    # calling the log reg file - basically make log reg only take in an X and a Y, and that way we can replicate the "logreg" file in the backtester since all it's doing is fitting a model and not any
    # of the preprocessing -- that can all be handled here

    return X_scaled, y

if __name__ == '__main__':
    # use for testing
    csv = 'data/bigOne.csv'
    dataToNumpy(pd.read_csv(csv))
