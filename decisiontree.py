import pandas as pd
import numpy as np

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import log_loss, confusion_matrix
from quantfeatures import dataToNumpy

MAX_DEPTH = 6

def getModelFromNumpy(X, y):
    clf = DecisionTreeClassifier(max_depth= MAX_DEPTH)
    clf.fit(X, y)
    return clf


def getModelFromDataframe(df): # method to be used in backtester
    X_scaled,y = dataToNumpy(df, 'training df')
    return getModelFromNumpy(X_scaled, y)

def getModelFromCSV(csv): 
    df = pd.read_csv(csv)
    getModelFromDataframe(df)


def trainAndTestFromDataframes(trainDf, testDf):
    model = getModelFromDataframe(trainDf)
    testX, testY = dataToNumpy(testDf, 'testing df')
    predictions = model.predict(testX)
    return predictions

if __name__ == '__main__':

    X_scaled, y = dataToNumpy('data/bigOne.csv')
    clf = getModelFromNumpy(X_scaled, y)

    length = X_scaled.shape[0]

    # MANUAL TUNING DONE HERE
    predictions = clf.predict(X_scaled)
    predictions_proba = clf.predict_proba(X_scaled)

    print("confusion matrix:")
    print(confusion_matrix(y, predictions))

    print(f'prediction: {clf.predict_proba([X_scaled[140]])}')

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


    averageTrueTwoPredictionZeroProba = np.zeros(3)
    averageTrueTwoPredictionTwoProba = np.zeros(3) # 80 of these

    for i in range(length):

        if(y[i] == 2 and predictions[i] == 2):
            averageTrueTwoPredictionTwoProba += predictions_proba[i]
            continue

        if y[i] != predictions[i]:
            error += 1
        
    
    print(f'Misclass rate: {error/length}')
    



