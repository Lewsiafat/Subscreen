---
name: release
description: >
  Automate Picore-W version releases. Use when the user says "release",
  "版本發布", "發布新版本", "bump version", "tag and push", or wants to
  update CHANGELOG/README/CLAUDE.md and create a git tag.
  Handles: changelog update, docs update, commit, annotated tag, push.
---

# Release Workflow

## Procedure

1. **Check current state**
   - `git diff --stat HEAD` to see changed files
   - `git status` for untracked files
   - `git tag --sort=-v:refname | head -1` for latest version

2. **Ask the user** (use AskUserQuestion):
   - Version number (suggest based on change type: major/minor/patch)
   - Which untracked files to include (if any)
   - Any unclear changelog details

3. **Update documentation files** (all 4 must be updated):

   **CHANGELOG.md** — Add new version section at the top (before previous version), following Keep a Changelog format:
   ```
   ## [X.Y.Z] - YYYY-MM-DD

   ### Added / Changed / Fixed / Removed
   - Description of changes
   ```

   **CLAUDE.md** — Update Key Files list, Project Structure, or API sections if new files/APIs were added.

   **README.md** — Update Architecture & Files section. Add new entry points or public APIs.

   **README.zh-TW.md** — Mirror all README.md changes in Traditional Chinese.

4. **Commit** with format:
   ```
   <type>(<scope>): <description>

   <body explaining the changes>

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```
   Use HEREDOC for the message. Stage only relevant files (never `.claude/`, `deploy.sh`, `run*.sh`, `ref_source/`).

5. **Merge to main** (if not already on main):
   - If the current branch is not `main`, merge it back to main before tagging:
     ```bash
     git checkout main
     git merge <feature-branch> --no-ff -m "Merge '<feature-branch>' into main"
     ```
   - If merge conflicts occur, stop and ask the user for guidance.
   - After successful merge, optionally delete the feature branch:
     ```bash
     git branch -d <feature-branch>
     ```

6. **Tag** with annotated tag (on main):
   ```
   git tag -a vX.Y.Z -m "Release vX.Y.Z: <summary>"
   ```

7. **Push** main, tag, and clean up remote feature branch:
   ```
   git push && git push --tags
   ```
   If a feature branch was merged, also push the deletion:
   ```
   git push origin --delete <feature-branch>
   ```

8. **Report** — Summarize: commit hash, tag, merged branch (if any), changed files, and key changes.

## Version Number Guidelines

- **Major** (X.0.0): Breaking API changes (constructor signature, removed public methods)
- **Minor** (x.Y.0): New features, new public APIs, non-breaking refactors
- **Patch** (x.y.Z): Bug fixes, doc-only changes, internal tweaks

## Files to Never Stage

- `.claude/` directory
- `deploy.sh`, `run.sh`, `run_debug.sh`
- `ref_source/`
