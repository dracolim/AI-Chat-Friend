from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import json
import pickle
import numpy as np
import requests

import nltk
from nltk.stem import WordNetLemmatizer

from tensorflow import keras
from keras.models import load_model
import sys
# nltk.download('wordnet')

app = Flask(__name__)

CORS(app)


@app.route('/predict', methods=['POST'])
def predict():
    # Get the message from the request and process it
    message = request.json['message']
    ints = predict_class(message)
    res = get_response(ints, intents)
    return jsonify({'response': res})

lemmatizer = WordNetLemmatizer()
intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbotmodel.h5')

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i,r] for i ,r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x:x[1], reverse = True)

    return_list = []
    for r in results:
        return_list.append({"intent" : classes[r[0]], "probability": str(r[1])})

    return return_list

def get_response(intents_list, intents_json):
    tag = intents_list[0]['intent']
    if tag == "weather":
        get_location()
    else: 
        list_of_intents = intents_json['intents']
        for i in list_of_intents:
            if i['tag'] == tag:
                result = random.choice(i['responses'])
                break
        return result

def get_weather(lat, lon):
    # Replace YOUR_API_KEY with your actual API key
    api_key = "1560e1d13aee922f4fea8714c57ce559"
    # Send a request to the OpenWeatherMap API to get the current weather for the city
    response = requests.get(f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=current&appid={api_key}")
    # Check the status code of the response to ensure that the request was successful
    if response.status_code == 200:
        # If the request was successful, parse the JSON data from the response
        data = response.json()
        # Get the temperature and weather description from the data
        temperature = data["main"]["temp"]
        description = data["weather"][0]["description"]
        # Return the temperature and description as a string
        return f"The current temperature is {temperature}°C and the sky is {description}"
    else:
        # If the request was not successful, return an error message
        return "Sorry, there was an error getting the weather data."

def get_location():
    # Replace YOUR_API_KEY with your actual API key
    api_key = "AIzaSyCEd94_pjMfFU3y5GxPzY-vJeFJeacdI-c"

    # Set the request parameters
    params = {
        "key": api_key,
        "considerIp": "true"  # Use the IP address of the client as the location to look up
    }

    # Make the request to the API
    response = requests.get("https://www.googleapis.com/geolocation/v1/geolocate", params=params)

    # Check the status code of the response to ensure that the request was successful
    if response.status_code == 200:
        # If the request was successful, parse the JSON data from the response
        data = response.json()
        # Get the latitude and longitude from the data
        latitude = data["location"]["lat"]
        longitude = data["location"]["lng"]
        # Print the latitude and longitude
        print(f"Latitude: {latitude}")
        print(f"Longitude: {longitude}")
    else:
        # If the request was not successful, print an error message
        print("Sorry, there was an error getting the location data.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=True)