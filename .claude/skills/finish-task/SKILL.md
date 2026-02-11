---
name: finish-task
description: >
  結束目前的開發任務：產出 walkthrough 文件、commit 所有變更、merge 回 main。
  Use when the user says "/finish-task", "結束任務", "完成任務", "finish",
  "收工", "merge back", or wants to wrap up the current development task
  and merge changes back to main branch.
---

# Finish Task — 結束開發任務

## Overview

自動化開發任務的結束流程：分析變更 → 撰寫 walkthrough → commit → merge 回 main。與 `/task` skill 搭配使用，確保每個任務有完整的收尾記錄。

## Workflow

### Step 1: 確認狀態

1. 取得目前分支名稱，確認不在 `main` 上（若在 main 則提示錯誤）
2. 從分支名稱解析 `{type}` 和 `{scope-name}`（例如 `feat/ui-framework` → type=`feat`, scope=`ui-framework`）
3. 執行 `git status` 和 `git diff main...HEAD` 檢視所有變更
4. 檢查是否有對應的 spec 文件 `specs/{scope-name}.md`，若有則讀取作為參考

### Step 2: 撰寫 Walkthrough

1. 分析所有變更（新增/修改/刪除的檔案、commit 歷史）
2. 讀取模板 `.claude/skills/finish-task/assets/walkthrough-template.md`
3. 填入內容，寫入 `specs/{scope-name}-walkthrough.md`：
   - `{title}` — 從 spec 或分支名稱推導標題
   - `{branch}` — 目前分支名稱
   - `{date}` — 當天日期（YYYY-MM-DD）
   - `{summary}` — 1-3 句話總結做了什麼
   - `{files}` — 列出所有變更的檔案，每個附簡要說明
   - `{details}` — 重要的技術決策或實作細節
4. 若有 spec 文件，更新其中的任務清單（將完成項目打勾 `- [x]`）

### Step 3: Commit

1. 將所有變更加入 staging（包含 walkthrough 文件）
2. 以 `{type}({scope-name}): <描述>` 格式建立 commit message
3. 執行 commit

### Step 4: Merge 回 Main

1. 切換到 `main` 分支
2. 執行 `git merge {branch-name} --no-ff`（保留 merge commit）
3. 確認 merge 成功，顯示結果
4. 詢問使用者是否要刪除已合併的分支

## Notes

- 若有未 commit 的變更，在 Step 3 一併 commit
- Merge 使用 `--no-ff` 保留分支歷史
- Walkthrough 文件放在 `specs/` 目錄下，與 spec 文件配對
- 若 merge 有衝突，停下來請使用者處理
