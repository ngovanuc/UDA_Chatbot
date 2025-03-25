import json
from typing import Dict, List

from pydantic import BaseModel, Field
from uac.agents.base import Base
from uac.configs.config import Config
from uac.llms.llms import model_id_to_backend
from uac.prompts.retrieval_phase_prompt import QUERY_CONTEXTUAL_SYSTEM_PROMPT


class Contextualization(BaseModel):
    """
    A class for contextualizing user queries using a language model.
    """

    contextualized_query: str = Field(description="The contextualized query.", max_length=1)


class QueryContextual(Base):
    """
    A class for contextualizing user queries using a language model.

    This class extends the Base class and provides functionality to enhance
    user queries with additional context, potentially improving the relevance
    and accuracy of subsequent processing or retrieval operations.

    Attributes:
        config (Config): Configuration object containing settings for the contextualizer.

    Methods:
        contextualize_query(query: Union[str, List[str]]) -> Union[str, List[str]]:
            Contextualizes the given query or list of queries.
    """

    def __init__(self, config: Config):
        super().__init__(config, mode="extraction")
        self.model_backend = model_id_to_backend(self.client.model_id)

    @staticmethod
    def process_history_chat(history_chat: List[Dict]) -> str:
        """
        Process the history chat to extract relevant information.
        """
        if history_chat == []:
            return ""
        else:
            # history_chat = history_chat[-10:]
            processed_history_chat = [
                (
                    f"User: {item['content']}"
                    if item["role"] == "user"
                    else f"Assistant: {item['content']}"
                )
                for item in history_chat
            ]
            return "\n".join(processed_history_chat)

    def contextualize_query(self, query: str, history_chat: List[Dict]) -> str:
        """
        Contextualizes the user's query using a language model.
        """

        query_input = f"History Chat: {self.process_history_chat(history_chat)}\n\nQuery: {query}"
        conversations = [
            {
                "role": "system",
                "content": QUERY_CONTEXTUAL_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": query_input,
            },
        ]

        if self.model_backend in ["OLLAMA"]:
            try:
                res = self.client_response(conversations, format="json")
                output_content = json.loads(res["message"]["content"])["contextualized_query"]
            except Exception:
                output_content = query
        elif self.model_backend in ["GROQ", "OPENAI", "LOCAL_AI"]:
            try:
                res = self.client_response(conversations, response_format=Contextualization)
                left_buckets_index = res.choices[0].message.content.find("{")
                right_buckets_index = res.choices[0].message.content.find("}")

                parsed_content = res.choices[0].message.content[
                    left_buckets_index : right_buckets_index + 1
                ]
                output_content = json.loads(parsed_content)["contextualized_query"]
            except Exception:
                output_content = query
        return output_content
