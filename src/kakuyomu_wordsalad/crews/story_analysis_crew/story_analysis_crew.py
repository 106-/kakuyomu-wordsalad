import json
import logging
from copy import deepcopy
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

# Import Pydantic models for structured outputs
from kakuyomu_wordsalad.models import EpisodeVerdict
from mcp import StdioServerParameters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@CrewBase
class StoryAnalysisCrew:
    """Story Analysis Crew for Kakuyomu novels"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # MCP server configuration for Kakuyomu
    mcp_server_params = StdioServerParameters(
        command="docker", args=["run", "-i", "--rm", "ubiq/kakuyomu-mcp:latest"]
    )

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, work_id: str, episodes_num: int = 10):
        self.work_id = work_id
        self.episodes_num = episodes_num

        episodes = self._get_work_episodes(work_id)
        self.episodes = episodes[:episodes_num]
        logger.info(f"episodes: {self.episodes}")

    @agent
    def word_salad_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["word_salad_reviewer"],
            tools=self.get_mcp_tools("get_episode_content"),
        )

    @agent
    def word_salad_aggregator(self) -> Agent:
        return Agent(
            config=self.agents_config["word_salad_aggregator"],
        )

    @task
    def aggregate_word_salad(self) -> Task:
        return Task(config=self.tasks_config["aggregate_word_salad"])

    @crew
    def crew(self) -> Crew:
        episode_tasks = self._build_episode_tasks()
        aggregate = self.aggregate_word_salad()
        return Crew(
            agents=[self.word_salad_reviewer(), self.word_salad_aggregator()],
            tasks=episode_tasks + [aggregate],
            process=Process.sequential,
            verbose=True,
        )

    # 各話ごとの評価タスクを生成する
    def _build_episode_tasks(self) -> list[Task]:
        base = deepcopy(self.tasks_config["evaluating_word_salad"])
        tasks: list[Task] = []
        for ep in self.episodes:
            desc = base["description"].format(work_id=self.work_id, episode_id=ep)
            # agentは実体を渡す（configの 'agent' キーは無視）
            t = Task(
                description=desc,
                expected_output=base.get("expected_output", "EpisodeVerdict JSON"),
                agent=self.word_salad_reviewer(),
                output_pydantic=EpisodeVerdict,
            )
            tasks.append(t)
        return tasks

    # ----- このへんはkakuyomu-mcpからコピペ -----
    def _kakuyomu_request(self, url: str, params: dict = None) -> BeautifulSoup:
        """カクヨムのページを取得してBeautifulSoupオブジェクトを返す"""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            )
        }
        res = requests.get(url, params=params, headers=headers)
        res.raise_for_status()
        return BeautifulSoup(res.text, "html.parser")

    def _parse_apollo_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """__NEXT_DATA__からApollo状態データを抽出"""
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            raise ValueError("__NEXT_DATA__スクリプトタグが見つかりません")

        data = json.loads(script_tag.string)
        return data["props"]["pageProps"]["__APOLLO_STATE__"]

    def _get_work_episodes(self, work_id: str, limit: int = 20) -> str:
        """特定の作品のエピソード一覧を取得"""
        try:
            soup = self._kakuyomu_request(f"https://kakuyomu.jp/works/{work_id}")
            data = self._parse_apollo_data(soup)
            episodes = list(filter(lambda x: x.startswith("Episode:"), data.keys()))
            episodes = [e.split(":")[1] for e in episodes]
            return episodes
        except Exception as e:
            logger.error(f"Error in get_work_episodes: {str(e)}")
            raise

    # ----- コピペはここまで -----
