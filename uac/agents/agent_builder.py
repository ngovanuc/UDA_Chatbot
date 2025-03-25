from uac.agents.out_of_domain_agent import OutOfDomainAgent
from uac.agents.manager_agent import ManagerAgent
from uac.agents.qa_agent import QuestionAnsweringAgent
from uac.configs.config import Config


class AgentBuilder:
    """
    Class to build and manage tutor agents.

    Args:
        config (Config): Configuration object.

    Attributes:
        agents (dict): Dictionary of initialized agents.
    """

    def __init__(self, config: Config):
        """
        Initialize the AgentBuilder.

        Args:
            config (Config): Configuration object for the agents.
        """
        self.config = config
        self.agents = self._build_agents()

    def _build_agents(self):
        """
        Build and return all tutor agents.

        Returns:
            dict: Dictionary of initialized agents.
        """
        agents = {
            "ManagerAgent": ManagerAgent(self.config),
            "QuestionAnswering": QuestionAnsweringAgent(self.config),
            "OutOfDomain": OutOfDomainAgent(self.config)
        }
        return agents

    def get_agent(self, agent_name: str):
        """
        Get a specific agent by name.

        Args:
            agent_name (str): The name of the agent to retrieve.

        Returns:
            object: The requested agent object.
        """
        return self.agents[agent_name]
