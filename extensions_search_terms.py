# ============================================================================
# SEARCH TERMS REPORT - Extension for google_ads_mcp.py
# ============================================================================
# Add these classes and functions to google_ads_mcp.py

# --- PYDANTIC INPUT MODELS (add near line 190) ---

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


# --- TOOL IMPLEMENTATION (add after google_ads_get_campaign_insights) ---

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
