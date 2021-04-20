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
import logreg
import decisiontree
from tqdm import tqdm
from interruptingcow import timeout
import neuralnet



trainingWindow = 20 # let's say it's a 20 day window idk
testingWindow = 5 # and we see how the model does ove 5 day increments

csv = 'data/bigOne.csv'
df = pd.read_csv(csv)

# get first and last dates for loop
lastDate = df['date'].max()
currentStartTrainDate = df['date'].min()

currentEndTrainDate = date.fromtimestamp(currentStartTrainDate) + timedelta(days=trainingWindow) 
currentStartTestDate = currentEndTrainDate + timedelta(days=1)
currentEndTestDate = currentStartTestDate + timedelta(days=testingWindow)

# now make them into timestamps to compare them to what's in the dataframe
currentEndTrainDate = time.mktime(currentEndTrainDate.timetuple())
currentStartTestDate = time.mktime(currentStartTestDate.timetuple())
currentEndTestDate = time.mktime(currentEndTestDate.timetuple())


performanceDicts = []


#MODEL_NAME = "DECISION_TREE"
MODEL_NAME = "SELFTEXT_MODEL"


print(f'Model name is {MODEL_NAME}')

while currentEndTestDate < lastDate:
    print(f'Starting train window at {date.fromtimestamp(currentStartTrainDate).isoformat()}')
    performanceDict = {'appreciationOfBuys': [], 'appreciationOfHolds': [], 'appreciationOfSells': []}

    # now let's filter for the correct dates in the dataframe
    trainWindow = df.query(f'date >= {currentStartTrainDate} & date <= {currentEndTrainDate}')
    testWindow = df.query(f'date >= {currentStartTestDate} & date <= {currentEndTestDate}')

    # now make copies so that we can modify them and generate our features accordingly -- throws a warning about potentially using views if we don't do this
    trainWindow = trainWindow.copy()
    testWindow = testWindow.copy()

    # get predictions from training over train window, testing over test window --> maybe add if statements for different models? doing log for now
    #testPredictions = decisiontree.trainAndTestFromDataframes(trainWindow, testWindow)
    
    print('Training model...')
    testPredictions = neuralnet.train_test_predict(trainWindow, testWindow, modelName)
    print('Done training model and making predictions.')

    testPredictions = []

    if MODEL_NAME == "DECISION_TREE":
        testPredictions = decisiontree.trainAndTestFromDataframes(trainWindow, testWindow, max_depth=15, min_samples_leaf=0.001)
    elif MODEL_NAME == "LOGREG":
        testPredictions = logreg.trainAndTestFromDataframes(trainWindow, testWindow)
    elif MODEL_NAME == "SELFTEXT_MODEL":
        testPredictions = decisiontree.trainAndTestFromDataframes(trainWindow, testWindow) # change from tree to Neural Net
>>>>>>> 35cc5b51b750a5a94e1fb35a0534e0aee3ef4625

    # now, for each buy, we want to track how much assets appreciated, and for each sell, we want to track how much assets depreciated


    for i in tqdm(range(len(testPredictions))):
        itWorked = False
        try:
            with timeout(20, exception=RuntimeError):
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

                daysIncreased = 0
                while histAppreciationDate.empty:
                    appreciationDate = appreciationDate + timedelta(days=1) # we want to take action as soon as we can on the post -- but if markets closed on day post was made, have to wait
                    appreciationDateString = appreciationDate.isoformat()
                    isAppreciationDate = maxHist.index==appreciationDateString
                    histAppreciationDate = maxHist[isAppreciationDate]
                    daysIncreased += 1
                    if daysIncreased > 365: # if we moved forward a whole year and nothing yet, future data just unavailable
                        raise Exception(f"Went too far forward for post about ticker {tickerName}")


                appreciationDatePrice = histAppreciationDate['Close'].array[0]

                priceDifference = appreciationDatePrice - datePostedPrice
                percentageChange = priceDifference / datePostedPrice

            itWorked = True
            prediction = testPredictions[i]
        except:
            print(f"Error assessing {tickerName} on post made on {currentRow['date']}")
            print(f'Post info: {currentRow}')

        # get performance of each prediction and add it to the performance dict if it worked
        if itWorked:
            if prediction == 2:
                performanceDict['appreciationOfBuys'].append(percentageChange)

            elif prediction == 1:
                performanceDict['appreciationOfHolds'].append(percentageChange)
            
            else:
                performanceDict['appreciationOfSells'].append(percentageChange)
    
    # now average out the values
    for key in performanceDict:
        if len(performanceDict[key]) == 0:
            performanceDict[key] = 0
        else:
            totalPerformance = sum(performanceDict[key])
            averagePerformance = totalPerformance / len(performanceDict[key]) # divide sum by number of predictions that we assessed in that category
            performanceDict[key] = averagePerformance

    print(f'Performance dict was {performanceDict}')    
    print(f'Adding to list of performance dicts...')
    performanceDicts.append(performanceDict)

    # get new dates by first dropping all rows that were published on the same day as the row we're assessing, or rows whose date is less than the next day
    nextDay = date.fromtimestamp(currentStartTrainDate) + timedelta(days=1)
    nextDayTimestamp = time.mktime(nextDay.timetuple())
    df = df.drop(df[df['date'] < nextDayTimestamp].index)

    # now we get our minimum again, which is the min timestamp among posts that were made at least one day after the start date of our previous train window
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


