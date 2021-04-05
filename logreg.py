import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, confusion_matrix

csv = 'data/quantfeatures.csv'

if __name__ == '__main__':

# NOW -- HAVE THIS CALL THE FUNCTINOS FROM QUANTFEATURES AND GET X AND Y FROM THERE RATHER THAN RE GENERATING IT HERE

    # df = pd.read_csv(csv)
    # data = df.to_numpy()
    # print(f'Dataframe columns are {df.columns}')

    # data = np.delete(data, [0, 1, 2], 1) # delete columns for ticker, ID on axis 1 


    # y = data[:, 7] # signal is 8th column (so index 7)
    # X = np.delete(data, 7, 1) # X will be everything else


    # scaler = preprocessing.StandardScaler().fit(X)
    # X_scaled = scaler.transform(X)

    # # So columns are ['num_comments', 'score', 'upvote_ratio', 'ups', 'downs', 'is_locked',
    # # 'is_self', 'compound_sentiment', 'selftext_length',
    # # 'title_length', 'num_emojis', 'num_rockets', 'is_Gain', 'is_DD',
    # # 'is_Discussion', 'is_News', 'is_Technical Analysis', 'is_Meme',
    # # 'is_YOLO', 'is_Loss', 'is_Daily Discussion', 'is_Chart', 'is_Shitpost']


    # length = X_scaled.shape[0]

    # # normalize the y
    # y = y+1
    # y=y.astype('int')


    clf = LogisticRegression(max_iter = 1000)
    clf.fit(X_scaled, y)
    predictions = clf.predict(X_scaled)
    predictions_proba = clf.predict_proba(X_scaled)

    print("confusion matrix:")
    print(confusion_matrix(y, predictions))

    print(f'prediction: {clf.predict_proba([X[140]])}')

    zeroCounter = 0
    oneCounter = 0
    twoCounter = 0

    for i in range(length):
        if predictions[i] == 0:
            zeroCounter += 1
        if predictions[i] == 1:
            oneCounter += 1
        if predictions[i] == 2:
            twoCounter += 1
    
    print(f'zeroCounter: {zeroCounter}')
    print(f'oneCounter: {oneCounter}')
    print(f'twoCounter: {twoCounter}')

    error = 0

    trueZeroPredictionOne = 0
    trueZeroPredictionTwo = 0
    trueOnePredictionZero = 0
    trueOnePredictionTwo = 0
    trueTwoPredictionZero = 0
    trueTwoPredictionOne = 0

    averageTrueTwoPredictionZeroProba = np.zeros(3)
    averageTrueTwoPredictionTwoProba = np.zeros(3) # 80 of these

    for i in range(length):

        if(y[i] == 2 and predictions[i] == 2):
            averageTrueTwoPredictionTwoProba += predictions_proba[i]
            continue

        if y[i] != predictions[i]:
            error += 1
        
            if y[i] == 0 and predictions[i] == 1:
                trueZeroPredictionOne += 1
            
            if y[i] == 0 and predictions[i] == 2:
                trueZeroPredictionTwo += 1
            
            if y[i] == 1 and predictions[i] == 0:
                trueOnePredictionZero += 1
            
            if y[i] == 1 and predictions[i] == 2:
                trueOnePredictionTwo += 1
            
            if y[i] == 2 and predictions[i] == 0:
                trueTwoPredictionZero += 1
                averageTrueTwoPredictionZeroProba += predictions_proba[i]  

            if y[i] == 2 and predictions[i] == 1:
                trueTwoPredictionOne += 1   
    
    print(f'Misclass rate: {error/length}')
    
    print(f"trueZeroPredictionOne {trueZeroPredictionOne}")
    print(f"trueZeroPredictionTwo {trueZeroPredictionTwo}")
    print(f"trueOnePredictionZero {trueOnePredictionZero}")
    print(f"trueOnePredictionTwo {trueOnePredictionTwo}")
    print(f"trueTwoPredictionZero {trueTwoPredictionZero}")
    print(f"trueTwoPredictionOne {trueTwoPredictionOne}")

    print(f"true two prediction zero average probabilities = {averageTrueTwoPredictionZeroProba / trueTwoPredictionZero}")
    print(f"true two prediction two average probabilities = {averageTrueTwoPredictionTwoProba / 80}")

    # number of emojis?