import os
import shutil
from github import Github

TOKEN = os.getenv("GH_TOKEN")
g = Github(TOKEN)

SOURCE_REPO = g.get_repo("JamesonRGrieve/Workflows")
TARGET_REPOS = [
    "AGInfrastructure", "AGInteractive", "AGInterface", "AGInYourPC", "AGIteration",
    "nursegpt", "nursegpt_web", "ServerFramework", "auth", "zod2gql", "dynamic-form", "ClientFramework"
]
ORG = "JamesonRGrieve"

TEMPLATE_DIRS = [".github/ISSUE_TEMPLATE", ".github/PULL_REQUEST_TEMPLATE"]

for repo_name in TARGET_REPOS:
    target_repo = g.get_repo(f"{ORG}/{repo_name}")
    contents = target_repo.get_contents(".github")
    existing_files = [c.path for c in contents]
    
    for dir_name in TEMPLATE_DIRS:
        try:
            source_files = SOURCE_REPO.get_contents(dir_name)
            for file in source_files:
                print(f"\n📁 Syncing {file.path} to {repo_name}")
                content = file.decoded_content.decode("utf-8")
                target_repo.create_file(
                    path=file.path,
                    message=f"sync: update template {file.name}",
                    content=content,
                    branch="main"
                )
        except Exception as e:
            print(f"⚠️ Skipping {dir_name} for {repo_name}: {e}")
