from keras.layers import Dense, Dropout, CuDNNLSTM, Bidirectional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
import csv

reader = csv.reader(open('Dataset.csv', 'r'))
scaler = MinMaxScaler()
dataset = []

target = []
for r in reader:

    for i, c in enumerate(r):
        r[i] = eval(c)

    minimum_length = 16
    length = len(r) - 1
    if length > minimum_length:
        target.append(r.pop(-1))

        scaler.fit(r)
        r = scaler.transform(r)

        extra = length - minimum_length
        offset = extra // 2
        r = r[offset:minimum_length + offset + 1]

        dataset.append(r)

dataset = np.array(dataset)
target = np.array(target)

x_train, x_test, y_train, y_test = train_test_split(dataset, target, test_size=0.2, random_state=4)

model = Sequential()

model.add(Bidirectional(CuDNNLSTM(128, return_sequences=True), input_shape=x_train.shape[1:]))
model.add(Bidirectional(CuDNNLSTM(64)))

model.add(Dense(254, activation='relu'))
model.add(Dense(128, activation='relu'))
model.add(Dense(64, activation='relu'))
model.add(Dense(1, activation='sigmoid'))
model.compile(loss=tf.keras.metrics.binary_crossentropy, optimizer='adam', metrics=['accuracy'])

history = model.fit(x_train, y_train, epochs=50, batch_size=30, validation_data=(x_test, y_test))

plt.subplot(121)
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()

plt.subplot(122)
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

model.save('FaintingDetector.h5')