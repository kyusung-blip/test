# Queue-Based Crawling System Architecture

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Streamlit UI                                │
│                    (pages/4_new프로젝션.py)                          │
│                                                                     │
│  ┌──────────────┐  ┌────────────────────────────────────────────┐ │
│  │   Sidebar    │  │         Main Content                       │ │
│  │              │  │                                            │ │
│  │ • User       │  │  ┌──────────────┐  ┌──────────────────┐  │ │
│  │ • HD_ID      │  │  │ Tab 1:       │  │ Tab 2:           │  │ │
│  │ • Links      │  │  │ Progress     │  │ Completed        │  │ │
│  │ • Buyers     │  │  │              │  │                  │  │ │
│  │              │  │  │ • 진행중 작업  │  │ • 완료된 작업     │  │ │
│  │ [💾 Save]    │  │  │ • 대기중 작업  │  │ • 실패한 작업     │  │ │
│  │              │  │  └──────────────┘  └──────────────────┘  │ │
│  │ [🚀 Start]   │  │                                            │ │
│  │ [⏸️ Stop]     │  │  Status: 🔄 크롤링 진행 중... (대기: 3건)   │ │
│  └──────────────┘  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ imports
                              ▼
        ┌──────────────────────────────────────────┐
        │   Queue Manager                          │
        │   (crawling_queue_manager.py)            │
        │                                          │
        │  • add_tasks()                           │
        │  • get_pending_tasks()                   │
        │  • get_running_tasks()                   │
        │  • get_completed_tasks()                 │
        │  • update_status()                       │
        │  • run_next_task() ──────┐               │
        └──────────────────────────┼───────────────┘
                              │    │
                              │    │ calls
                              │    ▼
                              │  ┌─────────────────────────┐
                              │  │  Crawling Engine        │
                              │  │  (seobuk_251001A.py)    │
                              │  │                         │
                              │  │  • run_pipeline()       │
                              │  │  • make_driver()        │
                              │  │  • scrape_*()           │
                              │  └─────────────────────────┘
                              │
                              │ uses
                              ▼
        ┌──────────────────────────────────────────┐
        │   Google Sheets Manager                  │
        │   (google_sheet_manager.py)              │
        │                                          │
        │  • get_crawling_queue_sheet()            │
        │  • get_spreadsheet_open()                │
        └──────────────────────────────────────────┘
                              │
                              │ connects to
                              ▼
        ┌──────────────────────────────────────────┐
        │         Google Sheets                    │
        │     (SEOBUK PROJECTION)                  │
        │                                          │
        │  Worksheet: Crawling_Queue               │
        │  ┌────────────────────────────────────┐  │
        │  │ NO │ User │ HD_ID │ Link │ ...    │  │
        │  ├────┼──────┼───────┼──────┼────────┤  │
        │  │ 1  │JINSU │seobuk │https │대기중  │  │
        │  │ 2  │MINJI │inter77│https │진행중  │  │
        │  │ 3  │ANGEL │leeks21│https │완료    │  │
        │  └────────────────────────────────────┘  │
        └──────────────────────────────────────────┘
```

## 🔄 Data Flow

### 1. Adding Tasks
```
User Input (UI) 
    → validate (links == buyers length)
    → crawling_queue_manager.add_tasks()
    → Google Sheets (append rows)
    → Status: "대기중"
```

### 2. Auto-Crawling Loop
```
Start Button Clicked
    ↓
while crawling_active:
    ↓
    get_pending_tasks()
    ↓
    if tasks exist:
        ↓
        run_next_task()
        ↓
        ├─ update_status("진행중")
        ├─ En.run_pipeline(task)
        └─ update_status("완료" or "실패")
        ↓
        rerun UI
    else:
        ↓
        stop and notify "완료"
```

### 3. Status Updates
```
Task Status Transitions:

대기중 ──[Start]──→ 진행중 ──[Success]──→ 완료
                            └──[Error]────→ 실패

Timestamps:
• Created_At:    Set when task added
• Started_At:    Set when status → "진행중"
• Completed_At:  Set when status → "완료" or "실패"
```

## 📊 Data Model

### Google Sheets Structure
```
Crawling_Queue Worksheet:
┌──────┬──────┬───────┬──────┬───────┬────────┬────────────┬────────────┬──────────────┬────────┐
│ NO   │ User │ HD_ID │ Link │ Buyer │ Status │ Created_At │ Started_At │ Completed_At │ Result │
├──────┼──────┼───────┼──────┼───────┼────────┼────────────┼────────────┼──────────────┼────────┤
│ int  │ str  │ str   │ str  │ str   │ enum   │ datetime   │ datetime   │ datetime     │ str    │
└──────┴──────┴───────┴──────┴───────┴────────┴────────────┴────────────┴──────────────┴────────┘

Status enum: "대기중" | "진행중" | "완료" | "실패"
```

### Task Dictionary Format
```python
{
    "row_num": int,        # Sheet row number
    "no": str,             # Task number
    "user": str,           # User name
    "hd_id": str,          # HeyDealer ID
    "link": str,           # URL to crawl
    "buyer": str,          # Buyer name
    "status": str,         # Current status
    "created_at": str,     # Creation timestamp
    "started_at": str,     # Start timestamp (if started)
    "completed_at": str,   # Completion timestamp (if completed)
    "result": str          # Result message (if completed)
}
```

## 🔧 Key Functions

### crawling_queue_manager.py

#### add_tasks(user, hd_id, links, buyers)
```python
Purpose: Add multiple tasks to the queue
Input:   user (str), hd_id (str), links (list), buyers (list)
Output:  int (number of tasks added)
Process: 
  1. Validate links and buyers have same length
  2. Get current sheet data
  3. Create rows with status "대기중"
  4. Append to sheet
  5. Return count
```

#### get_pending_tasks()
```python
Purpose: Get all tasks with status "대기중"
Input:   None
Output:  list[dict] (task dictionaries)
Process:
  1. Get all sheet data
  2. Filter rows where status == "대기중"
  3. Convert to task dictionaries
  4. Return list
```

#### update_status(row_num, status, result="")
```python
Purpose: Update task status and timestamps
Input:   row_num (int), status (str), result (str, optional)
Output:  None
Process:
  If "진행중":
    - Update column F (Status)
    - Update column H (Started_At)
  If "완료" or "실패":
    - Update column F (Status)
    - Update column I (Completed_At)
    - Update column J (Result)
```

#### run_next_task()
```python
Purpose: Execute the next pending task
Input:   None
Output:  dict (status and message)
Process:
  1. Get pending tasks
  2. If none, return "no_task"
  3. Take first task
  4. Update status to "진행중"
  5. Call En.run_pipeline()
  6. If success, update to "완료"
  7. If error, update to "실패"
  8. Return result
```

## 🎯 Usage Patterns

### Pattern 1: Single User Adding Tasks
```
1. User opens page
2. Selects user/HD_ID
3. Enters links and buyers
4. Clicks "💾 저장 및 큐에 추가"
5. Tasks appear in queue
6. Clicks "🚀 시작"
7. System processes tasks automatically
```

### Pattern 2: Multiple Users Collaborating
```
User A:                          User B:
1. Adds 5 tasks                  1. Opens page
2. Starts crawling               2. Sees User A's tasks
3. Tasks processing...           3. Adds 3 more tasks
4. Completes task 1              4. User B's tasks queued
5. Completes task 2              5. Waits for User A to finish
6. ...                           6. Starts own batch
```

### Pattern 3: Error Recovery
```
1. Task fails during crawling
2. Status → "실패"
3. Result column shows error message
4. User reviews error in "완료" tab
5. User can manually re-add task if needed
```

## �� Concurrency & Thread Safety

### Google Sheets as Queue
- Google Sheets API handles concurrent access
- Each operation is atomic
- Status updates are row-specific
- No race conditions for status updates

### Streamlit Session State
- Each user has independent session
- `crawling_active` is per-session
- Multiple users can run simultaneously
- Each processes from shared queue

### Limitations
- One task processed at a time per user
- No distributed locking mechanism
- Tasks processed FIFO from single queue
- Users see same queue state

## 📈 Scalability Considerations

### Current Design
- Sequential processing (one task at a time per user)
- Google Sheets API rate limits apply
- Suitable for small teams (5-10 users)

### Future Improvements
- Add task priority field
- Implement parallel processing
- Add retry mechanism for failed tasks
- Cache sheet data to reduce API calls
- Add task filtering by user

## 🔍 Monitoring & Debugging

### UI Feedback
- Real-time status in main content
- Task count displayed
- Recent history (last 10 completed)
- Error messages in result column

### Google Sheets
- Complete audit trail
- All timestamps preserved
- Easy to export/analyze
- Manual intervention possible

### Logs
- Streamlit console shows execution
- Errors displayed in UI
- Result column captures exceptions

---

**Architecture Version**: 1.0  
**Last Updated**: 2026-02-13  
**Maintained By**: SEOBUK Team
