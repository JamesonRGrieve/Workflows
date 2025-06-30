import os
import requests

# Read the GitHub token from the environment
TOKEN = os.getenv("GH_TOKEN")
if not TOKEN:
    raise EnvironmentError("GH_TOKEN is not set in environment")

HEADERS = {"Authorization": f"token {TOKEN}"}

# Source repo where truth is stored
SOURCE_REPO = "JamesonRGrieve/Workflows"

# Target repos to sync to
TARGET_REPOS = [
    "JamesonRGrieve/AGInfrastructure",
    "JamesonRGrieve/AGInteractive",
    "JamesonRGrieve/AGInterface",
    "JamesonRGrieve/AGInYourPC",
    "JamesonRGrieve/AGIteration",
    "JamesonRGrieve/nursegpt",
    "JamesonRGrieve/nursegpt_web",
    "JamesonRGrieve/ServerFramework",
    "JamesonRGrieve/auth",
    "JamesonRGrieve/zod2gql",
    "JamesonRGrieve/dynamic-form",
    "JamesonRGrieve/ClientFramework"
]

def get_labels(repo):
    url = f"https://api.github.com/repos/{repo}/labels"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        print(f"✅ Fetched labels from {repo}")
        return res.json()
    else:
        print(f"❌ Failed to fetch labels from {repo}")
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text}")
        return []

def create_or_update_label(repo, label):
    url = f"https://api.github.com/repos/{repo}/labels"
    data = {
        "name": label["name"],
        "color": label["color"],
        "description": label.get("description", "")
    }
    res = requests.post(url, headers=HEADERS, json=data)
    
    if res.status_code == 201:
        print(f"✅ Created label '{label['name']}' in {repo}")
    elif res.status_code == 422 and "already_exists" in res.text:
        print(f"⚠️ Label '{label['name']}' already exists in {repo}")
    else:
        print(f"❌ Failed to create label '{label['name']}' in {repo}")
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text}")

def sync_labels():
    labels = get_labels(SOURCE_REPO)
    if not labels:
        print("⚠️ No labels found or failed to fetch. Exiting.")
        return

    for target_repo in TARGET_REPOS:
        print(f"\n🔄 Syncing labels to {target_repo}")
        for label in labels:
            create_or_update_label(target_repo, label)

if __name__ == "__main__":
    sync_labels()
