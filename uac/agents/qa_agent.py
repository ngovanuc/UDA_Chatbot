import asyncio
from typing import List

from uac.agents.base import Base
from uac.configs.config import Config
from uac.prompts.tool_prompt import QUESTION_ANSWERING_SYSTEM_PROMPT


class QuestionAnsweringAgent(Base):
    """
    Agent for generating content based on user input and conversation history.

    Methods:
        generate_content(self, user_input: str, conversation: List = None) -> str:
            Generates content based on user input and conversation history.
    """

    def __init__(self, config: Config):
        super().__init__(config)

    def run_agent(
        self,
        user_input: str,
        conversation: List = None,
        retrieval_context=None,
        human_preference=None,
    ) -> str:
        """
        Generates content based on user input and conversation history.

        Args:
            retrieval_context:
            user_input (str): The input message from the user.
            conversation (List, optional): The conversation history. Defaults to None.

        Returns:
            str: The generated content.
        """
        messages = self._build_messages(
            user_input,
            conversation,
            QUESTION_ANSWERING_SYSTEM_PROMPT.format(
                bot_name=self.config.bot_name, human_preference=human_preference
            ),
            retrieval_context,
        )
        content = asyncio.run(self.aclient_response(messages, max_tokens=4090, streaming=True))
        return content
