import os
from typing import Dict, List, Optional, Union

from dotenv import load_dotenv
from pymongo import MongoClient
from uac.configs.config import Config


load_dotenv()


class UserInfoManagement:
    """
    A class for managing user information in a MongoDB database.

    This class provides methods for inserting, retrieving, and updating user data
    in a specified MongoDB collection. It uses the configuration provided to connect
    to the appropriate database and collection.

    Attributes:
        client (MongoClient): The MongoDB client connection.
        db (Database): The MongoDB database instance.
        collection (Collection): The MongoDB collection for user management.
        mongo_collection_name (str): The name of the MongoDB collection.
    Methods:
        insert_one(self, data: Dict) -> None:
            Inserts a single user document into the collection.

        find_one(self, query: Dict) -> Optional[Dict]:
            Retrieves a single user document based on the provided query.

        update_one(self, query: Dict, update: Dict) -> None:
            Updates a single user document based on the provided query and update.

        find_all(self) -> List[Dict]:
            Retrieves all user documents from the collection.

        delete_one(self, query: Dict) -> None:
            Deletes a single user document based on the provided query.

        delete_all(self) -> None:
            Deletes all user documents from the collection.
    """

    def __init__(self, config: Config):
        self.client = MongoClient(host=os.environ["MONGO_URL"])
        if config.db_name in self.client.list_database_names():
            self.db = self.client[config.db_name]
        else:
            raise ValueError(f"Database {config.db_name} does not exist in Mongo Server")

        self.mongo_collection_name = config.user_management_collection_name

        if self.mongo_collection_name in self.db.list_collection_names():
            self.collection = self.db[self.mongo_collection_name]
        else:
            self.collection = self.db.create_collection(self.mongo_collection_name)

    def insert_one(self, data: Dict) -> None:
        """
        Inserts a single document into the MongoDB collection.

        Args:
            data (Dict): The document to be inserted.

        Returns:
            None
        """
        return self.collection.insert_one(data)

    def insert_many(self, data: List[Dict]) -> None:
        """
        Inserts multiple documents into the MongoDB collection.

        Args:
            data (List[Dict]): A list of documents to be inserted.

        Returns:
            None
        """

        return self.collection.insert_many(data)

    def find_one(
        self, query: Dict, output_field: Optional[Union[str, List[str]]]
    ) -> Optional[Dict]:
        """
        Finds a single document in the MongoDB collection that matches the given query, and returns the specified output fields.

        Args:
            query (Dict): The query to find the document.
            output_field (Optional[Union[str, List[str]]]): The field(s) to return from the matched document. If a single string is provided, only that field will be returned. If a list of strings is provided, those fields will be returned.

        Returns:
            A matched documents, or None if no document is found.
        """

        if isinstance(output_field, str):
            return self.collection.find_one(query, {f"{output_field}": 1})
        elif isinstance(output_field, list):
            output_fields = {}
            for field in output_field:
                output_fields[field] = 1
            return self.collection.find_one(query, output_fields)
        else:
            return self.collection.find_one(query)

    def find(self, query: Dict, output_field: Optional[Union[str, List[str]]]) -> Optional[Dict]:
        """
        Finds a single document in the MongoDB collection that matches the given query, and returns the specified output fields.

        Args:
            query (Dict): The query to find the document.
            output_field (Optional[Union[str, List[str]]]): The field(s) to return from the matched document. If a single string is provided, only that field will be returned. If a list of strings is provided, those fields will be returned.

        Returns:
            All matched documents, or None if no document is found.
        """

        if isinstance(output_field, str):
            return self.collection.find(query, {f"{output_field}": 1})
        elif isinstance(output_field, list):
            output_fields = {}
            for field in output_field:
                output_fields[field] = 1
            return self.collection.find(query, output_fields)
        else:
            return self.collection.find(query)

    def update_one(self, query: Dict, update_data: Dict) -> None:
        """
        Updates a single document in the MongoDB collection that matches the given query, with the provided update data.

        Args:
            query (Dict): The query to find the document to update.
            update_data (Dict): The data to update the matched document with.

        Returns:
            None
        """

        return self.collection.update_one(query, {"$set": update_data})

    def delete_one(self, query: Dict) -> None:
        """
        Deletes a single document in the MongoDB collection that matches the given query.
        """
        return self.collection.delete_one(query)
