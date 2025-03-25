import json
from typing import List

from pydantic import BaseModel, Field
from uac.agents.base import Base
from uac.configs.config import Config
from uac.llms.llms import model_id_to_backend
from uac.prompts.retrieval_phase_prompt import QUERY_REWRITING_SYSTEM_PROMPT


class QueryRewrittenFormat(BaseModel):
    """
    A class for contextualizing user queries using a language model.
    """

    rewritten_query: List[str] = Field(description="The contextualized query.", max_length=3)


class QueryRewriting(Base):
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

    def rewrite_query(self, query: str) -> List[str]:
        """
        Contextualizes the user's query using a language model.
        """
        conversations = [
            {
                "role": "system",
                "content": QUERY_REWRITING_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": query,
            },
        ]
        if self.model_backend in ["OLLAMA"]:
            try:
                res = self.client_response(conversations, format="json")
                output_content = json.loads(res["message"]["content"])["rewritten_query"]
            except Exception:
                output_content = [query]
        elif self.model_backend in ["GROQ", "OPENAI", "LOCAL_AI"]:
            try:
                res = self.client_response(conversations, response_format=QueryRewrittenFormat)
                left_buckets_index = res.choices[0].message.content.find("{")
                right_buckets_index = res.choices[0].message.content.find("}")

                parsed_content = res.choices[0].message.content[
                    left_buckets_index : right_buckets_index + 1
                ]
                output_content = json.loads(parsed_content)["rewritten_query"]
            except Exception:
                output_content = [query]
        return output_content
