from typing import Any, Dict, Optional

from uac.llms.openai_client import OpenAIClient


class LocalAIClient(OpenAIClient):
    """
    LocalAIClient extends the functionality of OpenAIClient for interacting
    with a local AI model server. It inherits the configuration and connection
    settings from the parent class.

    Attributes:
        config (Dict[str, Any]): Configuration settings for the client.
        host (Optional[str]): The host URL of the AI service (defaults to None).
        api_key (Optional[str]): The API key for accessing the service (optional, defaults to None).
    """

    def __init__(
        self, config: Dict[str, Any], host: Optional[str] = None, api_key: Optional[str] = None
    ):
        """
        Initialize the LocalAIClient with configuration, host, and API key.

        Args:
            config (Dict[str, Any]): A dictionary containing configuration settings.
            host (Optional[str]): The URL of the local AI service, if applicable.
            api_key (Optional[str]): The API key for authenticating to the local AI service, if needed.
        """
        super().__init__(config, host, api_key)
