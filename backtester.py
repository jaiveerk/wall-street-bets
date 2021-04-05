# given dataset:
#   - establish window size for both training and testing
#   - for given time window, train new model
#   - use trained model for test window, compare predictions to how the stock actually did -- both in terms of label and in terms of percent change
#   - return performance for that window - % of correct posts, average delta in value IF decisions were made according to the model (so this is going to require actual yfinance data)
#   - do that for a bunch of different windows and average out performance



trainingWindow = 90 # let's say it's a 90 day window idk
testingWindow = 5 # and we see how the model does ove 5 day increments

csv = 'data/postsWithDate.csv'
df = pd.read_csv(csv)

# sort by date column
currentStartTrainDate = df['date'].min()
currentEndTrainDate = currentDateStart + timedelta(days=trainingWindow)
currentStartTestDate = currentEndTrainDate + timedelta(days=1)
currentEndTestDate = currentStartTestDate + timedelta(days=testingWindow) # set it to its correct value now, instead of the placeholder

while currentEndTestDate < lastDate:

    # now let's filter for the correct dates in the dataframe
    isInTrainWindow = currentStartTrainDate < df.date and df.date < currentEndTrainDate # replace this with whatever it needs to be
    isInTestWindow = currentStartTestDate < df.date and df.date < currentEndTestDate # replace this with whatever it needs to be

    trainWindow = df[isInTrainWindow]
    testWindow = df[isInTestWindow]

    # assess models here

    y = trainWindow[:, 7] # signal is 8th column (so index 7)
    X = np.trainWindow(data, 7, 1) # X will be everything else

    scaler = preprocessing.StandardScaler().fit(X)
    X_scaled = scaler.transform(X)

    # GET PREDICTIONS HERE

    # NOW BASED ON PREDICTIONS GET WHAT ACTUALLY HAPPENED... NEED TICKER FOR THAT THOUGH






    # get new dates
    dateIsCurrentStartDate = df.date == currentStartTrainDate
    df = df.drop(df[dateIsCurrentStartDate].index)

    currentStartTrainDate = df['date'].min()
    currentEndTrainDate = currentDateStart + timedelta(days=trainingWindow)
    currentStartTestDate = currentEndTrainDate + timedelta(days=1)
    currentEndTestDate = currentStartTestDate + timedelta(days=testingWindow) # set it to its correct value now, instead of the placeholder



