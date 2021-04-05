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
currentStartTrainDate = THE_FIRST_DATE
currentEndTestDate = THE_FIRST_DATE # this is just a placeholder to begin the loop

while currentEndTestDate < lastDate:
    currentStartTrainDate = 0
    currentEndTrainDate = currentDateStart + timedelta(days=trainingWindow)
    currentStartTestDate = currentEndTrainDate + timedelta(days=1)
    currentEndTestDate = currentStartTestDate + timedelta(days=testingWindow) # set it to its correct value now, instead of the placeholder

    # now let's filter for the correct dates in the dataframe
    isInTrainWindow = df.index==tenDaysPriorString # replace this with whatever it needs to be
    isInTestWindow = df.index==tenDaysPriorString # replace this with whatever it needs to be

    trainWindow = df[isInTrainWindow]
    testWindow = df[isInTestWindow]

    



