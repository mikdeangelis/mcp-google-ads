# Google Ads MCP Server

Model Context Protocol (MCP) server for Google Ads API integration. Provides comprehensive tools for managing Google Ads campaigns, ad groups, ads, keywords, assets, and performance insights.

## Features

### Phase 1 - MVP (Implemented)

**Account Management:**
- ✅ `google_ads_list_accounts` - List all accessible accounts
- ✅ `google_ads_get_account_info` - Get detailed account information

**Campaign Operations:**
- ✅ `google_ads_list_campaigns` - List campaigns with filtering and pagination
- ✅ `google_ads_get_campaign` - Get detailed campaign settings
- ✅ `google_ads_get_campaign_insights` - Get performance metrics
- ✅ `google_ads_create_campaign` - Create new campaigns
- ✅ `google_ads_update_campaign_status` - Enable/pause/remove campaigns

### Roadmap (Coming Soon)

**Phase 2 - Core Functionality:**
- Ad Groups (list, create, update, delete)
- Ads (list, create responsive search ads, update status)
- Keywords (list, add, update, remove, negative keywords)

**Phase 3 - Assets & Extensions:**
- Asset management (images, videos, text)
- Sitelinks (create, link to campaigns)
- Callouts (create, link)
- Structured Snippets (create, link)

**Phase 4 - Advanced:**
- Batch operations
- Advanced insights with breakdowns
- Asset groups for Performance Max

## Installation

### Prerequisites

- Python 3.9 or later
- Google Ads API access (developer token, OAuth2 credentials)
- Active Google Ads account

### Setup

1. **Clone or download this directory**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Google Ads API credentials:**

   Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```
   GOOGLE_ADS_DEVELOPER_TOKEN=your_token
   GOOGLE_ADS_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GOOGLE_ADS_CLIENT_SECRET=your_secret
   GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
   ```

### Getting Google Ads API Credentials

1. **Developer Token:**
   - Go to [Google Ads API Center](https://ads.google.com/aw/apicenter)
   - Apply for API access and get your developer token

2. **OAuth2 Credentials:**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com)
   - Enable Google Ads API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download client ID and secret

3. **Refresh Token:**
   - Use the [Google Ads API authentication guide](https://developers.google.com/google-ads/api/docs/oauth/overview)
   - Run OAuth flow to generate refresh token

## Usage

### Running the Server

```bash
python google_ads_mcp.py
```

### Adding to Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["/path/to/google-ads-mcp/google_ads_mcp.py"],
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "your_token",
        "GOOGLE_ADS_CLIENT_ID": "your_client_id",
        "GOOGLE_ADS_CLIENT_SECRET": "your_secret",
        "GOOGLE_ADS_REFRESH_TOKEN": "your_refresh_token"
      }
    }
  }
}
```

Or use environment variables:
```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["/path/to/google-ads-mcp/google_ads_mcp.py"]
    }
  }
}
```

## Tool Documentation

### Account Tools

#### `google_ads_list_accounts`
Lists all Google Ads accounts accessible with your credentials.

**Parameters:**
- `limit` (optional): Max accounts to return (1-100, default: 25)
- `response_format` (optional): "markdown" or "json" (default: markdown)

**Example:**
```
List all my Google Ads accounts
```

#### `google_ads_get_account_info`
Gets detailed information about a specific account.

**Parameters:**
- `customer_id` (required): 10-digit account ID
- `response_format` (optional): Output format

**Example:**
```
Get info for account 1234567890
```

### Campaign Tools

#### `google_ads_list_campaigns`
Lists campaigns with optional filtering.

**Parameters:**
- `customer_id` (required): 10-digit account ID
- `status_filter` (optional): ENABLED, PAUSED, or REMOVED
- `limit` (optional): Max campaigns (1-100, default: 20)
- `offset` (optional): Pagination offset (default: 0)
- `response_format` (optional): Output format

**Examples:**
```
List all campaigns for account 1234567890
Show me active campaigns
Get paused campaigns with limit 50
```

#### `google_ads_get_campaign`
Gets detailed settings for a specific campaign.

**Parameters:**
- `customer_id` (required): 10-digit account ID
- `campaign_id` (required): Campaign ID
- `response_format` (optional): Output format

**Example:**
```
Get details for campaign 123456789
```

#### `google_ads_get_campaign_insights`
Gets performance metrics for a campaign.

**Parameters:**
- `customer_id` (required): 10-digit account ID
- `campaign_id` (required): Campaign ID
- `date_range` (optional): TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, etc. (default: LAST_30_DAYS)
- `response_format` (optional): Output format

**Example:**
```
Get performance for campaign 123456789 in the last 7 days
```

#### `google_ads_create_campaign`
Creates a new campaign.

**Parameters:**
- `customer_id` (required): 10-digit account ID
- `campaign_name` (required): Campaign name (1-255 chars)
- `budget_amount_micros` (required): Daily budget in micros (min: 1000000 = $1)
- `advertising_channel_type` (required): SEARCH, DISPLAY, SHOPPING, VIDEO, PERFORMANCE_MAX, etc.
- `bidding_strategy` (optional): MANUAL_CPC, MAXIMIZE_CONVERSIONS, TARGET_CPA, etc. (default: MANUAL_CPC)
- `target_google_search` (optional): Target Google Search (default: true)
- `target_search_network` (optional): Target Search partners (default: false)
- `target_content_network` (optional): Target Display Network (default: false)
- `start_date` (optional): Start date (YYYYMMDD)
- `end_date` (optional): End date (YYYYMMDD)

**Example:**
```
Create a search campaign called "Summer Sale" with $50 daily budget
```

**Note:** Campaigns are created in PAUSED status for safety.

#### `google_ads_update_campaign_status`
Updates campaign status (enable, pause, or remove).

**Parameters:**
- `customer_id` (required): 10-digit account ID
- `campaign_id` (required): Campaign ID
- `status` (required): ENABLED, PAUSED, or REMOVED

**Examples:**
```
Enable campaign 123456789
Pause campaign 987654321
```

**Warning:** Setting status to REMOVED is permanent.

## Response Formats

### Markdown Format (Default)
Human-readable format with:
- Headers and sections
- Bullet points
- Tables for metrics
- Clear hierarchy
- Formatted dates and currency

### JSON Format
Machine-readable format with:
- Complete structured data
- All available fields
- Nested objects
- Pagination metadata

## Error Handling

The server provides clear, actionable error messages for:
- ✅ Authentication errors (invalid credentials)
- ✅ Authorization errors (no access to account)
- ✅ Rate limiting (API quota exceeded)
- ✅ Invalid customer IDs
- ✅ Resource not found
- ✅ Budget configuration issues
- ✅ Field validation errors

## Character Limits

Responses are automatically truncated at 25,000 characters with:
- Clear truncation warning
- Suggestion to use filters or pagination
- Indication of original size

## Best Practices

1. **Start Paused:** New campaigns are created in PAUSED status - review settings before enabling
2. **Test Accounts:** Use test accounts for development
3. **Monitor Budgets:** Set appropriate budget limits
4. **Use Filters:** Apply status filters and pagination for large accounts
5. **Check Permissions:** Ensure proper access to customer accounts

## Troubleshooting

### Authentication Errors
- Verify developer token is valid
- Check OAuth credentials are current
- Regenerate refresh token if expired

### Permission Errors
- Confirm you have access to the customer account
- For MCC accounts, set GOOGLE_ADS_LOGIN_CUSTOMER_ID

### Rate Limiting
- Implement delays between requests
- Use batch operations when available
- Monitor API quota in Google Ads API Center

## Development

### Testing
```bash
# Syntax check
python -m py_compile google_ads_mcp.py

# Run server
python google_ads_mcp.py
```

### Code Structure
- **Enums:** Response formats, campaign types, statuses
- **Pydantic Models:** Input validation with constraints
- **Utility Functions:** Shared logic (auth, errors, formatting)
- **Tool Implementations:** FastMCP decorated async functions

## Support

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [Google Ads Python Client](https://github.com/googleads/google-ads-python)
- [MCP Documentation](https://modelcontextprotocol.io)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Follow existing code style
2. Add comprehensive docstrings
3. Test with real Google Ads accounts
4. Update documentation

## Version History

### v1.0.0 (Phase 1 - MVP)
- Initial release
- Account management tools
- Campaign CRUD operations
- Performance insights
- Status updates

### Planned
- v1.1.0: Ad Groups and Ads (Phase 2)
- v1.2.0: Keywords and Negative Keywords (Phase 2)
- v1.3.0: Assets and Extensions (Phase 3)
- v2.0.0: Advanced Features (Phase 4)
