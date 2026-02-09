# 차량 매입 관리 시스템 (Vehicle Purchase Management System)

Complete Streamlit web application converted from Tkinter GUI for managing vehicle purchases at 서북인터내셔널.

## 📋 Overview

This application provides a comprehensive system for:
- Vehicle information input and management
- Dealer and buyer database management
- Google Sheets integration for inventory tracking
- Odoo ERP integration
- OCR processing for auction certificates
- Automated message generation
- Exchange rate tracking

## 🚀 Features

### Core Functionality
- **Korean Currency Parsing**: Handles 만원 (10,000) and 억 (100,000,000) formats
- **VIN Auto-Detection**: Automatically detects brand and year from VIN codes
- **Color Normalization**: Standardizes color names across different inputs
- **Address Region Detection**: Extracts region information from Korean addresses
- **Tab-Separated Data Parsing**: Bulk input from Excel/spreadsheet data

### Google Sheets Integration
- **Dealer Information**: Store and retrieve dealer contact and account information
- **Inventory Tracking**: Dual sheet registration (Yard Status + 2025)
- **Buyer Management**: Country lookup and tracking
- **Car Name Mapping**: Automatic vehicle name standardization
- **VIN Duplicate Detection**: Prevents duplicate vehicle entries

### Odoo ERP Integration
- Direct insertion to `seobuk.car` model
- XML-RPC based communication
- Secure credential management

### Message Generation
Generate formatted messages for:
- **Confirmations**: Inspector, Sales Team, Outsourcing, Address Sharing
- **Remittance Requests**: Regular, Scrap, Down Payment, Autowini, HeyDealer
- **Operations**: Warehouse Entry, Auction Output, Document Guidance

### OCR Processing
- Upload auction certificate images
- Automatic data extraction using Gemini AI
- Extracts: Vehicle name, plate number, VIN, prices, company info, auction details

### Exchange Rate Tracking
- Automated web scraping from Woori Bank
- Real-time USD/KRW exchange rates
- Selenium-based with auto-installing ChromeDriver

## 📦 Installation

### Requirements
```bash
pip install -r requirements.txt
```

Required packages:
- streamlit
- gspread
- google-auth
- oauth2client
- google-generativeai
- selenium
- webdriver-manager
- Pillow
- pandas
- requests

### Configuration

#### Option 1: Streamlit Secrets (Recommended for Production)

Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your_gemini_api_key"

[gcp_service_account]
type = "service_account"
project_id = "your_project"
private_key_id = "key_id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "account@project.iam.gserviceaccount.com"
client_id = "client_id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

[odoo]
url = "https://your-odoo.com"
db_name = "database"
username = "user"
password = "pass"
```

#### Option 2: Environment Variables

Set the following environment variables:
```bash
export GCP_SERVICE_KEY='{"type": "service_account", ...}'
export GEMINI_API_KEY="your_key"
export ODOO_URL="https://your-odoo.com"
export ODOO_DB="database"
export ODOO_USER="username"
export ODOO_PASSWORD="password"
```

### Google Sheets Setup

The application expects the following Google Sheets:

1. **SEOBUK DEALER** (Dealer List)
   - Columns: 연락처, 상호, 사업자번호, 차량대계좌, 매도비계좌, 송금자명

2. **Inventory SEOBUK** (Yard Status + 2025)
   - Vehicle inventory tracking sheets

3. **SEOBUK BUYER** (Sheet1)
   - Columns: 바이어명, 국가

4. **SEOBUK COMPANY** (Company Info)
   - Trading company information

5. **SEOBUK CAR NAMES** (Mapping)
   - Columns: 원본차명, 송금용차명

Ensure your Google Cloud service account has access to all these sheets.

## 🎯 Usage

### Starting the Application

```bash
streamlit run streamlit_app.py
```

Navigate to the "차량 매입 관리" page in the sidebar.

### Input Methods

#### Method 1: Manual Input
Enter information directly into the form fields.

#### Method 2: Tab-Separated Paste
1. Copy data from Excel (select and copy)
2. Paste into the "데이터 붙여넣기" text area
3. Click "데이터 파싱 및 자동 입력" button
4. Fields will auto-populate with:
   - Auto-detected brand and year from VIN
   - Normalized color names
   - Detected region from address
   - Mapped alternative car names

#### Method 3: OCR from Image
1. Go to "옥션 낙찰증 OCR" section
2. Upload auction certificate image (PNG/JPG)
3. Click "OCR 실행" button
4. Data automatically fills from image

### Workflow Example

1. **Input Vehicle Data**
   - Paste from Excel or enter manually
   - Click dealer phone lookup to retrieve account info
   - Verify auto-detected brand/year from VIN

2. **Register Vehicle**
   - Review all information
   - Click "인벤토리 등록" to save to Google Sheets
   - Click "ODOO 입력" to register in ERP system

3. **Generate Messages**
   - Go to "메시지 출력" tab
   - Click appropriate button for message type
   - Copy or download generated message

4. **Lookup Information**
   - Use "딜러/바이어 조회" tab
   - Search by phone or name
   - Add/update dealer or buyer information

## 🔧 Data Maps

### VIN Year Detection
- 10th character of VIN maps to model year
- Supports years 2010-2030 (A-Y, excluding I, O, Q)

### Color Normalization
- Standardizes Korean color names
- Examples: 검정→블랙, 흰색→화이트, 은색→실버

### Region Detection
- Extracts province/city from address
- Supports all Korean provinces and major cities

## 📊 Message Templates

### Confirmation Messages
- **Inspector**: Vehicle inspection request with details
- **Sales Team**: Purchase completion notification
- **Outsourcing**: Transport request with pickup/delivery info
- **Share Address**: Yard address and contact information

### Remittance Messages
- **Regular**: Standard vehicle + fee payment request
- **Scrap**: Scrappage vehicle payment
- **Down Payment**: Initial deposit with balance due
- **Autowini**: International auction payment with exchange info
- **HeyDealer**: HeyDealer platform payment details

### Operational Messages
- **Warehouse Entry**: Vehicle arrival notification
- **Auction Output**: Vehicle release for auction
- **Document Text**: Required document checklist

## 🔐 Security

- **No Hardcoded Credentials**: All sensitive data in secrets/environment
- **Service Account Authentication**: Google Sheets access via GCP
- **Encrypted Connections**: HTTPS for all external API calls
- **Secrets in .gitignore**: Prevents accidental commits

## 🐛 Troubleshooting

### Google Sheets Authentication Errors
- Verify `GCP_SERVICE_KEY` is valid JSON
- Check service account has sheet access (Share → Add account email)
- Ensure all required sheets exist with correct names

### Gemini OCR Not Working
- Verify `GEMINI_API_KEY` is set correctly
- Check API quota limits in Google Cloud Console
- Ensure image is clear and readable

### Exchange Rate Scraping Fails
- Requires Chrome browser and internet access
- Check Woori Bank website is accessible
- Verify no firewall blocking Selenium

### Odoo Connection Issues
- Confirm Odoo URL, database name, credentials
- Test connection manually with XML-RPC
- Check Odoo API access is enabled

## 📝 Development

### File Structure
```
.
├── pages/
│   ├── 1_차량_매입_관리.py       # Main application (1,317 lines)
│   ├── 2_탁송_관리.py            # Transport management
│   └── 3_프로젝션.py             # Projections
├── .streamlit/
│   └── secrets.toml.template     # Secrets template
├── auth.py                        # Google Sheets helpers
├── Personal_path.py               # Legacy path configuration
├── requirements.txt               # Python dependencies
└── streamlit_app.py              # Main entry point
```

### Code Organization

The main application (`pages/1_차량_매입_관리.py`) is organized into:

1. **Imports & Constants** (Lines 1-70)
2. **Session State Initialization** (Lines 72-110)
3. **Google Sheets Functions** (Lines 112-220)
4. **Utility Functions** (Lines 222-380)
5. **Dealer/Buyer Functions** (Lines 382-470)
6. **Registration Functions** (Lines 472-550)
7. **Odoo Integration** (Lines 552-620)
8. **Message Generation** (Lines 622-780)
9. **OCR Functions** (Lines 782-850)
10. **Exchange Rate** (Lines 852-900)
11. **UI Layout** (Lines 902-1317)

## 📄 License

Proprietary - 서북인터내셔널 (Seobuk International)

## 👥 Contact

For support or questions, contact:
- **Company**: 서북인터내셔널
- **Address**: 경기도 평택시 포승읍 만호리 457-1
- **Phone**: 031-683-1234

## 🔄 Version History

### v2.0.0 (2025-02-09)
- Complete conversion from Tkinter to Streamlit
- Added OCR functionality with Gemini AI
- Implemented comprehensive message templates
- Added Odoo ERP integration
- Improved data validation and error handling
- Added exchange rate auto-fetch
- Enhanced UI with three-tab layout
- Added session state management
- Implemented dealer/buyer management

### v1.0.0 (Legacy)
- Original Tkinter GUI application
