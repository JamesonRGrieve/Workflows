#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys


def run_gh_command(args, input_data=None):
    result = subprocess.run(
        ["gh"] + args, capture_output=True, text=True, input=input_data
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout


def get_labels(repo):
    output = run_gh_command(
        [
            "label",
            "list",
            "--repo",
            repo,
            "--json",
            "name,color,description",
            "--limit",
            "1000",
        ]
    )
    return json.loads(output)


def get_milestones(repo):
    output = run_gh_command(
        [
            "api",
            f"/repos/{repo}/milestones",
            "--method",
            "GET",
            "--field",
            "state=all",
            "--field",
            "per_page=100",
        ]
    )
    milestones = json.loads(output)

    # Sort by number to ensure consistent ordering
    milestones.sort(key=lambda m: m["number"])

    return milestones


def update_label(repo, name, color, description):
    args = ["label", "edit", name, "--repo", repo, "--color", color]
    if description is not None:
        args.extend(["--description", description])

    try:
        run_gh_command(args)
        print(f"Updated label: {name}")
    except SystemExit:
        print(f"Failed to update label: {name}")


def create_label(repo, name, color, description):
    args = ["label", "create", name, "--repo", repo, "--color", color, "--force"]
    if description:
        args.extend(["--description", description])

    try:
        run_gh_command(args)
        print(f"Created label: {name}")
    except SystemExit:
        print(f"Failed to create label: {name}")


def delete_label(repo, label_name):
    try:
        run_gh_command(["label", "delete", label_name, "--repo", repo, "--yes"])
        print(f"Deleted label: {label_name}")
    except SystemExit:
        print(f"Failed to delete label: {label_name}")


def create_milestone(repo, number, title, description, due_on):
    data = {"title": title, "description": description or ""}

    if due_on:
        data["due_on"] = due_on

    try:
        run_gh_command(
            ["api", f"/repos/{repo}/milestones", "--method", "POST", "--input", "-"],
            input_data=json.dumps(data),
        )
        print(f"Created milestone #{number}: {title}")
    except SystemExit:
        print(f"Failed to create milestone #{number}: {title}")


def update_milestone(repo, milestone_number, title, description, due_on):
    data = {"title": title, "description": description or ""}

    if due_on:
        data["due_on"] = due_on

    try:
        run_gh_command(
            [
                "api",
                f"/repos/{repo}/milestones/{milestone_number}",
                "--method",
                "PATCH",
                "--input",
                "-",
            ],
            input_data=json.dumps(data),
        )
        print(f"Updated milestone #{milestone_number}: {title}")
    except SystemExit:
        print(f"Failed to update milestone #{milestone_number}: {title}")


def sync_labels(source_repo, target_repo):
    print(f"Fetching labels from source repository: {source_repo}")
    source_labels = get_labels(source_repo)
    print(f"Found {len(source_labels)} labels in source repository")

    print(f"\nFetching labels from target repository: {target_repo}")
    target_labels = get_labels(target_repo)
    target_label_map = {label["name"]: label for label in target_labels}
    print(f"Found {len(target_labels)} labels in target repository")

    print(f"\nSynchronizing labels...")

    source_label_names = {label["name"] for label in source_labels}
    for label in target_labels:
        if label["name"] not in source_label_names:
            delete_label(target_repo, label["name"])

    for label in source_labels:
        if label["name"] in target_label_map:
            existing_label = target_label_map[label["name"]]
            if existing_label["color"] != label["color"] or existing_label.get(
                "description", ""
            ) != label.get("description", ""):
                update_label(
                    target_repo,
                    label["name"],
                    label["color"],
                    label.get("description", ""),
                )
            else:
                print(f"Label already up to date: {label['name']}")
        else:
            create_label(
                target_repo, label["name"], label["color"], label.get("description", "")
            )


def sync_milestones(source_repo, target_repo, ceiling=None):
    print(f"\nFetching milestones from source repository: {source_repo}")
    source_milestones = get_milestones(source_repo)
    print(f"Found {len(source_milestones)} milestones in source repository")

    print(f"\nFetching milestones from target repository: {target_repo}")
    target_milestones = get_milestones(target_repo)
    print(f"Found {len(target_milestones)} milestones in target repository")

    if ceiling:
        print(f"\nSynchronizing milestones up to #{ceiling}...")
    else:
        print(f"\nSynchronizing all milestones...")

    target_milestones_by_number = {m["number"]: m for m in target_milestones}

    for source_milestone in source_milestones:
        number = source_milestone["number"]

        if ceiling and number > ceiling:
            print(f"Skipping milestone #{number} (above ceiling)")
            continue

        title = source_milestone["title"]
        description = source_milestone.get("description", "")
        due_on = source_milestone.get("due_on")

        if number in target_milestones_by_number:
            target_milestone = target_milestones_by_number[number]

            if (
                target_milestone["title"] != title
                or target_milestone.get("description", "") != description
                or target_milestone.get("due_on") != due_on
            ):
                update_milestone(target_repo, number, title, description, due_on)
            else:
                print(f"Milestone #{number} already up to date: {title}")
        else:
            create_milestone(target_repo, number, title, description, due_on)


def sync_all(source_repo, target_repo, milestone_ceiling=None):
    print(f"GitHub Repository Synchronizer")
    print(f"==============================")
    print(f"Source: {source_repo}")
    print(f"Target: {target_repo}")
    if milestone_ceiling:
        print(
            f"\nThis will synchronize labels and milestones (up to #{milestone_ceiling}) from {source_repo} to {target_repo}"
        )
    else:
        print(
            f"\nThis will synchronize labels and milestones from {source_repo} to {target_repo}"
        )

    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("Operation cancelled")
        sys.exit(0)

    sync_labels(source_repo, target_repo)
    sync_milestones(source_repo, target_repo, milestone_ceiling)

    print(f"\nSynchronization complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Synchronize GitHub labels and milestones between repositories"
    )
    parser.add_argument("source", help="Source repository (e.g., owner/repo)")
    parser.add_argument("target", help="Target repository (e.g., owner/repo)")
    parser.add_argument("--labels-only", action="store_true", help="Only sync labels")
    parser.add_argument(
        "--milestones-only", action="store_true", help="Only sync milestones"
    )
    parser.add_argument(
        "--milestone-ceiling",
        type=int,
        help="Only sync milestones up to and including this number",
    )

    args = parser.parse_args()

    if args.labels_only and args.milestones_only:
        print("Error: Cannot specify both --labels-only and --milestones-only")
        sys.exit(1)

    if args.labels_only:
        print(f"GitHub Label Synchronizer")
        print(f"========================")
        print(f"Source: {args.source}")
        print(f"Target: {args.target}")
        print(f"\nThis will synchronize labels from {args.source} to {args.target}")

        response = input("\nDo you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Operation cancelled")
            sys.exit(0)

        sync_labels(args.source, args.target)
        print(f"\nLabel synchronization complete!")
    elif args.milestones_only:
        print(f"GitHub Milestone Synchronizer")
        print(f"============================")
        print(f"Source: {args.source}")
        print(f"Target: {args.target}")
        if args.milestone_ceiling:
            print(
                f"\nThis will synchronize milestones (up to #{args.milestone_ceiling}) from {args.source} to {args.target}"
            )
        else:
            print(
                f"\nThis will synchronize milestones from {args.source} to {args.target}"
            )

        response = input("\nDo you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Operation cancelled")
            sys.exit(0)

        sync_milestones(args.source, args.target, args.milestone_ceiling)
        print(f"\nMilestone synchronization complete!")
    else:
        sync_all(args.source, args.target, args.milestone_ceiling)


if __name__ == "__main__":
    main()
