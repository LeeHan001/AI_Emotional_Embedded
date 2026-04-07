import os 
import pandas as pd #read CSV
import numpy as np
import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

Data = pd.read_csv('Mediapipe_DNN_V2.csv')
x = Data.iloc[:,:-1] #52 Flaot Type 
y = Data.iloc[:,-1] #8 Emotional 

le = LabelEncoder()
y_encoded = le.fit_transform(y) #One Hot Encoding

# 80% training 20% test, shuffle, stratify, 
x_train, x_test, y_train, y_test = train_test_split(x, y_encoded, test_size=0.2, shuffle=True, stratify=y_encoded, random_state=34)

#Model
model = Sequential([
    
   Dense(64, activation='relu', input_shape=(21,)),#input shape 52
   BatchNormalization(), 
   Dropout(0.3),       
   
   Dense(32, activation='relu'),
   BatchNormalization(), 
   Dropout(0.3),      
   
   Dense(8, activation='relu'),
   BatchNormalization(), 
   Dropout(0.3),       
    
   Dense(8, activation='softmax'),#output 8
])

model.compile(optimizer= 'adam', loss = 'sparse_categorical_crossentropy', metrics=['accuracy'])

model.summary()

history = model.fit(x_train, y_train,
    epochs=100,
    batch_size=32, 
    validation_data=(x_test, y_test))

plt.figure(figsize=(12, 4))

# Accuracy graph
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Test Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()

# Loss graph
plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Test Loss')
plt.title('Model Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()

plt.show()

test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
print(f"\n Accuracy: {test_acc * 100:.2f}%")
