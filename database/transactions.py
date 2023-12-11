from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from database.database import (
    MONGO_CONNECTION_URL, DATABASE_NAME)


# Replace this with your MongoDB collection name for transaction
TRANSACTIONS_COLLECTION_NAME = "transactions"


class TransactionsDB:
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_URL)
        self.db = self.client[DATABASE_NAME]
        self.transaction_collection = self.db[TRANSACTIONS_COLLECTION_NAME]

    def create_transaction(self, user_id, description, amount, transaction_id, user_name, user_email, date_time, type):
        result = self.transaction_collection.insert_one({
            "user_id": user_id,
            "description": description,
            "amount": amount,
            "transaction_id": transaction_id,
            "user_name": user_name,
            "user_email": user_email,
            "date_time": date_time,
            "type": type
        })
        return result.inserted_id
    
    def get_transaction_by_id(self, transaction_id):
        transaction = self.transaction_collection.find_one({"transaction_id": transaction_id})
        if not transaction:
            return None
        transaction["_id"] = str(transaction["_id"])
        transaction["user_id"] = str(transaction["user_id"])
        return transaction

    def get_transactions(self, limit, id):
        if not id or id == "null":
            transaction_cursor = self.transaction_collection.find().sort([("_id", DESCENDING)]).limit(limit)
            transaction_list = list(transaction_cursor)
            for transaction in transaction_list:
                transaction["_id"] = str(transaction["_id"])
                transaction["user_id"] = str(transaction["user_id"])
            return transaction_list
        
        transaction = self.transaction_collection.find_one({"_id": ObjectId(id)}) # Find the document with the given id
        if not transaction:
            return None
        
        transaction_cursor = self.transaction_collection.find({"_id": {"$lt": ObjectId(id)}}).sort([("_id", DESCENDING)]).limit(limit) # Find the documents after the given id and get 'limit' number of rows
        transaction_list = list(transaction_cursor)
        for transaction in transaction_list:
                transaction["_id"] = str(transaction["_id"])
                transaction["user_id"] = str(transaction["user_id"])
        return transaction_list
    
    def get_transaction_by_user_id(self, user_id, limit, id):
        if not id or id == "null":
            transaction_cursor = self.transaction_collection.find({"user_id": ObjectId(user_id)}).sort([("_id", DESCENDING)]).limit(limit)
            transaction_list = list(transaction_cursor)
            for transaction in transaction_list:
                transaction["_id"] = str(transaction["_id"])
                transaction["user_id"] = str(transaction["user_id"])
                transaction.pop("user_name")
                transaction.pop("user_email")
                transaction.pop("_id")
                transaction.pop("user_id")
            return transaction_list
        
        transaction = self.transaction_collection.find_one({"_id": ObjectId(id)})
        if not transaction:
            return None
        
        transaction_cursor = self.transaction_collection.find({"user_id": ObjectId(user_id), "_id": {"$lt": ObjectId(id)}}).sort([("_id", DESCENDING)]).limit(limit)
        transaction_list = list(transaction_cursor)
        for transaction in transaction_list:
                transaction["_id"] = str(transaction["_id"])
                transaction["user_id"] = str(transaction["user_id"])
                transaction.pop("user_name")
                transaction.pop("user_email")
                transaction.pop("_id")
                transaction.pop("user_id")
        return transaction_list

    

