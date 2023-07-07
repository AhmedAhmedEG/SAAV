from keras.layers import Conv2D, MaxPool2D, Dense, Flatten, Rescaling, RandomFlip, RandomZoom, RandomRotation, Resizing
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from keras.optimizers import adam_v2
from keras.utils import to_categorical
from keras.models import Sequential
from keras.models import load_model
import matplotlib.pyplot as plt
from pathlib import Path
import tensorflow as tf
import numpy as np
import csv
import cv2
import os

PARALLELIZM = 10
BATCH_SIZE = 32

image_paths = []
image_classes = []
for root, sf, files in os.walk('Train'):

    for f in files:
        image_paths.append(str(Path(root) / f))
        image_classes.append(int(Path(root).name))

image_classes = to_categorical(image_classes, 43)
train_images, test_images, train_labels, test_labels = train_test_split(image_paths, image_classes, test_size=0.2, random_state=42)


def dataset_generator(paths, classes):
    paths = [n.decode('utf-8') if type(n) == bytes else n for n in paths]
    image_rescaler = Sequential([Resizing(height=30, width=30), Rescaling(scale=1.0 / 255)])

    images = [cv2.imread(p) for p in paths]
    for i, c in zip(images, classes):
        yield image_rescaler(i), c


image_augmenter = Sequential([RandomFlip("horizontal_and_vertical"),
                              RandomZoom(height_factor=(-0.05, -0.2), width_factor=(-0.05, -0.2)),
                              RandomRotation(0.5)])


training_dataset = tf.data.Dataset.from_generator(dataset_generator,
                                                  args=(train_images, train_labels),
                                                  output_signature=(tf.TensorSpec(shape=(30, 30, 3), dtype=tf.float16),
                                                                    tf.TensorSpec(shape=(43), dtype=tf.uint8)))
testing_dataset = tf.data.Dataset.from_generator(dataset_generator,
                                                 args=(test_images, test_labels),
                                                 output_signature=(tf.TensorSpec(shape=(30, 30, 3), dtype=tf.float16),
                                                                   tf.TensorSpec(shape=(43), dtype=tf.uint8)))

training_dataset = training_dataset.map(lambda x, y: [image_augmenter(x, training=True), y], num_parallel_calls=PARALLELIZM).batch(BATCH_SIZE).prefetch(PARALLELIZM)
testing_dataset = testing_dataset.batch(BATCH_SIZE).prefetch(PARALLELIZM)

model = Sequential()
model.add(Conv2D(filters=32, kernel_size=(5, 5), activation='relu', input_shape=(30, 30, 3)))
model.add(Conv2D(filters=32, kernel_size=(5, 5), activation='relu'))
model.add(MaxPool2D(pool_size=(2, 2)))

model.add(Conv2D(filters=64, kernel_size=(3, 3), activation='relu'))
model.add(Conv2D(filters=64, kernel_size=(3, 3), activation='relu'))
model.add(MaxPool2D(pool_size=(2, 2)))

model.add(Flatten())
model.add(Dense(units=1024, activation="relu"))
model.add(Dense(units=256, activation="relu"))
model.add(Dense(units=43, activation="softmax"))

model.compile(loss='categorical_crossentropy', optimizer=adam_v2.Adam(), metrics=['accuracy'])
history = model.fit(training_dataset, batch_size=BATCH_SIZE, epochs=50, validation_data=testing_dataset)

model.save("SignDetetctorNew.h5")

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

# model = load_model('SignDetetctor.h5')

reader = csv.reader(open('Test.csv', 'r', encoding='utf-8'))
next(reader)

predicted_classes = []
actual_classes = []
for r in reader:
    image_rescaler = Sequential([Resizing(height=30, width=30), Rescaling(scale=1.0 / 255)])
    image = image_rescaler(cv2.imread(r[-1]))

    prediction = model.predict(np.expand_dims(image, axis=0))
    predicted_classes.append(np.argmax(prediction))

    actual_classes.append(int(r[-2]))

print(accuracy_score(actual_classes, predicted_classes))