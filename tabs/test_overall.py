import streamlit as st
import pandas as pd
from components import styled_kpi_card
from streamlit_extras.stylable_container import stylable_container

def display(query_data, active_filters, min_date, max_date):
    # Helper function to safely handle None values
    def safe_value(val, default=0):
        return val if pd.notna(val) else default
    
    # Query summary data from the first table - adding KPI_Metric for filtering
    summary_columns = [
        "net_media_cost", "Cost", "plan_active_day", "active_day", "Impression", 
        "Engagements", "Clicks", "Views", "sessions", "add_to_carts", "ecommerce_purchases",
        "impression_plan", "engagement_plan", "click_plan", "views_plan"
    ]
    
    # Get all data for committed value calculation (without aggregations)
    all_data_df = query_data(
        columns=summary_columns + ["KPI_Metric"],  # Add KPI_Metric for filtering
        tablename="report_campaign_overall_total",
        filters=active_filters,
        start_date=min_date,
        end_date=max_date,
        aggregations=None,  # No aggregations to get individual rows
        group_by=None
    )
    
    if all_data_df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Calculate committed values based on KPI_Metric filtering
    committed_values = {}
    for _, row in all_data_df.iterrows():
        kpi_metric = row.get('KPI_Metric', '')
        if kpi_metric:
            if kpi_metric == 'Impression':
                committed_values['Impression'] = committed_values.get('Impression', 0) + safe_value(row['Impression'])
            elif kpi_metric == 'Engagement':
                committed_values['Engagements'] = committed_values.get('Engagements', 0) + safe_value(row['Engagements'])
            elif kpi_metric == 'Click':
                committed_values['Clicks'] = committed_values.get('Clicks', 0) + safe_value(row['Clicks'])
            elif kpi_metric == 'View':
                committed_values['Views'] = committed_values.get('Views', 0) + safe_value(row['Views'])
    
    # Get total data (sum of all rows)
    total_data_df = query_data(
        columns=summary_columns,
        tablename="report_campaign_overall_total",
        filters=active_filters,
        start_date=min_date,
        end_date=max_date,
        aggregations={
            "net_media_cost": "AVG", "plan_active_day": "AVG", "impression_plan": "AVG",
            "engagement_plan": "AVG", "click_plan": "AVG", "views_plan": "AVG",
            "Cost": "SUM", "active_day": "SUM", "Impression": "SUM", "Engagements": "SUM",
            "Clicks": "SUM", "Views": "SUM", "sessions": "SUM", "add_to_carts": "SUM",
            "ecommerce_purchases": "SUM"
        },
        group_by=[]  # No grouping for total values
    )
    
    if total_data_df.empty:
        st.warning("No data available for the selected filters.")
        return
        
    total_data = total_data_df.iloc[0]
    
    # --- Calculations ---
    run_rate = (safe_value(total_data['active_day']) / safe_value(total_data['plan_active_day'])) if safe_value(total_data['plan_active_day']) > 0 else 0
    spent = safe_value(total_data['Cost'])
    planned_spend = safe_value(total_data['net_media_cost'])
    progress_diff = run_rate - (spent / planned_spend) if planned_spend > 0 else 0

    # --- Page Layout ---
    st.header("Campaign Performance Overview")
    st.markdown("---")

    # --- Row 1: Key Performance Indicators (KPIs) ---
    st.subheader("Campaign Progress")
    display_campaign_calendar(
        active_days=int(safe_value(total_data['active_day'])),
        plan_days=int(safe_value(total_data['plan_active_day'])),
        spent=spent,
        planned_spend=planned_spend,
        progress_diff=progress_diff
    )

    st.markdown("---")

    # --- Row 2: Enhanced Metrics Cards with Total vs Committed ---
    st.subheader("Primary Metrics: Total vs Committed")
    
    color_map = {
        "blue": "rgba(59, 130, 246, 0.1)",
        "green": "rgba(16, 185, 129, 0.1)",
        "orange": "rgba(249, 115, 22, 0.1)",
        "purple": "rgba(168, 85, 247, 0.1)",
    }

    # Create enhanced metric cards with committed values from KPI_Metric filtering
    metrics_data = [
        {
            "name": "Impressions",
            "actual": safe_value(total_data['Impression']),
            "committed": committed_values.get('Impression', 0),
            "planned": safe_value(total_data['impression_plan']),
            "icon": "👁️",
            "color": "blue",
            "color_map": color_map
        },
        {
            "name": "Engagements", 
            "actual": safe_value(total_data['Engagements']),
            "committed": committed_values.get('Engagements', 0),
            "planned": safe_value(total_data['engagement_plan']),
            "icon": "👍",
            "color": "green",
            "color_map": color_map
        },
        {
            "name": "Clicks",
            "actual": safe_value(total_data['Clicks']),
            "committed": committed_values.get('Clicks', 0),
            "planned": safe_value(total_data['click_plan']),
            "icon": "🖱️",
            "color": "orange",
            "color_map": color_map
        },
        {
            "name": "Views",
            "actual": safe_value(total_data['Views']),
            "committed": committed_values.get('Views', 0),
            "planned": safe_value(total_data['views_plan']),
            "icon": "📺",
            "color": "purple",
            "color_map": color_map
        }
    ]
    
    # Display metrics in a 2x2 grid
    cols = st.columns(4)

    for idx, metric in enumerate(metrics_data):
        with cols[idx]:
            display_enhanced_metric_card(metric)

    # --- Row 3: GA / Conversion Metrics ---
    st.subheader("GA & Conversion Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🌐 Sessions", value=f"{safe_value(total_data['sessions']):,.0f}")
    with col2:
        st.metric(label="🛒 Add to Carts", value=f"{safe_value(total_data['add_to_carts']):,.0f}")
    with col3:
        st.metric(label="🛍️ Purchases", value=f"{safe_value(total_data['ecommerce_purchases']):,.0f}")

    # --- Row 4: Performance Summary Table ---
    st.markdown("---")
    st.subheader("📊 Performance Summary")
    
    # Create summary table
    summary_data = []
    for metric in metrics_data:
        actual_pct_committed = (metric['actual'] / metric['committed'] * 100) if metric['committed'] > 0 else 0
        
        summary_data.append({
            "Metric": metric['name'],
            "Total": f"{metric['actual']:,.0f}",
            "Committed": f"{metric['committed']:,.0f}",
            "Planned": f"{metric['planned']:,.0f}",
            "Total vs Committed": f"{actual_pct_committed:.1f}%" if metric['committed'] > 0 else "N/A",
            "Status": get_status_indicator(actual_pct_committed)
        })
    
    # Display as a styled table
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

def display_campaign_calendar(active_days, plan_days, spent, planned_spend, progress_diff):
    calendar_html = '<div class="calendar-container"><div class="calendar-grid">'
    for day in range(1, plan_days + 1):
        day_class = "calendar-day active" if day <= active_days else "calendar-day"
        calendar_html += f'<div class="{day_class}"></div>'
    calendar_html += '</div>'
    
    calendar_html += '<div class="calendar-metrics">'
    calendar_html += f"""
        <div class="calendar-metric-item">
            <div class="calendar-metric-label">Spent</div>
            <div class="calendar-metric-value">${spent:,.0f}</div>
        </div>
        <div class="calendar-metric-item">
            <div class="calendar-metric-label">Budget</div>
            <div class="calendar-metric-value">${planned_spend:,.0f}</div>
        </div>
        <div class="calendar-metric-item">
            <div class="calendar-metric-label">Progress</div>
            <div class="calendar-metric-value">{progress_diff:+.2f} pts</div>
        </div>
    """
    calendar_html += '</div></div>'
    
    st.markdown(calendar_html, unsafe_allow_html=True)

def display_enhanced_metric_card(metric):
    """Display a simplified and modern metric card with gradient progress bar."""

    actual_pct_committed = (metric['actual'] / metric['committed'] * 100) if metric['committed'] > 0 else 0
    progress_width = min(actual_pct_committed, 100)
    progress_color = "green" if actual_pct_committed >= 100 else "orange" if actual_pct_committed >= 80 else "red"
    metric_class = f"metric-card metric-card-{metric['name'].lower()}"
    
    # Get the background color from the color_map
    background_color = metric['color_map'].get(metric['color'], 'rgba(209, 213, 219, 0.1)')
    
    # Get the main color for the progress bar and text
    main_color = metric.get('color', '#6b7280')

    st.markdown(f"""
        <div class="{metric_class}" style="background: linear-gradient(to right, {background_color}, #ffffff);">
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <div style="font-size: 20px; margin-right: 8px;">{metric['icon']}</div>
                <div style="font-weight: 600; color: #1f2937;">{metric['name']}</div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #6b7280;">
                <div>Actual</div><div>Committed</div>
            </div>
            <div style="display: flex; justify-content: space-between; font-weight: 600; margin-bottom: 6px;">
                <div style="color: {main_color};">{metric['actual']:,.0f}</div>
                <div style="color: #111827;">{metric['committed']:,.0f}</div>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {progress_width}%; background-image: linear-gradient(to right, {main_color}, #d1fae5);"></div>
            </div>
            <div style="text-align: right; font-size: 11px; font-weight: 500; color: {progress_color}; margin-top: 2px;">
                {actual_pct_committed:.1f}%
            </div>
        </div>
    """, unsafe_allow_html=True)

def get_status_indicator(percentage):
    """Get status indicator based on percentage"""
    if percentage >= 100:
        return "✅ Exceeding"
    elif percentage >= 80:
        return "⚠️ On Track"
    else:
        return "❌ Behind"