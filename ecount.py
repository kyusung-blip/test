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
        "ZONE": ZONE 
    }
    try:
        response = requests.post(login_url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        if str(res_data.get("Status")) == "200":
            return res_data["Data"]["Datas"]["SESSION_ID"], None
        else:
            return None, res_data
    except Exception as e:
        return None , {"Status": "500", "Message": str(e)}

def check_item_exists(session_id, prod_cd):
    """품목 존재 여부 확인 (응답 구조 정밀 판독)"""
    # 1. URL 확인 (InventoryBasic 계열)
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/GetListBasicProduct?SESSION_ID={session_id}"
    
    # 2. 검색 조건 (정확한 코드로 검색)
    payload = {"PROD_CD": str(prod_cd)}
    
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        
        if str(res_data.get("Status")) == "200":
            # 이카운트가 돌려준 데이터 리스트 추출
            items = res_data.get("Data", {}).get("Datas", [])
            
            # 리스트를 돌면서 내가 찾는 코드와 100% 일치하는게 있는지 확인
            for item in items:
                if str(item.get("PROD_CD")).strip() == str(prod_cd).strip():
                    return True, item # 찾았음!
            
            return False, None # 리스트는 왔지만 일치하는 코드가 없음
        return False, None
    except Exception:
        return False, None

def register_item(data, session_id, final_spec_no): # 세 번째 인자 이름을 spec_no로 명확히 함
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/SaveBasicProduct?SESSION_ID={session_id}"
    
    prod_name = str(data.get("car_name_remit", "")).strip()
    if not prod_name:
        prod_name = f"미지정차량({data.get('vin')})"

    def to_float(val):
        try:
            if val is None: return 0.0
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    cbm_val = to_float(data.get("v_c", 0))

    payload = {
        "ProductList": [{
            "BulkDatas": {
                "PROD_CD": str(data.get("vin", "")),
                "PROD_DES": prod_name,
                "UNIT": "EA",
                "ADD_TXT_01_T": str(data.get("brand", "")),
                "CONT1": str(final_spec_no),
                "CONT2": str(data.get("plate", "")),
                "CONT3": str(data.get("km", "")),
                "CONT4": str(data.get("color", "")),
                "CONT5": str(data.get("year", "")),
                "ADD_DATE_01_T": datetime.now().strftime("%Y%m%d"),
                "NO_USER2": to_float(data.get("length", 0)), 
                "NO_USER3": to_float(data.get("width", 0)), 
                "NO_USER4": to_float(data.get("height", 0)),
                "NO_USER5": to_float(data.get("weight", 0)),
                "NO_USER6": cbm_val
            }
        }]
    }
    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": str(e)}

def register_customer(data, session_id):
    """신규 거래처 등록 (중복 여부는 buyprogram.py에서 에러 메시지로 판단)"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/AccountBasic/SaveBasicCust?SESSION_ID={session_id}"
    
    biz_num = re.sub(r'[^0-9]', '', str(data.get("biz_num", "")))
    
    payload = {
        "CustList": [{
            "BulkDatas": {
                "CUST": biz_num,
                "CUST_NAME": str(data.get("biz_name", biz_num)),
                "BUSINESS_NO": biz_num,
                "USE_GUBUN": "Y"
            }
        }]
    }
    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"거래처 등록 통신 오류: {str(e)}"}

def register_purchase(data, session_id, username):
    """정리해주신 필드 매핑이 모두 적용된 구매입력 함수"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/Purchases/SavePurchases?SESSION_ID={session_id}"
    
    # 1. 금액 처리 함수
    def to_amt_str(val):
        if not val: return "0"
        clean = re.sub(r'[^0-9.]', '', str(val))
        try:
            num = float(clean)
            if "만원" in str(val): return str(int(num * 10000))
            return str(int(num))
        except: return "0"

    # 2. 추가코드형식1 (ADD_CODE_01_T) 로직 변환
    h_id = data.get("h_id", "")
    h_code = ""
    if h_id == "seobuk": h_code = "001"
    elif h_id == "inter77": h_code = "002"
    elif h_id == "leeks21": h_code = "003"

    # 3. 페이로드 구성
    purchase_data = {
        "PurchasesList": [{
            "BulkDatas": {
                # [기본 정보]
                "IO_DATE": datetime.now().strftime("%Y%m%d"),
                "CUST": re.sub(r'[^0-9]', '', str(data.get("biz_num", ""))),
                "EMP_CD": str(username), # 담당자
                "WH_CD": "100",
                
                # [품목 및 금액]
                "PROD_CD": str(data.get("vin", "")),
                "QTY": "1",
                "PRICE": to_amt_str(data.get("price")),
                "SUPPLY_AMT": to_amt_str(data.get("price")),
                "VAT_AMT": "0",

                # [구매입력 하단 메모 - U_MEMO]
                "U_MEMO1": str(data.get("plate", "")),         # plate
                "U_MEMO2": str(data.get("vin", "")),           # vin
                "U_MEMO3": str(data.get("psource", "")),       # psource
                "U_MEMO4": str(data.get("car_name_remit", "")), # car_name_remit
                "U_MEMO5": str(data.get("sales", "")),         # sales

                # [구매 상단 추가항목 - ADD_TXT]
                "ADD_TXT_01_T": str(data.get("buyer", "")),    # buyer
                "ADD_TXT_02_T": str(data.get("country", "")),  # country
                "ADD_TXT_03_T": "",                            # 빈칸
                "ADD_TXT_04_T": str(data.get("region", "")),   # region
                "ADD_TXT_05_T": str(data.get("year", "")),     # year
                "ADD_TXT_06_T": str(data.get("color", "")),    # color
                "ADD_TXT_07_T": str(data.get("km", "")),       # km
                "ADD_TXT_09_T": "",                            # 빈칸
                "ADD_TXT_10_T": str(data.get("brand", "")),    # brand
                
                # [구매 상단 추가코드]
                "ADD_CODE_01_T": h_code                        # h_id에 따른 코드
            }
        }]
    }

    try:
        response = requests.post(url, json=purchase_data, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신오류: {str(e)}"}

def register_purchase_test(session_id):
    """이카운트 매뉴얼 예시와 100% 동일한 페이로드 테스트"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/Purchases/SavePurchases?SESSION_ID={session_id}"
    
    # 요청하신 예시와 완전히 동일한 구조 (값은 비어있거나 예시값 그대로)
    # 이카운트 매뉴얼 제공 예시 구조와 100% 동일
    payload = {
     "PurchasesList": [{
      "BulkDatas": {
                "IO_DATE": "20260220",     
                "CUST": "1244617538",   
                "PROD_CD":"WVGZZZ5NZLM176975" ,   
                "QTY": "1",         
                "WH_CD": "100",    
                "PRICE": "100000"                
                    }
             }]
        }

    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신 오류: {str(e)}"}

def register_customer_test(session_id):
    """거래처 등록 API 테스트 함수 (알려주신 샌드박스 URL 및 데이터 구조)"""
    # 샌드박스용 sboapi URL 사용
    url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/AccountBasic/SaveBasicCust?SESSION_ID={session_id}"
    
    payload = {
            "CustList": [{
        	    "BulkDatas": {
        		    "BUSINESS_NO": "111111",
        		    "CUST_NAME": "Test Cust",
        		    "BOSS_NAME": "",
        		    "UPTAE": "",
        		    "JONGMOK": "",
        		    "TEL": "",
        		    "EMAIL": "",
        		    "POST_NO": "",
        		    "ADDR": "",
        		    "G_GUBUN": "",
        		    "G_BUSINESS_TYPE": "",
        		    "G_BUSINESS_CD": "",
        		    "TAX_REG_ID": "",
        		    "FAX": "",
        		    "HP_NO": "",
        		    "DM_POST": "",
        		    "DM_ADDR": "",
        		    "REMARKS_WIN": "",
        		    "GUBUN": "",
        		    "FOREIGN_FLAG": "",
        		    "EXCHANGE_CODE": "",
        		    "CUST_GROUP1": "",
        		    "CUST_GROUP2": "",
        		    "URL_PATH": "",
        		    "REMARKS": "",
        		    "OUTORDER_YN": "",
        		    "IO_CODE_SL_BASE_YN": "",
        		    "IO_CODE_SL": "",
        		    "IO_CODE_BY_BASE_YN": "",
        		    "IO_CODE_BY": "",
        		    "EMP_CD": "",
        		    "MANAGE_BOND_NO": "",
        		    "MANAGE_DEBIT_NO": "",
        		    "CUST_LIMIT": "",
        		    "O_RATE": "",
        		    "I_RATE": "",
        		    "PRICE_GROUP": "",
        		    "PRICE_GROUP2": "",
        		    "CUST_LIMIT_TERM": "",
        		    "CONT1": "",
        		    "CONT2": "",
        		    "CONT3": "",
        		    "CONT4": "",
        		    "CONT5": "",
        		    "CONT6": "",
        		    "NO_CUST_USER1": "",
        		    "NO_CUST_USER2": "",
        		    "NO_CUST_USER3": ""
        	    }
        	}]
        }
    
    try:
        # 샌드박스 서버는 인증서가 불안정할 수 있으므로 verify=False 유지
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"테스트 통신 오류: {str(e)}"}
