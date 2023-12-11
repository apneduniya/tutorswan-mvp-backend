from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from database.database import (
    MONGO_CONNECTION_URL, DATABASE_NAME)


# Replace this with your MongoDB collection name for transaction
PAPER_PATTERN_COLLECTION_NAME = "paper_pattern"
RESULTS_COLLECTION_NAME = "results"


class PaperPatternDB:
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_URL)
        self.db = self.client[DATABASE_NAME]
        self.paper_pattern_collection = self.db[PAPER_PATTERN_COLLECTION_NAME]
        self.results_collection = self.db[RESULTS_COLLECTION_NAME]

    def create_paper_pattern(self, data):
        result = self.paper_pattern_collection.insert_one(data)
        return result.inserted_id
    
    def get_paper_pattern(self, user_id, id):
        paper_pattern = self.paper_pattern_collection.find_one({"_id": ObjectId(id), "user_id": user_id})
        print(paper_pattern)
        if not paper_pattern:
            return None
        paper_pattern["_id"] = str(paper_pattern["_id"])
        paper_pattern["user_id"] = str(paper_pattern["user_id"])
        return paper_pattern
    
    def get_all_paper_pattern(self, user_id, subject, id, limit):
        if not id or id == "null":
            paper_pattern_cursor = self.paper_pattern_collection.find({"user_id": user_id, "subject": subject}).sort([("_id", DESCENDING)]).limit(limit)
            paper_pattern_list = list(paper_pattern_cursor)
            for paper_pattern in paper_pattern_list:
                paper_pattern["_id"] = str(paper_pattern["_id"])
                paper_pattern["user_id"] = str(paper_pattern["user_id"])
            return paper_pattern_list
        paper_pattern = self.paper_pattern_collection.find_one({"_id": ObjectId(id), "user_id": user_id, "subject": subject})
        if not paper_pattern:
            return None
        
        paper_pattern_cursor = self.paper_pattern_collection.find({"_id": {"$lt": ObjectId(id)}, "user_id": user_id, "subject": subject}).sort([("_id", DESCENDING)]).limit(limit)
        paper_pattern_list = list(paper_pattern_cursor)
        for paper_pattern in paper_pattern_list:
            paper_pattern["_id"] = str(paper_pattern["_id"])
            paper_pattern["user_id"] = str(paper_pattern["user_id"])
        return paper_pattern_list
    
    def create_result(self, data):
        result = self.results_collection.insert_one(data)
        return result.inserted_id
    
    def get_result(self, user_id, id):
        result = self.results_collection.find_one({"_id": ObjectId(id), "user_id": user_id})
        if not result:
            return None
        result["_id"] = str(result["_id"])
        result["user_id"] = str(result["user_id"])
        return result
    
    def get_all_result(self, user_id, paper_pattern_id, id, limit):
        if not id or id == "null":
            result_cursor = self.results_collection.find({"user_id": user_id, "paper_pattern_id": paper_pattern_id}).sort([("_id", DESCENDING)]).limit(limit)
            result_list = list(result_cursor)
            for result in result_list:
                result["_id"] = str(result["_id"])
                result["user_id"] = str(result["user_id"])
            return result_list
        result = self.results_collection.find_one({"_id": ObjectId(id), "user_id": user_id, "paper_pattern_id": paper_pattern_id})
        if not result:
            return None
        
        result_cursor = self.results_collection.find({"_id": {"$lt": ObjectId(id)}, "user_id": user_id, "paper_pattern_id": paper_pattern_id}).sort([("_id", DESCENDING)]).limit(limit)
        result_list = list(result_cursor)
        for result in result_list:
            result["_id"] = str(result["_id"])
            result["user_id"] = str(result["user_id"])
        return result_list

