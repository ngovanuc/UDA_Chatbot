from typing import List, Union

import numpy as np
from openai import AsyncOpenAI, OpenAI
from uac.configs.config import Config


class OpenAIClient:
    """
    A client for interfacing with OpenAI's API to generate responses from language models.

    This class encapsulates the functionality for both synchronous and asynchronous interactions
    with OpenAI's language models, allowing the client to send requests and receive generated
    responses. It supports custom configurations and model specifications.

    Attributes:
        aclient (AsyncOpenAI): An instance of the asynchronous OpenAI client for handling requests asynchronously.
        client (OpenAI): An instance of the synchronous OpenAI client for handling requests synchronously.
        model_name (str): The name of the model to be used for generating responses, as specified in the configuration.

    Methods:
        __init__(self, config: Config): Initializes the OpenAIClient with the specified configuration settings.
        aclient_response(self, model_id: str, messages: list, max_tokens: int = 1024, **kwargs) -> str:
            Asynchronously generates and returns a response from the specified model.
        client_response(self, model_id: str, messages: list, max_tokens: int = 1024, **kwargs) -> str:
            Synchronously generates and returns a response from the specified model.
    """

    def __init__(self, config: Config, host: str = None, api_key: str = None):
        """
        Initializes the OpenAIClient with the provided configuration.

        Parameters:
            config (Config): A configuration object that includes settings for the client, such as the model name.

        Examples:
            >>> config = Config(model_name="text-davinci-003")
            >>> client = OpenAIClient(config)
        """
        self.aclient = AsyncOpenAI(base_url=host, api_key=api_key)
        self.client = OpenAI(base_url=host, api_key=api_key)
        self.embedding_model_name = config.embedding_model_name

    async def toolcall_response(
        self,
        model_id: str,
        messages: list,
        max_tokens: int = 1024,
        tools: List = None,
        tool_choice: str = None,
    ) -> str:
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
        chat_completion = await self.aclient.chat.completions.create(
            messages=messages,
            model=model_id,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice=tool_choice,
            top_p=0.8,
        )

        message = chat_completion.choices[0].message.model_dump(mode="json")

        return message

    async def aclient_response(
        self, model_id: str, messages: list, max_tokens: int = 1024, **kwargs
    ) -> str:
        """
        Asynchronously generates a response from the specified model based on a list of input messages.

        Parameters:
            model_id (str): The identifier of the model to be used.
            messages (list): A list of input messages to be processed by the model.
            max_tokens (int, optional): The maximum number of tokens to generate in the response (default is 1024).
            **kwargs: Additional keyword arguments that can control the behavior of the model, such as 'streaming'.

        Returns:
            str: The generated response from the model.

        Examples:
            >>> response = await client.aclient_response("text-davinci-003", [{"role": "user", "content": "Hello"}])
            >>> print(response)
            "Hello! How can I assist you today?"
        """
        if kwargs.get("streaming"):
            return await self.aclient.chat.completions.create(
                messages=messages,
                model=model_id,
                temperature=0.1,
                top_p=0.9,
                max_tokens=max_tokens,
                stream=True,
            )
        elif kwargs.get("response_format"):
            return self.client.chat.completions.create(
                messages=messages,
                model=model_id,
                temperature=0.1,
                top_p=0.9,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
        chat_completion = await self.aclient.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.1,
            top_p=0.9,
            max_tokens=max_tokens,
        )

        content = chat_completion.choices[0].message.content

        return content

    def client_response(
        self, model_id: str, messages: list, max_tokens: int = 1024, **kwargs
    ) -> str:
        """
        Generates a synchronous response from the specified model based on a list of input messages.

        Parameters:
            model_id (str): The identifier of the model to be used.
            messages (list): A list of input messages to be processed by the model.
            max_tokens (int, optional): The maximum number of tokens to generate in the response (default is 1024).
            **kwargs: Additional keyword arguments that can control the behavior of the model, such as 'streaming'.

        Returns:
            str: The generated response from the model.

        Examples:
            >>> response = client.client_response("text-davinci-003", [{"role": "user", "content": "Hello"}])
            >>> print(response)
            "Hello! How can I assist you today?"
        """
        if kwargs.get("streaming"):
            return self.client.chat.completions.create(
                messages=messages,
                model=model_id,
                temperature=0.1,
                top_p=0.9,
                max_tokens=max_tokens,
                stream=True,
            )
        elif kwargs.get("response_format"):
            return self.client.chat.completions.create(
                messages=messages,
                model=model_id,
                temperature=0.1,
                top_p=0.9,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.1,
            top_p=0.9,
            max_tokens=max_tokens,
        )
        content = chat_completion.choices[0].message.content

        return content

    def embed(
        self,
        sentences: Union[List[str], str],
        **kwargs,
    ) -> str:
        """ """
        if isinstance(sentences, str):
            embeddings = self.client.embeddings.create(
                model=self.embedding_model_name, input=sentences, encoding_format="float"
            )

            return embeddings.data[0].embedding
        else:
            embeddings = self.client.embeddings.create(
                model=self.embedding_model_name, input=sentences, encoding_format="float"
            )

            return [d.embedding for d in embeddings.data]

    async def aembed(
        self,
        sentences: Union[List[str], str],
        **kwargs,
    ) -> str:
        """ """
        if isinstance(sentences, str):
            embeddings = self.client.embeddings.create(
                model=self.embedding_model_name, input=sentences, encoding_format="float"
            )

            return embeddings.data[0].embedding
        else:
            embeddings = await self.aclient.embeddings.create(
                model=self.embedding_model_name, input=sentences, encoding_format="float"
            )
            return [d.embedding for d in embeddings.data]
