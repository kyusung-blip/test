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
    """이카운트 구매입력(전표) 저장 API - 다중 품목 대응"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/Purchases/SavePurchases?SESSION_ID={session_id}"
    
    import re
    # 1. 거래처 번호 정제
    biz_num = str(data.get("biz_num", ""))
    cust_code = re.sub(r'[^0-9]', '', biz_num)
    
    # 2. h_id 매핑
    h_map = {"seobuk": "001", "inter77": "002", "leeks21": "003"}
    custom_code1 = h_map.get(data.get("h_id", ""), "")
    
    # 3. 숫자 변환 유틸리티
    def to_float(val):
        if not val: return 0
        clean = re.sub(r'[^0-9.]', '', str(val))
        return float(clean) if clean else 0

    vin = str(data.get("vin", ""))
        # 🔍 디버깅: 기본 데이터 확인
    print("=" * 50)
    print("구매입력 전송 데이터 확인:")
    print(f"거래처번호(원본): {biz_num}")
    print(f"거래처코드(정제): {cust_code}")
    print(f"VIN: {vin}")
    print(f"username: {username}")
    print(f"h_id: {data.get('h_id')} → CustomCode1: {custom_code1}")
    print(f"price: {data.get('price')} → {to_float(data.get('price', 0))}")
    print(f"fee: {data.get('fee')} → {to_float(data.get('fee', 0))}")
    print(f"contract_x: {data.get('contract_x')} → {to_float(data.get('contract_x', 0))}")
    print("=" * 50)
    purchase_list = []

    # --- 하단 품목 구성 로직 ---
    
    # A. 차량대 (Price)
    v_price = to_float(data.get("price", 0))
    if v_price > 0:
        purchase_list.append({
            "BulkDatas": {
                "IO_DATE": datetime.now().strftime("%Y%m%d"),
                "CUST": cust_code,
                "PROD_CD": vin,
                "QTY": 1,
                "PRICE": v_price,
                "EMP_CD": username,
                "U_MEMO1": str(data.get("plate", "")),
                "U_MEMO2": vin,
                "U_MEMO3": str(data.get("psource", "")),
                "U_MEMO4": str(data.get("car_name_remit", "")),
                "U_MEMO5": str(data.get("sales", "")),
                "CustomField1": str(data.get("buyer", "")),
                "CustomField2": str(data.get("country", "")),
                "CustomField4": str(data.get("region", "")),
                "CustomField5": str(data.get("year", "")),
                "CustomField6": str(data.get("color", "")),
                "CustomField7": str(data.get("km", "")),
                "CustomField10": str(data.get("brand", "")),
                "CustomCode1": custom_code1
            }
        })

    # B. 매도비 (Fee)
    v_fee = to_float(data.get("fee", 0))
    if v_fee > 0:
        purchase_list.append({
            "BulkDatas": {
                "IO_DATE": datetime.now().strftime("%Y%m%d"),
                "CUST": cust_code,
                "PROD_CD": vin,
                "QTY": 1,
                "PRICE": v_fee, # 매도비는 단가에 입력
                "EMP_CD": username,
                "U_MEMO1": str(data.get("plate", "")),
                "U_MEMO2": vin,
                "U_MEMO4": f"[매도비] {data.get('car_name_remit', '')}"
            }
        })

    # C. 계산서X (Contract_x)
    v_contract = to_float(data.get("contract_x", 0))
    if v_contract > 0:
        purchase_list.append({
            "BulkDatas": {
                "IO_DATE": datetime.now().strftime("%Y%m%d"),
                "CUST": cust_code,
                "PROD_CD": vin,
                "QTY": 1,
                "SUPPLY_AMT": v_contract, # 계산서X는 공급가액에 직접 입력
                "EMP_CD": username,
                "U_MEMO1": str(data.get("plate", "")),
                "U_MEMO2": vin,
                "U_MEMO4": f"[계산서X] {data.get('car_name_remit', '')}"
            }
        })

    payload = {"PurchaseList": purchase_list}
        # 🔍 디버깅: 최종 Payload 확인
    print(f"전송할 품목 수: {len(purchase_list)}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("=" * 50)

    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        result = response.json()
        
        # 🔍 디버깅: 응답 확인
        print(f"응답 Status: {result.get('Status')}")
        print(f"응답 Data: {json.dumps(result.get('Data', {}), indent=2, ensure_ascii=False)}")
        print("=" * 50)
        
        return result
    except Exception as e:
        error_result = {"Status": "500", "Message": f"구매입력 통신 오류: {str(e)}"}
        print(f"❌ 오류 발생: {error_result}")
        return error_result
