import requests
import json
from datetime import datetime
import urllib3
import re

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# [설정] 발급받으신 정보
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "2dac8e71fcd314e77af2ce35eb89185442"
ZONE = "AD" 

def get_session_id():
    """세션 획득"""
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
    except Exception:
        return None

def check_item_exists(session_id, prod_cd):
    """품목 존재 여부 확인"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/GetListBasicProduct?SESSION_ID={session_id}"
    payload = {"PROD_CD": str(prod_cd)}
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        if str(res_data.get("Status")) == "200":
            items = res_data.get("Data", {}).get("Datas", [])
            return len(items) > 0, items[0] if items else None
        return False, None
    except Exception:
        return False, None

def check_customer_exists(session_id, biz_num):
    """거래처 존재 여부 확인"""
    cust_code = re.sub(r'[^0-9]', '', str(biz_num))
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/CustomerCenter/GetListCustomer?SESSION_ID={session_id}"
    payload = {"CUST": cust_code}
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        if str(res_data.get("Status")) == "200":
            customers = res_data.get("Data", {}).get("Datas", [])
            return len(customers) > 0
        return False
    except Exception:
        return False

def register_item(data, session_id, sheet_no):
    """신규 품목 등록"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/SaveBasicProduct?SESSION_ID={session_id}"
    
    def to_float(val):
        try:
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    l, w, h = to_float(data.get("length")), to_float(data.get("width")), to_float(data.get("height"))
    cmb_val = (l / 1000) * (w / 1000) * (h / 1000)

    payload = {
        "ProductList": [{
            "BulkDatas": {
                "PROD_CD": str(data.get("vin", "")),
                "PROD_DES": str(data.get("car_name_remit", "")),
                "UNIT": "EA",
                "ADD_TXT_01_T": str(data.get("brand", "")),
                "CONT1": str(sheet_no),
                "CONT2": str(data.get("plate", "")),
                "CONT3": str(data.get("km", "")),
                "CONT4": str(data.get("color", "")),
                "CONT5": str(data.get("year", "")),
                "ADD_DATE_01_T": datetime.now().strftime("%Y%m%d"),
                "NO_USER2": l, "NO_USER3": w, "NO_USER4": h,
                "NO_USER6": round(cmb_val, 4)
            }
        }]
    }
    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": str(e)}

def register_purchase(data, session_id, username):
    """구매 입력 (이카운트 API 필수 항목 준수 버전)"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/Purchases/SavePurchases?SESSION_ID={session_id}"
    
    # [필수 1] CUST_CODE (구매처 코드): 사업자번호에서 숫자만 추출
    # 주의: 이 코드는 반드시 이카운트 거래처 등록에 미리 존재해야 합니다.
    biz_num = str(data.get("biz_num", ""))
    cust_code = re.sub(r'[^0-9]', '', biz_num)
    
    # [필수 2] IO_DATE (입고일자): YYYYMMDD 형식
    io_date = datetime.now().strftime("%Y%m%d")

    # [필수 3] PROD_CD (품목코드): 차대번호(vin) 사용
    # 주의: 이 코드는 반드시 이카운트 품목 등록에 미리 존재해야 합니다.
    vin = str(data.get("vin", ""))
    
    # 금액 변환 함수
    def to_amt_int(val):
        if not val: return 0
        clean = re.sub(r'[^0-9.]', '', str(val))
        try:
            num = float(clean)
            if "만원" in str(val): return int(num * 10000)
            return int(num)
        except: return 0

    # BulkDatas 생성 함수 (필수 항목 포함)
    def create_bulk(price_val, memo_suffix=""):
        return {
            "BulkDatas": {
                "IO_DATE": io_date,      # [필수] 입고일자 (YYYYMMDD)
                "CUST": cust_code,       # [필수] 거래처코드
                "PROD_CD": vin,          # [필수] 품목코드
                "QTY": "1",               # [필수] 수량 (양수)
                "WH_CD": "100",          # [선택이나 권장] 창고코드
                "PRICE": str(price_val), # 단가
                "SUPPLY_AMT": str(price_val), # 공급가액
                "VAT_AMT": "0",          # 부가세
                "U_MEMO2": vin,          # 메모 등 (차대번호)
                "U_MEMO4": f"{memo_suffix} {data.get('car_name_remit', '')}".strip()
            }
        }

    # [필수 4] PURCHASE_LIST 내부 BulkDatas는 하나 이상이어야 함
    purchases_list = []
    
    # 각 금액 항목별로 데이터 생성
    p_val = to_amt_int(data.get("price"))
    if p_val > 0: purchases_list.append(create_bulk(p_val))
    
    f_val = to_amt_int(data.get("fee"))
    if f_val > 0: purchases_list.append(create_bulk(f_val, "[매도비]"))
    
    c_val = to_amt_int(data.get("contract_x"))
    if c_val > 0: purchases_list.append(create_bulk(c_val, "[계산서X]"))

    # 최종 유효성 검사
    if not purchases_list:
        return {"Status": "400", "Message": "등록할 품목/금액 데이터가 없습니다. (QTY가 0인 상태)"}
    
    if not cust_code:
        return {"Status": "400", "Message": "거래처 코드(사업자번호)가 없습니다."}
        
    if not vin:
        return {"Status": "400", "Message": "품목 코드(차대번호)가 없습니다."}

    try:
        # API 요청 데이터 전송
        response = requests.post(url, json={"PurchasesList": purchases_list}, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신오류: {str(e)}"}
