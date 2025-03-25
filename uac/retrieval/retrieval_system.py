from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

import chainlit as cl

# from cohere_rerank import CohereRerank  # Giả sử bạn đã cài và có thư viện này
from langchain_cohere import CohereRerank
from loguru import logger
from uac.configs.config import Config
from uac.retrieval.autocut_irrelevant_context import AutoCut
from uac.retrieval.query_contextual import QueryContextual
from uac.retrieval.query_rewriting import QueryRewriting
from uac.storage.storing import Recall
from uac.storage.schema import DocumentAdmissionSchema


# Define an abstract class for Retrieval
class IRetrieval(ABC):
    @abstractmethod
    def retrieve(self, query: Union[str, List[str]]) -> List[Dict]:
        pass

    @abstractmethod
    def process_candidates(self, topk_candidates: List[Dict]) -> Optional[str]:
        pass


class Retrieval:
    """
    Retrieval module to handle data recall from the storage.

    Args:
        config (Config): Configuration object.
        topk (int): Number of top-k results for recall.
        embedding_fn (Callable): Embedding function for recall.
        user_id (str): The ID of the user for whom the recall is performed.

    Attributes:
        config (Config): Configuration object.
        recall (RecallStorage): Instance of the RecallStorage class.
        topk (int): Number of top-k results for recall.
        user_id (str): User ID for the recall process.
        reranker (CohereRerank): Instance of CohereRerank for reranking results.
    """

    def __init__(
        self, config: Config, topk: int, embedding_fn, rerank_model: CohereRerank
    ) -> None:
        self.config = config
        self.topk = topk
        self.database = Recall(
            config=config
        )
        self.query_contextual = QueryContextual(config)
        self.query_rewriting = QueryRewriting(config)
        self.reranker = rerank_model  # Thêm mô hình rerank

    @cl.step(name="Contextualize", type="retrieval")
    def _contextualize_query(self, query: str, history_chat: List[Dict]) -> str:
        return self.query_contextual.contextualize_query(query, history_chat)

    @cl.step(name="Rewrite", type="retrieval")
    def _rewrite_query(self, query: str) -> List[str]:
        return self.query_rewriting.rewrite_query(query)

    @cl.step(name="Search", type="retrieval")
    async def search(self, query: str) -> Optional[List[Dict]]:
        logger.info(f"Retrieving top-{self.topk} candidates for query: {query}")
        try:
            contents, _ = await self.database.search(query, topk=3)
            return contents
        except Exception as e:
            logger.error(f"Error retrieving candidates: {str(e)}")

    @cl.step(name="Rerank", type="rerank")
    def _rerank(self, retrieval_results: List[List[Any]], k: int = 60) -> List[Tuple[Any, float]]:
        """
        Rerank the retrieval results using reciprocal rank fusion.

        This method takes the retrieval results and applies a reranking algorithm
        based on reciprocal rank fusion. It assigns scores to documents based on
        their ranks across multiple retrieval results and returns a sorted list
        of reranked documents.

        Args:
            retrieval_results (List[List[Any]]): A list of retrieval results, where
                each inner list contains document strings.
            k (int, optional): A constant used in the reciprocal rank fusion
                formula. Defaults to 60.

        Returns:
            List[Tuple[Any, float]]: A list of tuples, where each tuple contains
                a document and its corresponding fused score. The list is sorted
                in descending order of the fused scores.
        """

        fused_scores = {}
        for docs in retrieval_results:
            for rank, doc_str in enumerate(docs):
                if doc_str not in fused_scores:
                    fused_scores[doc_str] = 0.0
                else:
                    fused_scores[doc_str] += 1 / (rank + k)

        reranked_results = [
            (doc, score)
            for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        ]

        return reranked_results

    async def retrieve(self, query: str, history_chat: List) -> List[Tuple[str, float]]:
        """
        Retrieve the top-k candidates from the database based on the user query.
        Caching is used to optimize repeated queries.

        Args:
            query (str): The user's input query.

        Returns:
            List[Dict]: The top-k candidates from the recall process
        """

        # contextualize query

        contextualized_query = self._contextualize_query(query, list(history_chat))
        logger.info(f"Contextualized query: {contextualized_query}")

        # rewrite query
        # queries = self._rewrite_query(contextualized_query)
        # logger.info(f"Rewritten queries: {queries}")

        # search
        if isinstance(contextualized_query, str):
            context_retrieval = await self.search(contextualized_query)
            return context_retrieval
        else:
            raise ValueError("Query must be a string")

        # rerank
        # if not context_retrieval or all(
        #     context_retrieval is None for context_retrieval in context_retrieval
        # ):
        #     return None
        # else:
        #     precessed_contexts = []
        #     for contexts in context_retrieval:
        #         precessed_contexts.append([context["text"] for context in contexts])
        #     rerank_result = self._rerank(precessed_contexts)
            
