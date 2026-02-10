import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_google_sheet():
    """구글 스프레드시트 연결 설정"""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # JSON 키 파일 이름 (파일이 brand.py와 같은 경로에 있어야 함)
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "concise-isotope-456307-n5-8cf3eb97b093.json", scope)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open("Dealer Information")
        return spreadsheet.worksheet("브랜드")
    except Exception as e:
        print(f"구글 시트 연결 실패: {e}")
        return None

def get_brand_from_vin(vin):
    """VIN 코드를 받아 브랜드를 반환"""
    vin = str(vin).strip().upper()
    if len(vin) < 3:
        return ""

    key = vin[1:3]  # VIN 2~3번째 자리 추출

    try:
        sheet = get_google_sheet()
        if not sheet:
            return "연결 오류"

        records = sheet.get_all_records()

        for row in records:
            # 시트의 헤더가 'VIN'과 '브랜드'여야 합니다.
            vin_code = str(row.get("VIN", "")).strip().upper()
            if vin_code == key:
                return row.get("브랜드", "").strip()

        return "브랜드 미등록"

    except Exception as e:
        print(f"[브랜드 조회 오류] {e}")
        return "조회 오류"
