# Branch policy

Main is human-controlled. Never push implementation to main, merge to main, enable auto-merge, force-push, delete branches or rewrite history without explicit human approval.
Work on one branch at a time. Save only to that active branch. Never merge, cherry-pick or rebase between development branches without explicit approval. Record dependencies and use documented interfaces or test mocks instead.

Create context/project-knowledge from the recorded main SHA. Create foundation/core-platform from the human-approved context commit. Pin the foundation commit before creating all agent, RAG and security branches. Create integration/release-candidate only with explicit approval specifying source commits and base.

Every branch maintains BRANCH_README.md, BRANCH_DELIVERABLES.md and its Markdown/JSON knowledge delta. Read these before reading relevant implementation files. Changes require scope review, tests, docs, commit, push of exactly one branch, remote HEAD verification and confirmation main is untouched.
