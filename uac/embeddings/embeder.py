import os
from typing import List, Optional, Union

from loguru import logger
from uac.configs.config import Config
from uac.embeddings.infinity_emb import InfinityEmbedding
from uac.llms.ollama_client import OllamaClient
from uac.llms.openai_client import OpenAIClient


config = Config()
ollama = OllamaClient(config)
openai = OpenAIClient(
    config, host=os.environ["OPENAI_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"]
)

all_models = {
    "GROQ": [],
    "OPENAI": [
        ("ADA-002", "text-embedding-ada-002"),
        ("3-SMALL", "text-embedding-3-small"),
        ("3-LARGE", "text-embedding-3-large"),
    ],
    "LOCAL_AI": [],
    "OLLAMA": [],
}

if ollama.client:
    all_models["OLLAMA"] = ollama.models


def model_id_to_backend(model_name: str) -> Optional[str]:
    """
    Determines the backend corresponding to a given model identifier.

    Args:
        model_name (str): The identifier of the model.

    Returns:
        Optional[str]: The name of the backend supporting the model if found; otherwise, None.

    Example:
        >>> backend = model_id_to_backend("llama3-8b-8192")
        >>> print(backend)
        "GROQ"
    """
    for backend, models in all_models.items():
        for model in models:
            if model[1] == model_name:
                return backend
    return None


class EmbeddingClient:
    """
    Provides an abstraction for interacting with different embedding models, such as OLLAMA and OpenAI.

    The `EmbeddingClient` class handles the initialization and usage of the underlying embedding model client.

    The `_get_client` method is used internally to retrieve the appropriate embedding model client based on the configured backend.
    """

    def __init__(self, config: Config = Config(), device: str = "cuda"):
        self.config = config
        self.client = self._get_client()

    def _get_client(self) -> Union[InfinityEmbedding, OllamaClient, OpenAIClient]:
        model_backend = model_id_to_backend(self.config.embedding_model_name)
        if model_backend is None:
            raise ValueError(f"Model '{self.config.embedding_model_name}' is not supported.")
        logger.success(f"Model: {self.config.embedding_model_name}, Backend: {model_backend}")

        model_mapping = {"OLLAMA": ollama, "OPENAI": openai}

        try: 
            model_client = model_mapping[model_backend]
            return model_client
        except KeyError:
            raise ValueError(f"Backend '{model_backend}' is not supported.")

    async def aembed(self, sentences: Union[List[str], str]):
        return await self.client.aembed(sentences)

    def embed(self, sentences: Union[List[str], str]):
        return self.client.embed(sentences)
