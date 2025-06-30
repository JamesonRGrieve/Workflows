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

PROTECTED_BRANCHES = ["main", "dev", "legacy"]

rules = {
    "enforce_admins": True,
    "required_status_checks": None,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": True,
        "required_approving_review_count": 1,
    },
    "restrictions": None,
    "allow_force_pushes": False,
    "allow_deletions": False,
    "required_linear_history": True,
    "required_conversation_resolution": True
}

for repo_name in TARGET_REPOS:
    repo = g.get_repo(f"{ORG}/{repo_name}")
    for branch in PROTECTED_BRANCHES:
        try:
            print(f"🔐 Protecting {branch} in {repo_name}")
            b = repo.get_branch(branch)
            b.edit_protection(**rules)
        except Exception as e:
            print(f"⚠️ Error protecting {branch} in {repo_name}: {e}")
