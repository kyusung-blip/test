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

def check_item_exists(session_id, prod_cd):
    """
    이카운트에 해당 품목코드(VIN)가 이미 등록되어 있는지 확인합니다.
    """
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/GetListBasicProduct?SESSION_ID={session_id}"
    
    # 검색 조건: 품목코드(PROD_CD)가 입력받은 VIN과 일치하는 것
    payload = {
        "PROD_CD": str(prod_cd)
    }
    
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        
        if str(res_data.get("Status")) == "200":
            # Datas 리스트에 항목이 있으면 이미 존재하는 것임
            items = res_data.get("Data", {}).get("Datas", [])
            if len(items) > 0:
                # 이미 존재하면 True와 해당 품목의 정보를 반환
                return True, items[0]
            return False, None
        else:
            print(f"조회 API 오류: {res_data.get('Message')}")
            return False, None
    except Exception as e:
        print(f"품목 조회 중 통신 오류: {e}")
        return False, None

def check_customer_exists(session_id, biz_num):
    """
    사업자번호(CUST)로 거래처가 이미 등록되어 있는지 확인합니다.
    """
    import re
    cust_code = re.sub(r'[^0-9]', '', str(biz_num)) # 숫자만 추출
    
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/CustomerCenter/GetListCustomer?SESSION_ID={session_id}"
    payload = {
        "CUST": cust_code
    }
    
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        
        if str(res_data.get("Status")) == "200":
            customers = res_data.get("Data", {}).get("Datas", [])
            return len(customers) > 0
        return False
    except:
        return False

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
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/Purchases/SavePurchases?SESSION_ID={session_id}"
    
    import re
    biz_num = str(data.get("biz_num", ""))
    cust_code = re.sub(r'[^0-9]', '', biz_num)
    
    def to_float(val):
        if not val: return 0
        val_str = str(val)
        clean = re.sub(r'[^0-9.]', '', val_str)
        if "만원" in val_str:
            return float(clean) * 10000 if clean else 0
        return float(clean) if clean else 0

    vin = str(data.get("vin", ""))
    v_price = to_float(data.get("price", 0))
    v_fee = to_float(data.get("fee", 0))
    v_contract = to_float(data.get("contract_x", 0))
    io_date = datetime.now().strftime("%Y%m%d")
    
    # h_id 매핑
    h_map = {"seobuk": "001", "inter77": "002", "leeks21": "003"}
    custom_code1 = h_map.get(data.get("h_id", ""), "")

    purchases_list = []
    
    def create_bulk(price_val, memo_suffix=""):
        bulk = {
            "IO_DATE": io_date,
            "CUST": cust_code,
            "EMP_CD": username,
            "WH_CD": "100",
            "PROD_CD": vin,
            "QTY": 1,
            "PRICE": price_val,
            "U_MEMO1": str(data.get("plate", "")),
            "U_MEMO2": vin,
            "U_MEMO3": str(data.get("psource", "")),
            "U_MEMO4": f"{memo_suffix} {data.get('car_name_remit', '')}".strip(),
            "CustomField1": str(data.get("buyer", "")),
            "CustomField2": str(data.get("country", "")),
            "CustomField4": str(data.get("region", "")),
            "CustomField5": str(data.get("year", "")),
            "CustomField6": str(data.get("color", "")),
            "CustomField7": str(data.get("km", "")),
            "CustomField10": str(data.get("brand", ""))
        }
        if custom_code1:
            bulk["CustomCode1"] = custom_code1
        return {"BulkDatas": bulk}

    if v_price > 0: purchases_list.append(create_bulk(v_price))
    if v_fee > 0: purchases_list.append(create_bulk(v_fee, "[매도비]"))
    if v_contract > 0: purchases_list.append(create_bulk(v_contract, "[계산서X]"))

    payload = {"PurchasesList": purchases_list}

    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        # response 자체가 비어있는지 체크
        if not response.text:
            return {"Status": "500", "Message": "이카운트 서버에서 빈 응답을 보냈습니다."}
            
        res_data = response.json()
        
        # 안전한 에러 메시지 추출
        if str(res_data.get("Status")) != "200":
            data_part = res_data.get("Data")
            if data_part and isinstance(data_part, dict):
                errors = data_part.get("Errors", [])
                if errors and len(errors) > 0:
                    res_data["Message"] = errors[0].get("Message", "상세 에러 메시지 없음")

        return res_data
    except Exception as e:
        return {"Status": "500", "Message": f"구매입력 통신 오류: {str(e)}"}
