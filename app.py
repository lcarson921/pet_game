from flask import Flask, render_template, request, redirect, url_for
import json
import random
import openai  # Ensure you have the OpenAI library installed and configured
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

class Game:
    def __init__(self, username):
        self.allUsersFile = "allUsers.txt"
        self.allUsers = []
        self.username = username
        self.userPetlist = []

    def load_users(self):
        try:
            with open(self.allUsersFile, "r") as file:
                self.allUsers = json.load(file)
        except FileNotFoundError:
            self.allUsers = []

    def save_users(self):
        with open(self.allUsersFile, "w") as file:
            json.dump(self.allUsers, file)

    def create_user(self):
        new_user = {"Username": self.username, "Pets": self.userPetlist}
        self.allUsers.append(new_user)
        self.save_users()

    def get_user(self):
        self.load_users()
        for user in self.allUsers:
            if user['Username'] == self.username:
                self.userPetlist = user['Pets']
                return user
        self.create_user()
        return self.allUsers[-1]

    def create_pet(self, pet_type, name):
        if len(self.userPetlist) < 3:
            if pet_type == 'Dragon':
                new_pet = Dragon(name)
            elif pet_type == 'Rock':
                new_pet = Rock(name)
            elif pet_type == 'Hedgehog':
                new_pet = Hedgehog(name)
            pet_dict = new_pet.save_pet()
            pet_dict['Backstory'] = self.load_backstory(pet_dict)
            self.userPetlist.append(pet_dict)
            self.save_users()

    def get_pets(self):
        return self.userPetlist

    def save_pet(self, pet):
        for i, p in enumerate(self.userPetlist):
            if p['Name'] == pet['Name']:
                self.userPetlist[i] = pet
                break
        self.save_users()

    def load_backstory(self, petDict):
        name = petDict["Name"]
        species = petDict["Animal Type"]
        prompt = f"Create a four-sentence backstory for the user's pet named {name}, which is a {species}."
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

class Pet:
    def __init__(self, name, animal_type):
        self.name = name
        self.animal_type = animal_type

    def save_pet(self):
        return {"Name": self.name, "Animal Type": self.animal_type, "Hunger": self.hunger, "Energy": self.energy, "Happiness": self.happiness}

class Dragon(Pet):
    def __init__(self, name):
        super().__init__(name, "Dragon")
        self.hunger = 3
        self.energy = 7
        self.happiness = 5

class Rock(Pet):
    def __init__(self, name):
        super().__init__(name, "Rock")
        self.hunger = 5
        self.energy = 4
        self.happiness = 10

class Hedgehog(Pet):
    def __init__(self, name):
        super().__init__(name, "Hedgehog")
        self.hunger = 10
        self.energy = 7
        self.happiness = 10

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu', methods=['POST', 'GET'])
def menu():
    if request.method == 'POST':
        username = request.form['username']
        game = Game(username)
        #user_data = game.get_user()
        pets = game.get_pets()
        return render_template('menu.html', username=username, pets=pets)
    else:
        username = request.args.get('username')
        game = Game(username)
        pets = game.get_pets()
        return render_template('menu.html', username=username, pets=pets)  

@app.route('/activity', methods=['POST'])
def activity():
    username = request.form.get('username')
    selected_activity = request.form.get('activity')
    if selected_activity == "Feed":
        return redirect(url_for('feed_pet', username=username))
    elif selected_activity == "Play":
        return redirect(url_for('play_pet', username=username))
    elif selected_activity == "Fight":
        return redirect(url_for('fight_pet', username=username))
    elif selected_activity == "Quit":
        return redirect(url_for('index'))  # Or another action for quitting
    return redirect(url_for('menu', username=username))

@app.route('/create_pet', methods=['POST'])
def create_pet():
    username = request.form['username']
    pet_type = request.form['pet_type']
    pet_name = request.form['pet_name']
    game = Game(username)
    game.create_pet(pet_type, pet_name)
    return redirect(url_for('menu', username=username))

@app.route('/feed_pet', methods=['POST'])
def feed_pet():
    username = request.form['username']
    pet_name = request.form['pet_name']
    food = request.form.get('food', 'Kibble')  # Default to 'Kibble' if not specified
    game = Game(username)
    pet = next((p for p in game.get_pets() if p['Name'] == pet_name), None)
    if pet:
        food_effects = {
            'Kibble': {'hunger': 2, 'energy': 1, 'happiness': 1},
            'Fish': {'hunger': 3, 'energy': 2, 'happiness': 2},
            'Chicken': {'hunger': 4, 'energy': 3, 'happiness': 3},
            'Vegetables': {'hunger': 1, 'energy': 2, 'happiness': 1}
        }
        effects = food_effects.get(food, {})
        pet['Hunger'] = min(10, pet['Hunger'] + effects.get('hunger', 0))
        pet['Energy'] = min(10, pet['Energy'] + effects.get('energy', 0))
        pet['Happiness'] = min(10, pet['Happiness'] + effects.get('happiness', 0))
        game.save_pet(pet)
    return redirect(url_for('menu', username=username))

@app.route('/play_pet', methods=['POST'])
def play_pet():
    username = request.form['username']
    pet_name = request.form['pet_name']
    game = Game(username)
    pet = next((p for p in game.get_pets() if p['Name'] == pet_name), None)
    if pet:
        pet['Hunger'] = max(0, pet['Hunger'] - 1)
        pet['Energy'] = max(0, pet['Energy'] - 1)
        pet['Happiness'] = min(10, pet['Happiness'] + 3)
        game.save_pet(pet)
    return redirect(url_for('menu', username=username))

@app.route('/fight_pet', methods=['POST'])
def fight_pet():
    username = request.form['username']
    pet_name = request.form['pet_name']
    move = request.form['move']
    game = Game(username)
    pet = next((p for p in game.get_pets() if p['Name'] == pet_name), None)
    if pet:
        if move in ['Punch', 'Kick']:
            pet['Happiness'] = max(0, pet['Happiness'] - 1)
        else:
            pet['Happiness'] = min(10, pet['Happiness'] + 1)
        game.save_pet(pet)
    return redirect(url_for('menu', username=username))

if __name__ == "__main__":
    app.run(debug=True)