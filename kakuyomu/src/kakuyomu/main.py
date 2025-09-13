#!/usr/bin/env python
import asyncio
from typing import List, Dict, Any
import logging
import requests
import json
from bs4 import BeautifulSoup
from kakuyomu.crews.story_analysis_crew.story_analysis_crew import StoryAnalysisCrew
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- このへんはkakuyomu-mcpからコピペ -----

def kakuyomu_request(url: str, params: dict = None) -> BeautifulSoup:
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


def parse_apollo_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """__NEXT_DATA__からApollo状態データを抽出"""
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        raise ValueError("__NEXT_DATA__スクリプトタグが見つかりません")

    data = json.loads(script_tag.string)
    return data["props"]["pageProps"]["__APOLLO_STATE__"]

def get_work_episodes(work_id: str, limit: int = 20) -> str:
    """特定の作品のエピソード一覧を取得"""
    try:
        soup = kakuyomu_request(f"https://kakuyomu.jp/works/{work_id}")
        data = parse_apollo_data(soup)
        episodes = list(filter(lambda x: x.startswith("Episode:"), data.keys()))
        episodes = [e.split(":")[1] for e in episodes]
        return episodes
    except Exception as e:
        logger.error(f"Error in get_work_episodes: {str(e)}")
        raise

# ----- コピペはここまで -----

async def analyze_story():
# def analyze_story():
    """Main function to analyze a Kakuyomu story"""
    print("=== Kakuyomu Story Analysis ===")
    
    # Get URL from user
    kakuyomu_id = input("カクヨムの作品IDを入力してください: ")
    
    if not kakuyomu_id.strip():
        print("IDが入力されていません。")
        return
    
    print(f"分析開始: {kakuyomu_id}")
    
    # Execute crew analysis
    episodes = get_work_episodes(kakuyomu_id)
    episodes = episodes[:10]
    print(f"episodes: {episodes}")

    crew = StoryAnalysisCrew()
    inputs = [{"work_id": kakuyomu_id, "episode_id": e} for e in episodes]
    results = await crew.crew().kickoff_for_each_async(inputs=inputs)
    
    # Format and display results nicely
    print("\n" + "="*60)
    print("📊 文章品質チェック結果")
    print("="*60)
    
    problem_count = 0
    attention_count = 0
    ok_count = 0
    
    for i, result in enumerate(results, 1):
        if result.pydantic:
            episode_id = result.pydantic.episode_id
            judge = result.pydantic.judge
            reason = result.pydantic.reason
            
            # Count by judgment
            if judge == "問題なし":
                status_emoji = "✅"
                ok_count += 1
            elif judge == "要注意":
                status_emoji = "⚠️"
                attention_count += 1
            elif judge == "文章破綻":
                status_emoji = "❌"
                problem_count += 1
            else:
                status_emoji = "❓"
            
            print(f"\n{status_emoji} エピソード {i}")
            print(f"   ID: {episode_id}")
            print(f"   判定: {judge}")
            print(f"   理由: {reason}")
    
    # Summary
    total = len(results)
    print("\n" + "-"*60)
    print("📋 総合結果")
    print("-"*60)
    print(f"✅ 問題なし:   {ok_count:2d}/{total} ({ok_count/total*100:.1f}%)")
    print(f"⚠️  要注意:     {attention_count:2d}/{total} ({attention_count/total*100:.1f}%)")
    print(f"❌ 文章破綻:   {problem_count:2d}/{total} ({problem_count/total*100:.1f}%)")
    print("="*60)
    
    # Overall assessment
    if problem_count > 0:
        print("🚨 注意: 文章破綻が検出されました。確認が必要です。")
    elif attention_count > 0:
        print("⚠️  要注意エピソードがあります。目視確認を推奨します。")
    else:
        print("🎉 すべてのエピソードで問題は検出されませんでした。")
    
    return results


def kickoff():
    """Entry point for command line execution"""
    return asyncio.run(analyze_story())
    # return analyze_story()


def plot():
    """Generate crew workflow visualization"""
    print("Generating crew workflow plot...")
    crew = StoryAnalysisCrew()
    crew.crew().plot()


if __name__ == "__main__":
    kickoff()
