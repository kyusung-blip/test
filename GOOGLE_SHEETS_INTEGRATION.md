# Google Sheets Integration

This document describes the Google Sheets integration implemented in `Personal_path.py` and `auth.py`.

## Overview

The project integrates with Google Sheets using environment variables for secure credential management. This approach enhances security by avoiding hardcoded credentials and is compatible with GitHub Secrets and other CI/CD secret management systems.

## Environment Variables

The integration requires the following environment variables:

- **GCP_SERVICE_KEY**: JSON string containing the Google Cloud Platform service account credentials
- **SPREADSHEET_NAME**: Name of the Google Sheets spreadsheet (default: "SEOBUK PROJECTION")
- **WORKSHEET_NAME**: Name of the worksheet within the spreadsheet (default: "NUEVO PROJECTION#2")

### Setting Up Environment Variables

#### Local Development

For local development, you can set environment variables in your shell:

```bash
export GCP_SERVICE_KEY='{"type": "service_account", "project_id": "...", ...}'
export SPREADSHEET_NAME="Your Spreadsheet Name"
export WORKSHEET_NAME="Your Worksheet Name"
```

#### Production (GitHub Secrets)

1. Go to your GitHub repository settings
2. Navigate to "Secrets and variables" → "Actions"
3. Add the following repository secrets:
   - `GCP_SERVICE_KEY`: Paste your service account JSON
   - `SPREADSHEET_NAME`: Your spreadsheet name
   - `WORKSHEET_NAME`: Your worksheet name

## Usage

### Using Personal_path Module

The `Personal_path.py` module provides the main interface for Google Sheets operations:

```python
import Personal_path

# Read data from Google Sheets into a pandas DataFrame
df = Personal_path.Read_gspread()

# Get spreadsheet and worksheet names
spreadsheet_name = Personal_path.File_name()
worksheet_name = Personal_path.Sheet_name()

# Get authenticated client (advanced usage)
client = Personal_path.get_gspread_client_for_personal()
```

### Using auth Module

The `auth.py` module provides compatibility functions:

```python
import auth

# Read data using auth module (delegates to Personal_path internally)
df = auth.read_google_sheets()

# Get a specific worksheet
worksheet = auth.get_google_sheet("Spreadsheet Name", "Worksheet Name")

# Get authenticated clients
client_seobuk = auth.get_gspread_client_seobuk()
client_concise = auth.get_gspread_client_concise()
```

## Key Functions

### Personal_path.py

- `Read_gspread()`: Reads data from the configured Google Sheet and returns a pandas DataFrame
- `get_gspread_client_for_personal()`: Returns an authenticated gspread client
- `File_name()`: Returns the configured spreadsheet name
- `Sheet_name()`: Returns the configured worksheet name
- `User()`: Returns the user name (fixed value: "이규성")

### auth.py

- `read_google_sheets()`: Reads data from the default Google Sheet (same as Personal_path.Read_gspread())
- `connect_to_google_sheets()`: Connects to the default Google Sheet and returns a worksheet object
- `get_google_sheet(spreadsheet_name, worksheet_name)`: Opens a specific worksheet
- `get_gspread_client_seobuk()`: Returns an authenticated client for Seobuk project
- `get_gspread_client_concise()`: Returns an authenticated client for Concise project

## Security Features

1. **Environment Variables**: Credentials are stored in environment variables, not in code
2. **No Hardcoded Secrets**: All sensitive information is externalized
3. **GitHub Secrets Integration**: Seamless integration with GitHub Actions and other CI/CD systems
4. **Service Account Authentication**: Uses Google Cloud service account for secure, token-based authentication

## Migration Guide

If you're migrating from the old implementation:

1. Replace any calls to `auth.read_google_sheets()` with `Personal_path.Read_gspread()` (recommended)
2. Ensure environment variables are set in your deployment environment
3. Update any Streamlit secrets usage to use environment variables instead

### Example Migration

**Before:**
```python
import streamlit as st
spreadsheet_name = st.secrets["gcp_service_account"]["spreadsheet_name"]
```

**After:**
```python
import os
spreadsheet_name = os.getenv("SPREADSHEET_NAME", "SEOBUK PROJECTION")
```

## Troubleshooting

### Common Issues

1. **"Google Sheets 클라이언트 생성 실패"**
   - Check that `GCP_SERVICE_KEY` is set and contains valid JSON
   - Verify that the service account has access to the spreadsheet

2. **"워크시트 열기 실패"**
   - Verify that `SPREADSHEET_NAME` and `WORKSHEET_NAME` are correct
   - Ensure the service account has been granted access to the spreadsheet

3. **"Module not found" errors**
   - Install required dependencies: `pip install -r requirements.txt`

## Dependencies

- `gspread`: Google Sheets API wrapper
- `google-auth`: Google authentication library
- `oauth2client`: OAuth 2.0 client library
- `pandas`: Data manipulation library
- `requests`: HTTP library (for retry logic)

## Best Practices

1. Always use environment variables for credentials
2. Never commit credentials to version control
3. Use `Personal_path.Read_gspread()` for new code
4. Keep service account permissions minimal (principle of least privilege)
5. Regularly rotate service account keys
