from logging import error
import pandas as pd
import numpy as np
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import emoji


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



if __name__ == '__main__':
    nltk.downloader.download('vader_lexicon')
    sia = SentimentIntensityAnalyzer()
    csv = 'data/postsWithDate.csv'
    csvOut = 'data/quantfeatures.csv'
    df = pd.read_csv(csv)

    # engineer additional features, starting with sentiment and lengths of selftext and title
    df['compound_sentiment'] = df.apply(lambda row: getCompoundSentiment(row, sia), axis=1)

    # lengths of title and selftext
    df['selftext_length'] = df.apply(lambda row: getLength(row['selftext']), axis=1)
    df['title_length'] = df.apply(lambda row: getLength(row['title']), axis=1)
    df['num_emojis'] = df.apply(lambda row: getNumEmojis(row), axis=1)
    df['num_rockets'] = df.apply(lambda row: getNumEmojis(row, "rocket"), axis=1)


    uniqueFlairs = df['link_flair_text'].unique()

    for flair in uniqueFlairs:
        df[f"is_{flair}"] = df.apply(lambda row: 1 if row['link_flair_text'] == flair else 0, axis=1)

    df = df.drop(columns=['selftext', 'title', 'is_distinguished', 'link_flair_text'])

    print(f'Dataframe columns are {df.columns}')

    df.to_csv(csvOut, index=False)


    # now write it to the correct csv file
