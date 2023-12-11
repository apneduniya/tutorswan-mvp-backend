from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from database.database import (MONGO_CONNECTION_URL, DATABASE_NAME)


# Replace this with your MongoDB collection name for users
USERS_COLLECTION_NAME = "users"
TEMP_USERS_COLLECTION_NAME = "temp_users"

class UserDB:
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_URL)
        self.db = self.client[DATABASE_NAME]
        self.users_collection = self.db[USERS_COLLECTION_NAME]
        self.temp_users_collection = self.db[TEMP_USERS_COLLECTION_NAME]

    def create_user(self, user_data):
        result = self.users_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        return user_id
    
    def create_temp_user(self, user_data):
        result = self.temp_users_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        return user_id
    
    def get_temp_user_transaction_id(self, id):
        user = self.temp_users_collection.find_one({"transaction_id": id})
        return user
    
    def delete_temp_user(self, id):
        self.temp_users_collection.delete_one({"_id": ObjectId(id)})

    def create_new_subject(self, user_id, subject_name):
        result = self.users_collection.update_one({"_id": ObjectId(user_id)}, {"$push": {"subjects": subject_name}})
        return result
    
    def reduce_credits(self, user_id, credits):
        result = self.users_collection.update_one({"_id": ObjectId(user_id)}, {"$inc": {"total_credits": -credits}})
        return result
    
    def get_all_user(self, id, limit):
        if not id or id == "null":
            users_cursor = self.users_collection.find({}, {"password": False}).sort([("_id", DESCENDING)]).limit(limit) # Find the documents after the given id and get 'limit' number of rows
            users_list = list(users_cursor)
            return users_list
        user = self.users_collection.find_one({"_id": ObjectId(id)}) # Find the document with the given id
        if not user:
            return None
        
        users_cursor = self.users_collection.find({"_id": {"$lt": ObjectId(id)}}).sort([("_id", DESCENDING)]).limit(limit) # Find the documents after the given id and get 'limit' number of rows
        users_list = list(users_cursor)
        return users_list

    def get_user(self, user_id):
        user = self.users_collection.find_one({"_id": ObjectId(user_id)})
        return user
    
    def get_user_email(self, email):
        user = self.users_collection.find_one({"email": email})
        return user
    
    def get_total_invested_money(self):
        result = self.users_collection.aggregate([
            {
                "$group": {
                    "_id": '',
                    "invested": {"$sum": "$invested"}
                }
            }, {
                "$project": {
                    "_id": 0,
                    "invested": '$invested'
                }
            }
        ])

        result = list(result)
        print(result)
        if len(result) == 0:
            return 0
        return result[0]["invested"]
    
    def add_profit(self, user_id, amount):
        self.users_collection.update_one({"_id": ObjectId(user_id)}, {"$inc": {"profit": amount}})

    def add_invested(self, user_id, amount):
        self.users_collection.update_one({"_id": ObjectId(user_id)}, {"$inc": {"invested": amount}})

    def deduct_profit(self, user_id, amount):
        self.users_collection.update_one({"_id": ObjectId(user_id)}, {"$inc": {"profit": -amount}})

    def deduct_invested(self, user_id, amount):
        self.users_collection.update_one({"_id": ObjectId(user_id)}, {"$inc": {"invested": -amount}})

    