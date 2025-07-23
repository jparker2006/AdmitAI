"""Legacy proxy for old tests – provides EssayPlanner, EssayPlan, Phase."""

from essay_agent.models import EssayPlanner, EssayPlan, Phase  # re-export

__all__ = [
    "EssayPlanner",
    "EssayPlan",
    "Phase",
] 