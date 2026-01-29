# Google Ads MCP Server

Model Context Protocol (MCP) server for Google Ads API integration. Provides comprehensive tools for managing Google Ads campaigns, ad groups, ads, keywords, assets, and performance insights.

## Features

### Account Management
- `google_ads_list_accounts` - List all accessible accounts
- `google_ads_get_account_info` - Get detailed account information

### Campaign Operations
- `google_ads_list_campaigns` - List campaigns with filtering and pagination
- `google_ads_get_campaign` - Get detailed campaign settings
- `google_ads_get_campaign_insights` - Get performance metrics
- `google_ads_create_campaign` - Create new campaigns
- `google_ads_update_campaign_status` - Enable/pause/remove campaigns
- `google_ads_set_campaign_schedule` - Set ad scheduling (day parting)
- `google_ads_update_campaign_budget` - Update daily budget

### Ad Groups
- `google_ads_list_ad_groups` - List ad groups for a campaign
- `google_ads_create_ad_group` - Create new ad groups
- `google_ads_update_ad_group_status` - Enable/pause/remove ad groups

### Ads
- `google_ads_list_ads` - List ads for an ad group
- `google_ads_create_responsive_search_ad` - Create RSA ads
- `google_ads_update_ad_status` - Enable/pause/remove ads

### Keywords
- `google_ads_list_keywords` - List keywords for an ad group
- `google_ads_add_keywords` - Add keywords with match types
- `google_ads_remove_keywords` - Remove keywords

### Negative Keywords
- `google_ads_list_negative_keywords` - List negative keywords
- `google_ads_add_negative_keywords` - Add negative keywords (campaign/ad group level)
- `google_ads_remove_negative_keywords` - Remove negative keywords

### Performance Max Campaigns
- `google_ads_create_pmax_campaign` - **NEW** Create complete PMAX campaigns with text and image assets
- `google_ads_get_asset_performance` - Get PMax asset performance metrics
- `google_ads_create_text_assets` - Create and add text assets to asset groups
- `google_ads_remove_asset_from_group` - Remove assets from asset groups
- `google_ads_update_asset_group_assets` - Batch update assets (add + remove)

### Search Terms & Insights
- `google_ads_get_search_terms` - Get search terms report
- `google_ads_get_budget_utilization` - Check budget spend vs allocation

### Quality & Optimization
- `google_ads_get_keyword_quality_scores` - Get Quality Score breakdown
- `google_ads_get_ad_strength` - Get RSA Ad Strength ratings
- `google_ads_get_policy_issues` - Find disapproved ads/assets

### Recommendations
- `google_ads_list_recommendations` - List Google's optimization recommendations
- `google_ads_apply_recommendation` - Apply a recommendation
- `google_ads_dismiss_recommendation` - Dismiss a recommendation

### Conversion Tracking
- `google_ads_list_conversion_actions` - List configured conversion actions
- `google_ads_get_conversion_stats` - Get conversion statistics by campaign
- `google_ads_get_conversions_by_action` - **NEW** Get conversions breakdown by conversion action name
- `google_ads_get_campaign_conversion_goals` - Get campaign conversion goals configuration

### Geographic Targeting
- `google_ads_get_geo_targets` - Get campaign geo targeting settings
- `google_ads_search_geo_targets` - Search for locations to target
- `google_ads_set_geo_targets` - Add geo targeting (include/exclude)
- `google_ads_remove_geo_targets` - Remove geo targeting
- `google_ads_get_geo_performance` - Get performance by geographic location

## Installation

### Prerequisites

- Python 3.9 or later
- Google Ads API access (developer token, OAuth2 credentials)
- Active Google Ads account

### Setup

1. **Clone or download this repository**

2. **Create virtual environment and install dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
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
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_mcc_id  # Optional, for MCC accounts
   ```

### Getting Google Ads API Credentials

Segui questi 4 passaggi per ottenere tutte le credenziali necessarie.

#### Step 1: Developer Token (da Google Ads)

1. Vai su [Google Ads API Center](https://ads.google.com/aw/apicenter)
2. Accedi con l'account Google Ads
3. Richiedi l'accesso API (se non già attivo)
4. Copia il **Developer Token**

> **Nota:** Il token in modalità "test" funziona solo sui tuoi account. Per accesso completo serve approvazione.

#### Step 2: Progetto Google Cloud

1. Vai su [Google Cloud Console](https://console.cloud.google.com)
2. Crea un nuovo progetto (o selezionane uno esistente)
3. Vai su **APIs & Services → Library**
4. Cerca "Google Ads API" e clicca **Enable**

#### Step 3: Credenziali OAuth2

1. In Google Cloud Console, vai su **APIs & Services → Credentials**
2. Clicca **Create Credentials → OAuth 2.0 Client IDs**
3. Se richiesto, configura la schermata di consenso OAuth (tipo: External, inserisci nome app e email)
4. Seleziona **Application type: Desktop app**
5. Assegna un nome (es. "Google Ads MCP")
6. Clicca **Create**
7. Salva **Client ID** e **Client Secret**

#### Step 4: Genera il Refresh Token

Usa lo script incluso in questo repository:

```bash
# Dalla cartella del progetto mcp-google-ads
source .venv/bin/activate
python generate_token.py
```

Lo script:
1. Ti chiederà Client ID e Client Secret
2. Aprirà il browser per l'autorizzazione Google
3. Dopo l'autorizzazione, mostrerà il **Refresh Token**

Copia il token e aggiungilo al file `.env`.

#### Riepilogo Credenziali

| Credenziale | Dove trovarla |
|-------------|---------------|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads API Center |
| `GOOGLE_ADS_CLIENT_ID` | Google Cloud Console → Credentials |
| `GOOGLE_ADS_CLIENT_SECRET` | Google Cloud Console → Credentials |
| `GOOGLE_ADS_REFRESH_TOKEN` | Generato con `python generate_token.py` |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | ID account MCC (opzionale, 10 cifre senza trattini) |

## Usage

### Running the Server

```bash
source .venv/bin/activate
python google_ads_mcp.py
```

### Adding to Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "/path/to/mcp-google-ads/.venv/bin/python",
      "args": ["/path/to/mcp-google-ads/google_ads_mcp.py"],
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "your_token",
        "GOOGLE_ADS_CLIENT_ID": "your_client_id",
        "GOOGLE_ADS_CLIENT_SECRET": "your_secret",
        "GOOGLE_ADS_REFRESH_TOKEN": "your_refresh_token",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "your_mcc_id"
      }
    }
  }
}
```

### Adding to Claude Code

```bash
claude mcp add google-ads \
  -e GOOGLE_ADS_DEVELOPER_TOKEN=your_token \
  -e GOOGLE_ADS_CLIENT_ID=your_client_id \
  -e GOOGLE_ADS_CLIENT_SECRET=your_secret \
  -e GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token \
  -e GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_mcc_id \
  -- /path/to/mcp-google-ads/.venv/bin/python /path/to/mcp-google-ads/google_ads_mcp.py
```

## Tool Documentation

### Performance Max Campaign Creation

#### `google_ads_create_pmax_campaign`
Create a complete Performance Max campaign with all required assets in a single operation.

**Parameters:**
- `customer_id` (required): 10-digit account ID
- `campaign_name` (required): Campaign name
- `daily_budget_micros` (required): Daily budget in micros (1000000 = $1)
- `final_urls` (required): Landing page URLs (1-10)
- `headlines` (required): Headlines (3-15, max 30 chars each)
- `long_headlines` (required): Long headlines (1-5, max 90 chars each)
- `descriptions` (required): Descriptions (2-5, max 90 chars each)
- `business_name` (required): Business name (max 25 chars)
- `marketing_images` (required): Local file paths for landscape images (1.91:1 ratio)
- `square_marketing_images` (required): Local file paths for square images (1:1 ratio)
- `logo_images` (required): Local file paths for logo images (1:1 ratio)
- `portrait_marketing_images` (optional): Local file paths for portrait images (4:5 ratio)
- `geo_target_country_codes` (required): Country codes for targeting (e.g., ["IT", "US"])
- `bidding_strategy` (optional): MAXIMIZE_CONVERSIONS or MAXIMIZE_CONVERSION_VALUE
- `start_paused` (optional): Create paused for review (default: true)

**Example:**
```
Create a PMAX campaign "Summer Sale" with $50/day budget targeting Italy
```

**Features:**
- Creates budget, campaign, asset group, and all assets atomically
- Uploads images from local file paths
- Supports all PMAX asset types (text + images)
- Automatic geo targeting configuration
- Created in PAUSED status for safety review

### Conversion Tools

#### `google_ads_get_conversions_by_action`
Get conversions breakdown by conversion action name. Shows which conversion types are performing best.

**Parameters:**
- `customer_id` (required): 10-digit account ID
- `campaign_id` (optional): Filter by campaign
- `date_range` (optional): TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, etc. (default: LAST_30_DAYS)
- `min_conversions` (optional): Minimum conversions threshold (default: 0)
- `limit` (optional): Max results (1-200, default: 50)
- `response_format` (optional): "markdown" or "json"

**Example:**
```
Show me conversions breakdown by action for account 1234567890
Which conversion actions have the highest value?
```

**Note:** Cost/CPA metrics are not available per conversion action due to Google Ads API limitations. Use `google_ads_get_conversion_stats` for cost metrics at campaign level.

### Response Formats

#### Markdown Format (Default)
Human-readable format with:
- Headers and sections
- Bullet points
- Tables for metrics
- Clear hierarchy
- Formatted dates and currency

#### JSON Format
Machine-readable format with:
- Complete structured data
- All available fields
- Nested objects
- Pagination metadata

## Error Handling

The server provides clear, actionable error messages for:
- Authentication errors (invalid credentials)
- Authorization errors (no access to account)
- Rate limiting (API quota exceeded)
- Invalid customer IDs
- Resource not found
- Budget configuration issues
- Field validation errors

## Best Practices

1. **Start Paused:** New campaigns/ad groups are created in PAUSED status - review settings before enabling
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

## Support

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [Google Ads Python Client](https://github.com/googleads/google-ads-python)
- [MCP Documentation](https://modelcontextprotocol.io)

## License

MIT License - See LICENSE file for details

## Version History

### v1.4.0 (Current)
- Added `google_ads_create_pmax_campaign` - Create complete PMAX campaigns with text and image assets
- PMAX campaigns now support local image file uploads (marketing, square, logo, portrait)
- Atomic batch operations using `GoogleAdsService.Mutate` with temporary IDs
- All PMAX asset management tools tested and verified

### v1.3.0
- Added `google_ads_get_conversions_by_action` - Conversion breakdown by action name
- Full conversion tracking tools
- Geographic targeting and performance
- Performance Max asset management
- Quality scores and ad strength
- Recommendations management
- Budget utilization tracking

### v1.0.0 (Initial)
- Account management tools
- Campaign CRUD operations
- Ad groups, ads, keywords
- Performance insights
