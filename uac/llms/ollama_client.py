import os
from typing import Dict, List, Union

import numpy as np
from dotenv import load_dotenv
from ollama import AsyncClient, Client
from uac.configs.config import Config


load_dotenv()


class OllamaClient:
    """
    A client for interfacing with Ollama's API to generate responses from language models.

    This class offers both synchronous and asynchronous methods to communicate with Ollama's language models, facilitating
    the generation of text-based responses. It is designed to handle requests with custom configurations and model parameters.

    Attributes:
        aclient (AsyncClient): An instance of the asynchronous client for handling non-blocking requests.
        client (Client): An instance of the synchronous client for handling standard blocking requests.
        models (list): A list of models available through the API, each represented by a tuple containing the model name and its ID.
        model_name (str): The name of the model to be used, as configured.

    Methods:
        __init__(self, config: Config): Initializes the OllamaClient with the specified configuration settings.
        aclient_response(self, model_id: str, messages: list, max_tokens: int = 1024, **kwargs) -> Union[str, Any]:
            Asynchronously generates and returns a response from the specified model.
        client_response(self, model_id: str, messages: list, max_tokens: int = 1024, **kwargs) -> str:
            Synchronously generates and returns a response from the specified model.
    """

    def __init__(self, config: Config):
        """
        Initializes the OllamaClient with the specified configuration settings, preparing it for API interactions.

        Parameters:
            config (Config): The configuration object containing settings such as the model name and API endpoints.

        Examples:
            >>> config = Config(model_name="gpt-3.5-turbo")
            >>> client = OllamaClient(config)
        """
        OLLAMA_API_URL = os.environ["OLLAMA_BASE_URL"]
        self.aclient = AsyncClient(host=OLLAMA_API_URL)
        self.client = Client(host=OLLAMA_API_URL)
        self.models = [(model["name"], model["model"]) for model in self.client.list()["models"]]
        self.embedding_model_name = config.embedding_model_name

    async def aclient_response(
        self,
        model_id: str,
        messages: List[Dict],
        max_tokens: int = 1024,
        temperature: float = 0.1,
        **kwargs,
    ) -> str:
        """
        Asynchronously generates a response from the specified model based on a list of input messages, with optional streaming.

        Parameters:
            model_id (str): The identifier of the model to be used.
            messages (list): Input messages to be processed by the model.
            max_tokens (int, optional): Maximum number of tokens to generate (default is 1024).
            **kwargs: Additional keyword arguments for customizing the request, such as 'streaming'.

        Returns:
            Union[str, Any]: The generated response or a streaming generator if 'streaming' is enabled.

        Examples:
            >>> response = await client.aclient_response("gpt-3.5-turbo", [{"role": "user", "content": "Hello"}])
            >>> print(response)
            "Hello! How can I assist you today?"
        """
        if kwargs.get("streaming"):
            return await self.aclient.chat(
                messages=messages,
                model=model_id,
                keep_alive="30m",
                options={
                    "num_ctx": 8192,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "num_predict": max_tokens,
                    "low_vram": True,
                },
                stream=True,
            )

        elif kwargs.get("format"):
            return self.client.chat(
                messages=messages,
                model=model_id,
                format="json",
                keep_alive="30m",
                options={
                    "num_ctx": 8192,
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": max_tokens,
                    "low_vram": True,
                },
            )

        chat_completion = await self.aclient.chat(
            messages=messages,
            model=model_id,
            keep_alive="30m",
            options={
                "num_ctx": 8192,
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens,
                "low_vram": True,
            },
        )
        content = chat_completion["message"]["content"]
        return content

    def client_response(
        self, model_id: str, messages: List[Dict], max_tokens: int = 1024, **kwargs
    ) -> str:
        """
        Synchronously generates a response from the specified model based on a list of input messages, with optional streaming.

        Parameters:
            model_id (str): The identifier of the model to be used.
            messages (list): Input messages to be processed by the model.
            max_tokens (int, optional): Maximum number of tokens to generate (default is 1024).
            **kwargs: Additional keyword arguments for customizing the request, such as 'streaming'.

        Returns:
            str: The generated response from the model.

        Examples:
            >>> response = client.client_response("gpt-3.5-turbo", [{"role": "user", "content": "Hello"}])
            >>> print(response)
            "Hello! How can I assist you today?"
        """
        if kwargs.get("streaming"):
            return self.client.chat(
                messages=messages,
                model=model_id,
                keep_alive=0,
                options={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": max_tokens,
                    "num_ctx": 8192,
                    "low_vram": True,
                },
                stream=True,
            )

        elif kwargs.get("format"):
            return self.client.chat(
                messages=messages,
                model=model_id,
                format="json",
                keep_alive="30m",
                options={
                    "num_ctx": 8192,
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": max_tokens,
                    "low_vram": True,
                },
            )

        chat_completion = self.client.chat(
            messages=messages,
            model=model_id,
            keep_alive=0,
            options={
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": max_tokens,
                "num_ctx": 8192,
                "low_vram": True,
            },
        )

        content = chat_completion["message"]["content"]
        return content

    async def toolcall_response(
        self,
        model_id: str,
        messages: List[Dict],
        max_tokens: int = 1024,
        tools: List = None,
        tool_choice: str = None,
    ):
        """
        Asynchronously generates a response from the specified model based on a list of input messages.

        Parameters:
        -----------
        model_id : str
            The identifier of the model to be used.
        messages : list
            A list of input messages to be processed by the model.
        max_tokens : int, optional
            The maximum number of tokens to generate in the response (default is 1024).
        tools: list
            A list of tools for calling agent
        tool_choice: str
            The choice mode of tool to use for calling agent eg.[none, auto, required]

        Returns:
        message: str
            Message instant of OpenAI Completions API
        """

        chat_completion = await self.aclient.chat(
            messages=messages,
            model=model_id,
            keep_alive="30m",
            tools=tools,
            options={
                "num_ctx": 8192,
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": max_tokens,
                "low_vram": True,
            },
        )
        return chat_completion["message"]

    async def aembed(
        self,
        sentences: Union[List[str], str],
        **kwargs,
    ) -> str:
        """
        Asynchronously generates a response from the specified model based on a list of input messages, with optional streaming.

        Parameters:
            model_id (str): The identifier of the model to be used.
            messages (list): Input messages to be processed by the model.
            max_tokens (int, optional): Maximum number of tokens to generate (default is 1024).
            **kwargs: Additional keyword arguments for customizing the request, such as 'streaming'.

        Returns:
            Union[str, Any]: The generated response or a streaming generator if 'streaming' is enabled.

        Examples:
            >>> response = await client.aclient_response("gpt-3.5-turbo", [{"role": "user", "content": "Hello"}])
            >>> print(response)
            "Hello! How can I assist you today?"
        """
        if isinstance(sentences, str):
            embeddings = await self.aclient.embed(
                model=self.embedding_model_name,
                input=sentences,
                options={
                    "num_ctx": 8192,
                },
            )

            return np.array(embeddings["embeddings"][0])
        else:
            embeddings = await self.aclient.embed(
                model=self.embedding_model_name,
                input=sentences,
                options={
                    "num_ctx": 8192,
                },
            )
            return np.array(embeddings["embeddings"])

    def embed(
        self,
        sentences: Union[List[str], str],
        **kwargs,
    ) -> str:
        """
        Asynchronously generates a response from the specified model based on a list of input messages, with optional streaming.

        Parameters:
            model_id (str): The identifier of the model to be used.
            messages (list): Input messages to be processed by the model.
            max_tokens (int, optional): Maximum number of tokens to generate (default is 1024).
            **kwargs: Additional keyword arguments for customizing the request, such as 'streaming'.

        Returns:
            Union[str, Any]: The generated response or a streaming generator if 'streaming' is enabled.

        Examples:
            >>> response = await client.aclient_response("gpt-3.5-turbo", [{"role": "user", "content": "Hello"}])
            >>> print(response)
            "Hello! How can I assist you today?"
        """
        if isinstance(sentences, str):
            embeddings = self.client.embed(
                model=self.embedding_model_name,
                input=sentences,
                options={
                    "num_ctx": 8192,
                },
            )

            return np.array(embeddings["embeddings"][0])
        else:
            embeddings = self.client.embed(
                model=self.embedding_model_name,
                input=sentences,
                options={
                    "num_ctx": 8192,
                },
            )
            return np.array(embeddings["embeddings"])
