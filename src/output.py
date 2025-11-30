"""Output handlers for writing opportunities to JSON and CSV files."""

import json
import csv
from pathlib import Path
from typing import List
from datetime import datetime
from rich.console import Console

from .models import Opportunity, GitHubIssue, OpportunityAnalysis

console = Console()


class OutputWriter:
    """Handles writing opportunities to various output formats."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize output writer.
        
        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def _opportunity_to_dict(self, issue: GitHubIssue, analysis: OpportunityAnalysis) -> dict:
        """Convert issue and analysis to dictionary."""
        return {
            "repo": issue.repo,
            "repo_full_name": issue.repo_full_name,
            "issue_number": issue.issue_number,
            "title": issue.title,
            "body": issue.body,
            "url": issue.url,
            "labels": issue.labels,
            "reactions": issue.reactions,
            "comments": issue.comments,
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "state": issue.state,
            "author": issue.author,
            "ai_analysis": {
                "market_potential": analysis.market_potential,
                "technical_feasibility": analysis.technical_feasibility,
                "competition": analysis.competition,
                "monetization_fit": analysis.monetization_fit,
                "total_score": analysis.total_score,
                "opportunity_summary": analysis.opportunity_summary,
                "product_idea": analysis.product_idea,
                "skip_reason": analysis.skip_reason,
            },
            "scraped_at": datetime.now().isoformat(),
        }
    
    def write_json(
        self,
        issues: List[GitHubIssue],
        analyses: List[OpportunityAnalysis],
        filename: str = "opportunities.json",
        sort_by: str = "total_score"
    ) -> None:
        """
        Write opportunities to JSON file.
        
        Args:
            issues: List of GitHubIssue objects
            analyses: List of OpportunityAnalysis objects (must match issues)
            filename: Output filename
            sort_by: Field to sort by (default: total_score)
        """
        if len(issues) != len(analyses):
            console.print("[red]Error: Issues and analyses lists must have the same length[/red]")
            return
        
        # Create opportunities list
        opportunities = []
        for issue, analysis in zip(issues, analyses):
            opportunities.append(self._opportunity_to_dict(issue, analysis))
        
        # Sort by specified field (descending)
        if sort_by == "total_score":
            opportunities.sort(key=lambda x: x["ai_analysis"]["total_score"], reverse=True)
        elif sort_by == "market_potential":
            opportunities.sort(key=lambda x: x["ai_analysis"]["market_potential"], reverse=True)
        elif sort_by == "reactions":
            opportunities.sort(key=lambda x: x["reactions"], reverse=True)
        elif sort_by == "comments":
            opportunities.sort(key=lambda x: x["comments"], reverse=True)
        
        # Write to file
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "total_opportunities": len(opportunities),
                        "sorted_by": sort_by,
                    },
                    "opportunities": opportunities,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        
        console.print(f"[green]✓ Wrote {len(opportunities)} opportunities to {output_path}[/green]")
    
    def write_csv(
        self,
        issues: List[GitHubIssue],
        analyses: List[OpportunityAnalysis],
        filename: str = "opportunities.csv",
        sort_by: str = "total_score"
    ) -> None:
        """
        Write opportunities to CSV file.
        
        Args:
            issues: List of GitHubIssue objects
            analyses: List of OpportunityAnalysis objects (must match issues)
            filename: Output filename
            sort_by: Field to sort by (default: total_score)
        """
        if len(issues) != len(analyses):
            console.print("[red]Error: Issues and analyses lists must have the same length[/red]")
            return
        
        # Create opportunities list
        opportunities = []
        for issue, analysis in zip(issues, analyses):
            opp = self._opportunity_to_dict(issue, analysis)
            opportunities.append(opp)
        
        # Sort by specified field (descending)
        if sort_by == "total_score":
            opportunities.sort(key=lambda x: x["ai_analysis"]["total_score"], reverse=True)
        elif sort_by == "market_potential":
            opportunities.sort(key=lambda x: x["ai_analysis"]["market_potential"], reverse=True)
        elif sort_by == "reactions":
            opportunities.sort(key=lambda x: x["reactions"], reverse=True)
        elif sort_by == "comments":
            opportunities.sort(key=lambda x: x["comments"], reverse=True)
        
        # Flatten for CSV
        csv_rows = []
        for opp in opportunities:
            row = {
                "repo": opp["repo"],
                "repo_full_name": opp["repo_full_name"],
                "issue_number": opp["issue_number"],
                "title": opp["title"],
                "url": opp["url"],
                "labels": ", ".join(opp["labels"]),
                "reactions": opp["reactions"],
                "comments": opp["comments"],
                "created_at": opp["created_at"],
                "updated_at": opp["updated_at"],
                "state": opp["state"],
                "author": opp["author"],
                "market_potential": opp["ai_analysis"]["market_potential"],
                "technical_feasibility": opp["ai_analysis"]["technical_feasibility"],
                "competition": opp["ai_analysis"]["competition"],
                "monetization_fit": opp["ai_analysis"]["monetization_fit"],
                "total_score": opp["ai_analysis"]["total_score"],
                "opportunity_summary": opp["ai_analysis"]["opportunity_summary"],
                "product_idea": opp["ai_analysis"]["product_idea"] or "",
                "skip_reason": opp["ai_analysis"]["skip_reason"] or "",
                "scraped_at": opp["scraped_at"],
            }
            csv_rows.append(row)
        
        # Write to CSV
        output_path = self.output_dir / filename
        if csv_rows:
            fieldnames = csv_rows[0].keys()
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
            
            console.print(f"[green]✓ Wrote {len(csv_rows)} opportunities to {output_path}[/green]")
        else:
            console.print("[yellow]No opportunities to write to CSV[/yellow]")

