"""
차량 매입 관리 시스템 (Vehicle Purchase Management System)
Complete Streamlit web application for managing vehicle purchases
"""

import streamlit as st
import xmlrpc.client
import gspread
from google.oauth2.service_account import Credentials as GoogleCredentials
import google.generativeai as genai
import requests
import base64
from PIL import Image
import io
import json
import re
import os
from datetime import datetime
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================================
# CONSTANTS AND DATA MAPS
# ============================================================================

VINYEAR_map = {
    'A': '2010', 'B': '2011', 'C': '2012', 'D': '2013', 'E': '2014',
    'F': '2015', 'G': '2016', 'H': '2017', 'J': '2018', 'K': '2019',
    'L': '2020', 'M': '2021', 'N': '2022', 'P': '2023', 'R': '2024',
    'S': '2025', 'T': '2026', 'V': '2027', 'W': '2028', 'X': '2029',
    'Y': '2030'
}

color_map = {
    '검정': '블랙', '검은색': '블랙', '흑색': '블랙', '진주흑색': '블랙',
    '흰색': '화이트', '백색': '화이트', '진주백색': '화이트', '크림': '화이트',
    '은색': '실버', '은백색': '실버',
    '짙은회색': '회색', '회색': '그레이',
    '빨강': '레드', '빨간색': '레드',
    '주황': '오렌지',
    '노랑': '옐로우',
    '파랑': '블루', '파란색': '블루', '남색': '네이비', '청색': '블루',
    '베이지': '베이지',
    '갈색': '브라운', '밤색': '브라운'
}

ADDRESS_REGION_MAP = {
    '서울': '서울', '부산': '부산', '대구': '대구', '인천': '인천',
    '광주': '광주', '대전': '대전', '울산': '울산', '세종': '세종',
    '경기': '경기', '강원': '강원', '충북': '충북', '충남': '충남',
    '전북': '전북', '전남': '전남', '경북': '경북', '경남': '경남',
    '제주': '제주'
}

sales_map = {
    '이규성': 'KS',
    '김동현': 'DH',
    '신동호': 'SH',
    '홍길동': 'HG'
}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    default_values = {
        # Basic info
        'plate': '',
        'vin': '',
        'car_name': '',
        'car_name_alt': '',
        'brand': '',
        'year': '',
        'km': '',
        'color': '',
        
        # Dealer info
        'phone': '',
        'address': '',
        'business_num': '',
        'company': '',
        
        # Account info
        'vehicle_account': '',
        'fee_account': '',
        'remitter_name': '',
        
        # Buyer info
        'buyer_name': '',
        'buyer_country': '',
        
        # Amount info
        'price': '',
        'fee': '',
        'invoice_x': '',
        'total': '',
        'deposit': '',
        'balance': '',
        'declaration': '',
        
        # Autowini info
        'autowini_company': '',
        'exchange_date': '',
        'exchange_rate': '',
        'usd_price': '',
        'zero_rate': '',
        
        # HeyDealer info
        'heydealer_type': '',
        'heydealer_id': '',
        'delivery': '',
        
        # Site/sales
        'site': '',
        'sales_team': '',
        
        # Auction info
        'region': '',
        'session': '',
        'number': '',
        
        # Cache and state
        'car_name_map_cache': {},
        'cache_last_load': None,
        'output_message': '',
        'dealer_update_mode': False,
        
        # Sidebar selections
        'auction_type': '선택 안함',
        'heydealer_type_select': '선택 안함',
        'heydealer_id_select': '선택 안함',
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================================================================
# CORE UTILITY FUNCTIONS
# ============================================================================

def parse_money(text):
    """Parse Korean currency format (만원, 억) to number"""
    if not text:
        return 0
    
    text = str(text).strip().replace(',', '').replace(' ', '')
    
    # Remove non-numeric characters except 억, 만, decimal point
    text = re.sub(r'[^\d억만.]', '', text)
    
    result = 0
    
    # Handle 억 (100 million)
    if '억' in text:
        parts = text.split('억')
        eok = float(parts[0]) if parts[0] else 0
        result += eok * 100000000
        text = parts[1] if len(parts) > 1 else ''
    
    # Handle 만 (10 thousand)
    if '만' in text:
        parts = text.split('만')
        man = float(parts[0]) if parts[0] else 0
        result += man * 10000
        text = parts[1] if len(parts) > 1 else ''
    
    # Handle remaining number
    if text:
        result += float(text)
    
    return int(result)

def format_number(num, use_korean=True):
    """Format number with Korean units (억, 만) or commas"""
    try:
        num = int(float(num))
    except (ValueError, TypeError):
        return '0'
    
    if not use_korean:
        return f"{num:,}"
    
    if num == 0:
        return '0'
    
    eok = num // 100000000
    remainder = num % 100000000
    man = remainder // 10000
    won = remainder % 10000
    
    parts = []
    if eok > 0:
        parts.append(f"{eok}억")
    if man > 0:
        parts.append(f"{man}만")
    if won > 0 or not parts:
        parts.append(f"{won}")
    
    return ' '.join(parts)

def detect_brand_from_vin(vin):
    """Auto-detect vehicle brand from VIN"""
    if not vin or len(vin) < 3:
        return ''
    
    vin = vin.upper()[:3]
    
    brand_map = {
        'KMH': '현대', 'KM8': '현대', 'KNA': '기아', 'KNE': '기아',
        'KNC': '기아', 'KND': '기아', 'MAL': '쉐보레', 'KL1': '쉐보레',
        'KL4': '쉐보레', 'Z6F': '기아', 'NLE': '르노삼성',
        'Y6D': '르노코리아', 'U5Y': '쌍용', 'U6Y': '쌍용'
    }
    
    return brand_map.get(vin, '')

def detect_vin_year(vin):
    """Extract year from VIN using 10th character"""
    if not vin or len(vin) < 10:
        return ''
    
    year_code = vin[9].upper()
    return VINYEAR_map.get(year_code, '')

def detect_region_from_address(address):
    """Extract region from address"""
    if not address:
        return ''
    
    for region_key, region_value in ADDRESS_REGION_MAP.items():
        if region_key in address:
            return region_value
    
    return ''

def normalize_color(color):
    """Normalize color names using color_map"""
    if not color:
        return ''
    
    return color_map.get(color, color)

def detect_alt_car_name(car_name):
    """Map car names using Google Sheets cache"""
    if not car_name:
        return ''
    
    # Load cache if needed
    if not st.session_state.car_name_map_cache or \
       not st.session_state.cache_last_load or \
       (datetime.now() - st.session_state.cache_last_load).seconds > 3600:
        try:
            sheet = get_google9_sheet()
            if sheet:
                records = sheet.get_all_records()
                cache = {}
                for record in records:
                    original = record.get('원본차명', '')
                    mapped = record.get('변환차명', '')
                    if original and mapped:
                        cache[original] = mapped
                st.session_state.car_name_map_cache = cache
                st.session_state.cache_last_load = datetime.now()
        except Exception as e:
            st.error(f"차명 매핑 로드 오류: {e}")
    
    return st.session_state.car_name_map_cache.get(car_name, car_name)

def fill_entries_from_input(paste_data):
    """Parse tab-separated data and fill entries"""
    if not paste_data:
        return
    
    lines = paste_data.strip().split('\n')
    for line in lines:
        parts = line.split('\t')
        
        if len(parts) >= 8:
            st.session_state.plate = parts[0].strip() if len(parts) > 0 else ''
            st.session_state.vin = parts[1].strip().upper() if len(parts) > 1 else ''
            st.session_state.car_name = parts[2].strip() if len(parts) > 2 else ''
            st.session_state.year = parts[3].strip() if len(parts) > 3 else ''
            st.session_state.km = parts[4].strip() if len(parts) > 4 else ''
            st.session_state.color = parts[5].strip() if len(parts) > 5 else ''
            st.session_state.price = parts[6].strip() if len(parts) > 6 else ''
            st.session_state.fee = parts[7].strip() if len(parts) > 7 else ''
            
            # Auto-detect brand and year from VIN
            if st.session_state.vin:
                st.session_state.brand = detect_brand_from_vin(st.session_state.vin)
                if not st.session_state.year:
                    st.session_state.year = detect_vin_year(st.session_state.vin)
            
            # Normalize color
            if st.session_state.color:
                st.session_state.color = normalize_color(st.session_state.color)

def calculate_balance():
    """Calculate remaining balance (total - deposit)"""
    try:
        total = parse_money(st.session_state.total)
        deposit = parse_money(st.session_state.deposit)
        balance = total - deposit
        st.session_state.balance = format_number(balance)
    except:
        st.session_state.balance = '0'

def update_declaration():
    """Auto-calculate 10% declaration from price"""
    try:
        price = parse_money(st.session_state.price)
        declaration = int(price * 0.1)
        st.session_state.declaration = format_number(declaration)
    except:
        st.session_state.declaration = '0'

def calculate_total():
    """Sum price + fee + invoice_x"""
    try:
        price = parse_money(st.session_state.price)
        fee = parse_money(st.session_state.fee)
        invoice_x = parse_money(st.session_state.invoice_x)
        total = price + fee + invoice_x
        st.session_state.total = format_number(total)
        calculate_balance()
    except:
        st.session_state.total = '0'

# ============================================================================
# GOOGLE SHEETS INTEGRATION
# ============================================================================

@st.cache_resource
def get_gspread_client():
    """Get authenticated gspread client"""
    try:
        # Try secrets first
        if 'gcp_service_account' in st.secrets:
            credentials_dict = dict(st.secrets['gcp_service_account'])
        elif 'GCP_SERVICE_KEY' in os.environ:
            credentials_dict = json.loads(os.environ['GCP_SERVICE_KEY'])
        else:
            st.error("Google Sheets 인증 정보가 없습니다.")
            return None
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = GoogleCredentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )
        
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Google Sheets 인증 오류: {e}")
        return None

def get_google_sheet(spreadsheet_name, worksheet_name):
    """Generic sheet accessor"""
    try:
        client = get_gspread_client()
        if not client:
            return None
        
        spreadsheet = client.open(spreadsheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        return worksheet
    except Exception as e:
        st.error(f"시트 접근 오류 ({spreadsheet_name}/{worksheet_name}): {e}")
        return None

def get_google2_sheet():
    """Inventory SEOBUK Yard Status"""
    return get_google_sheet('Inventory SEOBUK', 'Yard Status')

def get_google3_sheet():
    """SEOBUK BUYER Sheet1"""
    return get_google_sheet('SEOBUK BUYER', 'Sheet1')

def get_google4_sheet():
    """SEOBUK COMPANY Company Info"""
    return get_google_sheet('SEOBUK COMPANY', 'Company Info')

def get_google8_sheet():
    """Inventory SEOBUK 2025"""
    return get_google_sheet('Inventory SEOBUK', '2025')

def get_google9_sheet():
    """SEOBUK CAR NAMES Mapping"""
    return get_google_sheet('SEOBUK CAR NAMES', 'Mapping')

def get_dealer_sheet():
    """SEOBUK DEALER Sheet1"""
    return get_google_sheet('SEOBUK DEALER', 'Sheet1')

def 계좌확인(phone):
    """Lookup dealer by phone from SEOBUK DEALER"""
    try:
        sheet = get_dealer_sheet()
        if not sheet:
            return None
        
        records = sheet.get_all_records()
        for record in records:
            if str(record.get('전화번호', '')).replace('-', '') == phone.replace('-', ''):
                return {
                    'company': record.get('상호', ''),
                    'business_num': record.get('사업자번호', ''),
                    'vehicle_account': record.get('차량계좌', ''),
                    'fee_account': record.get('수수료계좌', ''),
                    'remitter_name': record.get('송금자명', '')
                }
        return None
    except Exception as e:
        st.error(f"계좌 확인 오류: {e}")
        return None

def 계좌업데이트(phone, company, business_num, vehicle_account, fee_account, remitter_name):
    """Update dealer info"""
    try:
        sheet = get_dealer_sheet()
        if not sheet:
            return False
        
        # Find existing record
        records = sheet.get_all_records()
        row_num = None
        
        for idx, record in enumerate(records, start=2):
            if str(record.get('전화번호', '')).replace('-', '') == phone.replace('-', ''):
                row_num = idx
                break
        
        # Update or append
        data = [phone, company, business_num, vehicle_account, fee_account, remitter_name]
        
        if row_num:
            sheet.update(f'A{row_num}:F{row_num}', [data])
        else:
            sheet.append_row(data)
        
        return True
    except Exception as e:
        st.error(f"계좌 업데이트 오류: {e}")
        return False

def 확인버튼_동작(buyer_name):
    """Lookup buyer country from SEOBUK BUYER"""
    try:
        sheet = get_google3_sheet()
        if not sheet:
            return None
        
        records = sheet.get_all_records()
        for record in records:
            if record.get('바이어명', '') == buyer_name:
                return record.get('국가', '')
        return None
    except Exception as e:
        st.error(f"바이어 확인 오류: {e}")
        return None

def check_vin_duplicate(vin):
    """Check VIN in inventory sheets"""
    if not vin:
        return False
    
    try:
        sheets = [get_google2_sheet(), get_google8_sheet()]
        
        for sheet in sheets:
            if not sheet:
                continue
            
            records = sheet.get_all_records()
            for record in records:
                if str(record.get('VIN', '')).upper() == vin.upper():
                    return True
        
        return False
    except Exception as e:
        st.error(f"VIN 중복 확인 오류: {e}")
        return False

def 등록_통합_처리():
    """Register to both inventory sheets with VIN check"""
    try:
        # Check VIN duplicate
        if check_vin_duplicate(st.session_state.vin):
            st.error(f"중복된 VIN이 존재합니다: {st.session_state.vin}")
            return False
        
        # Prepare data
        row_data = [
            st.session_state.plate,
            st.session_state.vin,
            st.session_state.car_name,
            st.session_state.car_name_alt,
            st.session_state.brand,
            st.session_state.year,
            st.session_state.km,
            st.session_state.color,
            st.session_state.price,
            st.session_state.fee,
            st.session_state.company,
            st.session_state.buyer_name,
            st.session_state.buyer_country,
            st.session_state.sales_team,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        # Register to Yard Status
        sheet2 = get_google2_sheet()
        if sheet2:
            sheet2.append_row(row_data)
        
        # Register to 2025
        sheet8 = get_google8_sheet()
        if sheet8:
            sheet8.append_row(row_data)
        
        st.success("재고 등록 완료!")
        return True
    except Exception as e:
        st.error(f"재고 등록 오류: {e}")
        return False

# ============================================================================
# ODOO ERP INTEGRATION
# ============================================================================

def insert_ODOO():
    """Insert to Odoo seobuk.car model"""
    try:
        # Get credentials
        if 'odoo' in st.secrets:
            url = st.secrets['odoo']['url']
            db = st.secrets['odoo']['db']
            username = st.secrets['odoo']['username']
            password = st.secrets['odoo']['password']
        else:
            url = os.environ.get('ODOO_URL', '')
            db = os.environ.get('ODOO_DB', '')
            username = os.environ.get('ODOO_USER', '')
            password = os.environ.get('ODOO_PASSWORD', '')
        
        if not all([url, db, username, password]):
            st.error("Odoo 인증 정보가 없습니다.")
            return False
        
        # Authenticate
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            st.error("Odoo 인증 실패")
            return False
        
        # Prepare data
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        values = {
            'plate_number': st.session_state.plate,
            'vin': st.session_state.vin,
            'car_name': st.session_state.car_name,
            'brand': st.session_state.brand,
            'year': st.session_state.year,
            'mileage': st.session_state.km,
            'color': st.session_state.color,
            'price': parse_money(st.session_state.price),
            'fee': parse_money(st.session_state.fee),
            'company': st.session_state.company,
            'buyer_name': st.session_state.buyer_name,
            'buyer_country': st.session_state.buyer_country,
        }
        
        # Create record
        record_id = models.execute_kw(
            db, uid, password,
            'seobuk.car', 'create',
            [values]
        )
        
        st.success(f"Odoo 입력 완료! (ID: {record_id})")
        return True
    except Exception as e:
        st.error(f"Odoo 입력 오류: {e}")
        return False

# ============================================================================
# MESSAGE GENERATION
# ============================================================================

def handle_confirm(confirm_type):
    """Generate confirmation messages"""
    messages = {
        'inspector': f"""[검수 확인]
차량번호: {st.session_state.plate}
차명: {st.session_state.car_name}
VIN: {st.session_state.vin}
연식: {st.session_state.year}
주행거리: {st.session_state.km}km
색상: {st.session_state.color}

검수 부탁드립니다.""",

        'sales': f"""[영업 확인]
차량: {st.session_state.car_name}
연식: {st.session_state.year}
가격: {st.session_state.price}
바이어: {st.session_state.buyer_name}
국가: {st.session_state.buyer_country}

확인 부탁드립니다.""",

        'outsourcing': f"""[외주 요청]
차량번호: {st.session_state.plate}
차명: {st.session_state.car_name}
VIN: {st.session_state.vin}
작업: 검수 및 정비

진행 부탁드립니다.""",

        'share_address': f"""[주소 공유]
업체: {st.session_state.company}
주소: {st.session_state.address}
연락처: {st.session_state.phone}

확인 부탁드립니다."""
    }
    
    st.session_state.output_message = messages.get(confirm_type, '')

def extract_message(msg_type):
    """Generate remittance messages"""
    if msg_type == 'regular':
        msg = f"""[송금 안내]
차량: {st.session_state.car_name} ({st.session_state.plate})
차량대금: {st.session_state.price}
수수료: {st.session_state.fee}
합계: {st.session_state.total}

차량대금 계좌: {st.session_state.vehicle_account}
수수료 계좌: {st.session_state.fee_account}
송금자명: {st.session_state.remitter_name}

송금 부탁드립니다."""

    elif msg_type == 'scrap':
        msg = f"""[폐차 송금 안내]
차량: {st.session_state.car_name} ({st.session_state.plate})
폐차대금: {st.session_state.price}

계좌: {st.session_state.vehicle_account}
송금자명: {st.session_state.remitter_name}"""

    elif msg_type == 'down_payment':
        msg = f"""[계약금 송금 안내]
차량: {st.session_state.car_name} ({st.session_state.plate})
총 금액: {st.session_state.total}
계약금: {st.session_state.deposit}
잔금: {st.session_state.balance}

계좌: {st.session_state.vehicle_account}
송금자명: {st.session_state.remitter_name}"""

    elif msg_type == 'autowini':
        msg = f"""[오토위니 송금 안내]
차량: {st.session_state.car_name}
업체: {st.session_state.autowini_company}
USD 가격: ${st.session_state.usd_price}
환율({st.session_state.exchange_date}): {st.session_state.exchange_rate}
제로금리: {st.session_state.zero_rate}%

송금 부탁드립니다."""

    elif msg_type == 'heydealer':
        msg = f"""[헤이딜러 송금 안내]
차량: {st.session_state.car_name} ({st.session_state.plate})
타입: {st.session_state.heydealer_type}
ID: {st.session_state.heydealer_id}
배송: {st.session_state.delivery}
금액: {st.session_state.total}

송금 부탁드립니다."""
    
    else:
        msg = ''
    
    st.session_state.output_message = msg

def show_entry_info():
    """Warehouse entry message"""
    msg = f"""[입고 정보]
일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}
차량번호: {st.session_state.plate}
차명: {st.session_state.car_name}
VIN: {st.session_state.vin}
연식: {st.session_state.year}
색상: {st.session_state.color}
주행거리: {st.session_state.km}km

입고 완료되었습니다."""
    
    st.session_state.output_message = msg

def handle_auction_output_unified():
    """Auction output message"""
    msg = f"""[경매 출고]
경매사: {st.session_state.auction_type}
지역: {st.session_state.region}
회차: {st.session_state.session}
번호: {st.session_state.number}

차량번호: {st.session_state.plate}
차명: {st.session_state.car_name}
VIN: {st.session_state.vin}
연식: {st.session_state.year}
주행거리: {st.session_state.km}km

출고 완료되었습니다."""
    
    st.session_state.output_message = msg

def send_document_text():
    """Document guidance message"""
    msg = f"""[서류 안내]
차량번호: {st.session_state.plate}

필요 서류:
1. 자동차등록증
2. 인감증명서
3. 양도증명서
4. 위임장
5. 사업자등록증 사본

업체: {st.session_state.company}
연락처: {st.session_state.phone}

서류 준비 부탁드립니다."""
    
    st.session_state.output_message = msg

# ============================================================================
# OCR FUNCTIONALITY
# ============================================================================

def handle_paste_auction_image(image_file):
    """Gemini API OCR for auction images"""
    try:
        # Get API key
        if 'gemini' in st.secrets and 'api_key' in st.secrets['gemini']:
            api_key = st.secrets['gemini']['api_key']
        else:
            api_key = os.environ.get('GEMINI_API_KEY', '')
        
        if not api_key:
            st.error("Gemini API 키가 없습니다.")
            return
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load image
        image = Image.open(image_file)
        
        # Create prompt
        prompt = """이 경매 이미지에서 다음 정보를 추출해주세요:
- 차명 (car_name)
- 차량번호 (plate)
- VIN
- 낙찰가 (price)
- 수수료 (fee)
- 합계 (total)
- 업체명 (company)
- 계좌번호 (account)
- 지역 (region)
- 회차 (session)

JSON 형식으로 응답해주세요."""
        
        # Generate content
        response = model.generate_content([prompt, image])
        
        # Parse response
        if response.text:
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                # Fill fields
                if 'car_name' in data:
                    st.session_state.car_name = data['car_name']
                if 'plate' in data:
                    st.session_state.plate = data['plate']
                if 'vin' in data:
                    st.session_state.vin = data['vin'].upper()
                    st.session_state.brand = detect_brand_from_vin(st.session_state.vin)
                    st.session_state.year = detect_vin_year(st.session_state.vin)
                if 'price' in data:
                    st.session_state.price = str(data['price'])
                if 'fee' in data:
                    st.session_state.fee = str(data['fee'])
                if 'total' in data:
                    st.session_state.total = str(data['total'])
                if 'company' in data:
                    st.session_state.company = data['company']
                if 'account' in data:
                    st.session_state.vehicle_account = data['account']
                if 'region' in data:
                    st.session_state.region = data['region']
                if 'session' in data:
                    st.session_state.session = data['session']
                
                calculate_total()
                update_declaration()
                
                st.success("OCR 완료!")
            else:
                st.warning("JSON 파싱 실패. 응답: " + response.text)
    except Exception as e:
        st.error(f"OCR 오류: {e}")

# ============================================================================
# EXCHANGE RATE SCRAPING
# ============================================================================

def get_exchange_rate():
    """Selenium scraping from Woori Bank"""
    try:
        with st.spinner('환율 조회 중...'):
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # Setup driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                # Navigate to Woori Bank exchange rate page
                driver.get('https://spot.wooribank.com/pot/Dream?withyou=FXXRT0016')
                
                # Wait for exchange rate element
                wait = WebDriverWait(driver, 10)
                element = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'USD')]"))
                )
                
                # Find exchange rate in the same row
                parent_row = element.find_element(By.XPATH, './..')
                rate_element = parent_row.find_element(By.XPATH, ".//td[3]")
                rate = rate_element.text.strip().replace(',', '')
                
                # Update session state
                st.session_state.exchange_rate = rate
                st.session_state.exchange_date = datetime.now().strftime('%Y-%m-%d')
                
                st.success(f"환율 조회 완료: {rate}원")
                
            finally:
                driver.quit()
                
    except Exception as e:
        st.error(f"환율 조회 오류: {e}")

# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================

def reset_all_fields():
    """Reset all form fields"""
    fields_to_reset = [
        'plate', 'vin', 'car_name', 'car_name_alt', 'brand', 'year', 'km', 'color',
        'phone', 'address', 'business_num', 'company',
        'vehicle_account', 'fee_account', 'remitter_name',
        'buyer_name', 'buyer_country',
        'price', 'fee', 'invoice_x', 'total', 'deposit', 'balance', 'declaration',
        'autowini_company', 'exchange_date', 'exchange_rate', 'usd_price', 'zero_rate',
        'heydealer_type', 'heydealer_id', 'delivery',
        'site', 'sales_team',
        'region', 'session', 'number'
    ]
    
    for field in fields_to_reset:
        st.session_state[field] = ''
    
    st.session_state.output_message = ''
    st.success("입력 필드를 초기화했습니다.")

def copy_to_clipboard():
    """Copy output message to clipboard"""
    if st.session_state.output_message:
        st.write("메시지를 복사하세요:")
        st.code(st.session_state.output_message, language=None)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    st.set_page_config(
        page_title="차량 매입 관리",
        page_icon="🚗",
        layout="wide"
    )
    
    st.title("🚗 차량 매입 관리 시스템")
    
    # Initialize session state
    init_session_state()
    
    # ========================================================================
    # SIDEBAR
    # ========================================================================
    with st.sidebar:
        st.header("⚙️ 설정")
        
        st.subheader("경매 정보")
        st.session_state.auction_type = st.selectbox(
            "경매 타입",
            ['선택 안함', '현대글로비스', '오토허브', '롯데', 'K car'],
            key='auction_type_select'
        )
        
        st.subheader("헤이딜러 정보")
        st.session_state.heydealer_type_select = st.selectbox(
            "헤이딜러 타입",
            ['선택 안함', '일반', '제로', '바로낙찰'],
            key='hd_type_select'
        )
        
        st.session_state.heydealer_id_select = st.selectbox(
            "헤이딜러 ID",
            ['선택 안함', 'seobuk', 'inter77', 'leeks21'],
            key='hd_id_select'
        )
        
        st.divider()
        
        st.subheader("시스템 정보")
        st.info(f"현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if st.session_state.cache_last_load:
            st.caption(f"캐시 로드: {st.session_state.cache_last_load.strftime('%H:%M:%S')}")
    
    # ========================================================================
    # MAIN TABS
    # ========================================================================
    tab1, tab2, tab3 = st.tabs(["📝 정보 입력", "💬 메시지 출력", "👥 딜러/바이어 조회"])
    
    # ========================================================================
    # TAB 1: INFORMATION INPUT
    # ========================================================================
    with tab1:
        st.header("차량 정보 입력")
        
        # Paste data section
        with st.expander("📋 데이터 붙여넣기", expanded=False):
            paste_data = st.text_area(
                "탭으로 구분된 데이터 (차량번호, VIN, 차명, 연식, 주행거리, 색상, 가격, 수수료)",
                height=100
            )
            if st.button("데이터 파싱", type="primary"):
                fill_entries_from_input(paste_data)
                st.rerun()
        
        # Main form
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("기본 정보")
            st.session_state.plate = st.text_input("차량번호", value=st.session_state.plate)
            st.session_state.vin = st.text_input("VIN", value=st.session_state.vin).upper()
            
            if st.session_state.vin and st.button("VIN 자동 감지"):
                st.session_state.brand = detect_brand_from_vin(st.session_state.vin)
                detected_year = detect_vin_year(st.session_state.vin)
                if detected_year:
                    st.session_state.year = detected_year
                st.rerun()
            
            col_car1, col_car2 = st.columns([3, 1])
            with col_car1:
                st.session_state.car_name = st.text_input("차명", value=st.session_state.car_name)
            with col_car2:
                if st.button("차명 매핑"):
                    st.session_state.car_name_alt = detect_alt_car_name(st.session_state.car_name)
                    st.rerun()
            
            st.session_state.car_name_alt = st.text_input("차명(변환)", value=st.session_state.car_name_alt)
            st.session_state.brand = st.text_input("브랜드", value=st.session_state.brand)
            st.session_state.year = st.text_input("연식", value=st.session_state.year)
            st.session_state.km = st.text_input("주행거리", value=st.session_state.km)
            st.session_state.color = st.text_input("색상", value=st.session_state.color)
            
            st.divider()
            st.subheader("딜러 정보")
            
            col_phone1, col_phone2 = st.columns([3, 1])
            with col_phone1:
                st.session_state.phone = st.text_input("전화번호", value=st.session_state.phone)
            with col_phone2:
                if st.button("계좌 조회"):
                    dealer_info = 계좌확인(st.session_state.phone)
                    if dealer_info:
                        st.session_state.company = dealer_info['company']
                        st.session_state.business_num = dealer_info['business_num']
                        st.session_state.vehicle_account = dealer_info['vehicle_account']
                        st.session_state.fee_account = dealer_info['fee_account']
                        st.session_state.remitter_name = dealer_info['remitter_name']
                        st.success("계좌 정보 로드 완료!")
                        st.rerun()
                    else:
                        st.warning("등록된 정보가 없습니다.")
            
            st.session_state.address = st.text_input("주소", value=st.session_state.address)
            if st.session_state.address and st.button("지역 자동 감지"):
                st.session_state.region = detect_region_from_address(st.session_state.address)
                st.rerun()
            
            st.session_state.business_num = st.text_input("사업자번호", value=st.session_state.business_num)
            st.session_state.company = st.text_input("상호", value=st.session_state.company)
            
            st.divider()
            st.subheader("계좌 정보")
            st.session_state.vehicle_account = st.text_input("차량대금 계좌", value=st.session_state.vehicle_account)
            st.session_state.fee_account = st.text_input("수수료 계좌", value=st.session_state.fee_account)
            st.session_state.remitter_name = st.text_input("송금자명", value=st.session_state.remitter_name)
            
            st.divider()
            st.subheader("바이어 정보")
            
            col_buyer1, col_buyer2 = st.columns([3, 1])
            with col_buyer1:
                st.session_state.buyer_name = st.text_input("바이어명", value=st.session_state.buyer_name)
            with col_buyer2:
                if st.button("국가 조회"):
                    country = 확인버튼_동작(st.session_state.buyer_name)
                    if country:
                        st.session_state.buyer_country = country
                        st.success(f"국가: {country}")
                        st.rerun()
                    else:
                        st.warning("등록된 바이어가 없습니다.")
            
            st.session_state.buyer_country = st.text_input("국가", value=st.session_state.buyer_country)
        
        with col_right:
            st.subheader("금액 정보")
            st.session_state.price = st.text_input("차량대금", value=st.session_state.price)
            st.session_state.fee = st.text_input("수수료", value=st.session_state.fee)
            st.session_state.invoice_x = st.text_input("기타 비용", value=st.session_state.invoice_x)
            
            if st.button("합계 계산", type="primary"):
                calculate_total()
                update_declaration()
                st.rerun()
            
            st.session_state.total = st.text_input("총 금액", value=st.session_state.total, disabled=True)
            st.session_state.deposit = st.text_input("계약금", value=st.session_state.deposit)
            
            if st.session_state.deposit:
                calculate_balance()
            
            st.session_state.balance = st.text_input("잔금", value=st.session_state.balance, disabled=True)
            st.session_state.declaration = st.text_input("신고가 (10%)", value=st.session_state.declaration, disabled=True)
            
            st.divider()
            st.subheader("오토위니 정보")
            st.session_state.autowini_company = st.text_input("오토위니 업체", value=st.session_state.autowini_company)
            st.session_state.exchange_date = st.text_input("환율 기준일", value=st.session_state.exchange_date)
            
            col_ex1, col_ex2 = st.columns([3, 1])
            with col_ex1:
                st.session_state.exchange_rate = st.text_input("환율", value=st.session_state.exchange_rate)
            with col_ex2:
                if st.button("환율 조회"):
                    get_exchange_rate()
                    st.rerun()
            
            st.session_state.usd_price = st.text_input("USD 가격", value=st.session_state.usd_price)
            st.session_state.zero_rate = st.text_input("제로금리 (%)", value=st.session_state.zero_rate)
            
            st.divider()
            st.subheader("헤이딜러 정보")
            st.session_state.heydealer_type = st.text_input("타입", value=st.session_state.heydealer_type_select if st.session_state.heydealer_type_select != '선택 안함' else '')
            st.session_state.heydealer_id = st.text_input("ID", value=st.session_state.heydealer_id_select if st.session_state.heydealer_id_select != '선택 안함' else '')
            st.session_state.delivery = st.text_input("배송", value=st.session_state.delivery)
            
            st.divider()
            st.subheader("사이트/영업")
            st.session_state.site = st.text_input("사이트", value=st.session_state.site)
            st.session_state.sales_team = st.text_input("영업팀", value=st.session_state.sales_team)
        
        st.divider()
        
        # Auction frame
        with st.expander("🖼️ 경매 이미지 OCR", expanded=False):
            uploaded_file = st.file_uploader("경매 이미지 업로드", type=['png', 'jpg', 'jpeg'])
            if uploaded_file and st.button("OCR 실행"):
                handle_paste_auction_image(uploaded_file)
                st.rerun()
            
            col_auc1, col_auc2, col_auc3 = st.columns(3)
            with col_auc1:
                st.session_state.region = st.text_input("경매 지역", value=st.session_state.region)
            with col_auc2:
                st.session_state.session = st.text_input("회차", value=st.session_state.session)
            with col_auc3:
                st.session_state.number = st.text_input("번호", value=st.session_state.number)
        
        st.divider()
        
        # Action buttons
        st.subheader("작업")
        col_action1, col_action2, col_action3 = st.columns(3)
        
        with col_action1:
            if st.button("📝 재고 등록", type="primary", use_container_width=True):
                등록_통합_처리()
        
        with col_action2:
            if st.button("💾 ODOO 입력", use_container_width=True):
                insert_ODOO()
        
        with col_action3:
            if st.button("🔄 입력 초기화", use_container_width=True):
                reset_all_fields()
                st.rerun()
    
    # ========================================================================
    # TAB 2: MESSAGE OUTPUT
    # ========================================================================
    with tab2:
        st.header("메시지 생성 및 출력")
        
        st.subheader("확인 메시지")
        col_conf1, col_conf2, col_conf3, col_conf4 = st.columns(4)
        
        with col_conf1:
            if st.button("검수 확인", use_container_width=True):
                handle_confirm('inspector')
        
        with col_conf2:
            if st.button("영업 확인", use_container_width=True):
                handle_confirm('sales')
        
        with col_conf3:
            if st.button("외주 요청", use_container_width=True):
                handle_confirm('outsourcing')
        
        with col_conf4:
            if st.button("주소 공유", use_container_width=True):
                handle_confirm('share_address')
        
        st.divider()
        
        st.subheader("송금 안내")
        col_rem1, col_rem2, col_rem3 = st.columns(3)
        
        with col_rem1:
            if st.button("일반 송금", use_container_width=True):
                extract_message('regular')
            if st.button("계약금", use_container_width=True):
                extract_message('down_payment')
        
        with col_rem2:
            if st.button("폐차 송금", use_container_width=True):
                extract_message('scrap')
            if st.button("오토위니", use_container_width=True):
                extract_message('autowini')
        
        with col_rem3:
            if st.button("송금 완료", use_container_width=True):
                st.session_state.output_message = "송금이 완료되었습니다.\n확인 부탁드립니다."
            if st.button("헤이딜러", use_container_width=True):
                extract_message('heydealer')
        
        st.divider()
        
        st.subheader("기타 메시지")
        col_other1, col_other2, col_other3 = st.columns(3)
        
        with col_other1:
            if st.button("입고 정보", use_container_width=True):
                show_entry_info()
        
        with col_other2:
            if st.button("경매 출고", use_container_width=True):
                handle_auction_output_unified()
        
        with col_other3:
            if st.button("서류 안내", use_container_width=True):
                send_document_text()
        
        st.divider()
        
        # Output area
        st.subheader("출력 메시지")
        output_text = st.text_area(
            "메시지 내용",
            value=st.session_state.output_message,
            height=300,
            key='output_display'
        )
        
        col_out1, col_out2 = st.columns(2)
        with col_out1:
            if st.button("📋 클립보드 복사", use_container_width=True):
                copy_to_clipboard()
        
        with col_out2:
            if st.session_state.output_message:
                st.download_button(
                    "💾 텍스트 다운로드",
                    data=st.session_state.output_message,
                    file_name=f"message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    # ========================================================================
    # TAB 3: DEALER/BUYER LOOKUP
    # ========================================================================
    with tab3:
        st.header("딜러/바이어 정보 조회")
        
        col_lookup1, col_lookup2 = st.columns(2)
        
        with col_lookup1:
            st.subheader("📞 딜러 조회")
            lookup_phone = st.text_input("전화번호로 조회", key='lookup_phone')
            
            if st.button("딜러 검색"):
                dealer_info = 계좌확인(lookup_phone)
                if dealer_info:
                    st.success("딜러 정보를 찾았습니다!")
                    st.write(f"**상호:** {dealer_info['company']}")
                    st.write(f"**사업자번호:** {dealer_info['business_num']}")
                    st.write(f"**차량계좌:** {dealer_info['vehicle_account']}")
                    st.write(f"**수수료계좌:** {dealer_info['fee_account']}")
                    st.write(f"**송금자명:** {dealer_info['remitter_name']}")
                else:
                    st.warning("등록된 딜러 정보가 없습니다.")
            
            st.divider()
            
            st.subheader("✏️ 딜러 정보 업데이트")
            
            if st.button("업데이트 모드"):
                st.session_state.dealer_update_mode = not st.session_state.dealer_update_mode
            
            if st.session_state.dealer_update_mode:
                with st.form("dealer_update_form"):
                    update_phone = st.text_input("전화번호", value=st.session_state.phone)
                    update_company = st.text_input("상호", value=st.session_state.company)
                    update_business = st.text_input("사업자번호", value=st.session_state.business_num)
                    update_vehicle = st.text_input("차량계좌", value=st.session_state.vehicle_account)
                    update_fee = st.text_input("수수료계좌", value=st.session_state.fee_account)
                    update_remitter = st.text_input("송금자명", value=st.session_state.remitter_name)
                    
                    if st.form_submit_button("딜러 정보 저장"):
                        if 계좌업데이트(update_phone, update_company, update_business, 
                                       update_vehicle, update_fee, update_remitter):
                            st.success("딜러 정보가 업데이트되었습니다!")
                            st.session_state.dealer_update_mode = False
                            st.rerun()
        
        with col_lookup2:
            st.subheader("👤 바이어 조회")
            lookup_buyer = st.text_input("바이어명으로 조회", key='lookup_buyer')
            
            if st.button("바이어 검색"):
                country = 확인버튼_동작(lookup_buyer)
                if country:
                    st.success(f"**바이어:** {lookup_buyer}")
                    st.write(f"**국가:** {country}")
                else:
                    st.warning("등록된 바이어 정보가 없습니다.")
            
            st.divider()
            
            st.subheader("📋 바이어 목록")
            if st.button("전체 바이어 조회"):
                try:
                    sheet = get_google3_sheet()
                    if sheet:
                        records = sheet.get_all_records()
                        if records:
                            df = pd.DataFrame(records)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("등록된 바이어가 없습니다.")
                except Exception as e:
                    st.error(f"바이어 목록 조회 오류: {e}")

if __name__ == "__main__":
    main()
