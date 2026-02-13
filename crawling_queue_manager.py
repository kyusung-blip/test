"""
크롤링 작업 큐를 Google Sheets로 관리하는 모듈
"""
import streamlit as st
from datetime import datetime
import google_sheet_manager as gsm
import seobuk_251001A as En
import time

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
    """
    sheet = gsm.get_crawling_queue_sheet()
    all_data = sheet.get_all_values()
    next_no = len(all_data)  # 헤더 포함이므로 다음 번호
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    rows = []
    for link, buyer in zip(links, buyers):
        next_no += 1
        rows.append([
            next_no, user, hd_id, link, buyer,
            "대기중", now, "", "", ""
        ])
    
    if rows:
        start_row = len(all_data) + 1
        sheet.append_rows(rows)
    
    return len(rows)

def get_pending_tasks():
    """대기중인 작업 조회"""
    sheet = gsm.get_crawling_queue_sheet()
    all_data = sheet.get_all_values()
    
    tasks = []
    for idx, row in enumerate(all_data[1:], start=2):  # 헤더 제외
        if len(row) >= 6 and row[5] == "대기중":
            tasks.append({
                "row_num": idx,
                "no": row[0],
                "user": row[1],
                "hd_id": row[2],
                "link": row[3],
                "buyer": row[4],
                "status": row[5],
                "created_at": row[6] if len(row) > 6 else ""
            })
    return tasks

def get_running_tasks():
    """진행중인 작업 조회"""
    sheet = gsm.get_crawling_queue_sheet()
    all_data = sheet.get_all_values()
    
    tasks = []
    for idx, row in enumerate(all_data[1:], start=2):
        if len(row) >= 6 and row[5] == "진행중":
            tasks.append({
                "row_num": idx,
                "no": row[0],
                "user": row[1],
                "hd_id": row[2],
                "link": row[3],
                "buyer": row[4],
                "status": row[5],
                "started_at": row[7] if len(row) > 7 else ""
            })
    return tasks

def get_completed_tasks():
    """완료된 작업 조회"""
    sheet = gsm.get_crawling_queue_sheet()
    all_data = sheet.get_all_values()
    
    tasks = []
    for idx, row in enumerate(all_data[1:], start=2):
        if len(row) >= 6 and row[5] in ["완료", "실패"]:
            tasks.append({
                "row_num": idx,
                "no": row[0],
                "user": row[1],
                "hd_id": row[2],
                "link": row[3],
                "buyer": row[4],
                "status": row[5],
                "completed_at": row[8] if len(row) > 8 else "",
                "result": row[9] if len(row) > 9 else ""
            })
    return tasks

def update_status(row_num, status, result=""):
    """작업 상태 업데이트"""
    sheet = gsm.get_crawling_queue_sheet()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if status == "진행중":
        # F: Status, H: Started_At (G: Created_At는 유지)
        sheet.update(f"F{row_num}", [[status]])
        sheet.update(f"H{row_num}", [[now]])
    elif status in ["완료", "실패"]:
        # F: Status, I: Completed_At, J: Result (G, H는 유지)
        sheet.update(f"F{row_num}", [[status]])
        sheet.update(f"I{row_num}", [[now]])
        sheet.update(f"J{row_num}", [[result]])

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
