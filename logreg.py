import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, confusion_matrix
from quantfeatures import dataToNumpy

csv = 'data/quantfeatures.csv'

def getModelFromNumpy(X, y):
    clf = LogisticRegression(max_iter = 1000)
    clf.fit(X, y)
    return clf


def getModelFromDataframe(df): # method to be used in backtester
    X_scaled,y = dataToNumpy(df)
    return getModelFromNumpy(X_scaled, y)

def getModelFromCSV(csv='data/postsWithDate.csv'): 
    df = pd.read_csv(csv)
    getModelFromDataframe(df)


def trainAndTestFromDataframes(trainDf, testDf):
    model = getModelFromDataframe(trainDf)
    testX, testY = dataToNumpy(testDf)
    predictions = model.predict(testX)
    return predictions

if __name__ == '__main__':

    X_scaled, y = dataToNumpy('data/postsWithDate.csv')
    clf = getModelFromNumpy(X_scaled, y)

    length = X_scaled.shape[0]

    # MANUAL TUNING DONE HERE
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

