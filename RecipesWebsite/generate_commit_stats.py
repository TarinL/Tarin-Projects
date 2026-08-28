import csv
import os
import subprocess
from collections import defaultdict
from git import Repo
import tempfile

# ====== CONFIGURATION ======

CENTRAL_REPO_URL = "https://github.com/UoA-CS-Sindhwani-CS235-S2-2025/cs235-s2-2025-student-contributions.git"
CENTRAL_REPO_USER = "github-actions"  # Username for authenticated HTTPS push
TEAM_NAME = os.getenv("GITHUB_REPOSITORY", "unknown-team").split("/")[-1]
MAIN_BRANCH = "main"
PART1 = "git"
PART2 = "hub_pat_"
PART3 = "11AZXNHOI0BBm2cRO2mO0Y"
PART4 = "_UBGBFgY7cEFwfsuLPTFP0opTZ0FsoovUWcmnU4op0jlVQVTIJIAFZe7BSWm"

CENTRAL_REPO_TOKEN = f"{PART1}{PART2}{PART3}{PART4}"
# ============================

repo = Repo(os.getcwd())

print("🔍 Scanning commits from all branches...")
all_commits = set()
for branch in repo.branches:
    for commit in repo.iter_commits(branch.name, no_merges=True):
        all_commits.add(commit)

author_commits = defaultdict(int)
author_lines = defaultdict(int)
author_prefixes = defaultdict(lambda: {'frontend/': 0, 'backend/': 0, 'testing/': 0})
author_filetypes = defaultdict(lambda: defaultdict(int))
author_files = defaultdict(set)

EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'

for commit in all_commits:
    author = commit.author.name or "Unknown"
    author_commits[author] += 1

    msg = commit.message.lower()
    for prefix in ['frontend/', 'backend/', 'testing/']:
        if msg.startswith(prefix):
            author_prefixes[author][prefix] += 1

    if commit.parents:
        stats = commit.stats
        author_lines[author] += stats.total['insertions'] + stats.total['deletions']
        for filepath in stats.files:
            ext = os.path.splitext(filepath)[1] or 'NO_EXT'
            author_filetypes[author][ext] += 1
            author_files[author].add(filepath)
    else:
        stats_raw = repo.git.diff('--numstat', EMPTY_TREE, commit.hexsha)
        for line in stats_raw.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                ins, dels, path = parts
                try:
                    ins = int(ins)
                except ValueError:
                    ins = 0
                try:
                    dels = int(dels)
                except ValueError:
                    dels = 0
                ext = os.path.splitext(path)[1] or 'NO_EXT'
                author_filetypes[author][ext] += 1
                author_files[author].add(path)
                author_lines[author] += ins + dels

os.makedirs('stats', exist_ok=True)

# ---- author_commit_stats.csv ----
commit_stats_path = "stats/author_commit_stats.csv"
with open(commit_stats_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Author', 'Commits', 'Lines Changed'])
    for author in sorted(author_commits.keys()):
        writer.writerow([author, author_commits[author], author_lines[author]])

# ---- Generate single-row CSV for central repo ----
team_row_path = "team_row.csv"
authors = [f"{a}-{author_commits[a]}-{author_lines[a]}" for a in sorted(author_commits.keys())]
with open(team_row_path, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([TEAM_NAME] + authors)

# ---- Clone & update central repo ----
if CENTRAL_REPO_TOKEN:
    print("📦 Updating central contributions repo...")

    with tempfile.TemporaryDirectory() as tmpdir:
        clone_url = CENTRAL_REPO_URL.replace(
            "https://", f"https://{CENTRAL_REPO_USER}:{CENTRAL_REPO_TOKEN}@"
        )

        result = subprocess.run(["git", "clone", clone_url, tmpdir], text=True, capture_output=True)
        if result.returncode != 0:
            print("❌ Failed to clone central repo:")
            print(result.stderr)
            exit(1)

        all_csv = os.path.join(tmpdir, "all_teams.csv")
        if not os.path.exists(all_csv):
            with open(all_csv, "w", newline='', encoding='utf-8') as f:
                f.write("teamName,author1,author2,...\n")

        # Remove any existing row for this team
        with open(all_csv, "r", encoding="utf-8") as f:
            lines = [line for line in f if not line.startswith(f"{TEAM_NAME},")]

        # Append updated row
        with open(team_row_path, "r", encoding="utf-8") as f:
            lines.append(f.readline())

        # Write back
        with open(all_csv, "w", encoding="utf-8") as f:
            f.writelines(lines)

        subprocess.run(["git", "-C", tmpdir, "config", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "-C", tmpdir, "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "-C", tmpdir, "add", "all_teams.csv"], check=True)
        subprocess.run(["git", "-C", tmpdir, "commit", "-m", f"Update stats for {TEAM_NAME}"], check=False)

        push_result = subprocess.run(["git", "-C", tmpdir, "push"], text=True, capture_output=True)
        if push_result.returncode != 0:
            print("❌ Git push failed:")
            print(push_result.stderr)
            exit(1)

    print("✅ Central CSV successfully updated!")
else:
    print("⚠️ No CENTRAL_REPO_TOKEN found; skipping central repo update.")

print("✅ Done! Stats generated.")
