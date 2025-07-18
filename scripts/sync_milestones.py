import os
from github import Github

TOKEN = os.getenv("GH_TOKEN")
g = Github(TOKEN)

SOURCE_REPO = g.get_repo("JamesonRGrieve/Workflows")
TARGET_REPOS = [
    "AGInfrastructure", "AGInteractive", "AGInterface", "AGInYourPC", "AGIteration",
    "nursegpt", "nursegpt_web", "ServerFramework", "auth", "zod2gql", "dynamic-form", "ClientFramework"
]
ORG = "JamesonRGrieve"

source_milestones = SOURCE_REPO.get_milestones()

for repo_name in TARGET_REPOS:
    target_repo = g.get_repo(f"{ORG}/{repo_name}")
    target_milestones = {m.title: m for m in target_repo.get_milestones(state="all")}

    for m in source_milestones:
        if m.title not in target_milestones:
            print(f"Creating milestone {m.title} in {repo_name}")
            target_repo.create_milestone(
                title=m.title,
                state=m.state,
                description=m.description,
                due_on=m.due_on
            )
