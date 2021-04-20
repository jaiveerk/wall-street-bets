#!/usr/bin/env python

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split

from keras.models import Sequential
from keras.layers import Dense
from keras.wrappers.scikit_learn import KerasClassifier
from keras.utils import np_utils
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize



def d2v_model(texts):
    tagged_data = [TaggedDocument(words=word_tokenize(_d.lower()), tags=[str(i)]) for i, _d in enumerate(texts)]
    
    max_epochs = 100
    vec_size = 10
    alpha = 0.025

    model = Doc2Vec(vector_size=vec_size,
                    alpha=alpha, 
                    min_alpha=0.00025,
                    min_count=1,
                    dm =1)
    model.build_vocab(tagged_data)
    for epoch in range(max_epochs):
        #print('iteration {0}'.format(epoch))
        model.train(tagged_data,
                    total_examples=model.corpus_count,
                    epochs=model.epochs)
        # decrease the learning rate
        model.alpha -= 0.0002
        # fix the learning rate, no decay
        model.min_alpha = model.alpha
    return model
    

def vec_for_learning(model, docs):
    vectors = [model.infer_vector(word_tokenize( doc.lower())) for doc in docs     ]
    return np.array(vectors)
    
def to_categorical(y):
    encoder = LabelEncoder()
    encoder.fit(y)
    encoded_Y = encoder.transform(y)
    return np_utils.to_categorical(encoded_Y)
    

def create_model(input_dim=20, layer_outputs=[60], activation='relu', optimizer='adam'):
    
    assert len(layer_outputs) > 0, print('layer_outputs must have length > 0')
    
    model = Sequential()
    model.add(Dense(layer_outputs[0], input_dim=input_dim, activation=activation))
    
    for output in layer_outputs[1:]:
        model.add(Dense(output, activation=activation))

    model.add(Dense(3, activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])
    
    return model
    

def predictions_to_categorical(predictions):
    choices = []
    for pred in predictions:
        if max(pred) == pred[0]:
            choices.append([1,0,0])
        elif max(pred) == pred[1]:
            choices.append([0,1,0])
        else:
            choices.append([0,0,1])
    return np.array(choices)

def baseline_model():
    # create model
    model = Sequential()
    model.add(Dense(10, input_dim=10, activation='relu'))
    model.add(Dense(10, activation='relu'))
    model.add(Dense(3, activation='softmax'))
    # Compile model
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model


def train_test_predict(train, test, column):
    
    X_train = train[column]
    X_test  = test[column]
    y_train = train['signal']
    y_test  = test['signal']
    
    title_model = d2v_model(X_train)
    
    input_vectors_train = vec_for_learning(title_model, X_train)
    input_vectors_test = vec_for_learning(title_model, X_test)
    y_train_categorical = to_categorical(y_train)
    y_test_categorical = to_categorical(y_test)
    
    model = baseline_model()
    model.fit(input_vectors_train, y_train_categorical, epochs=80, batch_size=30)
    
    _, accuracy = model.evaluate(input_vectors_test, y_test_categorical)
    predictions = model.predict(input_vectors_test)
    return predictions_to_categorical(predictions)
