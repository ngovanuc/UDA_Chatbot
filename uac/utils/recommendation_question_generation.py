import json
from typing import Dict, List

from pydantic import BaseModel, Field
from uac.agents.base import Base
from uac.configs.config import Config
from uac.llms.llms import model_id_to_backend
from uac.prompts.recommendation_question_generation_prompt import (
    RECOMMENDATION_QUESTION_GENERATION_SYSTEM_PROMPT,
)
from uac.utils.auto_booking_realtime import BookingTimeUpdater


class RecommendationQuestion(BaseModel):
    """
    A class representing a suggested question.
    """

    recommendation_question: List[str] = Field(
        description="The five recommended questions", max_length=5
    )


class RecommendationQuestionGeneration(Base):
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
        self.booking_time_updater = BookingTimeUpdater()

    @staticmethod
    def process_history_chat(lastest_history_chat: List[Dict], history_chat: List[Dict]) -> str:
        """
        Process the history chat to extract relevant information.
        """
        if history_chat == []:
            processed_history_chat = "không có thông tin"
        else:
            history_chat = history_chat[-10:]
            processed_history_chat = [
                (
                    f"User: {item['content']}"
                    if item["role"] == "user"
                    else f"Assistant: {item['content']}"
                )
                for item in history_chat
            ]
        processed_lastest_history_chat = f"Yêu cầu của người dùng: {lastest_history_chat[0]['content']}\n\nThông tin phản hồi: {lastest_history_chat[1]['content']}"

        processed_history_chat = "\n".join(processed_history_chat)

        return f"Thông tin trong quá khứ: \n{processed_history_chat}\n\nThông tin hội thoại ở hiện tại: \n{processed_lastest_history_chat}"

    async def generate_recommendation_question(
        self, lastest_history_chat: List[Dict], history_chat: List[Dict]
    ) -> List[str]:
        """
        Contextualizes the user's query using a language model.
        """
        this_weeks, next_week = self.booking_time_updater.update_booking_time()
        this_weeks_format = "\n".join(this_weeks + next_week)

        query_input = self.process_history_chat(lastest_history_chat, history_chat)
        conversations = [
            {
                "role": "system",
                "content": RECOMMENDATION_QUESTION_GENERATION_SYSTEM_PROMPT.format(
                    booking_time=this_weeks_format
                ),
            },
            {"role": "user", "content": query_input},
        ]

        if self.model_backend in ["OLLAMA"]:
            try:
                res = await self.aclient_response(conversations, format="json")
                output_content = json.loads(res["message"]["content"])["recommendation_question"]
            except Exception:
                output_content = []
        elif self.model_backend in ["GROQ", "OPENAI", "LOCAL_AI"]:
            try:
                res = await self.aclient_response(
                    conversations, response_format=RecommendationQuestion
                )
                left_buckets_index = res.choices[0].message.content.find("{")
                right_buckets_index = res.choices[0].message.content.find("}")

                parsed_content = res.choices[0].message.content[
                    left_buckets_index : right_buckets_index + 1
                ]
                output_content = json.loads(parsed_content)["recommendation_question"]
            except Exception:
                output_content = []

        return output_content
