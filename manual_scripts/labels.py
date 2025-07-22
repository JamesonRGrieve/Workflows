#!/usr/bin/env python3

import argparse
import json
import os
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


def create_label(repo, name, color, description):
    args = ["label", "create", name, "--repo", repo, "--color", color, "--force"]
    if description:
        args.extend(["--description", description])

    try:
        run_gh_command(args)
        print(f"Created/Updated label: {name}")
        return True
    except SystemExit:
        print(f"Failed to create label: {name}")
        return False


def update_label(repo, name, color, description):
    args = ["label", "edit", name, "--repo", repo, "--color", color]
    if description is not None:
        args.extend(["--description", description])

    try:
        run_gh_command(args)
        print(f"Updated label: {name}")
        return True
    except SystemExit:
        print(f"Failed to update label: {name}")
        return False


def delete_label(repo, label_name):
    try:
        run_gh_command(["label", "delete", label_name, "--repo", repo, "--yes"])
        print(f"Deleted label: {label_name}")
        return True
    except SystemExit:
        print(f"Failed to delete label: {label_name}")
        return False


def load_labels_config(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        sys.exit(1)

    with open(filepath, "r") as f:
        return json.load(f)


def get_labels_for_repo(config, repo_name):
    labels_to_apply = {}

    if repo_name not in config["repositories"]:
        print(f"Error: Repository {repo_name} not found in configuration")
        sys.exit(1)

    repo_groups = []
    for group_spec in config["repositories"][repo_name]:
        groups = [g.strip() for g in group_spec.split(",")]
        repo_groups.extend(groups)

    repo_groups.append("")

    for group in repo_groups:
        if group in config["labels"]:
            for category, category_data in config["labels"][group].items():
                color = category_data["color"]
                for label_name, description in category_data["labels"].items():
                    labels_to_apply[label_name] = {
                        "color": color.replace("#", ""),
                        "description": description,
                    }

    return labels_to_apply


def sync_labels_from_json(repo, config_file, delete_unmanaged=False):
    print(f"Loading label configuration from {config_file}")
    config = load_labels_config(config_file)

    print(f"Repository: {repo}")
    labels_to_apply = get_labels_for_repo(config, repo)
    print(f"Found {len(labels_to_apply)} labels to apply based on configuration")

    print(f"\nFetching current labels from repository...")
    current_labels = get_labels(repo)
    current_label_map = {label["name"]: label for label in current_labels}
    print(f"Found {len(current_labels)} existing labels in repository")

    print(f"\nSynchronizing labels...")

    success_count = 0
    for label_name, label_data in labels_to_apply.items():
        if label_name in current_label_map:
            existing = current_label_map[label_name]
            if (
                existing["color"] != label_data["color"]
                or existing.get("description", "") != label_data["description"]
            ):
                if update_label(
                    repo, label_name, label_data["color"], label_data["description"]
                ):
                    success_count += 1
            else:
                print(f"Label already up to date: {label_name}")
                success_count += 1
        else:
            if create_label(
                repo, label_name, label_data["color"], label_data["description"]
            ):
                success_count += 1

    if delete_unmanaged:
        print(f"\nDeleting unmanaged labels...")
        for label in current_labels:
            if label["name"] not in labels_to_apply:
                delete_label(repo, label["name"])

    print(
        f"\nSynchronization complete! Applied {success_count}/{len(labels_to_apply)} labels."
    )


def list_repos(config_file):
    config = load_labels_config(config_file)
    print("Configured repositories:")
    for repo, groups in config["repositories"].items():
        print(f"  {repo}: {', '.join(groups)}")


def preview_labels(repo, config_file):
    config = load_labels_config(config_file)
    labels = get_labels_for_repo(config, repo)

    print(f"Labels that would be applied to {repo}:")
    print(f"{'Label':<25} {'Color':<8} {'Description'}")
    print("-" * 80)

    for name, data in sorted(labels.items()):
        print(f"{name:<25} #{data['color']:<7} {data['description']}")

    print(f"\nTotal: {len(labels)} labels")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config = os.path.join(script_dir, "labels.json")

    parser = argparse.ArgumentParser(
        description="Synchronize GitHub labels from JSON configuration"
    )
    parser.add_argument(
        "repository",
        nargs="?",
        help="Target repository (e.g., owner/repo). If not specified, syncs all repositories.",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=default_config,
        help=f"Path to labels.json file (default: labels.json in script directory)",
    )
    parser.add_argument(
        "--delete-unmanaged",
        "-d",
        action="store_true",
        help="Delete labels not in configuration",
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all configured repositories"
    )
    parser.add_argument(
        "--preview", "-p", action="store_true", help="Preview labels without applying"
    )

    args = parser.parse_args()

    if args.list:
        list_repos(args.config)
        return

    config = load_labels_config(args.config)

    if args.repository:
        repositories = [args.repository]
    else:
        repositories = list(config["repositories"].keys())
        print(
            f"No repository specified. Will sync all {len(repositories)} configured repositories."
        )

    if args.preview:
        for repo in repositories:
            print(f"\n{'='*80}")
            preview_labels(repo, args.config)
        return

    print(f"GitHub Label JSON Synchronizer")
    print(f"==============================")
    print(f"Config: {args.config}")

    if len(repositories) == 1:
        print(f"Target: {repositories[0]}")
    else:
        print(f"Targets: {len(repositories)} repositories")
        for repo in repositories:
            print(f"  - {repo}")

    if args.delete_unmanaged:
        print(f"\nWARNING: This will delete all labels not in the configuration!")
    else:
        print(f"\nThis will update/create labels based on the configuration.")

    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("Operation cancelled")
        sys.exit(0)

    for i, repo in enumerate(repositories):
        if len(repositories) > 1:
            print(f"\n{'='*80}")
            print(f"Processing repository {i+1}/{len(repositories)}: {repo}")
            print(f"{'='*80}")
        sync_labels_from_json(repo, args.config, args.delete_unmanaged)

    if len(repositories) > 1:
        print(f"\n{'='*80}")
        print(f"Completed synchronization for all {len(repositories)} repositories!")


if __name__ == "__main__":
    main()
