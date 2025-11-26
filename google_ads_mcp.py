#!/usr/bin/env python3
"""
MCP Server for Google Ads API.

This server provides tools to interact with Google Ads API, including campaign management,
ad creation, keyword management, asset handling, and performance insights.

Supports both read (list, get, insights) and write (create, update, delete) operations.
"""

import os
import json
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Load environment variables from .env file
# Use absolute path to ensure it works when run from any directory
env_path = Path(__file__).parent.absolute() / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback: try to load from environment variables directly
    load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("google_ads_mcp")

# Constants
CHARACTER_LIMIT = 25000  # Maximum response size in characters
DEFAULT_API_VERSION = "v19"  # Google Ads API version (library v28.x supports v19+)


# ============================================================================
# ENUMS
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class CampaignStatus(str, Enum):
    """Campaign status values."""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


class AdvertisingChannelType(str, Enum):
    """Campaign advertising channel types."""
    SEARCH = "SEARCH"
    DISPLAY = "DISPLAY"
    SHOPPING = "SHOPPING"
    VIDEO = "VIDEO"
    MULTI_CHANNEL = "MULTI_CHANNEL"
    LOCAL = "LOCAL"
    SMART = "SMART"
    PERFORMANCE_MAX = "PERFORMANCE_MAX"
    LOCAL_SERVICES = "LOCAL_SERVICES"
    DISCOVERY = "DISCOVERY"
    DEMAND_GEN = "DEMAND_GEN"


class BiddingStrategyType(str, Enum):
    """Bidding strategy types."""
    MANUAL_CPC = "MANUAL_CPC"
    MANUAL_CPM = "MANUAL_CPM"
    MANUAL_CPV = "MANUAL_CPV"
    MAXIMIZE_CONVERSIONS = "MAXIMIZE_CONVERSIONS"
    MAXIMIZE_CONVERSION_VALUE = "MAXIMIZE_CONVERSION_VALUE"
    TARGET_CPA = "TARGET_CPA"
    TARGET_ROAS = "TARGET_ROAS"
    TARGET_SPEND = "TARGET_SPEND"
    TARGET_IMPRESSION_SHARE = "TARGET_IMPRESSION_SHARE"


class DatePreset(str, Enum):
    """Preset date ranges for insights."""
    TODAY = "TODAY"
    YESTERDAY = "YESTERDAY"
    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_14_DAYS = "LAST_14_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"
    LAST_WEEK = "LAST_WEEK"
    LAST_MONTH = "LAST_MONTH"
    THIS_MONTH = "THIS_MONTH"
    THIS_YEAR = "THIS_YEAR"


class DayOfWeek(str, Enum):
    """Days of the week for ad scheduling."""
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class AdGroupStatus(str, Enum):
    """Ad group status values."""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


class AdGroupType(str, Enum):
    """Ad group types."""
    SEARCH_STANDARD = "SEARCH_STANDARD"
    DISPLAY_STANDARD = "DISPLAY_STANDARD"
    SHOPPING_PRODUCT_ADS = "SHOPPING_PRODUCT_ADS"
    VIDEO_BUMPER = "VIDEO_BUMPER"
    VIDEO_TRUE_VIEW_IN_DISPLAY = "VIDEO_TRUE_VIEW_IN_DISPLAY"
    VIDEO_TRUE_VIEW_IN_STREAM = "VIDEO_TRUE_VIEW_IN_STREAM"
    VIDEO_NON_SKIPPABLE_IN_STREAM = "VIDEO_NON_SKIPPABLE_IN_STREAM"


class AdStatus(str, Enum):
    """Ad status values."""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


class KeywordMatchType(str, Enum):
    """Keyword match types."""
    EXACT = "EXACT"
    PHRASE = "PHRASE"
    BROAD = "BROAD"


class AssetFieldType(str, Enum):
    """Asset field types for Performance Max campaigns."""
    HEADLINE = "HEADLINE"
    LONG_HEADLINE = "LONG_HEADLINE"
    DESCRIPTION = "DESCRIPTION"
    BUSINESS_NAME = "BUSINESS_NAME"
    MARKETING_IMAGE = "MARKETING_IMAGE"
    SQUARE_MARKETING_IMAGE = "SQUARE_MARKETING_IMAGE"
    PORTRAIT_MARKETING_IMAGE = "PORTRAIT_MARKETING_IMAGE"
    LOGO = "LOGO"
    LANDSCAPE_LOGO = "LANDSCAPE_LOGO"
    YOUTUBE_VIDEO = "YOUTUBE_VIDEO"
    CALL_TO_ACTION_SELECTION = "CALL_TO_ACTION_SELECTION"


# ============================================================================
# PYDANTIC INPUT MODELS
# ============================================================================

class ListAccountsInput(BaseModel):
    """Input for listing accessible Google Ads accounts."""
    model_config = ConfigDict(str_strip_whitespace=True)

    limit: Optional[int] = Field(default=25, ge=1, le=100, description="Maximum number of accounts to return (1-100)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' or 'json'")


class GetAccountInfoInput(BaseModel):
    """Input for getting account information."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID (e.g., '1234567890')")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class ListCampaignsInput(BaseModel):
    """Input for listing campaigns."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    status_filter: Optional[CampaignStatus] = Field(None, description="Filter by campaign status")
    limit: Optional[int] = Field(default=20, ge=1, le=100, description="Maximum campaigns to return")
    offset: Optional[int] = Field(default=0, ge=0, description="Pagination offset")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class GetCampaignInput(BaseModel):
    """Input for getting single campaign details."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    campaign_id: str = Field(..., description="Campaign ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class GetCampaignInsightsInput(BaseModel):
    """Input for getting campaign performance metrics."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    campaign_id: str = Field(..., description="Campaign ID")
    date_range: DatePreset = Field(default=DatePreset.LAST_30_DAYS, description="Date range for metrics")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class GetSearchTermsInput(BaseModel):
    """Input for getting search terms report."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    campaign_id: Optional[str] = Field(None, description="Filter by campaign ID (optional)")
    ad_group_id: Optional[str] = Field(None, description="Filter by ad group ID (optional)")
    date_range: DatePreset = Field(default=DatePreset.LAST_30_DAYS, description="Date range for data")
    min_impressions: Optional[int] = Field(default=1, ge=1, description="Minimum impressions to include")
    limit: Optional[int] = Field(default=100, ge=1, le=500, description="Maximum search terms to return")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class GetAssetPerformanceInput(BaseModel):
    """Input for getting Performance Max asset performance."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    campaign_id: str = Field(..., description="Campaign ID (must be Performance Max)")
    asset_group_id: Optional[str] = Field(None, description="Filter by specific asset group (optional)")
    date_range: DatePreset = Field(default=DatePreset.LAST_30_DAYS, description="Date range for metrics")
    asset_type_filter: Optional[str] = Field(None, description="Filter by asset type: HEADLINE, DESCRIPTION, IMAGE, VIDEO, etc.")
    min_impressions: Optional[int] = Field(default=1, ge=1, description="Minimum impressions to include")
    limit: Optional[int] = Field(default=50, ge=1, le=200, description="Maximum assets to return")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class CreateCampaignInput(BaseModel):
    """Input for creating a new campaign."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    campaign_name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    budget_amount_micros: int = Field(..., ge=1000000, description="Daily budget in micros (e.g., 10000000 = $10)")
    advertising_channel_type: AdvertisingChannelType = Field(..., description="Campaign type (SEARCH, DISPLAY, etc.)")
    bidding_strategy: BiddingStrategyType = Field(default=BiddingStrategyType.MANUAL_CPC, description="Bidding strategy")
    target_google_search: bool = Field(default=True, description="Target Google Search")
    target_search_network: bool = Field(default=False, description="Target Search Network partners")
    target_content_network: bool = Field(default=False, description="Target Display Network")
    start_date: Optional[str] = Field(None, pattern=r'^\d{8}$', description="Start date (YYYYMMDD)")
    end_date: Optional[str] = Field(None, pattern=r'^\d{8}$', description="End date (YYYYMMDD)")


class UpdateCampaignStatusInput(BaseModel):
    """Input for updating campaign status."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    campaign_id: str = Field(..., description="Campaign ID")
    status: CampaignStatus = Field(..., description="New campaign status")


class SetCampaignScheduleInput(BaseModel):
    """Input for setting campaign ad schedule (day parting)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    campaign_id: str = Field(..., description="Campaign ID")
    days: List[DayOfWeek] = Field(..., description="Days of week when ads should run")
    start_hour: int = Field(..., ge=0, le=23, description="Start hour (0-23)")
    start_minute: int = Field(default=0, description="Start minute (0, 15, 30, or 45)")
    end_hour: int = Field(..., ge=0, le=24, description="End hour (0-24)")
    end_minute: int = Field(default=0, description="End minute (0, 15, 30, or 45)")

    @field_validator('start_minute', 'end_minute')
    @classmethod
    def validate_minutes(cls, v: int) -> int:
        """Validate that minutes are 0, 15, 30, or 45."""
        if v not in [0, 15, 30, 45]:
            raise ValueError("Minutes must be 0, 15, 30, or 45")
        return v


# Ad Groups Input Models

class ListAdGroupsInput(BaseModel):
    """Input for listing ad groups."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    campaign_id: str = Field(..., description="Campaign ID")
    status_filter: Optional[AdGroupStatus] = Field(None, description="Filter by ad group status")
    limit: Optional[int] = Field(default=50, ge=1, le=100, description="Maximum ad groups to return")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class CreateAdGroupInput(BaseModel):
    """Input for creating an ad group."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    campaign_id: str = Field(..., description="Campaign ID")
    ad_group_name: str = Field(..., min_length=1, max_length=255, description="Ad group name")
    cpc_bid_micros: Optional[int] = Field(None, ge=10000, description="CPC bid in micros (min: 10000 = $0.01)")
    status: AdGroupStatus = Field(default=AdGroupStatus.PAUSED, description="Initial status (default: PAUSED)")


class UpdateAdGroupStatusInput(BaseModel):
    """Input for updating ad group status."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    ad_group_id: str = Field(..., description="Ad group ID")
    status: AdGroupStatus = Field(..., description="New ad group status")


# Keywords Input Models

class ListKeywordsInput(BaseModel):
    """Input for listing keywords."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    ad_group_id: str = Field(..., description="Ad group ID")
    limit: Optional[int] = Field(default=100, ge=1, le=500, description="Maximum keywords to return")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class AddKeywordsInput(BaseModel):
    """Input for adding keywords to an ad group."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    ad_group_id: str = Field(..., description="Ad group ID")
    keywords: List[str] = Field(..., min_length=1, max_length=50, description="List of keywords to add (1-50)")
    match_type: KeywordMatchType = Field(default=KeywordMatchType.BROAD, description="Match type for all keywords")
    cpc_bid_micros: Optional[int] = Field(None, ge=10000, description="CPC bid override in micros")


class RemoveKeywordsInput(BaseModel):
    """Input for removing keywords."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    keyword_ids: List[str] = Field(..., min_length=1, description="List of keyword criterion IDs to remove")


# Ads Input Models

class ListAdsInput(BaseModel):
    """Input for listing ads."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    ad_group_id: str = Field(..., description="Ad group ID")
    status_filter: Optional[AdStatus] = Field(None, description="Filter by ad status")
    limit: Optional[int] = Field(default=50, ge=1, le=100, description="Maximum ads to return")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class CreateResponsiveSearchAdInput(BaseModel):
    """Input for creating a responsive search ad."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    ad_group_id: str = Field(..., description="Ad group ID")
    headlines: List[str] = Field(..., min_length=3, max_length=15, description="Headlines (3-15 required, max 30 chars each)")
    descriptions: List[str] = Field(..., min_length=2, max_length=4, description="Descriptions (2-4 required, max 90 chars each)")
    final_urls: List[str] = Field(..., min_length=1, description="Final URLs where users land")
    path1: Optional[str] = Field(None, max_length=15, description="Display path 1 (max 15 chars)")
    path2: Optional[str] = Field(None, max_length=15, description="Display path 2 (max 15 chars)")

    @field_validator('headlines')
    @classmethod
    def validate_headlines(cls, v: List[str]) -> List[str]:
        """Validate headlines length."""
        for headline in v:
            if len(headline) > 30:
                raise ValueError(f"Headline too long (max 30 chars): {headline}")
        return v

    @field_validator('descriptions')
    @classmethod
    def validate_descriptions(cls, v: List[str]) -> List[str]:
        """Validate descriptions length."""
        for description in v:
            if len(description) > 90:
                raise ValueError(f"Description too long (max 90 chars): {description}")
        return v


class UpdateAdStatusInput(BaseModel):
    """Input for updating ad status."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    ad_group_id: str = Field(..., description="Ad group ID")
    ad_id: str = Field(..., description="Ad ID")
    status: AdStatus = Field(..., description="New ad status")


class CreateTextAssetsInput(BaseModel):
    """Input for creating text assets and adding them to an asset group."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    asset_group_id: str = Field(..., description="Asset group ID")
    headlines: Optional[List[str]] = Field(default=None, min_length=0, max_length=15, description="Headlines to add (max 30 chars each, max 15 total)")
    descriptions: Optional[List[str]] = Field(default=None, min_length=0, max_length=5, description="Descriptions to add (max 90 chars each, max 5 total)")
    long_headlines: Optional[List[str]] = Field(default=None, min_length=0, max_length=5, description="Long headlines to add (max 90 chars each, max 5 total)")
    business_name: Optional[str] = Field(default=None, max_length=25, description="Business name (max 25 chars, optional)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('headlines', 'descriptions', 'long_headlines')
    @classmethod
    def validate_text_lengths(cls, v, info):
        """Validate text asset character limits."""
        if v is None:
            return v

        field_name = info.field_name
        max_lengths = {
            'headlines': 30,
            'descriptions': 90,
            'long_headlines': 90
        }

        max_len = max_lengths.get(field_name, 30)
        for text in v:
            if len(text) > max_len:
                raise ValueError(f"{field_name} text exceeds {max_len} characters: '{text[:50]}...'")

        return v


class RemoveAssetFromGroupInput(BaseModel):
    """Input for removing assets from an asset group."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    asset_group_asset_ids: List[str] = Field(..., min_length=1, description="List of asset_group_asset resource IDs to remove (format: customers/{customer_id}/assetGroupAssets/{asset_group_id}~{asset_id}~{field_type})")


class UpdateAssetGroupAssetsInput(BaseModel):
    """Input for batch updating assets in an asset group (add + remove in one operation)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=10, max_length=10, description="10-digit customer ID")
    asset_group_id: str = Field(..., description="Asset group ID")
    add_headlines: Optional[List[str]] = Field(default=None, description="Headlines to add")
    add_descriptions: Optional[List[str]] = Field(default=None, description="Descriptions to add")
    remove_asset_group_asset_ids: Optional[List[str]] = Field(default=None, description="Asset group asset IDs to remove")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


# ============================================================================
# SHARED UTILITY FUNCTIONS
# ============================================================================

def _get_google_ads_client() -> GoogleAdsClient:
    """
    Initialize and return Google Ads API client with credentials from environment.

    Returns:
        GoogleAdsClient: Initialized Google Ads client

    Raises:
        ValueError: If required environment variables are missing
    """
    # Check for required environment variables
    required_vars = [
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Please configure credentials before using this tool."
        )

    # Build credentials dictionary
    credentials = {
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        "use_proto_plus": True
    }

    # Add login customer ID if provided (for MCC accounts)
    if os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"):
        credentials["login_customer_id"] = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")

    return GoogleAdsClient.load_from_dict(credentials, version=DEFAULT_API_VERSION)


def _validate_customer_id(customer_id: str) -> str:
    """
    Validate and format customer ID (remove dashes if present).

    Args:
        customer_id: Customer ID string (with or without dashes)

    Returns:
        str: Formatted customer ID (10 digits, no dashes)
    """
    # Remove dashes if present
    customer_id = customer_id.replace("-", "")

    # Validate length
    if len(customer_id) != 10:
        raise ValueError(f"Customer ID must be 10 digits, got {len(customer_id)}")

    # Validate digits only
    if not customer_id.isdigit():
        raise ValueError("Customer ID must contain only digits")

    return customer_id


def _execute_query(client: GoogleAdsClient, customer_id: str, query: str) -> List[Dict[str, Any]]:
    """
    Execute a GAQL query and return results as list of dictionaries.

    Args:
        client: Google Ads client
        customer_id: Customer ID
        query: GAQL query string

    Returns:
        List[Dict]: Query results
    """
    ga_service = client.get_service("GoogleAdsService")

    results = []
    stream = ga_service.search_stream(customer_id=customer_id, query=query)

    for batch in stream:
        for row in batch.results:
            results.append(row)

    return results


def _handle_google_ads_error(error: Exception) -> str:
    """
    Handle Google Ads API errors with actionable messages.

    Args:
        error: Exception from Google Ads API

    Returns:
        str: User-friendly error message
    """
    if isinstance(error, GoogleAdsException):
        # Extract error details
        error_messages = []
        for err in error.failure.errors:
            error_messages.append(f"- {err.message}")

        # Check for common error types
        error_str = str(error)

        if "AUTHENTICATION_ERROR" in error_str:
            return (
                "Error: Authentication failed. Please verify:\n"
                "- GOOGLE_ADS_DEVELOPER_TOKEN is valid\n"
                "- GOOGLE_ADS_CLIENT_ID is correct\n"
                "- GOOGLE_ADS_REFRESH_TOKEN is current\n"
                "Run the OAuth flow again if needed."
            )

        if "AUTHORIZATION_ERROR" in error_str:
            return (
                "Error: Authorization failed. You don't have access to this customer account. "
                "Please verify the customer ID and ensure your account has proper permissions."
            )

        if "RATE_EXCEEDED" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            return "Error: API rate limit exceeded. Please wait a few moments before making more requests."

        if "INVALID_CUSTOMER_ID" in error_str:
            return "Error: Invalid customer ID. Use 10-digit format without dashes (e.g., '1234567890')."

        if "NOT_FOUND" in error_str or "RESOURCE_NOT_FOUND" in error_str:
            return "Error: Resource not found. Please verify the ID is correct and the resource exists."

        if "BUDGET_ERROR" in error_str:
            return "Error: Budget configuration issue. Ensure budget is at least $1.00 (1000000 micros)."

        # Return detailed error messages
        return "Error from Google Ads API:\n" + "\n".join(error_messages)

    elif isinstance(error, ValueError):
        return f"Error: {str(error)}"

    else:
        return f"Error: Unexpected error occurred - {type(error).__name__}: {str(error)}"


def _format_money_micros(micros: int, currency_code: str = "USD") -> str:
    """Format micros to currency string."""
    amount = micros / 1_000_000
    return f"{currency_code} {amount:,.2f}"


def _format_date_range(date_preset: DatePreset) -> str:
    """Convert date preset enum to GAQL date segment."""
    mapping = {
        DatePreset.TODAY: "segments.date DURING TODAY",
        DatePreset.YESTERDAY: "segments.date DURING YESTERDAY",
        DatePreset.LAST_7_DAYS: "segments.date DURING LAST_7_DAYS",
        DatePreset.LAST_14_DAYS: "segments.date DURING LAST_14_DAYS",
        DatePreset.LAST_30_DAYS: "segments.date DURING LAST_30_DAYS",
        DatePreset.LAST_WEEK: "segments.date DURING LAST_WEEK",
        DatePreset.LAST_MONTH: "segments.date DURING LAST_MONTH",
        DatePreset.THIS_MONTH: "segments.date DURING THIS_MONTH",
        DatePreset.THIS_YEAR: "segments.date DURING THIS_YEAR",
    }
    return mapping.get(date_preset, "segments.date DURING LAST_30_DAYS")


def _check_and_truncate(response: str, limit: int = CHARACTER_LIMIT) -> str:
    """
    Check response length and truncate if needed with clear message.

    Args:
        response: Response string
        limit: Character limit

    Returns:
        str: Original or truncated response with warning
    """
    if len(response) <= limit:
        return response

    # Truncate and add warning
    truncated = response[:limit]
    warning = (
        f"\n\n⚠️ **Response truncated** from {len(response):,} to {limit:,} characters. "
        "Use filters, pagination, or reduce date range to see more data."
    )

    return truncated + warning


# ============================================================================
# TOOL IMPLEMENTATIONS - PHASE 1 (MVP)
# ============================================================================

@mcp.tool(
    name="google_ads_list_accounts",
    annotations={
        "title": "List Google Ads Accounts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_list_accounts(params: ListAccountsInput) -> str:
    """
    List all accessible Google Ads accounts for the authenticated user.

    Retrieves a list of all customer accounts that the authenticated credentials
    can access, showing account names, IDs, currency, status, and timezone.

    Args:
        params (ListAccountsInput): Input parameters containing:
            - limit (Optional[int]): Maximum accounts to return (1-100, default: 25)
            - response_format (ResponseFormat): Output format ('markdown' or 'json')

    Returns:
        str: List of accessible accounts with details

        Markdown format:
        # Google Ads Accounts
        Found X accounts

        ## Account Name (1234567890)
        - **Currency**: USD
        - **Status**: ENABLED
        - **Timezone**: America/New_York

        JSON format:
        {
            "total": int,
            "count": int,
            "accounts": [
                {
                    "id": "1234567890",
                    "name": "Account Name",
                    "currency_code": "USD",
                    "status": "ENABLED",
                    "timezone": "America/New_York",
                    "resource_name": "customers/1234567890"
                }
            ]
        }

    Examples:
        - "Show me all my Google Ads accounts"
        - "List my accessible accounts"
        - "What accounts can I access?"

    Error Handling:
        - Returns authentication error if credentials are invalid
        - Returns authorization error if no access to accounts
        - Returns clear error messages for all failures
    """
    try:
        client = _get_google_ads_client()

        # Get customer service
        customer_service = client.get_service("CustomerService")

        # Get accessible customers
        accessible_customers = customer_service.list_accessible_customers()
        resource_names = accessible_customers.resource_names

        if not resource_names:
            return "No accessible Google Ads accounts found for the authenticated credentials."

        # Fetch details for each account
        accounts = []
        ga_service = client.get_service("GoogleAdsService")

        for resource_name in resource_names[:params.limit]:
            # Extract customer ID from resource name
            customer_id = resource_name.split("/")[1]

            # Query for account details
            query = """
                SELECT
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone,
                    customer.status
                FROM customer
                WHERE customer.id = {customer_id}
            """.format(customer_id=customer_id)

            try:
                results = _execute_query(client, customer_id, query)
                if results:
                    row = results[0]
                    accounts.append({
                        "id": str(row.customer.id),
                        "name": row.customer.descriptive_name,
                        "currency_code": row.customer.currency_code,
                        "status": row.customer.status.name,
                        "timezone": row.customer.time_zone,
                        "resource_name": resource_name
                    })
            except GoogleAdsException:
                # Skip accounts we can't access
                continue

        if not accounts:
            return "Unable to retrieve details for accessible accounts. You may lack sufficient permissions."

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = ["# Google Ads Accounts", ""]
            lines.append(f"Found **{len(accounts)}** accessible account(s)")
            lines.append("")

            for account in accounts:
                lines.append(f"## {account['name']} ({account['id']})")
                lines.append(f"- **Currency**: {account['currency_code']}")
                lines.append(f"- **Status**: {account['status']}")
                lines.append(f"- **Timezone**: {account['timezone']}")
                lines.append("")

            return "\n".join(lines)

        else:  # JSON format
            response = {
                "total": len(accounts),
                "count": len(accounts),
                "accounts": accounts
            }
            return json.dumps(response, indent=2)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_get_account_info",
    annotations={
        "title": "Get Account Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_get_account_info(params: GetAccountInfoInput) -> str:
    """
    Get detailed information about a specific Google Ads account.

    Retrieves comprehensive account details including currency, timezone,
    descriptive name, test account status, and manager status.

    Args:
        params (GetAccountInfoInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID (e.g., '1234567890')
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed account information

    Examples:
        - "Get info for account 1234567890"
        - "Show me details for customer 9876543210"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        query = """
            SELECT
                customer.id,
                customer.descriptive_name,
                customer.currency_code,
                customer.time_zone,
                customer.tracking_url_template,
                customer.auto_tagging_enabled,
                customer.has_partners_badge,
                customer.manager,
                customer.test_account,
                customer.status
            FROM customer
            WHERE customer.id = {customer_id}
        """.format(customer_id=customer_id)

        results = _execute_query(client, customer_id, query)

        if not results:
            return f"No account found with ID {customer_id}"

        row = results[0]
        customer = row.customer

        account_info = {
            "id": str(customer.id),
            "name": customer.descriptive_name,
            "currency_code": customer.currency_code,
            "timezone": customer.time_zone,
            "status": customer.status.name,
            "is_manager": customer.manager,
            "is_test_account": customer.test_account,
            "auto_tagging_enabled": customer.auto_tagging_enabled,
            "has_partners_badge": customer.has_partners_badge
        }

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Account: {account_info['name']} ({account_info['id']})", ""]
            lines.append("## Basic Information")
            lines.append(f"- **Currency**: {account_info['currency_code']}")
            lines.append(f"- **Timezone**: {account_info['timezone']}")
            lines.append(f"- **Status**: {account_info['status']}")
            lines.append("")
            lines.append("## Account Type")
            lines.append(f"- **Manager Account**: {'Yes' if account_info['is_manager'] else 'No'}")
            lines.append(f"- **Test Account**: {'Yes' if account_info['is_test_account'] else 'No'}")
            lines.append(f"- **Auto-tagging**: {'Enabled' if account_info['auto_tagging_enabled'] else 'Disabled'}")
            lines.append(f"- **Google Partners Badge**: {'Yes' if account_info['has_partners_badge'] else 'No'}")

            return "\n".join(lines)

        else:  # JSON
            return json.dumps(account_info, indent=2)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_list_campaigns",
    annotations={
        "title": "List Campaigns",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_list_campaigns(params: ListCampaignsInput) -> str:
    """
    List campaigns for a Google Ads account with optional filtering.

    Retrieves campaigns with details including name, status, type, budget,
    bidding strategy, and date range. Supports filtering by status and pagination.

    Args:
        params (ListCampaignsInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - status_filter (Optional[CampaignStatus]): Filter by status (ENABLED, PAUSED, REMOVED)
            - limit (Optional[int]): Maximum campaigns to return (1-100, default: 20)
            - offset (Optional[int]): Pagination offset (default: 0)
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of campaigns with details and pagination info

    Examples:
        - "List all campaigns for account 1234567890"
        - "Show me active campaigns"
        - "Get paused campaigns for customer 9876543210"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        # Build query with optional status filter
        where_clause = ""
        if params.status_filter:
            where_clause = f"WHERE campaign.status = {params.status_filter.value}"

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                campaign_budget.amount_micros,
                campaign.start_date,
                campaign.end_date,
                campaign.optimization_score
            FROM campaign
            {where_clause}
            ORDER BY campaign.id DESC
            LIMIT {params.limit}
        """

        results = _execute_query(client, customer_id, query)

        # Apply offset (since GAQL doesn't support OFFSET directly)
        if params.offset > 0:
            results = results[params.offset:]

        if not results:
            status_msg = f" with status {params.status_filter.value}" if params.status_filter else ""
            return f"No campaigns found{status_msg}"

        campaigns = []
        for row in results:
            campaign = row.campaign
            budget = row.campaign_budget

            campaigns.append({
                "id": str(campaign.id),
                "name": campaign.name,
                "status": campaign.status.name,
                "type": campaign.advertising_channel_type.name,
                "bidding_strategy": campaign.bidding_strategy_type.name,
                "budget_micros": budget.amount_micros if budget else None,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "optimization_score": campaign.optimization_score if hasattr(campaign, 'optimization_score') else None
            })

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = ["# Campaigns", ""]
            lines.append(f"Found **{len(campaigns)}** campaign(s)")
            lines.append("")

            for camp in campaigns:
                lines.append(f"## {camp['name']} ({camp['id']})")
                lines.append(f"- **Status**: {camp['status']}")
                lines.append(f"- **Type**: {camp['type']}")
                lines.append(f"- **Bidding**: {camp['bidding_strategy']}")
                if camp['budget_micros']:
                    lines.append(f"- **Daily Budget**: {_format_money_micros(camp['budget_micros'])}")
                lines.append(f"- **Start Date**: {camp['start_date']}")
                if camp['end_date']:
                    lines.append(f"- **End Date**: {camp['end_date']}")
                if camp['optimization_score'] is not None:
                    lines.append(f"- **Optimization Score**: {camp['optimization_score']:.2f}")
                lines.append("")

            # Add pagination info
            has_more = len(results) == params.limit
            if has_more:
                lines.append(f"*Use offset={params.offset + params.limit} to see more results*")

            result = "\n".join(lines)
            return _check_and_truncate(result)

        else:  # JSON
            response = {
                "total": len(campaigns),
                "count": len(campaigns),
                "offset": params.offset,
                "campaigns": campaigns,
                "has_more": len(results) == params.limit,
                "next_offset": params.offset + params.limit if len(results) == params.limit else None
            }
            result = json.dumps(response, indent=2)
            return _check_and_truncate(result)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_get_campaign",
    annotations={
        "title": "Get Campaign Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_get_campaign(params: GetCampaignInput) -> str:
    """
    Get detailed information about a specific campaign.

    Retrieves comprehensive campaign details including settings, targeting,
    budget, bidding strategy, and network settings.

    Args:
        params (GetCampaignInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - campaign_id (str): Campaign ID
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed campaign information

    Examples:
        - "Get details for campaign 123456789"
        - "Show me campaign 987654321 settings"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.advertising_channel_sub_type,
                campaign.bidding_strategy_type,
                campaign_budget.amount_micros,
                campaign_budget.delivery_method,
                campaign.start_date,
                campaign.end_date,
                campaign.network_settings.target_google_search,
                campaign.network_settings.target_search_network,
                campaign.network_settings.target_content_network,
                campaign.network_settings.target_partner_search_network,
                campaign.optimization_score,
                campaign.url_custom_parameters
            FROM campaign
            WHERE campaign.id = {params.campaign_id}
        """

        results = _execute_query(client, customer_id, query)

        if not results:
            return f"Campaign {params.campaign_id} not found"

        row = results[0]
        campaign = row.campaign
        budget = row.campaign_budget

        campaign_info = {
            "id": str(campaign.id),
            "name": campaign.name,
            "status": campaign.status.name,
            "type": campaign.advertising_channel_type.name,
            "sub_type": campaign.advertising_channel_sub_type.name if hasattr(campaign, 'advertising_channel_sub_type') else None,
            "bidding_strategy": campaign.bidding_strategy_type.name,
            "budget": {
                "amount_micros": budget.amount_micros if budget else None,
                "delivery_method": budget.delivery_method.name if budget else None
            },
            "dates": {
                "start": campaign.start_date,
                "end": campaign.end_date
            },
            "network_settings": {
                "google_search": campaign.network_settings.target_google_search,
                "search_network": campaign.network_settings.target_search_network,
                "content_network": campaign.network_settings.target_content_network,
                "partner_search_network": campaign.network_settings.target_partner_search_network
            },
            "optimization_score": campaign.optimization_score if hasattr(campaign, 'optimization_score') else None
        }

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Campaign: {campaign_info['name']} ({campaign_info['id']})", ""]

            lines.append("## Basic Settings")
            lines.append(f"- **Status**: {campaign_info['status']}")
            lines.append(f"- **Type**: {campaign_info['type']}")
            if campaign_info['sub_type']:
                lines.append(f"- **Sub-type**: {campaign_info['sub_type']}")
            lines.append(f"- **Bidding Strategy**: {campaign_info['bidding_strategy']}")
            lines.append("")

            lines.append("## Budget")
            if campaign_info['budget']['amount_micros']:
                lines.append(f"- **Daily Budget**: {_format_money_micros(campaign_info['budget']['amount_micros'])}")
                lines.append(f"- **Delivery Method**: {campaign_info['budget']['delivery_method']}")
            lines.append("")

            lines.append("## Schedule")
            lines.append(f"- **Start Date**: {campaign_info['dates']['start']}")
            if campaign_info['dates']['end']:
                lines.append(f"- **End Date**: {campaign_info['dates']['end']}")
            lines.append("")

            lines.append("## Network Targeting")
            ns = campaign_info['network_settings']
            lines.append(f"- **Google Search**: {'✓' if ns['google_search'] else '✗'}")
            lines.append(f"- **Search Network Partners**: {'✓' if ns['search_network'] else '✗'}")
            lines.append(f"- **Display Network**: {'✓' if ns['content_network'] else '✗'}")
            lines.append(f"- **Partner Search Network**: {'✓' if ns['partner_search_network'] else '✗'}")

            if campaign_info['optimization_score'] is not None:
                lines.append("")
                lines.append("## Optimization")
                lines.append(f"- **Score**: {campaign_info['optimization_score']:.2f}/100")

            return "\n".join(lines)

        else:  # JSON
            return json.dumps(campaign_info, indent=2)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_get_campaign_insights",
    annotations={
        "title": "Get Campaign Performance Metrics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_get_campaign_insights(params: GetCampaignInsightsInput) -> str:
    """
    Get performance metrics for a campaign.

    Retrieves key performance indicators including impressions, clicks, cost,
    conversions, CTR, average CPC, and conversion rate for the specified date range.

    Args:
        params (GetCampaignInsightsInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - campaign_id (str): Campaign ID
            - date_range (DatePreset): Date range (default: LAST_30_DAYS)
            - response_format (ResponseFormat): Output format

    Returns:
        str: Campaign performance metrics

    Examples:
        - "Get performance for campaign 123456789"
        - "Show me last 7 days metrics for campaign 987654321"
        - "What are the stats for campaign 555555555?"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        # Build date filter
        date_filter = _format_date_range(params.date_range)

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.average_cpm,
                metrics.cost_per_conversion
            FROM campaign
            WHERE campaign.id = {params.campaign_id}
            AND {date_filter}
        """

        results = _execute_query(client, customer_id, query)

        if not results:
            return f"No data found for campaign {params.campaign_id} in the selected date range"

        # Aggregate metrics (in case there are multiple rows)
        total_metrics = {
            "impressions": 0,
            "clicks": 0,
            "cost_micros": 0,
            "conversions": 0.0,
            "conversions_value": 0.0
        }

        campaign_name = ""
        for row in results:
            if not campaign_name:
                campaign_name = row.campaign.name

            metrics = row.metrics
            total_metrics["impressions"] += metrics.impressions
            total_metrics["clicks"] += metrics.clicks
            total_metrics["cost_micros"] += metrics.cost_micros
            total_metrics["conversions"] += metrics.conversions
            total_metrics["conversions_value"] += metrics.conversions_value

        # Calculate derived metrics
        ctr = (total_metrics["clicks"] / total_metrics["impressions"] * 100) if total_metrics["impressions"] > 0 else 0
        avg_cpc = (total_metrics["cost_micros"] / total_metrics["clicks"]) if total_metrics["clicks"] > 0 else 0
        conversion_rate = (total_metrics["conversions"] / total_metrics["clicks"] * 100) if total_metrics["clicks"] > 0 else 0
        cost_per_conversion = (total_metrics["cost_micros"] / total_metrics["conversions"]) if total_metrics["conversions"] > 0 else 0
        roas = (total_metrics["conversions_value"] / (total_metrics["cost_micros"] / 1_000_000)) if total_metrics["cost_micros"] > 0 else 0

        insights = {
            "campaign_id": params.campaign_id,
            "campaign_name": campaign_name,
            "date_range": params.date_range.value,
            "metrics": {
                "impressions": total_metrics["impressions"],
                "clicks": total_metrics["clicks"],
                "cost_micros": total_metrics["cost_micros"],
                "conversions": total_metrics["conversions"],
                "conversions_value": total_metrics["conversions_value"],
                "ctr": round(ctr, 2),
                "average_cpc_micros": int(avg_cpc),
                "conversion_rate": round(conversion_rate, 2),
                "cost_per_conversion_micros": int(cost_per_conversion),
                "roas": round(roas, 2)
            }
        }

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Performance: {campaign_name}", ""]
            lines.append(f"**Date Range**: {params.date_range.value}")
            lines.append("")

            lines.append("## Key Metrics")
            m = insights["metrics"]
            lines.append(f"- **Impressions**: {m['impressions']:,}")
            lines.append(f"- **Clicks**: {m['clicks']:,}")
            lines.append(f"- **CTR**: {m['ctr']:.2f}%")
            lines.append(f"- **Cost**: {_format_money_micros(m['cost_micros'])}")
            lines.append(f"- **Avg. CPC**: {_format_money_micros(m['average_cpc_micros'])}")
            lines.append("")

            lines.append("## Conversions")
            lines.append(f"- **Conversions**: {m['conversions']:.2f}")
            lines.append(f"- **Conversion Rate**: {m['conversion_rate']:.2f}%")
            lines.append(f"- **Cost per Conversion**: {_format_money_micros(m['cost_per_conversion_micros'])}")
            lines.append(f"- **Conversion Value**: {_format_money_micros(int(m['conversions_value'] * 1_000_000))}")
            lines.append(f"- **ROAS**: {m['roas']:.2f}x")

            return "\n".join(lines)

        else:  # JSON
            return json.dumps(insights, indent=2)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_get_search_terms",
    annotations={
        "title": "Get Search Terms Report",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_get_search_terms(params: GetSearchTermsInput) -> str:
    """
    Get search terms report showing what users actually searched for.

    This report shows the actual search queries that triggered your ads,
    along with performance metrics for each search term. Essential for:
    - Discovering new keyword opportunities
    - Finding negative keywords to exclude
    - Understanding user intent
    - Optimizing keyword match types

    Args:
        params (GetSearchTermsInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - campaign_id (Optional[str]): Filter by specific campaign
            - ad_group_id (Optional[str]): Filter by specific ad group
            - date_range (DatePreset): Date range (default: LAST_30_DAYS)
            - min_impressions (int): Minimum impressions threshold (default: 1)
            - limit (int): Maximum results to return (1-500, default: 100)
            - response_format (ResponseFormat): Output format

    Returns:
        str: Search terms with performance metrics

        Markdown format shows:
        - Search term text
        - Match type (EXACT, PHRASE, BROAD)
        - Campaign and ad group
        - Metrics: impressions, clicks, CTR, cost, conversions

        JSON format provides structured data for analysis

    Examples:
        - "Show me search terms for campaign 123456"
        - "What are users actually searching for?"
        - "Get search terms report last 7 days"

    Note:
        Use this to identify:
        - High-performing search terms → add as exact match keywords
        - Irrelevant search terms → add to negative keywords
        - Search intent patterns → inform ad copy and landing pages
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        # Build date filter
        date_filter = _format_date_range(params.date_range)

        # Build WHERE clauses
        where_clauses = [date_filter]
        if params.campaign_id:
            where_clauses.append(f"campaign.id = {params.campaign_id}")
        if params.ad_group_id:
            where_clauses.append(f"ad_group.id = {params.ad_group_id}")
        if params.min_impressions:
            where_clauses.append(f"metrics.impressions >= {params.min_impressions}")

        where_clause = " AND ".join(where_clauses)

        query = f"""
            SELECT
                search_term_view.search_term,
                search_term_view.status,
                campaign.id,
                campaign.name,
                ad_group.id,
                ad_group.name,
                segments.keyword.info.text,
                segments.keyword.info.match_type,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.average_cpc
            FROM search_term_view
            WHERE {where_clause}
            ORDER BY metrics.impressions DESC
            LIMIT {params.limit}
        """

        results = _execute_query(client, customer_id, query)

        if not results:
            filter_msg = f" for campaign {params.campaign_id}" if params.campaign_id else ""
            return f"No search terms found{filter_msg} in the selected date range"

        # Collect search terms data
        search_terms = []
        for row in results:
            stv = row.search_term_view
            metrics = row.metrics
            keyword = row.segments.keyword.info if hasattr(row.segments, 'keyword') else None

            ctr = metrics.ctr * 100 if hasattr(metrics, 'ctr') else 0

            search_terms.append({
                "search_term": stv.search_term,
                "status": stv.status.name if hasattr(stv, 'status') else "UNKNOWN",
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "keyword_text": keyword.text if keyword else "N/A",
                "match_type": keyword.match_type.name if keyword else "N/A",
                "metrics": {
                    "impressions": metrics.impressions,
                    "clicks": metrics.clicks,
                    "ctr": round(ctr, 2),
                    "cost_micros": metrics.cost_micros,
                    "conversions": metrics.conversions if hasattr(metrics, 'conversions') else 0,
                    "conversions_value": metrics.conversions_value if hasattr(metrics, 'conversions_value') else 0,
                    "average_cpc_micros": int(metrics.average_cpc) if hasattr(metrics, 'average_cpc') else 0
                }
            })

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Search Terms Report", ""]
            lines.append(f"**Date Range**: {params.date_range.value}")
            lines.append(f"**Found**: {len(search_terms)} search term(s)")
            lines.append("")

            for i, st in enumerate(search_terms[:50], 1):  # Limit markdown output
                m = st['metrics']

                # Icon based on performance
                if m['conversions'] > 0:
                    icon = "🎯"  # Converting
                elif m['clicks'] > 0:
                    icon = "👆"  # Getting clicks
                else:
                    icon = "👁️"  # Only impressions

                lines.append(f"## {icon} \"{st['search_term']}\"")
                lines.append(f"- **Campaign**: {st['campaign_name']}")
                lines.append(f"- **Ad Group**: {st['ad_group_name']}")
                lines.append(f"- **Keyword**: {st['keyword_text']} ({st['match_type']})")
                lines.append(f"- **Status**: {st['status']}")
                lines.append("")

                lines.append("**Performance:**")
                lines.append(f"- Impressions: {m['impressions']:,}")
                lines.append(f"- Clicks: {m['clicks']:,}")
                lines.append(f"- CTR: {m['ctr']:.2f}%")
                lines.append(f"- Cost: {_format_money_micros(m['cost_micros'])}")
                lines.append(f"- Avg CPC: {_format_money_micros(m['average_cpc_micros'])}")
                if m['conversions'] > 0:
                    lines.append(f"- Conversions: {m['conversions']:.2f}")
                    lines.append(f"- Conv. Value: {_format_money_micros(int(m['conversions_value'] * 1_000_000))}")
                lines.append("")

            if len(search_terms) > 50:
                lines.append(f"*Showing top 50 of {len(search_terms)} search terms*")
                lines.append(f"*Use JSON format or filters to see all results*")

            result = "\n".join(lines)
            return _check_and_truncate(result)

        else:  # JSON
            response = {
                "date_range": params.date_range.value,
                "total": len(search_terms),
                "search_terms": search_terms
            }
            result = json.dumps(response, indent=2)
            return _check_and_truncate(result)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_get_asset_performance",
    annotations={
        "title": "Get Performance Max Asset Performance",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_get_asset_performance(params: GetAssetPerformanceInput) -> str:
    """
    Get Performance Max asset performance showing which creatives work best.

    This report shows performance metrics for individual assets (headlines, descriptions,
    images, videos) in Performance Max campaigns. Essential for:
    - Identifying top-performing creatives
    - Finding underperforming assets to replace
    - Understanding which messages resonate with users
    - Optimizing creative strategy based on data

    Args:
        params (GetAssetPerformanceInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - campaign_id (str): Campaign ID (must be Performance Max type)
            - asset_group_id (Optional[str]): Filter by specific asset group
            - date_range (DatePreset): Date range (default: LAST_30_DAYS)
            - asset_type_filter (Optional[str]): Filter by type (HEADLINE, DESCRIPTION, IMAGE, etc.)
            - min_impressions (int): Minimum impressions threshold (default: 1)
            - limit (int): Maximum assets to return (1-200, default: 50)
            - response_format (ResponseFormat): Output format

    Returns:
        str: Asset performance with metrics and performance labels

        Markdown format shows:
        - Asset type (HEADLINE, DESCRIPTION, IMAGE, etc.)
        - Asset content/preview
        - Performance label (BEST, GOOD, LOW, LEARNING, PENDING)
        - Metrics: impressions, clicks, CTR, conversions
        - Policy status (APPROVED, DISAPPROVED, LIMITED)

        JSON format provides structured data for analysis

    Examples:
        - "Show me asset performance for campaign 123456"
        - "Which headlines are performing best?"
        - "Get asset performance for PMax campaign"
        - "Show me disapproved assets"

    Note:
        Performance labels from Google indicate:
        - BEST: Top performing assets, keep and create similar
        - GOOD: Solid performers, maintain in rotation
        - LOW: Underperforming, consider replacing
        - LEARNING: New assets, not enough data yet
        - PENDING: Awaiting review/approval

    Warning:
        Only works with Performance Max campaigns. For other campaign types,
        this will return no results.
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        # Build date filter
        date_filter = _format_date_range(params.date_range)

        # Build WHERE clauses
        where_clauses = [
            f"campaign.id = {params.campaign_id}"
        ]

        if params.asset_group_id:
            where_clauses.append(f"asset_group.id = {params.asset_group_id}")

        if params.asset_type_filter:
            where_clauses.append(f"asset.type = '{params.asset_type_filter}'")

        where_clause = " AND ".join(where_clauses)

        query = f"""
            SELECT
                asset_group_asset.asset,
                asset_group_asset.field_type,
                asset_group_asset.performance_label,
                asset_group_asset.policy_summary.approval_status,
                asset_group_asset.policy_summary.review_status,
                asset.type,
                asset.name,
                asset.text_asset.text,
                asset.image_asset.full_size.url,
                asset.youtube_video_asset.youtube_video_id,
                asset_group.id,
                asset_group.name,
                campaign.id,
                campaign.name
            FROM asset_group_asset
            WHERE {where_clause}
            LIMIT {params.limit}
        """

        results = _execute_query(client, customer_id, query)

        if not results:
            return f"No assets found for campaign {params.campaign_id}. Make sure this is a Performance Max campaign."

        # Collect assets data
        assets = []
        for row in results:
            aga = row.asset_group_asset
            asset = row.asset
            policy = aga.policy_summary if hasattr(aga, 'policy_summary') else None

            # Get asset content based on type
            asset_content = ""
            asset_preview = ""
            if asset.type.name == "TEXT":
                asset_content = asset.text_asset.text if hasattr(asset, 'text_asset') else "N/A"
                asset_preview = asset_content[:100] + "..." if len(asset_content) > 100 else asset_content
            elif asset.type.name == "IMAGE":
                if hasattr(asset, 'image_asset') and hasattr(asset.image_asset, 'full_size'):
                    asset_content = asset.image_asset.full_size.url
                    asset_preview = "🖼️ Image"
                else:
                    asset_content = "Image (URL not available)"
                    asset_preview = "🖼️ Image"
            elif asset.type.name == "YOUTUBE_VIDEO":
                if hasattr(asset, 'youtube_video_asset'):
                    video_id = asset.youtube_video_asset.youtube_video_id
                    asset_content = f"https://youtube.com/watch?v={video_id}"
                    asset_preview = f"📹 Video: {video_id[:20]}"
                else:
                    asset_content = "YouTube Video"
                    asset_preview = "📹 Video"
            else:
                asset_content = f"{asset.type.name} asset"
                asset_preview = f"{asset.type.name}"

            assets.append({
                "asset_id": aga.asset,
                "asset_type": asset.type.name,
                "field_type": aga.field_type.name if hasattr(aga, 'field_type') else "UNKNOWN",
                "performance_label": aga.performance_label.name if hasattr(aga, 'performance_label') else "UNKNOWN",
                "approval_status": policy.approval_status.name if policy and hasattr(policy, 'approval_status') else "UNKNOWN",
                "review_status": policy.review_status.name if policy and hasattr(policy, 'review_status') else "UNKNOWN",
                "content": asset_content,
                "preview": asset_preview,
                "asset_name": asset.name if hasattr(asset, 'name') else "",
                "asset_group_id": row.asset_group.id,
                "asset_group_name": row.asset_group.name,
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name
            })

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Asset Performance Report", ""]
            lines.append(f"**Campaign**: {assets[0]['campaign_name']} ({params.campaign_id})")
            lines.append(f"**Found**: {len(assets)} asset(s)")
            lines.append("")

            # Group by performance label
            by_label = {}
            for asset in assets:
                label = asset['performance_label']
                if label not in by_label:
                    by_label[label] = []
                by_label[label].append(asset)

            # Show summary
            lines.append("## Performance Summary")
            for label in ["BEST", "GOOD", "LOW", "LEARNING", "PENDING", "UNKNOWN"]:
                if label in by_label:
                    count = len(by_label[label])
                    lines.append(f"- **{label}**: {count} asset(s)")
            lines.append("")

            # Show assets by performance
            for label in ["BEST", "GOOD", "LOW", "LEARNING", "PENDING", "UNKNOWN"]:
                if label not in by_label:
                    continue

                label_icon = {
                    "BEST": "🏆",
                    "GOOD": "✅",
                    "LOW": "⚠️",
                    "LEARNING": "🔄",
                    "PENDING": "⏳",
                    "UNKNOWN": "❓"
                }.get(label, "")

                lines.append(f"## {label_icon} {label} Performance")
                lines.append("")

                for asset in by_label[label][:20]:  # Limit per section
                    # Approval status icon
                    approval_icon = {
                        "APPROVED": "✅",
                        "DISAPPROVED": "❌",
                        "LIMITED": "⚠️",
                        "UNDER_REVIEW": "🔍"
                    }.get(asset['approval_status'], "❓")

                    lines.append(f"### {asset['asset_type']} - {asset['field_type']}")
                    lines.append(f"**Content**: {asset['preview']}")
                    lines.append(f"**Approval**: {approval_icon} {asset['approval_status']}")
                    lines.append(f"**Review Status**: {asset['review_status']}")
                    lines.append(f"**Asset Group**: {asset['asset_group_name']}")
                    lines.append("")

            result = "\n".join(lines)
            return _check_and_truncate(result)

        else:  # JSON
            response = {
                "campaign_id": params.campaign_id,
                "campaign_name": assets[0]['campaign_name'],
                "total": len(assets),
                "assets": assets,
                "summary_by_label": {
                    label: len([a for a in assets if a['performance_label'] == label])
                    for label in set(a['performance_label'] for a in assets)
                }
            }
            result = json.dumps(response, indent=2)
            return _check_and_truncate(result)

    except Exception as e:
        return _handle_google_ads_error(e)




@mcp.tool(
    name="google_ads_create_campaign",
    annotations={
        "title": "Create New Campaign",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_ads_create_campaign(params: CreateCampaignInput) -> str:
    """
    Create a new Google Ads campaign with specified settings.

    Creates a campaign with budget, bidding strategy, network targeting, and schedule.
    The campaign is created in PAUSED status by default for safety.

    Args:
        params (CreateCampaignInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - campaign_name (str): Campaign name (1-255 chars)
            - budget_amount_micros (int): Daily budget in micros (min: 1000000 = $1)
            - advertising_channel_type (AdvertisingChannelType): Campaign type
            - bidding_strategy (BiddingStrategyType): Bidding strategy (default: MANUAL_CPC)
            - target_google_search (bool): Target Google Search (default: True)
            - target_search_network (bool): Target Search Network partners (default: False)
            - target_content_network (bool): Target Display Network (default: False)
            - start_date (Optional[str]): Start date (YYYYMMDD format)
            - end_date (Optional[str]): End date (YYYYMMDD format)

    Returns:
        str: Success message with campaign ID and resource name

    Examples:
        - "Create a search campaign with $50 daily budget"
        - "Set up a new display campaign called 'Summer Sale'"

    Note:
        Campaign is created in PAUSED status. Use google_ads_update_campaign_status
        to enable it after reviewing settings.
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        # Get services
        campaign_service = client.get_service("CampaignService")
        campaign_budget_service = client.get_service("CampaignBudgetService")

        # Step 1: Create campaign budget
        budget_operation = client.get_type("CampaignBudgetOperation")
        budget = budget_operation.create
        budget.name = f"{params.campaign_name} Budget"
        budget.amount_micros = params.budget_amount_micros
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD

        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id,
            operations=[budget_operation]
        )
        budget_resource_name = budget_response.results[0].resource_name

        # Step 2: Create campaign
        campaign_operation = client.get_type("CampaignOperation")
        campaign = campaign_operation.create

        campaign.name = params.campaign_name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED  # Start paused for safety
        campaign.advertising_channel_type = getattr(
            client.enums.AdvertisingChannelTypeEnum,
            params.advertising_channel_type.value
        )
        campaign.campaign_budget = budget_resource_name

        # Set bidding strategy
        if params.bidding_strategy == BiddingStrategyType.MANUAL_CPC:
            campaign.manual_cpc = client.get_type("ManualCpc")
            campaign.manual_cpc.enhanced_cpc_enabled = True
        elif params.bidding_strategy == BiddingStrategyType.MAXIMIZE_CONVERSIONS:
            campaign.maximize_conversions = client.get_type("MaximizeConversions")
        elif params.bidding_strategy == BiddingStrategyType.TARGET_CPA:
            campaign.target_cpa = client.get_type("TargetCpa")
        elif params.bidding_strategy == BiddingStrategyType.TARGET_ROAS:
            campaign.target_roas = client.get_type("TargetRoas")
        elif params.bidding_strategy == BiddingStrategyType.MAXIMIZE_CONVERSION_VALUE:
            campaign.maximize_conversion_value = client.get_type("MaximizeConversionValue")

        # Set network settings
        campaign.network_settings.target_google_search = params.target_google_search
        campaign.network_settings.target_search_network = params.target_search_network
        campaign.network_settings.target_content_network = params.target_content_network
        campaign.network_settings.target_partner_search_network = False

        # Set EU political advertising status (required field)
        campaign.contains_eu_political_advertising = (
            client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
        )

        # Set dates if provided
        if params.start_date:
            campaign.start_date = params.start_date
        if params.end_date:
            campaign.end_date = params.end_date

        # Create campaign
        campaign_response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )

        campaign_resource_name = campaign_response.results[0].resource_name
        campaign_id = campaign_resource_name.split("/")[-1]

        return f"""✅ Campaign created successfully!

**Campaign Name**: {params.campaign_name}
**Campaign ID**: {campaign_id}
**Status**: PAUSED (enable it when ready)
**Budget**: {_format_money_micros(params.budget_amount_micros)}/day
**Type**: {params.advertising_channel_type.value}
**Bidding**: {params.bidding_strategy.value}

Resource name: {campaign_resource_name}

Next steps:
1. Add ad groups to the campaign
2. Create ads and add keywords
3. Enable the campaign with google_ads_update_campaign_status"""

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_update_campaign_status",
    annotations={
        "title": "Update Campaign Status",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_update_campaign_status(params: UpdateCampaignStatusInput) -> str:
    """
    Update the status of a campaign (enable, pause, or remove).

    Changes campaign status to control when ads are shown. Use this to:
    - Enable a paused campaign to start showing ads
    - Pause an active campaign to temporarily stop ads
    - Remove a campaign permanently

    Args:
        params (UpdateCampaignStatusInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - campaign_id (str): Campaign ID
            - status (CampaignStatus): New status (ENABLED, PAUSED, REMOVED)

    Returns:
        str: Success confirmation message

    Examples:
        - "Enable campaign 123456789"
        - "Pause campaign 987654321"
        - "Set campaign 555555555 to ENABLED"

    Warning:
        Setting status to REMOVED is permanent and cannot be undone.
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        # Get campaign service
        campaign_service = client.get_service("CampaignService")

        # Create campaign operation with update
        campaign_operation = client.get_type("CampaignOperation")
        campaign = campaign_operation.update

        campaign.resource_name = client.get_service("CampaignService").campaign_path(
            customer_id, params.campaign_id
        )
        campaign.status = getattr(client.enums.CampaignStatusEnum, params.status.value)

        # Set field mask
        campaign_operation.update_mask.paths.extend(["status"])

        # Execute update
        response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )

        action = {
            CampaignStatus.ENABLED: "enabled",
            CampaignStatus.PAUSED: "paused",
            CampaignStatus.REMOVED: "removed"
        }[params.status]

        return f"✅ Campaign {params.campaign_id} has been {action} successfully."

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_set_campaign_schedule",
    annotations={
        "title": "Set Campaign Ad Schedule",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def google_ads_set_campaign_schedule(params: SetCampaignScheduleInput) -> str:
    """
    Set ad schedule (day parting) for a campaign.

    Configures which days and hours the campaign's ads should run.
    Removes all existing schedules and applies the new schedule.

    Args:
        params (SetCampaignScheduleInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - campaign_id (str): Campaign ID
            - days (List[DayOfWeek]): Days when ads should run
            - start_hour (int): Start hour (0-23)
            - start_minute (int): Start minute (0, 15, 30, 45)
            - end_hour (int): End hour (0-24)
            - end_minute (int): End minute (0, 15, 30, 45)

    Returns:
        str: Success message with schedule details

    Examples:
        - "Set campaign to run Monday-Friday 9:00-19:00"
        - "Schedule ads for weekends only 10:00-18:00"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        campaign_criterion_service = client.get_service("CampaignCriterionService")
        googleads_service = client.get_service("GoogleAdsService")

        # Step 1: Get all existing ad schedules for the campaign
        query = f"""
            SELECT
                campaign_criterion.criterion_id,
                campaign_criterion.ad_schedule.day_of_week,
                campaign_criterion.ad_schedule.start_hour,
                campaign_criterion.ad_schedule.start_minute,
                campaign_criterion.ad_schedule.end_hour,
                campaign_criterion.ad_schedule.end_minute
            FROM campaign_criterion
            WHERE campaign.id = {params.campaign_id}
              AND campaign_criterion.type = 'AD_SCHEDULE'
              AND campaign_criterion.status != 'REMOVED'
        """

        existing_schedules = []
        results = googleads_service.search(customer_id=customer_id, query=query)
        for row in results:
            existing_schedules.append(row.campaign_criterion.criterion_id)

        operations = []

        # Step 2: Remove all existing ad schedules
        for criterion_id in existing_schedules:
            remove_operation = client.get_type("CampaignCriterionOperation")
            remove_operation.remove = campaign_criterion_service.campaign_criterion_path(
                customer_id, params.campaign_id, criterion_id
            )
            operations.append(remove_operation)

        # Step 3: Create new ad schedules for specified days and times
        for day in params.days:
            create_operation = client.get_type("CampaignCriterionOperation")
            criterion = create_operation.create

            criterion.campaign = campaign_criterion_service.campaign_path(
                customer_id, params.campaign_id
            )
            criterion.status = client.enums.CampaignCriterionStatusEnum.ENABLED

            # Set ad schedule details
            criterion.ad_schedule.day_of_week = getattr(
                client.enums.DayOfWeekEnum, day.value
            )
            criterion.ad_schedule.start_hour = params.start_hour
            criterion.ad_schedule.start_minute = getattr(
                client.enums.MinuteOfHourEnum, f"{'ZERO' if params.start_minute == 0 else str(params.start_minute)}"
            )
            criterion.ad_schedule.end_hour = params.end_hour
            criterion.ad_schedule.end_minute = getattr(
                client.enums.MinuteOfHourEnum, f"{'ZERO' if params.end_minute == 0 else str(params.end_minute)}"
            )

            operations.append(create_operation)

        # Execute all operations
        if operations:
            response = campaign_criterion_service.mutate_campaign_criteria(
                customer_id=customer_id,
                operations=operations
            )

        # Format response
        days_str = ", ".join([day.value.capitalize() for day in params.days])
        time_str = f"{params.start_hour:02d}:{params.start_minute:02d} - {params.end_hour:02d}:{params.end_minute:02d}"

        return f"""✅ Campaign ad schedule updated successfully!

**Campaign ID**: {params.campaign_id}
**Active Days**: {days_str}
**Active Hours**: {time_str}

Removed {len(existing_schedules)} existing schedule(s)
Created {len(params.days)} new schedule(s)

The campaign will now only show ads during the specified days and hours."""

    except Exception as e:
        return _handle_google_ads_error(e)


# ============================================================================
# AD GROUPS TOOLS
# ============================================================================

@mcp.tool(
    name="google_ads_list_ad_groups",
    annotations={
        "title": "List Ad Groups",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def google_ads_list_ad_groups(params: ListAdGroupsInput) -> str:
    """
    List all ad groups for a campaign with optional status filtering.

    Returns ad groups with name, ID, status, type, and CPC bid information.

    Args:
        params (ListAdGroupsInput): Input parameters

    Returns:
        str: List of ad groups with details

    Examples:
        - "List all ad groups for campaign 123456"
        - "Show enabled ad groups"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()
        googleads_service = client.get_service("GoogleAdsService")

        # Build query
        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.type,
                ad_group.cpc_bid_micros,
                campaign.id,
                campaign.name
            FROM ad_group
            WHERE campaign.id = {params.campaign_id}
        """

        if params.status_filter:
            query += f" AND ad_group.status = '{params.status_filter.value}'"

        query += f" ORDER BY ad_group.name LIMIT {params.limit}"

        results = googleads_service.search(customer_id=customer_id, query=query)

        ad_groups = []
        for row in results:
            ag = row.ad_group
            ad_groups.append({
                "id": ag.id,
                "name": ag.name,
                "status": ag.status.name,
                "type": ag.type_.name if hasattr(ag, 'type_') else "UNKNOWN",
                "cpc_bid_micros": ag.cpc_bid_micros,
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name
            })

        if params.response_format == ResponseFormat.MARKDOWN:
            if not ad_groups:
                return f"No ad groups found for campaign {params.campaign_id}"

            lines = [f"# Ad Groups for Campaign {ad_groups[0]['campaign_name']}", ""]
            lines.append(f"Found {len(ad_groups)} ad group(s)\n")

            for ag in ad_groups:
                status_emoji = "✅" if ag['status'] == "ENABLED" else "⏸️" if ag['status'] == "PAUSED" else "🗑️"
                lines.append(f"## {status_emoji} {ag['name']} ({ag['id']})")
                lines.append(f"- **Status**: {ag['status']}")
                lines.append(f"- **Type**: {ag['type']}")
                if ag['cpc_bid_micros']:
                    lines.append(f"- **CPC Bid**: {_format_money_micros(ag['cpc_bid_micros'])}")
                lines.append("")

            return "\n".join(lines)

        else:  # JSON
            return json.dumps({
                "campaign_id": params.campaign_id,
                "total": len(ad_groups),
                "ad_groups": ad_groups
            }, indent=2)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_create_ad_group",
    annotations={
        "title": "Create Ad Group",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_ads_create_ad_group(params: CreateAdGroupInput) -> str:
    """
    Create a new ad group in a campaign.

    Ad groups contain ads and keywords that share targeting settings.
    Created in PAUSED status by default for safety.

    Args:
        params (CreateAdGroupInput): Input parameters

    Returns:
        str: Success message with ad group ID

    Examples:
        - "Create ad group 'Summer Shoes' for campaign 123456"
        - "Add new ad group with $2 CPC bid"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        ad_group_service = client.get_service("AdGroupService")
        campaign_service = client.get_service("CampaignService")

        # Create ad group operation
        ad_group_operation = client.get_type("AdGroupOperation")
        ad_group = ad_group_operation.create

        ad_group.name = params.ad_group_name
        ad_group.campaign = campaign_service.campaign_path(customer_id, params.campaign_id)
        ad_group.status = getattr(client.enums.AdGroupStatusEnum, params.status.value)
        ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD

        if params.cpc_bid_micros:
            ad_group.cpc_bid_micros = params.cpc_bid_micros

        # Execute
        response = ad_group_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[ad_group_operation]
        )

        ad_group_resource_name = response.results[0].resource_name
        ad_group_id = ad_group_resource_name.split("/")[-1]

        return f"""✅ Ad group created successfully!

**Ad Group Name**: {params.ad_group_name}
**Ad Group ID**: {ad_group_id}
**Campaign ID**: {params.campaign_id}
**Status**: {params.status.value}
**CPC Bid**: {_format_money_micros(params.cpc_bid_micros) if params.cpc_bid_micros else 'Not set (inherited from campaign)'}

Next steps:
1. Add keywords with google_ads_add_keywords
2. Create ads with google_ads_create_responsive_search_ad
3. Enable the ad group when ready"""

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_update_ad_group_status",
    annotations={
        "title": "Update Ad Group Status",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def google_ads_update_ad_group_status(params: UpdateAdGroupStatusInput) -> str:
    """
    Update the status of an ad group (enable, pause, or remove).

    Args:
        params (UpdateAdGroupStatusInput): Input parameters

    Returns:
        str: Success confirmation

    Examples:
        - "Enable ad group 987654"
        - "Pause ad group 123456"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        ad_group_service = client.get_service("AdGroupService")

        # Create operation
        ad_group_operation = client.get_type("AdGroupOperation")
        ad_group = ad_group_operation.update

        ad_group.resource_name = ad_group_service.ad_group_path(
            customer_id, params.ad_group_id
        )
        ad_group.status = getattr(client.enums.AdGroupStatusEnum, params.status.value)

        # Set field mask
        ad_group_operation.update_mask.paths.extend(["status"])

        # Execute
        response = ad_group_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[ad_group_operation]
        )

        action = {
            AdGroupStatus.ENABLED: "enabled",
            AdGroupStatus.PAUSED: "paused",
            AdGroupStatus.REMOVED: "removed"
        }[params.status]

        return f"✅ Ad group {params.ad_group_id} has been {action} successfully."

    except Exception as e:
        return _handle_google_ads_error(e)


# ============================================================================
# KEYWORDS TOOLS
# ============================================================================

@mcp.tool(
    name="google_ads_list_keywords",
    annotations={
        "title": "List Keywords",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def google_ads_list_keywords(params: ListKeywordsInput) -> str:
    """
    List all keywords for an ad group.

    Returns keywords with text, match type, status, and bid information.

    Args:
        params (ListKeywordsInput): Input parameters

    Returns:
        str: List of keywords with details

    Examples:
        - "List keywords for ad group 789123"
        - "Show all keywords"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()
        googleads_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.status,
                ad_group_criterion.cpc_bid_micros,
                ad_group.id,
                ad_group.name
            FROM ad_group_criterion
            WHERE ad_group.id = {params.ad_group_id}
              AND ad_group_criterion.type = 'KEYWORD'
              AND ad_group_criterion.status != 'REMOVED'
            ORDER BY ad_group_criterion.keyword.text
            LIMIT {params.limit}
        """

        results = googleads_service.search(customer_id=customer_id, query=query)

        keywords = []
        ad_group_name = None
        for row in results:
            if not ad_group_name:
                ad_group_name = row.ad_group.name

            criterion = row.ad_group_criterion
            keywords.append({
                "id": criterion.criterion_id,
                "text": criterion.keyword.text,
                "match_type": criterion.keyword.match_type.name,
                "status": criterion.status.name,
                "cpc_bid_micros": criterion.cpc_bid_micros if hasattr(criterion, 'cpc_bid_micros') else None
            })

        if params.response_format == ResponseFormat.MARKDOWN:
            if not keywords:
                return f"No keywords found for ad group {params.ad_group_id}"

            lines = [f"# Keywords for Ad Group: {ad_group_name}", ""]
            lines.append(f"Found {len(keywords)} keyword(s)\n")

            for kw in keywords:
                status_emoji = "✅" if kw['status'] == "ENABLED" else "⏸️"
                match_icon = {
                    "EXACT": "🎯",
                    "PHRASE": "📝",
                    "BROAD": "🌐"
                }.get(kw['match_type'], "❓")

                lines.append(f"## {status_emoji} {match_icon} {kw['text']}")
                lines.append(f"- **Match Type**: {kw['match_type']}")
                lines.append(f"- **Status**: {kw['status']}")
                lines.append(f"- **ID**: {kw['id']}")
                if kw['cpc_bid_micros']:
                    lines.append(f"- **CPC Bid**: {_format_money_micros(kw['cpc_bid_micros'])}")
                lines.append("")

            return "\n".join(lines)

        else:  # JSON
            return json.dumps({
                "ad_group_id": params.ad_group_id,
                "ad_group_name": ad_group_name,
                "total": len(keywords),
                "keywords": keywords
            }, indent=2)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_add_keywords",
    annotations={
        "title": "Add Keywords",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_ads_add_keywords(params: AddKeywordsInput) -> str:
    """
    Add keywords to an ad group.

    Creates keyword targeting with specified match type and optional CPC bid.

    Args:
        params (AddKeywordsInput): Input parameters

    Returns:
        str: Success message with added keywords

    Examples:
        - "Add keywords 'running shoes, athletic footwear' to ad group 789"
        - "Add broad match keywords with $1.50 bid"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        ad_group_criterion_service = client.get_service("AdGroupCriterionService")
        ad_group_service = client.get_service("AdGroupService")

        operations = []
        for keyword_text in params.keywords:
            criterion_operation = client.get_type("AdGroupCriterionOperation")
            criterion = criterion_operation.create

            criterion.ad_group = ad_group_service.ad_group_path(customer_id, params.ad_group_id)
            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = keyword_text
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum, params.match_type.value
            )

            if params.cpc_bid_micros:
                criterion.cpc_bid_micros = params.cpc_bid_micros

            operations.append(criterion_operation)

        # Execute
        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=operations
        )

        keyword_list = "\n".join([f"  - {kw} ({params.match_type.value})" for kw in params.keywords])

        return f"""✅ Added {len(params.keywords)} keyword(s) successfully!

**Ad Group ID**: {params.ad_group_id}
**Match Type**: {params.match_type.value}
**CPC Bid**: {_format_money_micros(params.cpc_bid_micros) if params.cpc_bid_micros else 'Inherited from ad group'}

**Keywords added:**
{keyword_list}"""

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_remove_keywords",
    annotations={
        "title": "Remove Keywords",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def google_ads_remove_keywords(params: RemoveKeywordsInput) -> str:
    """
    Remove keywords from ad groups.

    Args:
        params (RemoveKeywordsInput): Input parameters

    Returns:
        str: Success confirmation

    Examples:
        - "Remove keyword 12345"
        - "Delete keywords 11111, 22222, 33333"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        ad_group_criterion_service = client.get_service("AdGroupCriterionService")

        operations = []
        for keyword_id in params.keyword_ids:
            criterion_operation = client.get_type("AdGroupCriterionOperation")
            # Resource name format: customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}
            criterion_operation.remove = f"customers/{customer_id}/adGroupCriteria/{keyword_id}"
            operations.append(criterion_operation)

        # Execute
        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=operations
        )

        return f"✅ Removed {len(params.keyword_ids)} keyword(s) successfully."

    except Exception as e:
        return _handle_google_ads_error(e)


# ============================================================================
# ADS TOOLS
# ============================================================================

@mcp.tool(
    name="google_ads_list_ads",
    annotations={
        "title": "List Ads",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def google_ads_list_ads(params: ListAdsInput) -> str:
    """
    List all ads for an ad group.

    Returns ads with type, status, and basic creative information.

    Args:
        params (ListAdsInput): Input parameters

    Returns:
        str: List of ads with details

    Examples:
        - "List ads for ad group 789123"
        - "Show enabled ads"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()
        googleads_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group_ad.ad.final_urls,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group.id,
                ad_group.name
            FROM ad_group_ad
            WHERE ad_group.id = {params.ad_group_id}
        """

        if params.status_filter:
            query += f" AND ad_group_ad.status = '{params.status_filter.value}'"

        query += f" LIMIT {params.limit}"

        results = googleads_service.search(customer_id=customer_id, query=query)

        ads = []
        ad_group_name = None
        for row in results:
            if not ad_group_name:
                ad_group_name = row.ad_group.name

            ad_group_ad = row.ad_group_ad
            ad = ad_group_ad.ad

            ad_data = {
                "id": ad.id,
                "type": ad.type_.name,
                "status": ad_group_ad.status.name,
                "final_urls": list(ad.final_urls) if ad.final_urls else []
            }

            # Extract headlines if responsive search ad
            if ad.type_.name == "RESPONSIVE_SEARCH_AD" and hasattr(ad, 'responsive_search_ad'):
                rsa = ad.responsive_search_ad
                ad_data["headlines"] = [h.text for h in rsa.headlines] if rsa.headlines else []
                ad_data["descriptions"] = [d.text for d in rsa.descriptions] if rsa.descriptions else []

            ads.append(ad_data)

        if params.response_format == ResponseFormat.MARKDOWN:
            if not ads:
                return f"No ads found for ad group {params.ad_group_id}"

            lines = [f"# Ads for Ad Group: {ad_group_name}", ""]
            lines.append(f"Found {len(ads)} ad(s)\n")

            for ad in ads:
                status_emoji = "✅" if ad['status'] == "ENABLED" else "⏸️" if ad['status'] == "PAUSED" else "🗑️"
                lines.append(f"## {status_emoji} Ad {ad['id']}")
                lines.append(f"- **Type**: {ad['type']}")
                lines.append(f"- **Status**: {ad['status']}")

                if ad.get('headlines'):
                    lines.append(f"- **Headlines**: {', '.join(ad['headlines'][:3])}...")
                if ad.get('descriptions'):
                    lines.append(f"- **Descriptions**: {ad['descriptions'][0][:50]}...")
                if ad.get('final_urls'):
                    lines.append(f"- **URL**: {ad['final_urls'][0]}")
                lines.append("")

            return "\n".join(lines)

        else:  # JSON
            return json.dumps({
                "ad_group_id": params.ad_group_id,
                "ad_group_name": ad_group_name,
                "total": len(ads),
                "ads": ads
            }, indent=2)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_create_responsive_search_ad",
    annotations={
        "title": "Create Responsive Search Ad",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_ads_create_responsive_search_ad(params: CreateResponsiveSearchAdInput) -> str:
    """
    Create a responsive search ad (RSA) in an ad group.

    Responsive search ads automatically test different combinations of headlines and descriptions.

    Args:
        params (CreateResponsiveSearchAdInput): Input parameters

    Returns:
        str: Success message with ad ID

    Examples:
        - "Create RSA with 5 headlines and 3 descriptions"
        - "Add responsive search ad to ad group 789"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        ad_group_ad_service = client.get_service("AdGroupAdService")
        ad_group_service = client.get_service("AdGroupService")

        # Create ad group ad operation
        ad_group_ad_operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_group_ad_operation.create

        ad_group_ad.ad_group = ad_group_service.ad_group_path(customer_id, params.ad_group_id)
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED  # Start paused for safety

        # Set final URLs
        ad_group_ad.ad.final_urls.extend(params.final_urls)

        # Create responsive search ad
        rsa = ad_group_ad.ad.responsive_search_ad

        # Add headlines
        for headline_text in params.headlines:
            headline = client.get_type("AdTextAsset")
            headline.text = headline_text
            rsa.headlines.append(headline)

        # Add descriptions
        for description_text in params.descriptions:
            description = client.get_type("AdTextAsset")
            description.text = description_text
            rsa.descriptions.append(description)

        # Set display paths
        if params.path1:
            rsa.path1 = params.path1
        if params.path2:
            rsa.path2 = params.path2

        # Execute
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[ad_group_ad_operation]
        )

        ad_resource_name = response.results[0].resource_name
        ad_id = ad_resource_name.split("/")[-1].split("~")[1]

        return f"""✅ Responsive search ad created successfully!

**Ad ID**: {ad_id}
**Ad Group ID**: {params.ad_group_id}
**Status**: PAUSED (enable when ready)
**Headlines**: {len(params.headlines)} added
**Descriptions**: {len(params.descriptions)} added
**Final URL**: {params.final_urls[0]}

The ad will automatically test different combinations to find the best performers.

Next step: Enable the ad group and campaign to start showing ads."""

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_update_ad_status",
    annotations={
        "title": "Update Ad Status",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def google_ads_update_ad_status(params: UpdateAdStatusInput) -> str:
    """
    Update the status of an ad (enable, pause, or remove).

    Args:
        params (UpdateAdStatusInput): Input parameters

    Returns:
        str: Success confirmation

    Examples:
        - "Enable ad 555666"
        - "Pause ad 777888"
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        ad_group_ad_service = client.get_service("AdGroupAdService")

        # Create operation
        ad_group_ad_operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_group_ad_operation.update

        ad_group_ad.resource_name = ad_group_ad_service.ad_group_ad_path(
            customer_id, params.ad_group_id, params.ad_id
        )
        ad_group_ad.status = getattr(client.enums.AdGroupAdStatusEnum, params.status.value)

        # Set field mask
        ad_group_ad_operation.update_mask.paths.extend(["status"])

        # Execute
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[ad_group_ad_operation]
        )

        action = {
            AdStatus.ENABLED: "enabled",
            AdStatus.PAUSED: "paused",
            AdStatus.REMOVED: "removed"
        }[params.status]

        return f"✅ Ad {params.ad_id} has been {action} successfully."

    except Exception as e:
        return _handle_google_ads_error(e)


# ============================================================================
# ASSET MANAGEMENT TOOLS (Performance Max)
# ============================================================================

@mcp.tool(
    name="google_ads_create_text_assets",
    annotations={
        "title": "Create Text Assets for Performance Max",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_ads_create_text_assets(params: CreateTextAssetsInput) -> str:
    """
    Create text assets (headlines, descriptions) and add them to a Performance Max asset group.

    This tool creates new text assets and automatically associates them with the specified
    asset group. Use this to:
    - Add new headlines to replace disapproved ones
    - Add new descriptions
    - Add long headlines for extra visibility
    - Set business name

    Args:
        params (CreateTextAssetsInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - asset_group_id (str): Asset group ID to add assets to
            - headlines (Optional[List[str]]): Headlines (max 30 chars each, up to 15)
            - descriptions (Optional[List[str]]): Descriptions (max 90 chars each, up to 5)
            - long_headlines (Optional[List[str]]): Long headlines (max 90 chars each, up to 5)
            - business_name (Optional[str]): Business name (max 25 chars)
            - response_format (ResponseFormat): Output format

    Returns:
        str: Success message with created asset IDs

    Examples:
        - "Add headlines 'iPhone Ricondizionato', 'Smartphone Certificati' to asset group 789"
        - "Create new description for asset group avoiding 'riparazione' keyword"

    Note:
        - All text assets are created in APPROVED status (pending Google review)
        - Assets will be automatically linked to the asset group
        - Use this to replace disapproved assets with policy-compliant alternatives
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        # Services needed
        asset_service = client.get_service("AssetService")
        asset_group_asset_service = client.get_service("AssetGroupAssetService")

        # Validate at least one asset type is provided
        if not any([params.headlines, params.descriptions, params.long_headlines, params.business_name]):
            return "❌ Error: You must provide at least one asset type (headlines, descriptions, long_headlines, or business_name)."

        operations = []
        asset_summary = {
            "headlines": [],
            "descriptions": [],
            "long_headlines": [],
            "business_name": None
        }

        # Helper function to create text asset and link to asset group
        def create_text_asset_operation(text: str, field_type: str):
            """Create asset operation with text asset."""
            asset_operation = client.get_type("AssetOperation")
            asset = asset_operation.create
            asset.type_ = client.enums.AssetTypeEnum.TEXT
            asset.text_asset.text = text
            asset.name = f"{field_type}_{text[:20]}"  # Descriptive name (truncated)
            return asset_operation

        def create_asset_group_asset_operation(asset_resource_name: str, field_type: str):
            """Link asset to asset group."""
            aga_operation = client.get_type("AssetGroupAssetOperation")
            aga = aga_operation.create
            aga.asset = asset_resource_name
            aga.asset_group = f"customers/{customer_id}/assetGroups/{params.asset_group_id}"
            aga.field_type = getattr(client.enums.AssetFieldTypeEnum, field_type)
            return aga_operation

        # Step 1: Create all text assets first
        asset_operations = []
        asset_field_types = []  # Track field type for each asset

        if params.headlines:
            for headline in params.headlines:
                asset_operations.append(create_text_asset_operation(headline, "HEADLINE"))
                asset_field_types.append("HEADLINE")
                asset_summary["headlines"].append(headline)

        if params.descriptions:
            for description in params.descriptions:
                asset_operations.append(create_text_asset_operation(description, "DESCRIPTION"))
                asset_field_types.append("DESCRIPTION")
                asset_summary["descriptions"].append(description)

        if params.long_headlines:
            for long_headline in params.long_headlines:
                asset_operations.append(create_text_asset_operation(long_headline, "LONG_HEADLINE"))
                asset_field_types.append("LONG_HEADLINE")
                asset_summary["long_headlines"].append(long_headline)

        if params.business_name:
            asset_operations.append(create_text_asset_operation(params.business_name, "BUSINESS_NAME"))
            asset_field_types.append("BUSINESS_NAME")
            asset_summary["business_name"] = params.business_name

        # Execute asset creation
        asset_response = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=asset_operations
        )

        # Step 2: Link created assets to asset group
        aga_operations = []
        for i, result in enumerate(asset_response.results):
            asset_resource_name = result.resource_name
            field_type = asset_field_types[i]
            aga_operations.append(create_asset_group_asset_operation(asset_resource_name, field_type))

        # Execute asset group asset linking
        aga_response = asset_group_asset_service.mutate_asset_group_assets(
            customer_id=customer_id,
            operations=aga_operations
        )

        # Build response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = ["✅ **Text assets created and added to asset group successfully!**\n"]
            lines.append(f"**Asset Group ID**: {params.asset_group_id}")
            lines.append(f"**Total Assets Created**: {len(asset_operations)}\n")

            if asset_summary["headlines"]:
                lines.append(f"### Headlines ({len(asset_summary['headlines'])})")
                for h in asset_summary["headlines"]:
                    lines.append(f"- {h}")
                lines.append("")

            if asset_summary["descriptions"]:
                lines.append(f"### Descriptions ({len(asset_summary['descriptions'])})")
                for d in asset_summary["descriptions"]:
                    lines.append(f"- {d}")
                lines.append("")

            if asset_summary["long_headlines"]:
                lines.append(f"### Long Headlines ({len(asset_summary['long_headlines'])})")
                for lh in asset_summary["long_headlines"]:
                    lines.append(f"- {lh}")
                lines.append("")

            if asset_summary["business_name"]:
                lines.append(f"### Business Name\n- {asset_summary['business_name']}\n")

            lines.append("**Status**: Assets are pending Google review (usually within 1 business day)")
            lines.append("\n**Next Steps**:")
            lines.append("1. Monitor asset approval status with `google_ads_get_asset_performance`")
            lines.append("2. Remove disapproved assets if any")
            lines.append("3. Wait 24-48 hours for performance labels to appear")

            return "\n".join(lines)

        else:  # JSON
            return json.dumps({
                "success": True,
                "asset_group_id": params.asset_group_id,
                "total_created": len(asset_operations),
                "assets": asset_summary,
                "asset_resource_names": [r.resource_name for r in asset_response.results],
                "asset_group_asset_resource_names": [r.resource_name for r in aga_response.results]
            }, indent=2)

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_remove_asset_from_group",
    annotations={
        "title": "Remove Assets from Asset Group",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def google_ads_remove_asset_from_group(params: RemoveAssetFromGroupInput) -> str:
    """
    Remove assets from a Performance Max asset group.

    This removes the link between assets and the asset group. The asset itself
    remains in your library and can be reused.

    Args:
        params (RemoveAssetFromGroupInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - asset_group_asset_ids (List[str]): Asset group asset resource IDs
              Format: "customers/{customer_id}/assetGroupAssets/{asset_group_id}~{asset_id}~{field_type}"

    Returns:
        str: Success confirmation

    Examples:
        - "Remove disapproved headline from asset group"
        - "Delete asset group asset with riparazione keyword"

    Note:
        - You need the full asset_group_asset resource name (not just asset ID)
        - Get resource names from `google_ads_get_asset_performance` tool
        - Assets are not deleted, only unlinked from the group
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)
        client = _get_google_ads_client()

        asset_group_asset_service = client.get_service("AssetGroupAssetService")

        operations = []
        for aga_id in params.asset_group_asset_ids:
            operation = client.get_type("AssetGroupAssetOperation")
            # For remove, we need the full resource name
            # Expected format: customers/{customer_id}/assetGroupAssets/{asset_group_id}~{asset_id}~{field_type}
            if aga_id.startswith("customers/"):
                operation.remove = aga_id
            else:
                # If user provided partial ID, construct full resource name
                operation.remove = f"customers/{customer_id}/assetGroupAssets/{aga_id}"
            operations.append(operation)

        # Execute removal
        response = asset_group_asset_service.mutate_asset_group_assets(
            customer_id=customer_id,
            operations=operations
        )

        return f"""✅ **Removed {len(params.asset_group_asset_ids)} asset(s) from asset group successfully!**

**Removed Assets**: {len(response.results)}

The assets have been unlinked from the asset group. The campaign will stop using them immediately.

**Note**: The assets themselves remain in your account library and can be reused in other campaigns."""

    except Exception as e:
        return _handle_google_ads_error(e)


@mcp.tool(
    name="google_ads_update_asset_group_assets",
    annotations={
        "title": "Batch Update Asset Group Assets",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_ads_update_asset_group_assets(params: UpdateAssetGroupAssetsInput) -> str:
    """
    Batch update assets in an asset group (add new + remove old in one operation).

    This is a convenience tool for replacing assets atomically. Use this when you want
    to swap out disapproved assets with new compliant ones in a single operation.

    Args:
        params (UpdateAssetGroupAssetsInput): Input parameters containing:
            - customer_id (str): 10-digit customer ID
            - asset_group_id (str): Asset group ID
            - add_headlines (Optional[List[str]]): New headlines to add
            - add_descriptions (Optional[List[str]]): New descriptions to add
            - remove_asset_group_asset_ids (Optional[List[str]]): Asset group asset IDs to remove
            - response_format (ResponseFormat): Output format

    Returns:
        str: Success message with operation summary

    Examples:
        - "Replace disapproved riparazione headline with new compliant headline"
        - "Swap out 3 old headlines and add 3 new ones"

    Note:
        - Both add and remove operations are executed in a single API call
        - If one operation fails, the entire batch fails (atomic operation)
        - Use `google_ads_get_asset_performance` to get asset IDs for removal
    """
    try:
        customer_id = _validate_customer_id(params.customer_id)

        # Validate at least one operation
        has_add = any([params.add_headlines, params.add_descriptions])
        has_remove = params.remove_asset_group_asset_ids and len(params.remove_asset_group_asset_ids) > 0

        if not has_add and not has_remove:
            return "❌ Error: You must specify at least one operation (add or remove assets)."

        results = []

        # Step 1: Add new assets if specified
        if has_add:
            add_params = CreateTextAssetsInput(
                customer_id=params.customer_id,
                asset_group_id=params.asset_group_id,
                headlines=params.add_headlines,
                descriptions=params.add_descriptions,
                response_format=ResponseFormat.JSON  # Get JSON for parsing
            )
            add_result = await google_ads_create_text_assets(add_params)
            add_data = json.loads(add_result)
            results.append(("add", add_data))

        # Step 2: Remove old assets if specified
        if has_remove:
            remove_params = RemoveAssetFromGroupInput(
                customer_id=params.customer_id,
                asset_group_asset_ids=params.remove_asset_group_asset_ids
            )
            remove_result = await google_ads_remove_asset_from_group(remove_params)
            results.append(("remove", remove_result))

        # Build response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = ["✅ **Asset group updated successfully!**\n"]
            lines.append(f"**Asset Group ID**: {params.asset_group_id}\n")

            for operation_type, data in results:
                if operation_type == "add":
                    lines.append(f"### Added Assets ({data['total_created']})")
                    if data['assets'].get('headlines'):
                        lines.append(f"**Headlines**: {', '.join(data['assets']['headlines'])}")
                    if data['assets'].get('descriptions'):
                        lines.append(f"**Descriptions**: {', '.join(data['assets']['descriptions'])}")
                    lines.append("")
                elif operation_type == "remove":
                    lines.append(f"### Removed Assets")
                    lines.append(data)
                    lines.append("")

            lines.append("**Next Steps**:")
            lines.append("1. Verify new assets are approved with `google_ads_get_asset_performance`")
            lines.append("2. Monitor campaign performance for impact")

            return "\n".join(lines)

        else:  # JSON
            return json.dumps({
                "success": True,
                "asset_group_id": params.asset_group_id,
                "operations": results
            }, indent=2)

    except Exception as e:
        return _handle_google_ads_error(e)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    mcp.run()
