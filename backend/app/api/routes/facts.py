"""GET /api/facts -- returns one random GitHub fact.

Deliberately has no dependency on Groq or GitHub; it's pure local config, so
it never fails for reasons a user needs to see an error code for.
"""

import random

from fastapi import APIRouter

from app.config.facts import GITHUB_FACTS
from app.models.search_models import FactResponseModel

router = APIRouter()


@router.get("/api/facts", response_model=FactResponseModel)
async def get_fact() -> FactResponseModel:
    return FactResponseModel(fact=random.choice(GITHUB_FACTS))
