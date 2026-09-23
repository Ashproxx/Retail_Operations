"""Check tracked and untracked edits against the pinned M1 base."""
import subprocess
import sys

BASE = "3cc1a8df36c49147daac2c3967f37020bb0f5654"
ALLOWED = {".gitignore", ".env.example", "requirements.txt", "requirements-dev.txt", "pyproject.toml",
           "BRANCH_README.md", "BRANCH_DELIVERABLES.md", "scripts/check_branch_scope.py",
           "docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.md",
           "docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.json"}

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def main():
    if git("branch", "--show-current") != "foundation/core-platform":
        sys.exit("FAIL: this guard is scoped to foundation/core-platform")
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"], check=True)
    changed = set(git("diff", "--name-only", BASE).splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    bad = sorted(x for x in changed if x not in ALLOWED and not x.startswith(("app/", "tests/foundation/")))
    if bad:
        sys.exit("FAIL: out-of-scope files: " + ", ".join(bad))
    print(f"PASS: {len(changed)} changed paths within foundation scope")


if __name__ == "__main__":
    main()
