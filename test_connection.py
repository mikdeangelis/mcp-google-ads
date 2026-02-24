#!/usr/bin/env python3
"""Test Google Ads API connection"""

import os
from pathlib import Path
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Load .env
env_path = Path(__file__).parent.absolute() / '.env'
load_dotenv(dotenv_path=env_path)

print("🔍 Testing Google Ads API Connection...\n")

# Check credentials
print("📋 Checking credentials:")
creds = {
    "GOOGLE_ADS_DEVELOPER_TOKEN": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
    "GOOGLE_ADS_CLIENT_ID": os.getenv("GOOGLE_ADS_CLIENT_ID"),
    "GOOGLE_ADS_CLIENT_SECRET": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
    "GOOGLE_ADS_REFRESH_TOKEN": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
    "GOOGLE_ADS_LOGIN_CUSTOMER_ID": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
}

for key, value in creds.items():
    if value:
        masked = value[:10] + "..." if len(value) > 10 else value
        print(f"  ✅ {key}: {masked}")
    else:
        print(f"  ❌ {key}: NOT SET")

print("\n🔌 Attempting connection...")

try:
    # Build credentials
    credentials = {
        "developer_token": creds["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": creds["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": creds["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": creds["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True
    }

    if creds["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]:
        credentials["login_customer_id"] = creds["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]

    # Initialize client
    client = GoogleAdsClient.load_from_dict(credentials, version="v23")
    print("  ✅ Client initialized successfully")

    # Try to list accessible customers
    customer_service = client.get_service("CustomerService")
    accessible_customers = customer_service.list_accessible_customers()

    print(f"\n✅ SUCCESS! Found {len(accessible_customers.resource_names)} accessible customer(s):")
    for resource_name in accessible_customers.resource_names[:5]:
        customer_id = resource_name.split("/")[1]
        print(f"  - {customer_id}")

except GoogleAdsException as ex:
    print(f"\n❌ Google Ads API Error:")
    for error in ex.failure.errors:
        print(f"  - {error.message}")

except Exception as ex:
    print(f"\n❌ Error: {type(ex).__name__}: {ex}")
