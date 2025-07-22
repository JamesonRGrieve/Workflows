#!/usr/bin/env python3
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional


def run_gh_command(args: List[str], json_input: Optional[Dict[str, Any]] = None) -> str:
    cmd = ["gh"] + args
    try:
        if json_input:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                input=json.dumps(json_input),
            )
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        sys.exit(1)


def get_milestones(repo: str) -> List[Dict[str, Any]]:
    output = run_gh_command(
        [
            "api",
            f"repos/{repo}/milestones",
            "--jq",
            ".",
            "--paginate",
            "-H",
            "Accept: application/vnd.github.v3+json",
            "--method",
            "GET",
            "-F",
            "state=all",
            "-F",
            "sort=number",
            "-F",
            "direction=asc",
        ]
    )

    milestones = []
    for line in output.strip().split("\n"):
        if line:
            milestones.extend(json.loads(line))

    return milestones


def get_milestone_issues(repo: str, milestone_number: int) -> List[Dict[str, Any]]:
    output = run_gh_command(
        [
            "api",
            f"repos/{repo}/issues",
            "--jq",
            ".[] | {number: .number, pull_request: .pull_request}",
            "--paginate",
            "-H",
            "Accept: application/vnd.github.v3+json",
            "--method",
            "GET",
            "-F",
            f"milestone={milestone_number}",
            "-F",
            "state=all",
        ]
    )

    issues = []
    for line in output.strip().split("\n"):
        if line:
            issue_data = json.loads(line)
            issues.append(
                {
                    "number": issue_data["number"],
                    "is_pr": issue_data["pull_request"] is not None,
                }
            )

    return issues


def update_milestone(
    repo: str,
    milestone_number: int,
    title: str,
    state: str,
    description: Optional[str],
    due_on: Optional[str],
) -> None:
    data = {"title": f"TEMP_{milestone_number}_{title}", "state": state}

    if description is not None:
        data["description"] = description
    else:
        data["description"] = ""

    if due_on is not None:
        data["due_on"] = due_on
    else:
        data["due_on"] = None

    run_gh_command(
        [
            "api",
            f"repos/{repo}/milestones/{milestone_number}",
            "--method",
            "PATCH",
            "--input",
            "-",
        ],
        json_input=data,
    )


def finalize_milestone_title(repo: str, milestone_number: int, title: str) -> None:
    run_gh_command(
        [
            "api",
            f"repos/{repo}/milestones/{milestone_number}",
            "--method",
            "PATCH",
            "--input",
            "-",
        ],
        json_input={"title": title},
    )


def assign_issue_to_milestone(
    repo: str, issue_number: int, milestone_number: int
) -> None:
    run_gh_command(
        [
            "api",
            f"repos/{repo}/issues/{issue_number}",
            "--method",
            "PATCH",
            "--input",
            "-",
        ],
        json_input={"milestone": milestone_number},
    )


def main():
    if len(sys.argv) != 2:
        print("Usage: python reverse_milestones.py <owner/repo>")
        sys.exit(1)

    repo = sys.argv[1]

    print(f"Fetching milestones from {repo}...")
    milestones = get_milestones(repo)

    if not milestones:
        print("No milestones found.")
        return

    if len(milestones) == 1:
        print("Only one milestone found. Nothing to reverse.")
        return

    print(f"Found {len(milestones)} milestones")

    milestone_data = []
    all_issues = {}

    for m in milestones:
        print(f"Fetching data for milestone #{m['number']}: {m['title']}")
        issues = get_milestone_issues(repo, m["number"])

        milestone_data.append(
            {
                "number": m["number"],
                "title": m["title"],
                "description": m.get("description"),
                "state": m["state"],
                "due_on": m.get("due_on"),
            }
        )

        all_issues[m["number"]] = issues

    reversed_data = milestone_data[::-1]

    print(
        "\nStep 1: Updating milestones with temporary titles and reversed properties..."
    )
    for i, original_milestone in enumerate(milestone_data):
        reversed_props = reversed_data[i]

        print(
            f"Updating milestone #{original_milestone['number']} with properties from #{reversed_props['number']}"
        )

        update_milestone(
            repo,
            original_milestone["number"],
            reversed_props["title"],
            reversed_props["state"],
            reversed_props["description"],
            reversed_props["due_on"],
        )

    print("\nStep 2: Reassigning issues to their new milestones...")
    issue_moves = []
    for i, original_milestone in enumerate(milestone_data):
        reversed_milestone_number = reversed_data[i]["number"]
        issues_to_assign = all_issues[reversed_milestone_number]

        if issues_to_assign:
            for issue in issues_to_assign:
                issue_moves.append(
                    {
                        "issue_number": issue["number"],
                        "is_pr": issue["is_pr"],
                        "from_milestone": reversed_milestone_number,
                        "to_milestone": original_milestone["number"],
                    }
                )

    moved_issues = set()
    for move in issue_moves:
        if (
            move["from_milestone"] != move["to_milestone"]
            and move["issue_number"] not in moved_issues
        ):
            print(
                f"  Moving {'PR' if move['is_pr'] else 'issue'} #{move['issue_number']} from milestone #{move['from_milestone']} to #{move['to_milestone']}"
            )
            assign_issue_to_milestone(repo, move["issue_number"], move["to_milestone"])
            moved_issues.add(move["issue_number"])

    print("\nStep 3: Finalizing milestone titles...")
    for i, original_milestone in enumerate(milestone_data):
        reversed_props = reversed_data[i]
        print(
            f"  Setting final title for milestone #{original_milestone['number']}: {reversed_props['title']}"
        )
        finalize_milestone_title(
            repo, original_milestone["number"], reversed_props["title"]
        )

    print("\nMilestone reversal complete!")
    print("\nFinal milestone order:")
    updated_milestones = get_milestones(repo)
    for m in updated_milestones:
        issue_count = len(get_milestone_issues(repo, m["number"]))
        print(f"  #{m['number']}: {m['title']} ({issue_count} items)")


if __name__ == "__main__":
    main()
