import os
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pymilvus import Collection, connections, utility
from pymongo import MongoClient
from uac.configs.config import Config
from uac.embeddings.embeder import EmbeddingClient
from uac.storage.schema import DocumentAdmissionSchema


load_dotenv()


class RecallStorage:
    def __init__(
        self,
        embed_model: EmbeddingClient,
        config: Config,
        schema: Optional[DocumentAdmissionSchema] = None,
        milvus_config: Optional[Dict[str, str]] = None,
        mongo_config: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initializes the storage class using Milvus for vectors and MongoDB for text storage.

        Args:
            embed_model (Any): The embedding model used to embed documents.
            milvus_config (Optional[Dict[str, str]]): Milvus configuration, including host, port, and collection_name.
            mongo_config (Optional[Dict[str, str]]): MongoDB configuration, including host, port, and db/collection_name.
        """
        self.embed_model = embed_model
        self.milvus_config = milvus_config or {
            "host": os.environ.get("MILVUS_HOST"),
            "port": os.environ.get("MILVUS_PORT"),
            "db_name": config.db_name,
            "collection_name": config.collection_name,
            "vector_field_name": config.vector_field_name,
            "index_params": config.index_params,
            "vector_dim": config.vector_dim,
            "cosine_retrieval_threshold": config.cosine_retrieval_threshold,
        }

        self.milvus_connection = connections.connect(
            db_name=self.milvus_config["db_name"],
            host=self.milvus_config["host"],
            port=self.milvus_config["port"],
        )
        # Create Milvus collection if it doesn't exist
        self.milvus_collection = self.create_milvus_collection(self.milvus_config, schema=schema)

        self.mongo_config = mongo_config or {
            "mongo_url": os.environ.get("MONGO_URL"),
            "db_name": config.db_name,
            "collection_name": config.collection_name,
        }

        # Initialize MongoDB client
        self.mongo_client = MongoClient(self.mongo_config["mongo_url"])
        self.mongo_db = self.mongo_client[self.mongo_config["db_name"]]
        self.mongo_collection = self.mongo_db[self.mongo_config["collection_name"]]

    def create_milvus_collection(
        self, config: Config, schema: DocumentAdmissionSchema
    ) -> Collection:
        """
        Creates a Milvus collection for storing and retrieving data.

        Args:
            config (Config): The configuration object containing the necessary settings for the Milvus collection.
            schema (HistoryMessageSchema): The schema for the history messages to be stored in the collection.

        Returns:
            Collection: The Milvus collection object.
        """
        if utility.has_collection(config["collection_name"]):
            collection = Collection(name=config["collection_name"])
        else:
            collection = Collection(name=config["collection_name"], schema=schema)
            collection.create_index(
                field_name=config["vector_field_name"], index_params=config["index_params"]
            )

        collection.load()

        return collection

    def store_vectors(self, documents: List[Dict[str, Any]]):
        """
        Stores the embedded documents into Milvus and saves text into MongoDB.

        Args:
            documents (List[Dict[str, Any]]): A list of chunked documents containing both text and metadata.

        Returns:
            Milvus: The Milvus vector store with the embedded documents.

        Raises:
            ValueError: If the document list is empty.
        """
        if not documents:
            raise ValueError("Document list is empty, cannot store in Milvus.")

        # Generate IDs and prepare documents
        ids = [str(uuid.uuid4()) for _ in documents]
        embedding_list = [
            self.embed_model.embed(doc["title"] + "\n" + doc["content"]) for doc in documents
        ]

        metadata = [
            {"id": doc_id, "text": doc["title"] + "\n" + doc["content"]}
            for doc_id, doc in zip(ids, documents)
        ]

        vectorstore = [
            {"embedding": embedding, "metadata": metadata}
            for embedding, metadata in zip(embedding_list, metadata)
        ]

        # Store vectors in Milvus
        self.milvus_collection.insert(vectorstore)

        # Store text and metadata (including ID) in MongoDB
        for data in metadata:
            self.mongo_collection.insert_one(data)

        return vectorstore, ids

    def retrieve_vectors(
        self,
        query: str,
        topk: int = 3,
        param: Dict = None,
        expr: str = None,
        output_fields=None,
    ) -> List:
        """
        Performs a search in the Milvus collection for the given query and returns the top k results.

        Args:
            query (str): The query to search for.
            topk (int): The number of top results to return.
            param (Dict, optional): Additional parameters to pass to the search function. Defaults to None.

        Returns:
            List: The top k search results.
        """
        if not query:
            raise ValueError("Query string is empty.")

        # Perform the search
        vector_data = self.embed_model.embed([query])
        # Perform the search
        results = self.milvus_collection.search(
            data=vector_data,
            anns_field=self.milvus_config["vector_field_name"],
            param=param or self.milvus_config["index_params"],
            limit=topk,
            expr=expr,
            output_fields=output_fields or ["metadata"],
        )
        ids = []
        score = []
        for result in results:
            ids.extend([hit.metadata["id"] for hit in result])
            score.extend([hit.score for hit in result])
        return ids, score

    def retrieve_text_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves text and metadata from MongoDB based on the document ID.

        Args:
            doc_id (str): The ID of the document to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The retrieved document from MongoDB, or None if not found.
        """
        result = self.mongo_collection.find_one({"id": doc_id})
        return result["text"] if result else None
