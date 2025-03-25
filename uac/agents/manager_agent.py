import json
import re
from typing import Dict, List

from uac.agents.base import Base
from uac.configs.config import Config
from uac.llms.llms import model_id_to_backend
from uac.prompts.router_prompt import ROUTER_SYSTEM_PROMPT
from uac.router.router_construction import QuestionAnswering, OutOfDomian
from uac.utils.util import convert_pydantic_models


class ManagerAgent(Base):
    """
    The ManagerAgent is responsible for coordinating the tutoring process by routing user inputs
    to appropriate functions, managing conversation flow, and delegating tasks to specialized agents or tools.
    """

    def __init__(self, config: Config):
        super().__init__(config, mode="function_call")

    def _get_tools(self, function_calls: List) -> List:
        """
        Converts a list of Pydantic models to OpenAI tools.

        Args:
            function_calls (List): A list of Pydantic model classes to be converted.

        Returns:
            List: A list of corresponding OpenAI tools.
        """
        return convert_pydantic_models(function_calls)

    async def run_agent(self, user_input: str, history_chat: List[Dict]) -> str:
        """
        Processes the user's input, routes to the appropriate function, and returns the function name.

        Args:
            user_input (str): The user's input message.
            history_chat (List[Dict]): Conversation history.

        Returns:
            str: Function name to call or "NoFunctionCalling" if no function detected.
        """
        tools = self._get_tools([QuestionAnswering, OutOfDomian])

        messages = self._build_messages(
            user_input=user_input,
            conversation=history_chat[-6:],
            system_prompt=ROUTER_SYSTEM_PROMPT,
        )

        response = await self.toolcall_response(
            messages=messages, tools=tools, tool_choice="auto", max_tokens=512
        )
        print(response)
        return self._process_response(response)

    def _process_response(self, response: Dict) -> str:
        """
        Processes the response from the model and extracts the function call details.

        Args:
            response (Dict): The response object returned by the model.

        Returns:
            str: The name of the function to call and its arguments, or "NoFunctionCalling" if not found.
        """
        model_backend = model_id_to_backend(self.client.model_id)

        if model_backend in ["OLLAMA"]:
            return self._extract_ollama_function(response)
        elif model_backend in ["OPENAI", "GROQ", "LOCAL_AI"]:
            return self._extract_openai_function(response)

        return "NoFunctionCalling", "No arguments"

    def _extract_ollama_function(self, response: Dict) -> str:
        """
        Extracts function call details for the OLLAMA backend.

        Args:
            response (Dict): The response object returned by OLLAMA.

        Returns:
            str: The function name and arguments, or "NoFunctionCalling" if not found.
        """
        if "tool_calls" in response and response["tool_calls"]:
            return (
                response["tool_calls"][0]["function"]["name"],
                response["tool_calls"][0]["function"]["arguments"],
            )

        matches = re.findall(
            r"<tool_call>\s*(.*?)\s*</tool_call>", response.get("content", ""), re.DOTALL
        )
        if matches:
            try:
                parsed_json = json.loads(matches[0])
                return parsed_json["name"], parsed_json["arguments"]
            except json.JSONDecodeError:
                pass

        return "NoFunctionCalling", "No arguments"

    def _extract_openai_function(self, response: Dict) -> str:
        """
        Extracts function call details for the OPENAI and GROQ backends.

        Args:
            response (Dict): The response object returned by the model.

        Returns:
            str: The function name and arguments, or "NoFunctionCalling" if not found.
        """
        if response.tool_calls:
            return (
                response.tool_calls[0].function.name,
                json.loads(response.tool_calls[0].function.arguments),
            )
        matches = re.findall(
            r"<tool_call>\s*(.*?)\s*</tool_call>", response.content, re.DOTALL
        )
        if matches:
            try:
                parsed_json = json.loads(matches[0])
                return parsed_json["name"], parsed_json["arguments"]
            except json.JSONDecodeError:
                pass

        return "NoFunctionCalling", "No arguments"
