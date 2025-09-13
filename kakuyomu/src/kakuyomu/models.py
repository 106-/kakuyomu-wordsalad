from pydantic import BaseModel
from typing import List

class EpisodeVerdict(BaseModel):
    episode_id: str
    judge: str
    reason: str
