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
    """구매 입력 (표준 필드 구조)"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/Purchases/SavePurchases?SESSION_ID={session_id}"
    
    biz_num = str(data.get("biz_num", ""))
    cust_code = re.sub(r'[^0-9]', '', biz_num)
    
    def to_amt_str(val):
        if not val: return "0"
        val_str = str(val)
        clean = re.sub(r'[^0-9.]', '', val_str)
        if "만원" in val_str:
            return str(int(float(clean) * 10000)) if clean else "0"
        return str(int(float(clean))) if clean else "0"

    vin = str(data.get("vin", ""))
    io_date = datetime.now().strftime("%Y%m%d")

    def create_bulk(price_val, memo_suffix=""):
        return {
            "BulkDatas": {
                "ORD_DATE": "", "ORD_NO": "", "IO_DATE": io_date, "UPLOAD_SER_NO": "",
                "CUST": cust_code, "CUST_DES": "", "EMP_CD": "", "WH_CD": "100",
                "IO_TYPE": "", "EXCHANGE_TYPE": "", "EXCHANGE_RATE": "", "SITE": "",
                "PJT_CD": "", "DOC_NO": "", 
                "U_MEMO1": str(data.get("plate", "")), "U_MEMO2": vin,
                "U_MEMO3": str(data.get("psource", "")),
                "U_MEMO4": f"{memo_suffix} {data.get('car_name_remit', '')}".strip(),
                "U_MEMO5": str(data.get("sales", "")),
                "PROD_CD": vin, "QTY": "1", "PRICE": price_val,
                "SUPPLY_AMT": price_val, "VAT_AMT": "0",
                "CustomField4": str(data.get("region", "")),
                "CustomField5": str(data.get("year", "")),
                "CustomField6": str(data.get("color", "")),
                "CustomField7": str(data.get("km", "")),
                "CustomField10": str(data.get("brand", ""))
            }
        }

    purchases_list = []
    p_val = to_amt_str(data.get("price"))
    if p_val != "0": purchases_list.append(create_bulk(p_val))
    f_val = to_amt_str(data.get("fee"))
    if f_val != "0": purchases_list.append(create_bulk(f_val, "[매도비]"))
    c_val = to_amt_str(data.get("contract_x"))
    if c_val != "0": purchases_list.append(create_bulk(c_val, "[계산서X]"))

    if not purchases_list:
        return {"Status": "400", "Message": "전송 데이터 없음"}

    try:
        response = requests.post(url, json={"PurchasesList": purchases_list}, verify=False, timeout=15)
        res_data = response.json()
        if str(res_data.get("Status")) != "200":
            errs = res_data.get("Data", {}).get("Errors", [])
            if errs: res_data["Message"] = errs[0].get("Message")
        return res_data
    except Exception as e:
        return {"Status": "500", "Message": f"통신오류: {str(e)}"}
