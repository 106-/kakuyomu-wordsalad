from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from mcp import StdioServerParameters

# Import Pydantic models for structured outputs
from kakuyomu.models import EpisodeVerdict


@CrewBase
class StoryAnalysisCrew:
    """Story Analysis Crew for Kakuyomu novels"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # MCP server configuration for Kakuyomu
    mcp_server_params = StdioServerParameters(
        command="docker",
        args=["run", "-i", "--rm", "ubiq/kakuyomu-mcp:latest"]
    )
    # mcp_server_params = [
    #     {
    #         "url": "http://localhost:9468/mcp",
    #         "transport": "streamable-http"
    #     }
    # ]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def word_salad_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["word_salad_reviewer"],
            tools=self.get_mcp_tools("get_episode_content"),  # All agents can access Kakuyomu MCP tools
        )

    @task
    def evaluating_word_salad(self) -> Task:
        return Task(
            config=self.tasks_config["evaluating_word_salad"],
            output_pydantic=EpisodeVerdict,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Story Analysis Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )