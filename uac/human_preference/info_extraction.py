import json
from typing import Dict

from pydantic import BaseModel
from uac.agents.base import Base
from uac.configs.config import Config
from uac.llms.llms import model_id_to_backend


class InfoExtraction(Base):
    """
    Retrieves information based on a user's query using a language model.

    The `InfoRetriever` class is responsible for analyzing a user's query and retrieving relevant information.

    The `analyze_the_goal` method first cleans the input query by removing extra whitespace.
    """

    def __init__(self, config: Config):
        """
        Initialize the MathConceptRetriever.

        Args:
            config (Config): Configuration object for the InfoRetriever.
        """
        super().__init__(config, mode="extraction")
        self.model_backend = model_id_to_backend(self.client.model_id)

    async def analyze_the_response(self, system_prompt, queries: str) -> dict:
        """
        Analyzes the user's goal from the given query.

        Args:
            query (list): The input query to analyze.

        Returns:
            dict: Analyzed user's goal as a dictionary.
        """
        conversations = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": queries,
            },
        ]

        if self.model_backend in ["OLLAMA"]:
            try:
                res = await self.aclient_response(conversations, format="json")
                output_content = json.loads(res["message"]["content"])
            except Exception:
                output_content = {"goal": ""}
        elif self.model_backend in ["GROQ", "OPENAI"]:
            try:
                res = await self.aclient_response(conversations, response_format="json")
                left_buckets_index = res.find("{")
                right_buckets_index = res.rfind("}")
                parsed_content = res[
                    left_buckets_index : right_buckets_index + 1
                ]

                output_content = json.loads(parsed_content)
            except Exception:
                output_content = {"goal": ""}
        return output_content
