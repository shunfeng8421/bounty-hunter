"""
Bounty Discovery - Find real paid bounties across platforms
Sources: BountyScout aggregator, GitHub search, Algora, BOSS.dev
"""
import json, re, subprocess, sys
from datetime import datetime, timezone

def discover_from_bountyscout():
    """Find bounties from BountyScout aggregator repos."""
    repos = ["vansh-09/BountyScout", "dev-kp-eloper/BountyScout", "MoonFuji/BountyScout"]
    all_bounties = []

    for repo in repos:
        try:
            r = subprocess.run(
                ["gh", "issue", "list", "--repo", repo, "--label", "bounty-alert",
                 "--state", "open", "--limit", "3", "--json", "number,body,createdAt"],
                capture_output=True, text=True, timeout=15
            )
            if r.returncode != 0:
                continue
            issues = json.loads(r.stdout)
            for issue in issues:
                # Parse bounty URLs from body
                urls = re.findall(r'https://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull)/\d+', issue.get("body", ""))
                for url in urls:
                    all_bounties.append({
                        "url": url,
                        "source": repo,
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                    })
        except Exception:
            continue

    return all_bounties

def discover_from_github():
    """Search GitHub directly for /bounty issues."""
    queries = [
        "/bounty is:open label:good-first-issue",
        "/bounty is:open label:bug",
        "/bounty in:body is:open created:>2026-05-01",
    ]
    all_bounties = []

    for query in queries:
        try:
            r = subprocess.run(
                ["gh", "search", "issues", query, "--limit", "20",
                 "--json", "number,title,url,repository,body"],
                capture_output=True, text=True, timeout=15
            )
            if r.returncode != 0:
                continue
            issues = json.loads(r.stdout)
            for issue in issues:
                body = issue.get("body", "")
                amount = ""
                m = re.search(r'/bounty\s*(?:\$)?(\d+)', body)
                if m:
                    amount = amount

                all_bounties.append({
                    "url": issue["url"],
                    "title": issue["title"],
                    "repo": issue["repository"]["nameWithOwner"],
                    "amount": amount,
                    "source": "github",
                    "discovered_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception:
            continue

    return all_bounties

def discover_from_securebanana():
    """SecureBananaLabs has many low-hanging-fruit bounties."""
    try:
        r = subprocess.run(
            ["gh", "issue", "list", "--repo", "SecureBananaLabs/bug-bounty",
             "--state", "open", "--limit", "20", "--json", "number,title,url,labels"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode != 0:
            return []
        issues = json.loads(r.stdout)
        return [{
            "url": i["url"],
            "title": i["title"],
            "repo": "SecureBananaLabs/bug-bounty",
            "amount": "(bounty program)",
            "source": "securebanana",
            "difficulty": "low",
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        } for i in issues]
    except Exception:
        return []

def main():
    print("=== BOUNTY DISCOVERY ===")
    print()

    all_bounties = []
    all_bounties.extend(discover_from_bountyscout())
    all_bounties.extend(discover_from_github())
    all_bounties.extend(discover_from_securebanana())

    # Deduplicate by URL
    seen = set()
    unique = []
    for b in all_bounties:
        url = b["url"]
        if url not in seen:
            seen.add(url)
            unique.append(b)

    # Print results
    print(f"Found {len(unique)} unique bounties:\n")
    for i, b in enumerate(unique[:20], 1):
        amount = b.get("amount", "")
        if not amount:
            amount = b.get("difficulty", "?")
        title = b.get("title", "")[:80]
        print(f"{i:2d}. [{amount:>12s}] {b['repo']}")
        print(f"    {title}")
        print(f"    {b['url']}")
        print()

    # Save for later use
    with open("workspace/discovered_bounties.jsonl", "w", encoding="utf-8") as f:
        for b in unique:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    print(f"Saved to workspace/discovered_bounties.jsonl")

if __name__ == "__main__":
    main()
