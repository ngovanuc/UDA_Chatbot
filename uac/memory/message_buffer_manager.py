import os
import re
from typing import Dict, List, Tuple

from transformers import AutoTokenizer
from uac.agents.base import Base
from uac.configs.config import Config
from uac.prompts.summarizer_prompt import SUMMARIZER_HUMAN_TEMPLATE, SUMMARIZER_SYSTEM
from uac.utils.constants import MEMORY_BUFFER_LIMIT, SUMMARIZER_CONTEXT_LIMIT


config = Config()


class MessageBufferManager(Base):
    """
    Manages a buffer of chat messages, ensuring that the token count remains within specified limits
    by summarizing and trimming older messages.
    """

    def __init__(self):
        super().__init__(config, mode="preprocess")
        self.tokenizer = AutoTokenizer.from_pretrained(
            os.environ["TOKENIZER_PATH"], TOKENIZERS_PARALLELISM=True
        )

    @staticmethod
    def escape_braces(message_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Escapes curly braces in message contents to prevent them from being interpreted as placeholders in formatted strings.

        Args:
            message_history (List[Dict[str, str]]): A list of message dictionaries.

        Returns:
            List[Dict[str, str]]: Modified list with escaped braces.
        """
        return [
            {
                "role": message["role"],
                "content": re.sub(r"\{([^}]*)\}", r"{{\1}}", message["content"]),
            }
            for message in message_history
        ]

    @staticmethod
    def _format_message_history(message_history: List[Dict[str, str]]) -> str:
        """
        Formats the message history into a single string, suitable for summarization.

        Args:
            message_history (List[Dict[str, str]]): A list of message dictionaries.

        Returns:
            str: Formatted string of the message history.
        """
        return "\n".join(
            [f"{message['role']}: {message['content']}" for message in message_history]
        )

    def count_tokens(self, conversation: List[Dict[str, str]]) -> int:
        """
        Counts the total number of tokens in the conversation list using the configured tokenizer.

        Args:
            conversation (List[Dict[str, str]]): A list of message dictionaries.

        Returns:
            int: Total token count of the conversation.
        """
        if not conversation:
            return 0
        tokenized = self.tokenizer.apply_chat_template(
            conversation, tokenize=True, add_generation_prompt=True
        )
        return len(tokenized)

    def _trim_message_history(
        self, message_history: List[Dict[str, str]], cut_off_index: int = 0
    ) -> Tuple[int, List[Dict[str, str]], int]:
        """
        Recursively trims the message history to fit within the token limit.

        Args:
            message_history (List[Dict[str, str]]): The message history list.
            cut_off_index (int): The starting index to trim from.

        Returns:
            Tuple[int, List[Dict[str, str]], int]: The cut-off index, the remaining message buffer,
            and the token count of the conversation.
        """
        buffer_length = len(message_history)
        cut_off_step = buffer_length // 2
        cut_off_index += cut_off_step
        buffer_context = message_history[cut_off_step:]
        token_count = self.count_tokens(buffer_context)
        print(len(buffer_context), token_count)
        if token_count > MEMORY_BUFFER_LIMIT:
            return self._trim_message_history(message_history, cut_off_index)

        return cut_off_index, buffer_context, token_count

    async def summarize_message_history(
        self, message_history: List[Dict[str, str]], max_token: int = None
    ) -> str:
        """
        Summarizes the message history to reduce token count.

        Args:
            message_history (List[Dict[str, str]]): The message history list.
            max_token (int, optional): Max token count for summarization.

        Returns:
            str: Summarized message history.
        """
        message_history = self.escape_braces(message_history)
        formatted_history = self._format_message_history(message_history)

        conversation = [
            {"role": "system", "content": SUMMARIZER_SYSTEM},
            {
                "role": "user",
                "content": f"{SUMMARIZER_HUMAN_TEMPLATE.format(input=formatted_history)}",
            },
        ]

        token_count = self.count_tokens(conversation)

        if token_count > SUMMARIZER_CONTEXT_LIMIT:
            cut_off_index, buffer_context, buffer_token_count = self._trim_message_history(
                message_history
            )
            summarized_part = await self.summarize_message_history(
                message_history[:cut_off_index],
                max_token=SUMMARIZER_CONTEXT_LIMIT - buffer_token_count,
            )
            formatted_history = (
                f"assistant: {summarized_part}\n{self._format_message_history(buffer_context)}"
            )

        response = await self.aclient_response(conversation, max_tokens=max_token)
        return response

    async def reset_buffer(self, message_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Resets the buffer by summarizing older messages and keeping recent ones within the token limit.

        Args:
            message_history (List[Dict[str, str]]): Full message history.

        Returns:
            List[Dict[str, str]]: Updated buffer with summarized content and recent messages.
        """
        cut_off_index, message_buffer, token_count = self._trim_message_history(message_history)

        discarded_messages = self.escape_braces(message_history[:cut_off_index])
        summarized_content = await self.summarize_message_history(
            discarded_messages, max_token=MEMORY_BUFFER_LIMIT - token_count
        )

        # Prepend summarized content to the remaining message buffer
        message_buffer.insert(0, {"role": "assistant", "content": summarized_content})
        return message_buffer
