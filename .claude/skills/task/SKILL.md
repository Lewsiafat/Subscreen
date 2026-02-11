---
name: task
description: >
  開發任務流程自動化。建立新的開發任務，包含分支建立和規格確認。
  Use when the user says "/task", "建立任務", "新任務", "new task",
  "開新功能", or wants to start a new development task with branch
  creation and specification.
---

# Task — 開發任務流程

## Overview

自動化開發任務的啟動流程：收集 scope → 建立分支 → 討論規格 → 產出規格文件。確保每個開發任務都有一致的起始流程和文件記錄。

## Workflow

### Step 1: 輸入 Scope

使用 AskUserQuestion 向使用者詢問以下資訊：

- **任務類型** — 選項：`feat` / `fix` / `refactor` / `docs` / `chore`
- **Scope 名稱** — 簡短的 kebab-case 描述（例如 `add-led-control`、`fix-reconnect-loop`）
- **簡要描述** — 一句話說明這個任務要做什麼

### Step 2: 建立分支

從 main 分支建立新的開發分支：

- 分支格式：`{type}/{scope-name}`（例如 `feat/add-led-control`）
- 執行：
  ```bash
  git checkout main
  git checkout -b {type}/{scope-name}
  ```
- 確認分支建立成功後，告知使用者目前所在分支

### Step 3: 討論規格

與使用者互動，確認任務的技術細節：

1. 根據 scope 描述，分析專案中可能需要修改的檔案（參考 CLAUDE.md 的架構說明）
2. 提出技術方案建議，包括：
   - 需要修改或新增的檔案
   - 實作方式概述
   - 可能的影響範圍
3. 與使用者討論並確認最終方案
4. 整理出具體的任務清單（checklist 形式）

### Step 4: 紀錄規格

將確認的規格寫入文件：

1. 若 `specs/` 目錄不存在，先建立它
2. 讀取模板 `.claude/skills/task/assets/spec-template.md`
3. 填入內容，寫入 `specs/{scope-name}.md`：
   - `{title}` — 任務標題（中文或英文皆可）
   - `{branch}` — 分支名稱（例如 `feat/add-led-control`）
   - `{date}` — 當天日期（YYYY-MM-DD 格式）
   - `{description}` — 確認後的描述
   - `{task items}` — 展開為多個 `- [ ]` 項目
4. 告知使用者規格文件已建立，顯示檔案路徑

## Notes

- 分支名稱使用 kebab-case，與專案 commit message 的 scope 一致
- 規格文件放在專案根目錄的 `specs/` 下，方便追蹤
- 如果使用者已經在非 main 分支上，詢問是否要切換回 main 再建立新分支
