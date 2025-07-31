import streamlit as st
import pandas as pd
from components import styled_kpi_card
from streamlit_extras.stylable_container import stylable_container

def display(query_data, active_filters, min_date, max_date):
    st.markdown("""
    <style>
        .progress-bar-container {
            width: 100%;
            background-color: #e5e7eb;
            border-radius: 4px;
            height: 10px;
            overflow: hidden;
        }
        .progress-bar {
            height: 10px;
            border-radius: 4px;
            transition: width 0.3s ease-in-out;
        }
    </style>
""", unsafe_allow_html=True)
    # Helper function to safely handle None values
    def safe_value(val, default=0):
        return val if pd.notna(val) else default
    
    # Query summary data from the first table - adding KPI_Metric for filtering
    summary_columns = [
        "net_media_cost", "Cost", "plan_active_day", "active_day", "Impression", 
        "Engagements", "Clicks", "Views", "sessions", "add_to_carts", "ecommerce_purchases",
        "impression_plan", "engagement_plan", "click_plan", "views_plan"
    ]
    
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
    st.subheader("Key Performance Indicators")
    col1, col2, col3 = st.columns(3)
    with col1:
        styled_kpi_card(
            title="Run Rate",
            value=f"{run_rate:.1%}",
            delta=f"{total_data['active_day']} of {total_data['plan_active_day']} days",
            icon="🏃‍♂️",
            progress_value=total_data['active_day'],
            progress_max=total_data['plan_active_day'],
            color="blue"
        )
    with col2:
        styled_kpi_card(
            title="Spent",
            value=f"${spent:,.0f}",
            delta=f"Budget: ${planned_spend:,.0f}",
            icon="💰",
            progress_value=spent,
            progress_max=planned_spend,
            color="green"
        )
    with col3:
        styled_kpi_card(
            title="Progress",
            value=f"{progress_diff:+.2f} pts",
            delta="Run Rate vs. Spending",
            icon="📈",
            progress_value=abs(progress_diff),
            progress_max=0.5,
            color="orange"
        )

    st.markdown("---")

    # --- Row 2: Enhanced Metrics Cards with Total vs Committed ---
    st.subheader("Primary Metrics: Total vs Committed")
    
    metrics_data = [
        {
            "name": "Impressions",
            "actual": safe_value(total_data['Impression']),
            "committed": safe_value(total_data['impression_plan']),
            "planned": safe_value(total_data['impression_plan']),
            "icon": "👁️",
            "color": "blue"
        },
        {
            "name": "Engagements", 
            "actual": safe_value(total_data['Engagements']),
            "committed": safe_value(total_data['engagement_plan']),
            "planned": safe_value(total_data['engagement_plan']),
            "icon": "👍",
            "color": "green"
        },
        {
            "name": "Clicks",
            "actual": safe_value(total_data['Clicks']),
            "committed": safe_value(total_data['click_plan']),
            "planned": safe_value(total_data['click_plan']),
            "icon": "🖱️",
            "color": "orange"
        },
        {
            "name": "Views",
            "actual": safe_value(total_data['Views']),
            "committed": safe_value(total_data['views_plan']),
            "planned": safe_value(total_data['views_plan']),
            "icon": "📺",
            "color": "purple"
        }
    ]
    
    # Display metrics in a single row with four columns
    cols = st.columns(4)
    for i, metric in enumerate(metrics_data):
        with cols[i]:
            display_enhanced_metric_card(metric)

    st.markdown("---")

    # --- Row 3: GA / Conversion Metrics ---
    st.subheader("GA & Conversion Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        styled_kpi_card(title="Sessions", value=f"{safe_value(total_data['sessions']):,.0f}", icon="🌐", progress_value=100, progress_max=100)
    with col2:
        styled_kpi_card(title="Add to Carts", value=f"{safe_value(total_data['add_to_carts']):,.0f}", icon="🛒", progress_value=100, progress_max=100)
    with col3:
        styled_kpi_card(title="Purchases", value=f"{safe_value(total_data['ecommerce_purchases']):,.0f}", icon="🛍️", progress_value=100, progress_max=100)

    # --- Row 4: Performance Summary Table ---
    st.markdown("---")
    st.subheader("📊 Performance Summary")
    
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
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

def display_enhanced_metric_card(metric):
    """Display a self-contained metric card using a single HTML block."""
    
    actual_pct_committed = (metric['actual'] / metric['committed'] * 100) if metric['committed'] > 0 else 0
    progress_width = min(actual_pct_committed, 100)
    
    progress_color = "green" if actual_pct_committed >= 100 else "orange" if actual_pct_committed >= 80 else "red"
    
    metric_class = f"metric-card metric-card-{metric['name'].lower()}"
# linear-gradient(to right, {metric['color_map'].get(metric['color'], 'rgba(209, 213, 219, 0.1)')}, #ffffff)
    card_html = f"""
        <div class="{metric_class}" style="background: linear-gradient(to right, {metric['color'], 'rgba(209, 213, 219, 0.1)'}, #ffffff); padding: 12px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <div style="display: flex; align-items: center;">
                <div style="font-size: 24px; text-align: center; padding-right: 10px;">{metric['icon']}</div>
                <h3 style="margin: 0; color: #1f2937; font-weight: 600; flex-grow: 1;">{metric['name']}</h3>
            </div>
            <hr style="margin: 10px 0; border-color: #e5e7eb;">
            <div style="display: flex; justify-content: space-between;">
                <div style="text-align: left;">
                    <p style="font-size: 11px; color: #6b7280; margin: 0;">Total (Actual)</p>
                    <p style="font-size: 22px; font-weight: 700; color: {metric['color']}; margin: 0;">{metric['actual']:,.0f}</p>
                </div>
                <div style="text-align: right;">
                    <p style="font-size: 11px; color: #6b7280; margin: 0;">Committed</p>
                    <p style="font-size: 22px; font-weight: 700; color: #1f2937; margin: 0;">{metric['committed']:,.0f}</p>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <p style="font-size: 10px; color: #6b7280; margin: 0;">Progress vs. Committed</p>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {progress_width}%; background-color: {progress_color};"></div>
                </div>
                <p style="font-size: 12px; font-weight: 600; color: {progress_color}; text-align: right; margin-top: -2px;">{actual_pct_committed:.1f}%</p>
            </div>
        </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def get_status_indicator(percentage):
    """Get status indicator based on percentage"""
    if percentage >= 100:
        return "✅ Exceeding"
    elif percentage >= 80:
        return "⚠️ On Track"
    else:
        return "❌ Behind"