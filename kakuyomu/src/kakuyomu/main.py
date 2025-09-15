#!/usr/bin/env python
import logging

from kakuyomu.crews.story_analysis_crew.story_analysis_crew import StoryAnalysisCrew

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_story():
    """Main function to analyze a Kakuyomu story"""
    logger.info("=== Kakuyomu Story Analysis ===")

    # 近畿地方のある場所について
    kakuyomu_id = "16817330652495155185"

    # # Get URL from user
    # kakuyomu_id = input("カクヨムの作品IDを入力してください: ")

    # if not kakuyomu_id.strip():
    #     logger.error("IDが入力されていません。")
    #     return

    crew = StoryAnalysisCrew(kakuyomu_id, 3)
    result = crew.crew().kickoff()
    print(result)

    return result


def kickoff():
    """Entry point for command line execution"""
    return analyze_story()


def plot():
    """Generate crew workflow visualization"""
    print("Generating crew workflow plot...")
    crew = StoryAnalysisCrew()
    crew.crew().plot()


if __name__ == "__main__":
    kickoff()
