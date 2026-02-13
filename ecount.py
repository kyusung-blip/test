import requests
import json
from datetime import datetime
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# [설정] 발급받으신 정식 정보 적용
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "2dac8e71fcd314e77af2ce35eb89185442" # 정식 인증키
ZONE = "AD" 

def get_session_id():
    """정식 운영 서버(oapi) 세션 획득"""
    login_url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/OAPILogin"
    payload = {
        "COM_CODE": COM_CODE,
        "USER_ID": USER_ID,
        "API_CERT_KEY": API_CERT_KEY,
        "LAN_TYPE": "ko-KR",
        "ZONE": ZONE 
    }
    try:
        response = requests.post(login_url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        if str(res_data.get("Status")) == "200":
            return res_data["Data"]["Datas"]["SESSION_ID"]
        return None
    except Exception as e:
        print(f"로그인 통신 오류: {e}")
        return None

def register_item(data, session_id, sheet_no):
    """정식 URL을 사용하여 실제 차량 데이터를 품목으로 등록"""
    # 정식 URL 적용
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/SaveBasicProduct?SESSION_ID={session_id}"
    
    # 숫자형 데이터 정제 함수
    def to_float(val):
        try:
            import re
            if not val: return 0.0
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    # 길이, 너비, 높이 및 CMB 계산
    l = to_float(data.get("length", 0))
    w = to_float(data.get("width", 0))
    h = to_float(data.get("height", 0))
    cmb_val = (l / 1000) * (w / 1000) * (h / 1000)

    # 이카운트 BulkDatas 표준 필드 매핑
    payload = {
        "ProductList": [
            {
                "BulkDatas": {
                    "PROD_CD": str(data.get("vin", "")),             # 품목코드: VIN
                    "PROD_DES": str(data.get("car_name_remit", "")),    # 품목명: 차명(송금용)
                    "UNIT": "EA",
                    "ADD_TXT_01_T": str(data.get("brand", "")),             # 추가문자형식1: BRAND
                    "CONT1": str(sheet_no),                          # 문자형추가항목1: NO (구글시트 순번)
                    "CONT2": str(data.get("plate", "")),             # 문자형추가항목2: PLATE (차량번호)
                    "CONT3": str(data.get("km", "")),                # 문자형추가항목3: km (주행거리)
                    "CONT4": str(data.get("color", "")),             # 문자형추가항목4: COLOR (색상)
                    "CONT5": str(data.get("year", "")),              # 문자형추가항목5: YEAR (연식)
                    "ADD_DATE_01_T": datetime.now().strftime("%Y%m%d"),        # 추가일자형식1: 등록일자
                    "NO_USER2": l,                                   # 숫자형추가항목2: 길이
                    "NO_USER3": w,                                   # 숫자형추가항목3: 너비
                    "NO_USER4": h,                                   # 숫자형추가항목4: 높이
                    "NO_USER6": round(cmb_val, 4),                   # 숫자형추가항목6: CMB
                    "NO_USER7": 1,                                   # 숫자형추가항목7: 유로환율 (기본값 1)
                    "NO_USER8": 1                                    # 숫자형추가항목8: 달러환율 (기본값 1)
                }
            }
        ]
    }

    
    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"등록 통신 오류: {str(e)}"}

def register_purchase(data, session_id, username):
    """이카운트 구매입력(전표) 저장 API - 최소 필드 테스트"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/Purchases/SavePurchases?SESSION_ID={session_id}"
    
    import re
    # 1. 거래처 번호 정제
    biz_num = str(data.get("biz_num", ""))
    cust_code = re.sub(r'[^0-9]', '', biz_num)
    
    # 2. 숫자 변환 유틸리티
    def to_float(val):
        """금액 문자열을 숫자로 변환 (만원 단위 처리)"""
        if not val: return 0
        
        val_str = str(val)
        
        if "만원" in val_str:
            clean = re.sub(r'[^0-9.]', '', val_str)
            if clean:
                return float(clean) * 10000
            return 0
        
        if "원" in val_str:
            clean = re.sub(r'[^0-9.]', '', val_str)
            return float(clean) if clean else 0
        
        clean = re.sub(r'[^0-9.]', '', val_str)
        return float(clean) if clean else 0

    vin = str(data.get("vin", ""))
    v_price = to_float(data.get("price", 0))
    v_fee = to_float(data.get("fee", 0))
    
    io_date = datetime.now().strftime("%Y%m%d")
    
    # 최소 필드만 사용한 간단한 payload
    purchase_list = []
    
    # A. 차량대 - 필수 필드만
    if v_price > 0:
        purchase_list.append({
            "BulkDatas": {
                "IO_DATE": io_date,
                "CUST": cust_code,
                "PROD_CD": vin,
                "QTY": 1,
                "PRICE": v_price
            }
        })
    
    # B. 매도비 - 필수 필드만
    if v_fee > 0:
        purchase_list.append({
            "BulkDatas": {
                "IO_DATE": io_date,
                "CUST": cust_code,
                "PROD_CD": vin,
                "QTY": 1,
                "PRICE": v_fee
            }
        })
    
    if len(purchase_list) == 0:
        return {"Status": "400", "Message": "등록할 품목이 없습니다."}
    
    payload = {"PurchaseList": purchase_list}

    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        result = response.json()
        
        result["_DEBUG_INFO"] = {
            "테스트": "최소 필드만 사용",
            "변환_v_price": v_price,
            "변환_v_fee": v_fee,
            "cust_code": cust_code,
            "payload": payload
        }
        
        return result
    except Exception as e:
        return {"Status": "500", "Message": f"구매입력 통신 오류: {str(e)}"}
