import asyncio
import os
import uuid

import chainlit as cl
import torch
from dotenv import load_dotenv
from langchain_cohere import CohereRerank
from loguru import logger
from uac.configs.config import Config
from uac.embeddings.embeder import EmbeddingClient
from uac.human_preference.info_extraction import InfoExtraction
from uac.human_preference.info_save import store_info
from uac.human_preference.user_database import UserInfoManagement
from uac.llms.llms import model_id_to_backend
from uac.memory.message_buffer_manager import MessageBufferManager
from uac.prompts.human_preference_retrieval_prompt import (
    GOAL_EXTRACTOR_SYSTEM,
    USER_INFO_EXTRACTOR_SYSTEM,
)
from uac.router.router import EndToEndRouter
from uac.utils.constants import MEMORY_BUFFER_LIMIT
from uac.utils.recommendation_question_generation import RecommendationQuestionGeneration
from uac.utils.util import is_valid_email, is_vietnamese_phone_number


load_dotenv()

config = Config()


device = "cuda" if torch.cuda.is_available() else "cpu"
embedding_fn = EmbeddingClient(config, device=device)

info_extractor = InfoExtraction(config)
user_info_management = UserInfoManagement(config=config)

def setup_runnable():
    phone_number = cl.user_session.get("phone_number")
    user_name = cl.user_session.get("user_name")
    email = cl.user_session.get("email")

    user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, phone_number))
    cl.user_session.set("user_id", user_id)

    user_info = user_info_management.find_one(
        query={"phone_number": phone_number}, output_field=None
    )

    if user_info is None:
        user_info_management.insert_one(
            {
                "phone_number": phone_number,
                "user_id": user_id,
                "user_name": user_name,
                "email": email,
            }
        )
    elif user_info["user_name"] != user_name and user_info["email"] != email:
        user_info_management.update_one(
            query={"phone_number": phone_number},
            update_data={"user_name": user_name, "email": email},
        )
    elif user_info["email"] != email:
        user_info_management.update_one(
            query={"phone_number": phone_number},
            update_data={"email": email},
        )
    elif user_info["user_name"] != user_name:
        user_info_management.update_one(
            query={"phone_number": phone_number},
            update_data={"user_name": user_name},
        )
    else:
        logger.info(
            f"User info already exists: Name: {user_name}, Phone number: {phone_number}, Email: {email}, No need to update database."
        )

    logger.success(
        f"Login account: Name: {user_name}, Phone number: {phone_number}, Email: {email}"
    )

    runnable = EndToEndRouter(
        config=config, embedding_fn=embedding_fn, rerank_model=None, user_id=user_id
    )
    cl.user_session.set("runnable", runnable)


# Khởi tạo phiên chat với yêu cầu nhập số điện thoại
@cl.on_chat_start
async def on_chat_start():
    res = cl.Message(
        content="Xin chào! Mình là UDAchat, Chatbot hỗ trợ tư vấn tuyển sinh của Trường Đại học Đông Á.\n\nĐể thuận tiện cho việc tư vấn, bạn vui lòng nhập tên, số điện thoại và email của bạn để bắt đầu cuộc trò chuyện nhé."
    )
    await res.send()

    # Đặt cờ chờ số điện thoại
    cl.user_session.set("awaiting_info", True)
    cl.user_session.set("memory", list())
    cl.user_session.set("summary_memory", list())
    cl.user_session.set("thread", {"id": cl.user_session.get("id")})


# Xử lý từng tin nhắn
@cl.on_message
async def on_message(message: cl.Message):
    memory = cl.user_session.get("memory", -1)
    summary_memory = cl.user_session.get("summary_memory", -1)
    runnable: EndToEndRouter = cl.user_session.get("runnable")
    awaiting_phone_number = cl.user_session.get("awaiting_info", False)
    # Kiểm tra nếu đang chờ người dùng nhập số điện thoại
    if awaiting_phone_number:
        info = await info_extractor.analyze_the_response(
            USER_INFO_EXTRACTOR_SYSTEM, message.content
        )
        print(info)
        if (
            info.get("phone_number", "") == ""
            and info.get("user_name", "") == ""
            and info.get("email", "") == ""
        ):
            res = cl.Message(
                content="Xin chào! Mình là UDAchat, Chatbot hỗ trợ tư vấn tuyển sinh của Trường Đại học Đông Á.\n\nĐể thuận tiện cho việc tư vấn, bạn vui lòng nhập tên, số điện thoại và email của bạn để bắt đầu cuộc trò chuyện nhé."
            )
            await res.send()
            return
        else:
            for k, v in info.items():
                if v == "" and cl.user_session.get(f"{k}", "") == "":
                    if k == "phone_number":
                        res = cl.Message(
                            content="Số điện thoại không có hoặc không hợp lệ. Bạn hãy kiểm tra lại số điện thoại nhé."
                        )
                        await res.send()
                        return
                    elif k == "email" and cl.user_session.get("email", "") == "":
                        res = cl.Message(
                            content="Email không có hoặc không hợp lệ. Bạn hãy kiểm tra lại địa chỉ email nhé."
                        )
                        await res.send()
                        return
                    elif k == "user_name" and cl.user_session.get("user_name", "") == "":
                        res = cl.Message(
                            content="Không tìm thấy tên người dùng. Bạn hãy kiểm tra lại nhé. Điều này giúp mình tiện xưng hô ạ."
                        )
                        await res.send()
                        return
                else:
                    if k == "phone_number" and cl.user_session.get("phone_number", "") == "":
                        if is_vietnamese_phone_number(v):
                            cl.user_session.set("phone_number", v)
                            logger.info(f"Phone number: {v}")
                        else:
                            res = cl.Message(content="Số điện thoại không hợp lệ")
                            await res.send()
                            return
                    elif k == "email" and cl.user_session.get("email", "") == "":
                        if is_valid_email(v):
                            cl.user_session.set("email", v)
                            logger.info(f"Email: {v}")
                        else:
                            res = cl.Message(content="Email không hợp lệ")
                            await res.send()
                            return
                    elif k == "user_name" and cl.user_session.get("user_name", "") == "":
                        if v != "":
                            cl.user_session.set("user_name", v)
                            logger.info(f"User name: {v}")
                        else:
                            res = cl.Message(content="Tên không hợp lệ")
                            await res.send()
                            return

            if (
                cl.user_session.get("phone_number", "") != ""
                and cl.user_session.get("email", "") != ""
                and cl.user_session.get("user_name", "") != ""
            ):
                cl.user_session.set("awaiting_info", False)
                res = cl.Message(
                    content="Cảm ơn bạn đã cung cấp thông tin. Bây giờ bạn có thể đặt câu hỏi để mình tư vấn cho bạn nhé."
                )
                await res.send()
                setup_runnable()
                return

    else:
        res = cl.Message(content="", type="system_message")
        wait_message = "Đang xử lý ..."
        await res.stream_token(wait_message)

        if memory == -1:
            memory = list()
        if summary_memory == -1:
            summary_memory = list()

        # full_message_history = memory.copy()  # Sao lưu lại lịch sử tin nhắn
        queue_manager = MessageBufferManager()

        # Kiểm tra và làm mới bộ nhớ nếu vượt quá giới hạn
        if len(memory) > (len(cl.chat_context.to_openai()) - 1):
            memory = cl.chat_context.to_openai()[:-1]
            summary_memory = cl.chat_context.to_openai()[:-1]

        if queue_manager.count_tokens(summary_memory) > MEMORY_BUFFER_LIMIT:
            summary_memory = await queue_manager.reset_buffer(summary_memory)


        response = await runnable.run(message.content, summary_memory)

        await res.remove()
        res = cl.Message(content="")

        model_backend = model_id_to_backend(config.generate_model_name)

        if isinstance(response, str):
            await res.send()
        else:
            if model_backend in ["OLLAMA"]:
                async for part in response:
                    if token := part["message"]["content"]:
                        await res.stream_token(token)

            elif model_backend in ["OPENAI", "GROQ", "LOCAL_AI"]:
                async for part in response:
                    if token := part.choices[0].delta.content or "":
                        await res.stream_token(token)

        await res.send()

        memory.extend(
            [
                {"role": "user", "content": message.content},
                {"role": "assistant", "content": res.content},
            ]
        )

        summary_memory.extend(memory[-2:])  # Chỉ thêm 2 tin nhắn cuối cùng

        cl.user_session.set("memory", memory)
        cl.user_session.set("summary_memory", summary_memory)
