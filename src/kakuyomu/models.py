# models.py (Pydantic v2, Pylance 互換)

from datetime import datetime
from typing import Annotated, List, Literal

from pydantic import BaseModel, ConfigDict, Field

# 型エイリアス（Pylance が誤検出しにくい Annotated で制約表現）
Score0to5 = Annotated[int, Field(ge=0, le=5, description="0〜5 の整数")]
EvidenceSpan = Annotated[
    str, Field(max_length=50, description="原文抜粋（最大50文字）")
]
Reasons = Annotated[List[str], Field(min_items=1, description="理由の配列（最低1件）")]
EvidenceList = Annotated[
    List["EvidenceItem"], Field(max_items=3, description="証拠（最大3件）")
]
Confidence = Annotated[float, Field(ge=0.0, le=1.0, description="判定の信頼度（0–1）")]


class Metrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    global_incoherence: Score0to5 = Field(description="全体的無意味性")
    unreadable_expressions: Score0to5 = Field(description="理解不能表現の多さ")
    unnatural_flow: Score0to5 = Field(description="文章の流れの不自然さ")


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    span: EvidenceSpan
    explanation: str = Field(description="問題点の簡潔な説明")


class EpisodeVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    work_id: str
    episode_id: str
    verdict: Literal["問題なし", "要注意", "文章破綻"]
    reasons: Reasons
    metrics: Metrics
    evidence: EvidenceList = Field(default_factory=list)
    evaluated_at: datetime = Field(description="評価日時（ISO 8601）")
    confidence: Confidence
