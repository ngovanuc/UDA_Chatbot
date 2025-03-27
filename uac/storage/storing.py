import os
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pymilvus import MilvusClient
from uac.configs.config import Config
from uac.embeddings.embeder import EmbeddingClient
from uac.storage.schema import DocumentAdmissionSchema



class Recall:
    def __init__(
        self,
        config: Config
    ) -> None:
        """
        Initializes the Recall class.
        """
        self.config = config
        self.embedder = EmbeddingClient(config)
        self.schema = DocumentAdmissionSchema(config)
        self.client = MilvusClient("../../milvus.db")

    def create_collection(self):
        """
        Creates a new collection in Milvus.
        """
        index_params = self.client.prepare_index_params()

        index_params.add_index(
            field_name="embedding",
            metric_type="COSINE",
            index_type="HNSW",
            params={"M": 16, "efConstruction": 150}
        )


        self.client.create_collection(
            collection_name=self.config.collection_name,
            schema=self.schema
        )

        self.client.create_index(
            collection_name="knowledge_base",
            index_params=index_params
        )

    def insert(self, data: List[Dict]):
        """
        Inserts data into the collection.
        """
        self.client.insert(
            collection_name=self.config.collection_name,
            data=data
        )

    async def search(self, query: str, topk: int = 3) -> List:
        """
        Searches for the most relevant documents based on the query.
        """
        embedding = await self.embedder.aembed([query])

        results = self.client.search(
            collection_name=self.config.collection_name,
            data = embedding,
            output_fields=["metadata"],
            limit=topk
        )
        # print(results)

        
        contents = []
        scores = []
        for result in results[0]:
            contents.append(result["entity"]["metadata"]["content"])
            scores.append(result["distance"])
        return contents, scores


if __name__ == "__main__":
    def process_data(df):
        import uuid
        contents = []
        titles = []
        ids = []

        for row in df.iterrows():
            id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(row[1]["Title"])))
            if id not in ids:
                ids.append(id)
                titles.append(str(row[1]["Title"]))
                contents.append(str(row[1]["Text"]))
        return ids, titles, contents
    
    
    
    import asyncio
    config = Config()
    # recall = Recall(config)
    embedding_fn = EmbeddingClient(config)
    import pandas as pd
    df = pd.read_csv('./data.csv', encoding='utf-8')

    ids, titles, contents = process_data(df)
    data = []
    embeddings = asyncio.run(embedding_fn.aembed(titles[0]))
    print(titles[0])
    print(len(embeddings))

    # for id, embedding, content in zip(ids, embeddings.tolist(), contents):
    #     data.append(
    #         {
    #             "embedding": embedding
    # 
    # ,
    #             "metadata": {
    #                 "id": id,
    #                 "content": content,
    #             }
    #         }
    #     )
    
    # print(data)

    # recall.create_collection()
    # print(recall.client.list_collections())
    # recall.insert(data)
    # print("Suscessfully inserted")
    

    # async def main():
    #     contents, scores = await recall.search("CÁC NGÀNH ĐÀO TẠO CỦA ĐẠI HỌC ĐÔNG Á", topk=10)
    #     print(contents)
    #     print(scores)
      

    # asyncio.run(main())
