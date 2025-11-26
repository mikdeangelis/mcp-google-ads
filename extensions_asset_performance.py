# ============================================================================
# ASSET PERFORMANCE - Extension for google_ads_mcp.py
# ============================================================================
# Add these classes and functions to google_ads_mcp.py

# --- PYDANTIC INPUT MODELS (add near line 190) ---

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


# --- TOOL IMPLEMENTATION (add after google_ads_get_search_terms) ---

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
            f"campaign.id = {params.campaign_id}",
            date_filter
        ]

        if params.asset_group_id:
            where_clauses.append(f"asset_group.id = {params.asset_group_id}")

        if params.asset_type_filter:
            where_clauses.append(f"asset.type = '{params.asset_type_filter}'")

        if params.min_impressions:
            where_clauses.append(f"metrics.impressions >= {params.min_impressions}")

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
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM asset_group_asset
            WHERE {where_clause}
            ORDER BY metrics.impressions DESC
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
            metrics = row.metrics
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

            ctr = metrics.ctr * 100 if hasattr(metrics, 'ctr') else 0

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
                "campaign_name": row.campaign.name,
                "metrics": {
                    "impressions": metrics.impressions,
                    "clicks": metrics.clicks,
                    "ctr": round(ctr, 2),
                    "cost_micros": metrics.cost_micros,
                    "conversions": metrics.conversions if hasattr(metrics, 'conversions') else 0,
                    "conversions_value": metrics.conversions_value if hasattr(metrics, 'conversions_value') else 0
                }
            })

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Asset Performance Report", ""]
            lines.append(f"**Campaign**: {assets[0]['campaign_name']} ({params.campaign_id})")
            lines.append(f"**Date Range**: {params.date_range.value}")
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
                    m = asset['metrics']

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
                    lines.append(f"**Asset Group**: {asset['asset_group_name']}")
                    lines.append("")

                    lines.append("**Metrics:**")
                    lines.append(f"- Impressions: {m['impressions']:,}")
                    lines.append(f"- Clicks: {m['clicks']:,}")
                    lines.append(f"- CTR: {m['ctr']:.2f}%")
                    lines.append(f"- Cost: {_format_money_micros(m['cost_micros'])}")
                    if m['conversions'] > 0:
                        lines.append(f"- Conversions: {m['conversions']:.2f}")
                        lines.append(f"- Conv. Value: {_format_money_micros(int(m['conversions_value'] * 1_000_000))}")
                    lines.append("")

            result = "\n".join(lines)
            return _check_and_truncate(result)

        else:  # JSON
            response = {
                "campaign_id": params.campaign_id,
                "campaign_name": assets[0]['campaign_name'],
                "date_range": params.date_range.value,
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
