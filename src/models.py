"""Pydantic models for GitHub issues and opportunity analysis."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GitHubIssue(BaseModel):
    """Model representing a GitHub issue."""
    
    repo: str
    repo_full_name: str
    issue_number: int
    title: str
    body: str
    url: str
    labels: List[str]
    reactions: int = 0
    comments: int = 0
    created_at: datetime
    updated_at: datetime
    state: str = "open"
    author: str = ""


class OpportunityAnalysis(BaseModel):
    """AI analysis of a GitHub issue as a business opportunity."""
    
    market_potential: int = Field(ge=1, le=10, description="Market potential score (1-10)")
    technical_feasibility: int = Field(ge=1, le=10, description="Technical feasibility score (1-10)")
    competition: int = Field(ge=1, le=10, description="Competition score (1-10, 10 = no competition)")
    monetization_fit: int = Field(ge=1, le=10, description="Monetization fit score (1-10)")
    total_score: int = Field(description="Sum of all scores")
    opportunity_summary: str = Field(description="2-3 sentence analysis")
    product_idea: Optional[str] = Field(default=None, description="Suggested product if score >= 25")
    skip_reason: Optional[str] = Field(default=None, description="Why this isn't an opportunity if score < 15")
    
    def model_post_init(self, __context) -> None:
        """Calculate total_score after initialization."""
        if not hasattr(self, '_total_score_calculated'):
            self.total_score = (
                self.market_potential +
                self.technical_feasibility +
                self.competition +
                self.monetization_fit
            )
            self._total_score_calculated = True


class Opportunity(BaseModel):
    """Complete opportunity record combining issue and analysis."""
    
    issue: GitHubIssue
    analysis: OpportunityAnalysis
    scraped_at: datetime = Field(default_factory=datetime.now)

