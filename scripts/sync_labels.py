import requests
import os

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"}

SOURCE_REPO = "JamesonRGrieve/Workflows"
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
        return res.json()
    print(f"❌ Failed to fetch labels from {repo}")
    return []

def create_or_update_label(repo, label):
    url = f"https://api.github.com/repos/{repo}/labels"
    res = requests.post(url, headers=HEADERS, json={
        "name": label["name"],
        "color": label["color"],
        "description": label.get("description", "")
    })
    if res.status_code == 422 and "already_exists" in str(res.text):
        print(f"Label '{label['name']}' already exists in {repo}")
    elif res.status_code != 201:
        print(f"Failed to create label '{label['name']}' in {repo}")
    else:
        print(f"Synced label '{label['name']}' to {repo}")

def sync_labels():
    labels = get_labels(SOURCE_REPO)
    for target_repo in TARGET_REPOS:
        print(f"\nSyncing labels to {target_repo}")
        for label in labels:
            create_or_update_label(target_repo, label)

if __name__ == "__main__":
    sync_labels()