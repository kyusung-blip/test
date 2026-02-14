# 크롤링 큐 마이그레이션 가이드

## 변경 사항
- **이전**: Google Sheets API를 사용한 크롤링 큐 관리
- **현재**: 로컬 JSON 파일(`crawling_queue.json`)을 사용한 크롤링 큐 관리

### 주요 개선사항
1. ✅ **API 제한 해결**: Google Sheets API의 쿼터 제한 없음
2. ✅ **인증 단순화**: Google OAuth 인증 불필요
3. ✅ **성능 향상**: 로컬 파일 읽기/쓰기로 빠른 응답
4. ✅ **오프라인 작동**: 인터넷 연결 없이도 작동 가능
5. ✅ **의존성 감소**: gspread, oauth2client 라이브러리 의존성 제거

## 수정된 파일
1. **`crawling_queue_manager.py`** - Google Sheets API에서 JSON 파일 기반으로 전환
2. **`pages/4_new프로젝션.py`** - 사용하지 않는 `google_sheet_manager` import 제거
3. **`crawling_queue.json`** (신규) - 크롤링 큐 데이터를 저장하는 JSON 파일

## 데이터 구조

### JSON 파일 구조
```json
{
  "queue": [
    {
      "no": 1,
      "user": "JINSU",
      "hd_id": "seobuk",
      "link": "https://example.com/vehicle/123",
      "buyer": "John Doe",
      "status": "대기중",
      "created_at": "2024-01-01 10:00:00",
      "started_at": "",
      "completed_at": "",
      "result": ""
    }
  ],
  "last_updated": "2024-01-01 10:00:00",
  "version": "1.0"
}
```

### 작업 상태
- **대기중**: 작업이 생성되었으나 아직 시작되지 않음
- **진행중**: 크롤링이 현재 실행 중
- **완료**: 크롤링이 성공적으로 완료됨
- **실패**: 크롤링 중 오류가 발생함

## 테스트 방법

### 1. Streamlit 앱 실행
```bash
streamlit run app.py
```

### 2. "New 크롤링 시스템" 페이지로 이동
- 사이드바에서 페이지 선택

### 3. 작업 추가 테스트
1. 매입사원 선택 (예: JINSU)
2. 헤이딜러 ID 선택 (예: seobuk)
3. Links 입력 (한 줄에 하나씩)
4. Buyers 입력 (한 줄에 하나씩)
5. "💾 저장 및 큐에 추가" 버튼 클릭

### 4. JSON 파일 확인
```bash
cat crawling_queue.json
```

작업이 올바르게 추가되었는지 확인합니다.

### 5. 작업 상태 확인
- 대기 중 작업 탭에서 추가된 작업 확인
- 필요시 크롤링 시작 버튼으로 작업 실행

## 함수 인터페이스 (변경 없음)

모든 기존 함수의 시그니처는 동일하게 유지됩니다:

```python
# 작업 추가
add_tasks(user, hd_id, links, buyers) -> int

# 대기 중인 작업 조회
get_pending_tasks() -> list[dict]

# 진행 중인 작업 조회
get_running_tasks() -> list[dict]

# 완료된 작업 조회
get_completed_tasks() -> list[dict]

# 상태 업데이트
update_status(row_num, status, result="") -> None

# 다음 작업 실행
run_next_task() -> dict
```

## 롤백 방법

### Git을 사용한 롤백
```bash
# 이전 커밋으로 되돌리기
git revert HEAD

# 또는 특정 커밋으로
git reset --hard <commit-hash>
```

### 수동 롤백
`crawling_queue_manager.py`를 원래 버전으로 복원:
1. Google Sheets 관련 import 복원
2. JSON 파일 읽기/쓰기 함수 제거
3. 각 함수를 Google Sheets API 호출로 복원

## 기존 기능 영향

이 마이그레이션은 **크롤링 큐 기능만** 변경하며, 다른 기능들은 영향을 받지 않습니다:

- ✅ **Dealer Information** - 영향 없음 (여전히 Google Sheets 사용)
- ✅ **상사정보** - 영향 없음 (여전히 Google Sheets 사용)
- ✅ **바이어 정보** - 영향 없음 (여전히 Google Sheets 사용)
- ✅ **Inventory** - 영향 없음 (여전히 Google Sheets 사용)
- ✅ **Inspection** - 영향 없음 (여전히 Google Sheets 사용)

## 주의사항

### 1. 동시성 (Concurrency)
현재 구현은 단일 프로세스 환경을 가정합니다. 여러 프로세스가 동시에 파일을 수정할 경우:
- 파일 락(file locking) 메커니즘 추가 고려
- 또는 데이터베이스 솔루션으로 추가 마이그레이션 고려

### 2. 백업
`crawling_queue.json` 파일을 주기적으로 백업하는 것을 권장합니다:
```bash
# 백업 스크립트 예시
cp crawling_queue.json crawling_queue.json.backup.$(date +%Y%m%d_%H%M%S)
```

### 3. Git 관리
`.gitignore`에 `crawling_queue.json` 추가 여부 검토:
- **추가하는 경우**: 실제 운영 데이터가 Git에 커밋되지 않음 (권장)
- **추가하지 않는 경우**: 초기 템플릿이 버전 관리됨

현재 `.gitignore`에 추가하지 않았으므로, 실제 운영 시에는 다음과 같이 추가를 고려하세요:
```bash
echo "crawling_queue.json" >> .gitignore
```

## 문제 해결

### Q: JSON 파일이 손상되었습니다
**A**: 파일을 삭제하면 자동으로 초기 구조가 재생성됩니다:
```bash
rm crawling_queue.json
```

### Q: 한글이 깨져서 표시됩니다
**A**: 이미 `ensure_ascii=False`로 설정되어 있어 한글을 지원합니다. 파일을 UTF-8로 열어야 합니다.

### Q: 작업이 추가되지 않습니다
**A**: 
1. 파일 권한 확인: `ls -l crawling_queue.json`
2. 로그 확인: Streamlit 콘솔에서 에러 메시지 확인
3. 파일 존재 확인: `test -f crawling_queue.json && echo "exists"`

### Q: 기존 Google Sheets의 데이터는 어떻게 되나요?
**A**: 
- Google Sheets의 데이터는 그대로 유지됩니다
- 다른 기능들(Dealer Information 등)은 계속 Google Sheets를 사용합니다
- 크롤링 큐만 JSON 파일로 분리된 것입니다
- 필요시 기존 데이터를 JSON으로 수동 마이그레이션할 수 있습니다

## 추가 개선 사항 (향후)

1. **파일 락킹**: 동시성 지원을 위한 파일 락 구현
2. **데이터베이스 마이그레이션**: SQLite 또는 다른 DB로 전환
3. **자동 백업**: 크론잡을 통한 자동 백업 시스템
4. **히스토리 관리**: 완료된 작업의 아카이빙
5. **모니터링**: 큐 상태 모니터링 대시보드
