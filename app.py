from flask import Flask, render_template, request, redirect, url_for, session
import json
import random
import openai  # Ensure you have the OpenAI library installed and configured
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'secret' 
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
        self.get_user()
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
            print(self.userPetlist.append(pet_dict))
            self.save_users()
    def get_pet_by_name(self, pet_name):
        self.get_user()
        for pet in self.userPetlist:
            if pet['Name'] == pet_name:
                return pet
        return None
    
    def get_pets(self):
        self.get_user()
        # for i in range(len(self.userPetlist)):
        #     if self.userPetlist[i]['Name'] == pet_name:
        #         return self.userPetlist[i]
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
    
    def fashion(self, petDict, accessory):
        name = petDict["Name"]
        species = petDict["Animal Type"]
        prompt = f"Create an image using of your {species} wearing their {accessory} made of ascii characters to visualized in web services with <pre> tags "
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    def searchpet(self, petDict):
        for i in range(len(self.userPetlist)):
            if self.userPetlist[i] == petDict:
                return i 
        return -1
    def gameOver(self):
        self.get_user()
        for i in range(len(self.userPetlist)):
            if self.userPetlist[i]['Hunger'] < 0 or self.userPetlist[i]['Energy'] < 0 or self.userPetlist[i]['Happiness'] <0:
                died = self.userPetlist[i]
                index = self.searchPet(self.userPetlist[i])
                self.userPetlist.pop(index)
                self.saveFile
                return (True, died)
            
        return (False, None) # Tuples 


    
    
class Pet:
    def __init__(self, name, animal_type):
        self.name = name
        self.animal_type = animal_type

    def save_pet(self):
        return {"Name": self.name, "Animal Type": self.animal_type, "Hunger": self.hunger, "Energy": self.energy, "Happiness": self.happiness, "Backstory":""}

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
    else:
        username = request.args.get('username')

    game = Game(username)
    gameOver = game.gameOver()
    while not gameOver[0]:
        user_data = game.get_user()
        pets = user_data.get('Pets', [])  # Use .get() to safely access the 'Pets' key

        return render_template('menu.html', username=username, pets=pets)
    return render_template('death.html', username=username, pets=pets, pet = gameOver[1])

@app.route('/feed_pet', methods=['POST'])
def feed_pet():
    
    username = request.form['username']
    pet_name = request.form['pet_name']
    food = request.form.get('food', 'Kibble')  # Default to 'Kibble' if not specified
    game = Game(username)
    pets = game.get_pets()
    pet = next((p for p in pets if p['Name'] == pet_name), None)
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
    return render_template('feed.html', username=username, pet_name=pet_name, pets=pets)
@app.route('/create_pet', methods=['POST'])
def death():
    username = request.form.get('username')
    return redirect(url_for('menu', username=username))

@app.route('/create_pet', methods=['POST'])
def create_pet():
    username = request.form['username']
    pet_type = request.form['pet_type']
    pet_name = request.form['pet_name']
    game = Game(username)
    game.create_pet(pet_type, pet_name)
    return redirect(url_for('menu', username=username))

@app.route('/activity', methods=['POST'])
def activity():
    username = request.form.get('username')
    selected_activity = request.form.get('activity')
    pet_name = request.form.get('pet_name')
    
    game = Game(username)
    pet = next((p for p in game.get_pets() if p['Name'] == pet_name), None)
    
    return render_template('activity.html', username=username, pet=pet, selected_activity=selected_activity)


# @app.route('/activity', methods=['POST'])
# def activity():
#     username = request.form['username']
#     g1 = Game(username)
#     pet_name = request.form['pet_name']
#     pet = g1.get_pet_by_name(pet_name)
#     activity = request.form['activity']

#     if activity not in ['Feed', 'Play', 'Fasion']:
#         return render_template('activity.html', username=username, pet_name=pet_name, pet=pet)
    
#     if activity == 'Feed':
#         return render_template('feed.html', username=username, pet_name=pet_name,pet=pet )
#     elif activity == 'Play':
#         return render_template('play.html', username=username, pet_name=pet_name, pet=pet)
#     elif activity == 'Fashion':
#         return render_template('fashion.html', username=username, pet_name=pet_name, pet=pet)
#     else:
#         return render_template('activity.html', username=username, pet_name=pet_name, pet=pet)
    
@app.route('/fashion', methods=['POST'])
def fashion():
    username = request.form.get('username')
    pet_name = request.form.get('pet_name')
    accessory = request.form['accessory']
    
    game = Game(username)
    pet = game.get_pet_by_name(pet_name)
    if pet:
        # Add accessory to pet (this is an example, modify according to your logic)
        pet['Accessory'] = accessory
        
        # Generate description or any other logic
        description = game.fashion(pet, accessory)
        
        # Save updated pet state
        game.save_pet(pet)
        
        # Optionally, render a template or redirect
        return render_template('fashion.html', username=username, pet=pet, description=description)
    
    return redirect(url_for('menu', username=username))


# @app.route('/Fashion', methods=['POST'])
# def fashion():
#     username = request.form['username']
#     pet_name = request.form['pet_name']
#     game1 = Game(username)
#     accessory = str(request.form['accessory'])
#     petDict = game1.get_pet_by_name(pet_name)
#     game1.fashion(petDict, accessory)        
       
#     #use chatgpt to write a story about the users pet fighting another pet 

@app.route('/play', methods=['POST'])
def play():
    # Logic for handling play activity
    


    username = request.form['username']
    pet_name = request.form['pet_name']
    
    
    game = Game(username)
    pet = game.get_pet_by_name(pet_name)
    pet = next((p for p in game.get_pets() if p['Name'] == pet_name), None)
    if pet:
        pet['Hunger'] = max(0, pet['Hunger'] - 1)
        pet['Energy'] = max(0, pet['Energy'] - 1)
        pet['Happiness'] = min(10, pet['Happiness'] + 3)
        game.save_pet(pet)
    return render_template('play.html', username=username,pet_name=pet_name, pet=pet)


# @app.route('/fight', methods=['GET', 'POST'])
# def fight():
#     username = request.form.get('username') or request.args.get('username')
#     pet_name = request.form.get('pet_name') or request.args.get('pet_name')
#     game = Game(username)
#     pets = game.get_pets()
#     pet = next((p for p in pets if p['Name'] == pet_name), None)
    

#     if not pet:
#         return redirect(url_for('menu', username=username))

#     if 'opponent' not in session:
#         opponent_type = random.choice(['Dragon', 'Rock', 'Hedgehog'])
#         opponent = {
#             'Name': 'Opponent',
#             'Animal Type': opponent_type,
#             'Energy': 10,
#             'Happiness': 5
#         }
#         session['opponent'] = opponent
#     else:
#         opponent = session['opponent']

#     result = {}

#     if request.method == 'POST':
#         user_move = request.form.get('move')
#         result = game.run_fight_game(pet, opponent, user_move)
#         game.save_pet(pet)
#         session['opponent'] = opponent  # Update session with the opponent's current state

#         if pet['Energy'] <= 0 or opponent['Energy'] <= 0:
#             session.pop('opponent', None)
#             return render_template('fight_result.html', pet=pet, opponent=opponent, result=result)
#     # print(opponent.Type)
#     return render_template('fight.html', pet=pet, opponent=opponent, result=result, username=username)

# @app.route('/fight', methods=['GET', 'POST'])
# def fight():
#     username = request.form.get('username') or request.args.get('username')
#     pet_name = request.form.get('pet_name') or request.args.get('pet_name')
#     game = Game(username)
#     pets = game.get_pets()
#     pet = next((p for p in pets if p['Name'] == pet_name), None)

#     if not pet:
#         return redirect(url_for('menu', username=username))

#     if 'opponent' not in session or session['opponent'] is None:
#         opponent = game.choose_opponent(pet)
#         session['opponent'] = opponent
#     else:
#         opponent = session['opponent']

#     if request.method == 'POST':
#         user_move = request.form.get('move')
#         result = game.run_fight_game(pet, opponent, user_move)
#         game.save_pet(pet)
#         game.save_pet(opponent)

#         if pet['Energy'] <= 0 or opponent['Energy'] <= 0:
#             session.pop('opponent', None)
#             return render_template('fight_result.html', pet=pet, opponent=opponent, result=result)

#         return render_template('fight.html', pet=pet, opponent=opponent, result=result)

#     return render_template('fight.html', pet=pet, opponent=opponent)

if __name__ == "__main__":
    app.run(debug=True)