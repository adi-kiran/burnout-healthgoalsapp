import json
import bcrypt
from flask_pymongo import PyMongo
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, \
                               unset_jwt_cookies, jwt_required, JWTManager
from datetime import datetime, timedelta
from functools import reduce


api = Flask(__name__)
api.secret_key = 'secret'
api.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/test'
api.config['MONGO_CONNECT'] = False
mongo = PyMongo(api)
api.config["JWT_SECRET_KEY"] = "softwareEngineering"
api.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(api)
mongo = PyMongo(api)
    
@api.route('/token', methods=["POST"])
def create_token():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    user = mongo.db.user.find_one({"email": email})
    if (user is not None and (user["password"] == password)):
        access_token = create_access_token(identity=email)
        return jsonify({"message": "Login successful", "access_token":access_token})
    else:
        print("Invalid email or password")
        return jsonify({"message": "Invalid email or password"}),401

@api.route("/register", methods=['POST'])
def register():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    first_name = request.json.get('firstName', None)
    last_name = request.json.get('lastName', None)
    new_document = {
    "email": email,
    "password": password,
    "first_name": first_name,
    "last_name": last_name,
    }
    query = {
        "email": email,
    }
    print(last_name)
    try:
        inserted = mongo.db.user.update_one(query, {"$set": new_document}, upsert=True)
        if (inserted.upserted_id):
            response = jsonify({"msg": "register successful"})
        else:   
            print("User already exists")
            response = jsonify({"msg": "User already exists"})
    except Exception as e:
        response = jsonify({"msg": "register failed"})

    return response
    # """
    # register() function displays the Registration portal (register.html) template
    # route "/register" will redirect to register() function.
    # RegistrationForm() called and if the form is submitted then various values are fetched and updated into database
    # Input: Username, Email, Password, Confirm Password
    # Output: Value update in database and redirected to home login page
    # """
    # if not session.get('email'):
    #     form = RegistrationForm()
    #     if form.validate_on_submit():
    #         if request.method == 'POST':
    #             username = request.form.get('username')
    #             email = request.form.get('email')
    #             password = request.form.get('password')
    #             mongo.db.user.insert({'name': username, 'email': email, 'pwd': bcrypt.hashpw(
    #                 password.encode("utf-8"), bcrypt.gensalt())})
    #         flash(f'Account created for {form.username.data}!', 'success')
    #         return redirect(url_for('home'))
    # else:
    #     return redirect(url_for('home'))
    # return render_template('register.html', title='Register', form=form)

@api.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response

@api.route('/events', methods=['GET'])
def get_events():
    events_collection = mongo.db.events
    events = list(events_collection.find({}))
    for event in events:
        event["_id"] = str(event["_id"]) # Convert ObjectId to string
    return jsonify(events)

@api.route('/is-enrolled', methods=['POST'])
def is_enrolled():
    data = request.json
    userEmail = data['email']
    eventTitle = data['eventTitle']

    enrollment = mongo.db.user.find_one({"email": userEmail, "eventTitle": eventTitle})

    if enrollment:
        return jsonify({"isEnrolled": True})
    else:
        return jsonify({"isEnrolled": False})


@api.route('/enroll', methods=['POST'])
def enroll_event():
    data = request.get_json()  # get data from POST request
    try:
        # Insert data into MongoDB
        mongo.db.user.insert_one({
            "email": data['email'],
            "eventTitle": data['eventTitle']
        })
        response = {"status": "Data saved successfully"}
    except Exception as e:
        response = {"status": "Error", "message": str(e)}
    
    return jsonify(response)

@api.route('/profile')
@jwt_required()
def my_profile():
    response_body = {
        "name": "Nagato",
        "about" :"Hello! I'm a full stack developer that loves python and javascript"
    }

    return response_body

@api.route('/caloriesConsumed',methods=["POST"])
@jwt_required()
def addUserConsumedCalories():
    print("Hello")
    data = request.get_json()  # get data from POST request
    current_user = get_jwt_identity()
    print(data)
    print(current_user)
    try:
        # Insert data into MongoDB
        mongo.db.user.update_one({'email': current_user, "consumedDate": data['intakeDate']}, {"$push": {"foodConsumed": {"item":data["intakeFoodItem"],"calories":data["intakeCalories"]}}}, upsert=True)
        response = {"status": "Data saved successfully"}
        statusCode = 200
    except Exception as e:
        response = {"status": "Error", "message": str(e)}
        statusCode = 500
    return jsonify(response),statusCode

@api.route('/caloriesBurned',methods=["POST"])
@jwt_required()
def addUserBurnedCalories():
    print("Hello")
    data = request.get_json()  # get data from POST request
    current_user = get_jwt_identity()
    print(data)
    print(current_user)
    try:
        # Insert data into MongoDB
        mongo.db.user.update_one({'email': current_user, "consumedDate": data['burnoutDate']}, {"$inc": {"burntCalories": int(data["burntoutCalories"])}}, upsert=True)
        response = {"status": "Data saved successfully"}
        statusCode = 200
    except Exception as e:
        response = {"status": "Error", "message": str(e)}
        statusCode = 500
    return jsonify(response),statusCode

@api.route('/weekHistory',methods=["POST"])
@jwt_required()
def getWeekHistory():
    data = request.get_json()  # get data from POST request
    print(data)
    current_user = get_jwt_identity()
    todayDate = datetime.strptime(data["todayDate"],"%m/%d/%Y")
    dates = [(todayDate-timedelta(days=x)).strftime("%m/%d/%Y") for x in range(7)]
    print(dates)
    print(current_user)
    calorieLimit = 1000
    result = []
    try:
        for index,dateToFind in enumerate(dates):
            # Every day's res item should like this
            # {
            #   dayIndex: 0,               #Interger from 0-6
            #   date: "10/13/2023",        #Date 0=today, 6=7th day ago from today
            #   foodConsumed: [            # A list of dicts, each dict contains a food item and its calories
            #     {
            #       item: "Chicken Salad",
            #       calories: 500,
            #     },
            #     {
            #       item: "Onion Soup",
            #       calories: 300,
            #     },
            #     {
            #       item: "Potato Salad",
            #       calories: 500,
            #     },
            #     {
            #       item: "Cheese Burger",
            #       calories: 500,
            #     },
            #   ],
            #   caloriesConsumed: 1800,    # the sum of all calories consumed from above list
            #   exceededDailyLimit: false, # true or false based on whether caloriesConsumed is > limit user set
            #   burntCalories: 1200,       # calories burnt out on that day
            # }
            res = {}
            data = mongo.db.user.find_one({'email': current_user, "consumedDate": dateToFind})
            print(data)
            res["dayIndex"] = index
            res["date"] = dateToFind
            if data:
                if "foodConsumed" in data:
                    res["foodConsumed"] = data["foodConsumed"]
                    res["caloriesConsumed"] = reduce(lambda a,b: a+b, [int(item["calories"]) for item in data["foodConsumed"]])
                    res["exceededDailyLimit"] = res["caloriesConsumed"]>calorieLimit
                if "burntCalories" in data:
                    res["burntCalories"] = data["burntCalories"]
            if "foodConsumed" not in res:
                res["foodConsumed"] = []
            if "caloriesConsumed" not in res:
                res["caloriesConsumed"] = 0
            if "burntCalories" not in res:
                res["burntCalories"] = 0
            if "exceededDailyLimit" not in res:
                res["exceededDailyLimit"] = False
            result.append(res)
        response = result
        statusCode = 200
    except Exception as e:
        response = {"status": "Error", "message": str(e)}
        statusCode = 500
    return jsonify(response),statusCode

@api.route('/foodCalorieMapping',methods=["GET"])
@jwt_required()
def getFoodCalorieMapping():
    try:
        data = mongo.db.food.find()
        # Response should be in this format {foodItem: calories, foodItem: calories....} 
        # For Example { Potato: 50, Acai: 20, Cheeseburger: 80 }
        response = {item["food"]:item["calories"] for item in data}
        statusCode = 200
    except Exception as e:
        response = {"status": "Error", "message": str(e)}
        statusCode = 500
    return jsonify(response),statusCode