from uac.configs.config import Config
from uac.human_preference.info_extraction import InfoExtraction
from uac.human_preference.user_database import UserInfoManagement


config = Config()


async def store_info(
    system_prompt: str, content: str, user_id: str, user_database: UserInfoManagement
) -> None:
    """
    Stores and updates the frequency of math concepts extracted from the given content for a specific user.

    Args:
        content (str): The input content to analyze.
        user_id (str): The unique identifier for the user.
        filename (str, optional): The name of the file to store the data. Defaults to 'retrieved_math_concepts.pkl'.

    Returns:
        None
    """
    retriever = InfoExtraction(config)
    user_info = user_database.find_one(query={"user_id": user_id}, output_field=None)

    response = await retriever.analyze_the_response(system_prompt, content)
    if "goal" in response:
        if response["goal"] == "":
            return None
        else:
            if "goal" in user_info:
                user_info["goal"].append(response["goal"])
            else:
                user_info["goal"] = [response["goal"]]

            user_database.update_one(
                query={"user_id": user_id},
                update_data={"goal": user_info["goal"]},
            )
    else:
        return None
