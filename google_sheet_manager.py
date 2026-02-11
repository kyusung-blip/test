import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_spreadsheet():
    """
    구글 스프레드시트 'Dealer Information' 파일을 오픈하여 반환
    """
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # JSON 키 파일 이름 확인 (경로가 다르면 수정 필요)
    json_file = "concise-isotope-456307-n5-8cf3eb97b093.json"
    
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
    gc = gspread.authorize(creds)
    return gc.open("Dealer Information")

def get_dealer_sheet():
    """첫 번째 시트 (딜러 연락처) 반환"""
    return get_spreadsheet().sheet1

def get_company_sheet():
    """'상사정보' 워크시트 반환"""
    return get_spreadsheet().worksheet("상사정보")
