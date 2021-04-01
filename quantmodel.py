import pandas as pd
import numpy as np
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer




# we probably just care about compound sentiment -- other options are neg, neu, pos
def getCompoundSentiment(row, sia):
    contentString = row['title'] + row['selftext']
    sentimentDict = sia.polarity_scores(contentString)
    return sentimentDict['compound']





def getNumEmojis(row):
 return


if __name__ == '__main__':
    nltk.downloader.download('vader_lexicon')
    sia = SentimentIntensityAnalyzer()
    csv = 'data/posts.csv'
    df = pd.read_csv(csv)

    # engineer additional features, starting with sentiment and lengths of selftext and title
    df['compound_sentiment'] = df.apply(lambda row: getCompoundSentiment(row, sia), axis=1)

    # lengths of title and selftext
    df['selftext_length'] = df.apply(lambda row: len(row['selftext']), axis=1)
    df['title_length'] = df.apply(lambda row: len(row['title']), axis=1)

    df['title']

    # number of emojis?
