# Queue-Based Real-Time Crawling System Setup

## Overview
This document describes the setup for the new queue-based real-time crawling system implemented in `pages/4_new프로젝션.py`.

## Google Sheets Setup

### 1. Create the Queue Sheet

You need to create a worksheet named `Crawling_Queue` in the `SEOBUK PROJECTION` Google Spreadsheet.

#### Steps:
1. Open the `SEOBUK PROJECTION` spreadsheet in Google Sheets
2. Create a new worksheet named `Crawling_Queue`
3. Add the following header row (Row 1):

| NO | User | HD_ID | Link | Buyer | Status | Created_At | Started_At | Completed_At | Result |
|----|------|-------|------|-------|--------|------------|------------|--------------|--------|

#### Column Descriptions:
- **NO** (Column A): Sequential number (auto-incremented)
- **User** (Column B): Purchase employee name (JINSU, MINJI, etc.)
- **HD_ID** (Column C): HeyDealer ID (seobuk, inter77, leeks21)
- **Link** (Column D): URL to crawl
- **Buyer** (Column E): Buyer name
- **Status** (Column F): Task status (대기중/진행중/완료/실패)
- **Created_At** (Column G): Creation timestamp
- **Started_At** (Column H): Start timestamp
- **Completed_At** (Column I): Completion timestamp
- **Result** (Column J): Result message

## Files Created

### 1. `google_sheet_manager.py` (Modified)
- Added `get_crawling_queue_sheet()` function to access the Crawling_Queue worksheet

### 2. `crawling_queue_manager.py` (New)
Queue management module with the following functions:
- `add_tasks()` - Add multiple tasks to the queue
- `get_pending_tasks()` - Get tasks with status "대기중"
- `get_running_tasks()` - Get tasks with status "진행중"
- `get_completed_tasks()` - Get tasks with status "완료" or "실패"
- `update_status()` - Update task status and timestamps
- `run_next_task()` - Execute the next pending task

### 3. `pages/4_new프로젝션.py` (New)
New Streamlit page with queue-based UI:
- Sidebar for adding new tasks
- Start/Stop controls for auto-crawling
- Two tabs: "진행중/대기중" and "완료"
- Real-time status updates

## Features

### Adding Tasks
1. Select user and HeyDealer ID in the sidebar
2. Enter links (one per line)
3. Enter buyers (one per line, matching links)
4. Click "💾 저장 및 큐에 추가"
5. Tasks are added to the queue with status "대기중"

### Auto-Crawling
1. Click "🚀 시작" to begin auto-crawling
2. System processes tasks one by one from the queue
3. Status updates in real-time: 대기중 → 진행중 → 완료/실패
4. Click "⏸️ 중지" to stop at any time
5. System auto-stops when all tasks are completed

### Multi-User Support
- Multiple users can view the same queue (via Google Sheets)
- All status updates are reflected in real-time
- Concurrent access is supported through Google Sheets API

## Usage Flow

```
1. User adds tasks → Queue (대기중)
2. Click "🚀 시작" → System picks first "대기중" task
3. Status changes to "진행중"
4. Crawling executes (calls En.run_pipeline)
5. Status changes to "완료" (success) or "실패" (error)
6. System picks next "대기중" task
7. Repeat until no more "대기중" tasks
8. Auto-stop
```

## Important Notes

- **Existing files are NOT modified**: `pages/3_프로젝션.py` and `seobuk_251001A.py` remain unchanged
- Only new files were created and one function was added to `google_sheet_manager.py`
- The system uses the same crawling engine (`seobuk_251001A.py`) as the original page
- All tasks are stored in Google Sheets for persistence and sharing

## Testing Checklist

Before using in production, verify:
- [ ] `Crawling_Queue` worksheet exists in `SEOBUK PROJECTION`
- [ ] Headers are correctly set in row 1
- [ ] Can add tasks through the UI
- [ ] Tasks appear in Google Sheets with correct data
- [ ] Auto-crawling processes tasks sequentially
- [ ] Status updates correctly (대기중 → 진행중 → 완료/실패)
- [ ] Multiple users can see the same queue
- [ ] System stops when queue is empty
