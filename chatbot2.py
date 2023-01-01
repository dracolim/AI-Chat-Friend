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
    lat = request.json['lat']
    lon = request.json['lon']
    ints = predict_class(message)
    res = get_response(message,ints, intents,lat, lon)
    return jsonify({'response': res, 'lat': lat, 'lon': lon})

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

def get_response(message, intents_list, intents_json, lat , lon):
    tag = intents_list[0]['intent']
    if tag == "weather":
        result = get_weather(lat, lon)
    elif tag == "nearby restaurants":
        radius = ''
        last_index = 0
        for i in range(len(message)):
            if message[i].isdigit():
                radius += message[i]
                last_index = i
        if radius != '':
            radius = int(radius)
            if message[last_index+1] == 'k':
                radius = radius * 1000
        else: 
            radius = 1000
        result = get_nearby_restaurants(lat, lon,radius)
    else: 
        list_of_intents = intents_json['intents']
        for i in list_of_intents:
            if i['tag'] == tag:
                result = random.choice(i['responses'])
                break
    return result

def get_weather(lat, lon):
    with open('api_key.txt', 'r') as f:
        api_keys = []
        for line in f:
            list = line.strip().split('=')
            if(len(list) == 2):
                value = list[1]
                api_keys.append(value)
            else:
                break
    api_key = api_keys[0]
    # Send a request to the OpenWeatherMap API to get the current weather for the city
    response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}")
    if response.status_code == 200:
        data = response.json()
        temperature = round(int(data["main"]["temp"]) - 273.15 , 2)
        description = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        return f"The current temperature is {str(temperature)}°C and the sky is {description} with humidity of {humidity}"
    else:
        return "Sorry, there was an error getting the weather data."

def get_nearby_restaurants(lat, lon, radius):
    # Replace YOUR_API_KEY with your actual API key
    with open('api_key.txt', 'r') as f:
        api_keys = []
        for line in f:
            list = line.strip().split('=')
            if(len(list) == 2):
                value = list[1]
                api_keys.append(value)
            else:
                break
    api_key = api_keys[1]
    # Construct the URL for the request
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius={radius}&type=restaurant&key={api_key}"
    # Send the request to the Google Places API
    response = requests.get(url)
    # Check the status code of the response to ensure that the request was successful
    if response.status_code == 200:
        # If the request was successful, parse the JSON data from the response
        data = response.json()
        # Get the list of restaurants from the data
        restaurants = data["results"]
        restaurant_list = []
        for i in range(5):
            chosen = random.choice(restaurants)
            restaurants.remove(chosen)

            name = chosen['name']
            location = chosen["vicinity"]
            # link = link = chosen["photos"][0]["html_attributions"][0]
            if "opening_hours" in chosen:
                opening_hours = chosen["opening_hours"]
                if(opening_hours == 'true'):
                    opening_hours = "Currently it is open."
                else:
                    opening_hours = "Currently it is closed."
            else:
                opening_hours = "Not available"
            if "rating" in chosen:
                rating = chosen["rating"]
            else:
                rating = "Not available"

            restaurant = f"<br>Name: {name} <br>Location: {location} <br>Opening Hours: {opening_hours} <br>Rating: {rating} <br>"
            restaurant_list.append(restaurant)
        return restaurant_list
    else:
        # If the request was not successful, return an empty list
        return []

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=True)