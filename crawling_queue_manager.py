"""
크롤링 작업 큐를 로컬 JSON 파일로 관리하는 모듈
"""
import streamlit as st
from datetime import datetime
import seobuk_251001A as En
import time
import json
import os
from pathlib import Path

# JSON 파일 경로
JSON_FILE = Path(__file__).parent / "crawling_queue.json"

def _load_queue():
    """JSON 파일에서 큐 데이터를 로드"""
    if not JSON_FILE.exists():
        # 파일이 없으면 초기 구조 생성
        initial_data = {
            "queue": [],
            "last_updated": "",
            "version": "1.0"
        }
        _save_queue(initial_data)
        return initial_data
    
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        st.error(f"큐 데이터 파일이 손상되었습니다: {e}")
        return {"queue": [], "last_updated": "", "version": "1.0"}
    except PermissionError as e:
        st.error(f"큐 데이터 파일 접근 권한이 없습니다: {e}")
        return {"queue": [], "last_updated": "", "version": "1.0"}
    except Exception as e:
        st.error(f"큐 데이터 로드 실패: {e}")
        return {"queue": [], "last_updated": "", "version": "1.0"}

def _save_queue(data):
    """큐 데이터를 JSON 파일에 저장 (atomic write)"""
    import tempfile
    try:
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 임시 파일에 먼저 쓰기
        temp_fd, temp_path = tempfile.mkstemp(dir=JSON_FILE.parent, suffix='.tmp')
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 원자적으로 파일 교체
            os.replace(temp_path, JSON_FILE)
        except Exception:
            # 실패 시 임시 파일 삭제
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    except Exception as e:
        st.error(f"큐 데이터 저장 실패: {e}")

def add_tasks(user, hd_id, links, buyers):
    """
    여러 작업을 큐에 추가
    Args:
        user: str - 매입사원명
        hd_id: str - 헤이딜러 ID
        links: list[str] - 링크 목록
        buyers: list[str] - 바이어 목록
    Returns:
        int - 추가된 작업 수
    Raises:
        ValueError: links와 buyers의 길이가 다를 경우
    """
    if len(links) != len(buyers):
        raise ValueError(f"링크와 바이어 개수가 일치하지 않습니다: {len(links)} vs {len(buyers)}")
    
    data = _load_queue()
    queue = data.get("queue", [])
    
    # 다음 작업 번호 계산
    next_no = max((task.get("no", 0) for task in queue), default=0) + 1
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 새 작업들 추가
    for link, buyer in zip(links, buyers):
        queue.append({
            "no": next_no,
            "user": user,
            "hd_id": hd_id,
            "link": link,
            "buyer": buyer,
            "status": "대기중",
            "created_at": now,
            "started_at": "",
            "completed_at": "",
            "result": ""
        })
        next_no += 1
    
    data["queue"] = queue
    _save_queue(data)
    
    return len(links)

def get_pending_tasks():
    """대기중인 작업 조회"""
    data = _load_queue()
    queue = data.get("queue", [])
    
    tasks = []
    for idx, task in enumerate(queue):
        if task.get("status") == "대기중":
            task_copy = task.copy()
            task_copy["row_num"] = idx  # 배열 인덱스 저장
            tasks.append(task_copy)
    return tasks

def get_running_tasks():
    """진행중인 작업 조회"""
    data = _load_queue()
    queue = data.get("queue", [])
    
    tasks = []
    for idx, task in enumerate(queue):
        if task.get("status") == "진행중":
            task_copy = task.copy()
            task_copy["row_num"] = idx  # 배열 인덱스 저장
            tasks.append(task_copy)
    return tasks

def get_completed_tasks():
    """완료된 작업 조회"""
    data = _load_queue()
    queue = data.get("queue", [])
    
    tasks = []
    for idx, task in enumerate(queue):
        if task.get("status") in ["완료", "실패"]:
            task_copy = task.copy()
            task_copy["row_num"] = idx  # 배열 인덱스 저장
            tasks.append(task_copy)
    return tasks

def update_status(row_num, status, result=""):
    """작업 상태 업데이트"""
    data = _load_queue()
    queue = data.get("queue", [])
    
    if not (0 <= row_num < len(queue)):
        st.warning(f"잘못된 작업 번호입니다: {row_num} (큐에 {len(queue)}개 작업 존재)")
        return
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    queue[row_num]["status"] = status
    
    if status == "진행중":
        queue[row_num]["started_at"] = now
    elif status in ["완료", "실패"]:
        queue[row_num]["completed_at"] = now
        queue[row_num]["result"] = result
    
    data["queue"] = queue
    _save_queue(data)

def run_next_task():
    """
    대기중인 첫 번째 작업을 실행
    Returns:
        dict - {"status": "success/no_task/error", "message": str}
    """
    pending = get_pending_tasks()
    
    if not pending:
        return {"status": "no_task", "message": "대기 중인 작업이 없습니다."}
    
    task = pending[0]
    
    try:
        # 상태를 진행중으로 변경
        update_status(task["row_num"], "진행중")
        
        # 크롤링 실행
        list_pairs = [(task["link"], task["buyer"])]
        En.run_pipeline(
            list_pairs=list_pairs,
            user_name=task["user"],
            headless=True,
            hd_login_id=task["hd_id"]
        )
        
        # 완료 처리
        update_status(task["row_num"], "완료", "크롤링 성공")
        
        return {
            "status": "success",
            "message": f"✅ NO.{task['no']} 크롤링 완료"
        }
        
    except Exception as e:
        update_status(task["row_num"], "실패", str(e))
        return {
            "status": "error",
            "message": f"❌ NO.{task['no']} 실패: {str(e)}"
        }

def reset_stuck_tasks():
    """
    '진행중' 상태로 멈춰있는 작업을 '대기중'으로 되돌림
    Returns:
        int - 초기화된 작업 수
    """
    data = _load_queue()
    queue = data.get("queue", [])
    
    reset_count = 0
    for task in queue:
        if task.get("status") == "진행중":
            task["status"] = "대기중"
            task["started_at"] = ""
            reset_count += 1
    
    if reset_count > 0:
        data["queue"] = queue
        _save_queue(data)
    
    return reset_count

def retry_failed_tasks():
    """
    '실패' 상태인 작업을 다시 '대기중'으로 변경
    Returns:
        int - 재시도 설정된 작업 수
    """
    data = _load_queue()
    queue = data.get("queue", [])
    
    retry_count = 0
    for task in queue:
        if task.get("status") == "실패":
            task["status"] = "대기중"
            task["started_at"] = ""
            task["completed_at"] = ""
            task["result"] = ""
            retry_count += 1
    
    if retry_count > 0:
        data["queue"] = queue
        _save_queue(data)
    
    return retry_count
