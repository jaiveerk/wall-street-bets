# given dataset:
#   - establish window size for both training and testing
#   - for given time window, train new model
#   - use trained model for test window, compare predictions to how the stock actually did -- both in terms of label and in terms of percent change
#   - return performance for that window - % of correct posts, average delta in value IF decisions were made according to the model (so this is going to require actual yfinance data)
#   - do that for a bunch of different windows and average out performance

import yfinance as yf
import pandas as pd
from datetime import date, datetime, timedelta
import time
from logreg import trainAndTestFromDataframes
import decisiontree


trainingWindow = 90 # let's say it's a 90 day window idk
testingWindow = 5 # and we see how the model does ove 5 day increments

csv = 'data/postsWithDate.csv'
df = pd.read_csv(csv)

# get first and last dates for loop
lastDate = df['date'].max()
currentStartTrainDate = df['date'].min()

currentEndTrainDate = date.fromtimestamp(currentStartTrainDate) + timedelta(days=trainingWindow) # MAKE A SMARTER TRAIN AND TEST WINDOW
currentStartTestDate = currentEndTrainDate + timedelta(days=1)
currentEndTestDate = currentStartTestDate + timedelta(days=testingWindow)

# now make them into timestamps to compare them to what's in the dataframe
currentEndTrainDate = time.mktime(currentEndTrainDate.timetuple())
currentStartTestDate = time.mktime(currentStartTestDate.timetuple())
currentEndTestDate = time.mktime(currentEndTestDate.timetuple())


performanceDicts = []

print(date.fromtimestamp(currentEndTestDate).isoformat())
print(date.fromtimestamp(currentStartTrainDate).isoformat())
print(date.fromtimestamp(lastDate).isoformat())

while currentEndTestDate < lastDate:
    print(f'Starting train window at {date.fromisoformat(currentStartTrainDate).isoformat()}')
    performanceDict = {'appreciationOfBuys': [], 'appreciationOfHolds': [], 'depreciationOfSells': []}

    # now let's filter for the correct dates in the dataframe
    isInTrainWindow = currentStartTrainDate < df.date and df.date < currentEndTrainDate # replace this with whatever it needs to be
    isInTestWindow = currentStartTestDate < df.date and df.date < currentEndTestDate # replace this with whatever it needs to be

    trainWindow = df[isInTrainWindow]
    testWindow = df[isInTestWindow]

    # get predictions from training over train window, testing over test window --> maybe add if statements for different models? doing log for now
    testPredictions = decisiontree.trainAndTestFromDataframes(trainWindow, testWindow)

    # now, for each buy, we want to track how much assets appreciated, and for each sell, we want to track how much assets depreciated


    for i in range(len(testPredictions)):
        appreciationPeriod = 10 # see how we did after 10 days, since we trained our model to look at changes in price after 10 days
        currentRow = testWindow.iloc[i]
        tickerName = currentRow['ticker']
        
        ticker = yf.Ticker(tickerName)
        maxHist = ticker.history(period='max')

        datePosted = date.fromtimestamp(currentRow['date'])
        datePostedString = datePosted.isoformat()
        
        # isolate prices on day that post was made
        isDatePosted = maxHist.index==datePostedString
        histDatePosted = maxHist[isDatePosted]

        while histDatePosted.empty:
            datePosted = datePosted + timedelta(days=1) # we want to take action as soon as we can on the post -- but if markets closed on day post was made, have to wait
            datePostedString = datePosted.isoformat()
            isDatePosted = maxHist.index==datePostedString
            histDatePosted = maxHist[isDatePosted]

        datePostedPrice = histDatePosted['Open'].array[0]

        # now let's see how it changed:
        appreciationDate = datePosted + timedelta(days=appreciationPeriod)
        appreciationDateString = appreciationDate.isoformat()

        isAppreciationDate = maxHist.index==appreciationDateString
        histAppreciationDate = maxHist[isAppreciationDate]

        while histAppreciationDate.empty:
            appreciationDate = appreciationDate + timedelta(days=1) # we want to take action as soon as we can on the post -- but if markets closed on day post was made, have to wait
            appreciationDateString = appreciationDate.isoformat()
            isAppreciationDate = maxHist.index==appreciationDateString
            histAppreciationDate = maxHist[isAppreciationDate]

        appreciationDatePrice = histAppreciationDate['Close'].array[0]

        priceDifference = appreciationDatePrice - datePostedPrice
        percentageChange = priceDifference / datePostedPrice


        prediction = testPredictions[i]

        # get performance of each prediction and add it to the performance dict
        if prediction == 2:
            performanceDict['appreciationOfBuys'].append(percentageChange)

        elif prediction == 1:
            performanceDict['appreciationOfHolds'].append(percentageChange)
        
        else:
            performanceDict['depreciationOfSells'].append(percentageChange)
    
    # now average out the values
    for key in performanceDict:
        totalPerformance = sum(performanceDict['key'])
        averagePerformance = totalPerformance / len(performanceDict['key']) # divide sum by number of predictions that we assessed in that category
        performanceDict[key] = averagePerformance

    print(f'Performance dict was {performanceDict}')    
    print(f'Adding to list of performance dicts...')
    performanceDicts.append(performanceDict)

    # get new dates by first dropping all rows that were published on the same date as the row we're assessing
    dateIsCurrentStartDate = date.fromtimestamp(df.date) == date.fromtimestamp(currentStartTrainDate)
    df = df.drop(df[dateIsCurrentStartDate].index)

    currentStartTrainDate = df['date'].min()

    currentEndTrainDate = date.fromtimestamp(currentStartTrainDate) + timedelta(days=trainingWindow)
    currentStartTestDate = currentEndTrainDate + timedelta(days=1)
    currentEndTestDate = currentStartTestDate + timedelta(days=testingWindow)

    # put em back into timestamp form so that we can use them in the filtering for the data
    currentEndTrainDate = time.mktime(currentEndTrainDate.timetuple())
    currentStartTestDate = time.mktime(currentStartTestDate.timetuple())
    currentEndTestDate = time.mktime(currentEndTestDate.timetuple())


keys = performanceDicts[0].keys()
numPerformanceDicts = len(performanceDicts)

finalPerformance = {}

for key in keys:
    finalPerformance[key] = 0

    for i in range(numPerformanceDicts):
        finalPerformance[key] = finalPerformance[key] + performanceDicts[i][key] # get sum of all values of this current key
    
    finalPerformance[key] = finalPerformance[key]/numPerformanceDicts

print(f'Final performance: {finalPerformance}')


