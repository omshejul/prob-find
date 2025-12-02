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
        Write opportunities to JSON file (appends to existing file if present).
        
        Args:
            issues: List of GitHubIssue objects
            analyses: List of OpportunityAnalysis objects (must match issues)
            filename: Output filename
            sort_by: Field to sort by (default: total_score)
        """
        if len(issues) != len(analyses):
            console.print("[red]Error: Issues and analyses lists must have the same length[/red]")
            return
        
        output_path = self.output_dir / filename
        
        # Load existing opportunities if file exists
        existing_opportunities = []
        if output_path.exists():
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    existing_opportunities = existing_data.get("opportunities", [])
                    console.print(f"[yellow]Found {len(existing_opportunities)} existing opportunities[/yellow]")
            except (json.JSONDecodeError, KeyError) as e:
                console.print(f"[yellow]Warning: Could not load existing file, starting fresh: {e}[/yellow]")
        
        # Create new opportunities list
        new_opportunities = []
        for issue, analysis in zip(issues, analyses):
            new_opportunities.append(self._opportunity_to_dict(issue, analysis))
        
        # Merge: Create a map of existing opportunities by unique key (repo_full_name + issue_number)
        opportunity_map = {}
        for opp in existing_opportunities:
            key = f"{opp['repo_full_name']}#{opp['issue_number']}"
            opportunity_map[key] = opp
        
        # Add/update with new opportunities (newer data overwrites older)
        new_count = 0
        updated_count = 0
        for opp in new_opportunities:
            key = f"{opp['repo_full_name']}#{opp['issue_number']}"
            if key in opportunity_map:
                updated_count += 1
            else:
                new_count += 1
            opportunity_map[key] = opp  # Update or add
        
        # Convert map back to list
        all_opportunities = list(opportunity_map.values())
        
        # Sort by specified field (descending)
        if sort_by == "total_score":
            all_opportunities.sort(key=lambda x: x["ai_analysis"]["total_score"], reverse=True)
        elif sort_by == "market_potential":
            all_opportunities.sort(key=lambda x: x["ai_analysis"]["market_potential"], reverse=True)
        elif sort_by == "reactions":
            all_opportunities.sort(key=lambda x: x["reactions"], reverse=True)
        elif sort_by == "comments":
            all_opportunities.sort(key=lambda x: x["comments"], reverse=True)
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "total_opportunities": len(all_opportunities),
                        "sorted_by": sort_by,
                    },
                    "opportunities": all_opportunities,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        
        console.print(f"[green]✓ Wrote {len(all_opportunities)} total opportunities to {output_path}[/green]")
        console.print(f"[green]  → {new_count} new, {updated_count} updated[/green]")
    
    def write_csv(
        self,
        issues: List[GitHubIssue],
        analyses: List[OpportunityAnalysis],
        filename: str = "opportunities.csv",
        sort_by: str = "total_score"
    ) -> None:
        """
        Write opportunities to CSV file (appends to existing file if present).
        
        Args:
            issues: List of GitHubIssue objects
            analyses: List of OpportunityAnalysis objects (must match issues)
            filename: Output filename
            sort_by: Field to sort by (default: total_score)
        """
        if len(issues) != len(analyses):
            console.print("[red]Error: Issues and analyses lists must have the same length[/red]")
            return
        
        output_path = self.output_dir / filename
        
        # Load existing opportunities if file exists
        existing_opportunities = []
        if output_path.exists():
            try:
                with open(output_path, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Convert back to opportunity dict structure
                        opp = {
                            "repo": row["repo"],
                            "repo_full_name": row["repo_full_name"],
                            "issue_number": int(row["issue_number"]),
                            "title": row["title"],
                            "url": row["url"],
                            "labels": row["labels"].split(", ") if row["labels"] else [],
                            "reactions": int(row["reactions"]),
                            "comments": int(row["comments"]),
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                            "state": row["state"],
                            "author": row["author"],
                            "ai_analysis": {
                                "market_potential": int(row["market_potential"]),
                                "technical_feasibility": int(row["technical_feasibility"]),
                                "competition": int(row["competition"]),
                                "monetization_fit": int(row["monetization_fit"]),
                                "total_score": int(row["total_score"]),
                                "opportunity_summary": row["opportunity_summary"],
                                "product_idea": row["product_idea"] or None,
                                "skip_reason": row["skip_reason"] or None,
                            },
                            "scraped_at": row["scraped_at"],
                        }
                        existing_opportunities.append(opp)
                    console.print(f"[yellow]Found {len(existing_opportunities)} existing opportunities[/yellow]")
            except (csv.Error, KeyError, ValueError) as e:
                console.print(f"[yellow]Warning: Could not load existing CSV, starting fresh: {e}[/yellow]")
        
        # Create new opportunities list
        new_opportunities = []
        for issue, analysis in zip(issues, analyses):
            opp = self._opportunity_to_dict(issue, analysis)
            new_opportunities.append(opp)
        
        # Merge: Create a map of existing opportunities by unique key
        opportunity_map = {}
        for opp in existing_opportunities:
            key = f"{opp['repo_full_name']}#{opp['issue_number']}"
            opportunity_map[key] = opp
        
        # Add/update with new opportunities
        new_count = 0
        updated_count = 0
        for opp in new_opportunities:
            key = f"{opp['repo_full_name']}#{opp['issue_number']}"
            if key in opportunity_map:
                updated_count += 1
            else:
                new_count += 1
            opportunity_map[key] = opp
        
        # Convert map back to list
        all_opportunities = list(opportunity_map.values())
        
        # Sort by specified field (descending)
        if sort_by == "total_score":
            all_opportunities.sort(key=lambda x: x["ai_analysis"]["total_score"], reverse=True)
        elif sort_by == "market_potential":
            all_opportunities.sort(key=lambda x: x["ai_analysis"]["market_potential"], reverse=True)
        elif sort_by == "reactions":
            all_opportunities.sort(key=lambda x: x["reactions"], reverse=True)
        elif sort_by == "comments":
            all_opportunities.sort(key=lambda x: x["comments"], reverse=True)
        
        # Flatten for CSV
        csv_rows = []
        for opp in all_opportunities:
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
        if csv_rows:
            fieldnames = csv_rows[0].keys()
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
            
            console.print(f"[green]✓ Wrote {len(csv_rows)} total opportunities to {output_path}[/green]")
            console.print(f"[green]  → {new_count} new, {updated_count} updated[/green]")
        else:
            console.print("[yellow]No opportunities to write to CSV[/yellow]")

