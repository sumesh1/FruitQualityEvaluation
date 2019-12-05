import os
import numpy as np
import cv2
import skimage.color
import skimage.filters
import skimage.io
from sklearn.model_selection import train_test_split
from sklearn import preprocessing

from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D
from keras.losses import sparse_categorical_crossentropy
from keras.optimizers import adadelta
from keras.models import load_model



def getLBPimage(img):
    '''
    == Input ==
    gray_image  : color image of shape (height, width)

    == Output ==
    imgLBP : LBP converted image of the same shape as
    '''

    ### Step 0: Step 0: Convert an image to grayscale
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgLBP = np.zeros_like(gray_image)
    neighboor = 3
    for ih in range(0, img.shape[0] - neighboor):
        for iw in range(0, img.shape[1] - neighboor):
            ### Step 1: 3 by 3 pixel
            img = gray_image[ih:ih + neighboor, iw:iw + neighboor]
            center = img[1, 1]
            img01 = (img >= center) * 1.0
            img01_vector = img01.T.flatten()
            # it is ok to order counterclock manner
            # img01_vector = img01.flatten()
            ### Step 2: **Binary operation**:
            img01_vector = np.delete(img01_vector, 4)
            ### Step 3: Decimal: Convert the binary operated values to a digit.
            where_img01_vector = np.where(img01_vector)[0]
            if len(where_img01_vector) >= 1:
                num = np.sum(2 ** where_img01_vector)
            else:
                num = 0
            imgLBP[ih + 1, iw + 1] = num
    return (imgLBP)

def remove_background(img):

    blur = skimage.color.rgb2gray(img)
    blur = skimage.filters.gaussian(blur, sigma=2)
    mask = blur < 0.95
    sel = np.zeros_like(img)
    sel[mask] = img[mask]

    return sel


def rgb2gray(rgb):
    return np.dot(rgb[..., :3], [0.299, 0.587, 0.114])

# preparing training data. This includes cutting fruits out of images, storing and labeling them.
def prepare_training_data(data_folder_path, removeBackground = True, showImage = False):
    dirs = os.listdir(data_folder_path)

    fruits = []
    labels = []
    apples = []
    apple_labels = []
    oranges = []
    orange_labels = []
    bananas = []
    banana_labels = []

    # for each img in each directory from dataset:
    for dir_name in dirs:

        # if directory name does not start with "fresh" or "rotten" its irrelevant data.
        if not (dir_name.startswith("fresh") or dir_name.startswith("rotten")):
            continue;

        # dir name is label of the objects.
        full_label = str(dir_name)
        if dir_name == 'freshapples' or dir_name == 'rottenapple':
            label = 'apple'
        if dir_name == 'freshoranges' or dir_name == 'rottenoranges':
            label = 'orange'
        if dir_name == 'freshbanana' or dir_name == 'rottenbanana':
            label = 'banana'

        subject_dir_path = data_folder_path + "/" + dir_name
        # Matching label with related name
        subject_images_names = os.listdir(subject_dir_path)

        index = 0
        # for each image name in each folder read it, extract fruit and add to list
        for image_name in subject_images_names:

            # ignore system files
            if image_name.startswith("."):
                continue;

            image_path = subject_dir_path + "/" + image_name

            # read image
            image = cv2.imread(image_path)
            image = cv2.resize(image, (64, 64))
            # Normalize color values to between 0 and 1
            #image = image / 255
            # remove background
            if removeBackground:
                fruit = remove_background(image)
                #fruit = getLBPimage(image)
                #fruit = np.expand_dims(fruit, axis=2)
            else:
                fruit = image
                #fruit = np.expand_dims(fruit, axis=2)
                #fruit = getLBPimage(fruit)

            index += 1
            if showImage:
                if index % 10 == 0:
                    cv2.imshow(label, cv2.resize(fruit, (64, 64)))
                    cv2.waitKey(100)

            if fruit is not None:
                # add fruit to list of fruits
                fruits.append(fruit)
                # append label to fruit
                labels.append(label)
                if label is 'apple':
                    apples.append(fruit)
                    apple_labels.append(full_label)
                if label is 'orange':
                    oranges.append(fruit)
                    orange_labels.append(full_label)
                if label is 'banana':
                    bananas.append(fruit)
                    banana_labels.append(full_label)


    cv2.destroyAllWindows()
    cv2.waitKey(1)
    cv2.destroyAllWindows()

    return fruits, labels, apples, apple_labels, oranges, orange_labels, bananas, banana_labels



train = False
predict_fruit_type = False
train_with_bananas = False

print("Preparing data...")
fruits, labels, apples, apple_labels, oranges, orange_labels, bananas, banana_labels \
    = prepare_training_data("dataset", removeBackground=True, showImage=False)
print("Data prepared")
# print total fruits and labels
print("Total fruits: ", len(fruits))
print("Total labels: ", len(labels))
print("Total apples: ", len(apples))
print("Total apple labels: ", len(apple_labels))
print("Total oranges: ", len(oranges))
print("Total orange labels: ", len(orange_labels))
print("Total bananas: ", len(bananas))
print("Total banana labels: ", len(banana_labels))

X_train, X_test, y_train, y_test = train_test_split(fruits, labels, test_size=0.1)
Xb_train, Xb_test, yb_train, yb_test = train_test_split(bananas, banana_labels, test_size=0.1)

X_train = np.array(X_train)
X_test = np.array(X_test)
Xb_train = np.array(Xb_train)
Xb_test = np.array(Xb_test)

# Flatten data?
#X_flat_train = X_train.reshape(X_train.shape[0], 64*64)
#X_flat_test = X_test.reshape(X_test.shape[0], 64*64)


le = preprocessing.LabelEncoder()
le.fit(y_train)
print("Labels")
print(le.classes_)
Y_train = le.transform(y_train)
Y_test = le.transform(y_test)
print("Labels after encoding")
print(np.unique(Y_test))

X_train.reshape(5670, 64, 64, 3)
X_test.reshape(630, 64, 64, 3)
print(X_train.shape)
print(X_test.shape)
if train:

    #there are using maxpool convolution and final dense layer.
    model_cnn = Sequential()
    # First convolutional layer, note the specification of shape
    model_cnn.add(Conv2D(32, kernel_size=(3, 3),
                     activation='relu',
                     input_shape=(64, 64, 3)))
    model_cnn.add(Conv2D(64, (3, 3), activation='relu'))
    model_cnn.add(MaxPooling2D(pool_size=(2, 2)))
    model_cnn.add(Dropout(0.25))
    model_cnn.add(Flatten())
    model_cnn.add(Dense(64, activation='relu'))
    model_cnn.add(Dropout(0.5))
    model_cnn.add(Dense(3, activation='softmax'))

    opt = adadelta(lr=0.001, decay=1e-6)
    model_cnn.compile(optimizer=opt, loss=sparse_categorical_crossentropy, metrics=['accuracy'])



    model_cnn.fit(X_train, Y_train,
              batch_size=128,
              epochs=300,
              verbose=1,
              validation_data=(X_test, Y_test))
    model_cnn.save('300epoch.h5')
    score = model_cnn.evaluate(X_test, Y_test, verbose=0)
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])

if predict_fruit_type:
    total_banana, total_apple, total_orange = 0, 0, 0
    predicted_banana, predicted_apple, predicted_orange = 0, 0, 0
    total, correct = 0, 0
    bananas = []
    oranges = []
    apples = []
    # load model
    model = load_model('300epoch.h5')
    # summarize model.
    model.summary()
    score = model.evaluate(X_test, Y_test, verbose=0)
    predictions = model.predict_classes(X_test)
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])
    expected = le.inverse_transform(Y_test)
    predictions = le.inverse_transform(predictions)
    for i in range(len(X_test)):
        if expected[i] == 'orange':
            total_orange = total_orange + 1
            if predictions[i] == 'orange':
                predicted_orange = predicted_orange + 1
                correct = correct + 1
        elif expected[i] == 'banana':
            total_banana = total_banana + 1
            if predictions[i] == 'banana':
                predicted_banana = predicted_banana + 1
                correct = correct + 1
        elif expected[i] == 'apple':
            total_apple = total_apple + 1
            if predictions[i] == 'apple':
                predicted_apple = predicted_apple + 1
                correct = correct + 1
        total = total + 1


    print("X=%s, Predicted=%s" % (expected[i], predictions[i]))
    print("Orange accuracy: " + str(predicted_orange) + "/" + str(total_orange)+ " -- " +
          str(predicted_orange/total_orange*100) + "%")
    print("Banana accuracy: " + str(predicted_banana) + "/" + str(total_banana)+ " -- " +
          str(predicted_banana/total_banana*100) + "%")
    print("Apple accuracy: " + str(predicted_apple) + "/" + str(total_apple) + " -- " +
          str(predicted_apple/total_apple*100) + "%")
    print("Total accuracy: " + str(correct) + "/" + str(total) + " -- " + str(correct/total*100) + "%")

if train_with_bananas:
    le1 = preprocessing.LabelEncoder()
    le.fit(yb_train)
    print("Banana Labels")
    print(le.classes_)
    Y_train = le.transform(yb_train)
    Y_test = le.transform(yb_test)
    print("Banana Labels after encoding")
    print(np.unique(Y_test))


    #there are using maxpool convolution and final dense layer.
    model_cnn = Sequential()
    # First convolutional layer, note the specification of shape
    model_cnn.add(Conv2D(32, kernel_size=(3, 3),
                     activation='relu',
                     input_shape=(64, 64, 3)))
    model_cnn.add(Conv2D(64, (3, 3), activation='relu'))
    model_cnn.add(MaxPooling2D(pool_size=(2, 2)))
    model_cnn.add(Dropout(0.25))
    model_cnn.add(Flatten())
    model_cnn.add(Dense(64, activation='relu'))
    model_cnn.add(Dropout(0.5))
    model_cnn.add(Dense(3, activation='softmax'))

    opt = adadelta(lr=0.001, decay=1e-6)
    model_cnn.compile(optimizer=opt, loss=sparse_categorical_crossentropy, metrics=['accuracy'])



    model_cnn.fit(Xb_train, Y_train,
              batch_size=128,
              epochs=300,
              verbose=1,
              validation_data=(Xb_test, Y_test))
    model_cnn.save('300epochBananas.h5')
    score = model_cnn.evaluate(Xb_test, Y_test, verbose=0)
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])