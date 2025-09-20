import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from datetime import datetime, timedelta
import calendar

# Page config
st.set_page_config(
    page_title="💰 Weekly Income Flow Planner", 
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "income_plans.json"

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .positive {
        border-left-color: #2ca02c !important;
    }
    .negative {
        border-left-color: #d62728 !important;
    }
    .warning {
        border-left-color: #ff7f0e !important;
    }
    .stButton > button {
        width: 100%;
    }
    .plan-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin-bottom: 0.5rem;
    }
    .active-plan {
        border-color: #1f77b4;
        background-color: #e3f2fd;
    }
    .week-selector {
        background-color: #fff;
        border: 2px solid #1f77b4;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def get_week_key(date):
    """Generate a unique key for a week based on the Monday of that week"""
    # Find the Monday of the week containing the given date
    days_since_monday = date.weekday()
    monday = date - timedelta(days=days_since_monday)
    return monday.strftime("%Y-%m-%d")

def get_week_display(week_key):
    """Convert week key to display format"""
    monday = datetime.strptime(week_key, "%Y-%m-%d")
    sunday = monday + timedelta(days=6)
    return f"Week of {monday.strftime('%b %d')} - {sunday.strftime('%b %d, %Y')}"

def migrate_old_data():
    """Migrate old income_data.json format to new weekly format"""
    old_file = "income_data.json"
    if os.path.exists(old_file) and not os.path.exists(DATA_FILE):
        try:
            with open(old_file, "r") as f:
                old_data = json.load(f)
            
            # Get current week
            current_week = get_week_key(datetime.now())
            
            # Create new format
            new_data = {
                "plans": {
                    current_week: {
                        "categories": old_data.get("categories", {}),
                        "income": old_data.get("income", 0.0),
                        "created_at": datetime.now().isoformat(),
                        "notes": "Migrated from old format"
                    }
                }
            }
            
            # Save in new format
            with open(DATA_FILE, "w") as f:
                json.dump(new_data, f, indent=2)
            
            st.success("✅ Migrated your existing data to the new weekly format!")
            
        except Exception as e:
            st.error(f"Error migrating data: {e}")

# Initialize session state
if 'current_week' not in st.session_state:
    st.session_state.current_week = get_week_key(datetime.now())

if 'plans' not in st.session_state:
    # Try to migrate old data first
    migrate_old_data()
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            st.session_state.plans = data.get("plans", {})
    else:
        st.session_state.plans = {}

# Ensure current week exists in plans
if st.session_state.current_week not in st.session_state.plans:
    st.session_state.plans[st.session_state.current_week] = {
        "categories": {"Rent": 250.0, "Car": 200.0, "Roth IRA": 100.0, "Savings": 100.0, "Food": 120.0, "Day-offs Leisure": 30.0},
        "income": 800.0,
        "created_at": datetime.now().isoformat(),
        "notes": ""
    }

def save_data():
    """Save all plans to JSON file"""
    with open(DATA_FILE, "w") as f:
        json.dump({"plans": st.session_state.plans}, f, indent=2)

def get_current_plan():
    """Get the currently selected plan"""
    return st.session_state.plans.get(st.session_state.current_week, {
        "categories": {},
        "income": 0.0,
        "created_at": datetime.now().isoformat(),
        "notes": ""
    })

def calculate_metrics(plan):
    """Calculate key financial metrics for a plan"""
    total_allocated = sum(plan.get("categories", {}).values())
    income = plan.get("income", 0.0)
    remaining = income - total_allocated
    allocation_percentage = (total_allocated / income * 100) if income > 0 else 0
    
    return {
        'total_allocated': total_allocated,
        'remaining': remaining,
        'allocation_percentage': allocation_percentage,
        'over_budget': remaining < 0
    }

# Header
st.title("📅 Weekly Income Flow Planner")
st.markdown("Create and manage weekly income allocation plans")

# Sidebar for week selection and plan management
with st.sidebar:
    st.header("📅 Week Selection")
    
    # Current week info
    current_plan = get_current_plan()
    st.markdown(f"**Current Week:** {get_week_display(st.session_state.current_week)}")
    
    # Week navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Prev"):
            current_date = datetime.strptime(st.session_state.current_week, "%Y-%m-%d")
            prev_week = current_date - timedelta(days=7)
            st.session_state.current_week = get_week_key(prev_week)
            st.rerun()
    
    with col2:
        if st.button("📅 Today"):
            st.session_state.current_week = get_week_key(datetime.now())
            st.rerun()
    
    with col3:
        if st.button("➡️ Next"):
            current_date = datetime.strptime(st.session_state.current_week, "%Y-%m-%d")
            next_week = current_date + timedelta(days=7)
            st.session_state.current_week = get_week_key(next_week)
            st.rerun()
    
    # Date picker for specific week
    st.markdown("**Jump to specific week:**")
    selected_date = st.date_input(
        "Select any date in the week",
        value=datetime.strptime(st.session_state.current_week, "%Y-%m-%d"),
        key="week_picker"
    )
    
    new_week_key = get_week_key(selected_date)
    if new_week_key != st.session_state.current_week:
        st.session_state.current_week = new_week_key
        st.rerun()
    
    st.divider()
    
    # Plan management
    st.header("📋 Plan Management")
    
    # Show if current week has a plan
    if st.session_state.current_week in st.session_state.plans:
        st.success("✅ Plan exists for this week")
    else:
        st.info("➕ No plan for this week yet")
        if st.button("Create Plan for This Week"):
            st.session_state.plans[st.session_state.current_week] = {
                "categories": {"Rent": 250.0, "Car": 200.0, "Savings": 100.0, "Food": 120.0},
                "income": 800.0,
                "created_at": datetime.now().isoformat(),
                "notes": ""
            }
            save_data()
            st.rerun()
    
    # Copy from template/previous week
    if st.session_state.plans:
        st.markdown("**Copy from existing plan:**")
        template_weeks = list(st.session_state.plans.keys())
        template_week = st.selectbox(
            "Select template week",
            options=template_weeks,
            format_func=get_week_display,
            key="template_selector"
        )
        
        if st.button("📋 Copy to Current Week"):
            template_plan = st.session_state.plans[template_week].copy()
            template_plan["created_at"] = datetime.now().isoformat()
            template_plan["notes"] = f"Copied from {get_week_display(template_week)}"
            st.session_state.plans[st.session_state.current_week] = template_plan
            save_data()
            st.success("Plan copied successfully!")
            st.rerun()
    
    st.divider()
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save"):
            save_data()
            st.success("Saved!")
    
    with col2:
        if st.button("🗑️ Delete"):
            if st.session_state.current_week in st.session_state.plans:
                del st.session_state.plans[st.session_state.current_week]
                save_data()
                st.success("Plan deleted!")
                st.rerun()

# Main content area
if st.session_state.current_week not in st.session_state.plans:
    st.warning(f"No plan exists for {get_week_display(st.session_state.current_week)}. Create one using the sidebar.")
    st.stop()

current_plan = get_current_plan()

# Plan overview section
st.subheader(f"📊 Plan Overview - {get_week_display(st.session_state.current_week)}")

# Add notes section
notes = st.text_area(
    "📝 Plan Notes",
    value=current_plan.get("notes", ""),
    placeholder="Add notes about this week's plan...",
    height=60
)
if notes != current_plan.get("notes", ""):
    st.session_state.plans[st.session_state.current_week]["notes"] = notes
    save_data()

# Income and metrics
col1, col2 = st.columns([3, 2])

with col1:
    # Income input
    income = st.number_input(
        "💰 Weekly Income ($)",
        min_value=0.0,
        step=50.0,
        value=float(current_plan.get("income", 0.0)),
        help="Enter your total weekly income"
    )
    
    if income != current_plan.get("income", 0.0):
        st.session_state.plans[st.session_state.current_week]["income"] = income
        save_data()

with col2:
    # Calculate and display metrics
    metrics = calculate_metrics(current_plan)
    
    if metrics['over_budget']:
        st.error(f"⚠️ Over budget by ${abs(metrics['remaining']):,.2f}")
    elif metrics['remaining'] < 50:
        st.warning(f"⚡ Low remaining: ${metrics['remaining']:,.2f}")
    else:
        st.success(f"✅ Remaining: ${metrics['remaining']:,.2f}")

# Key metrics row
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric("Weekly Income", f"${current_plan.get('income', 0):,.2f}")

with metric_col2:
    st.metric(
        "Allocated", 
        f"${metrics['total_allocated']:,.2f}",
        f"{metrics['allocation_percentage']:.1f}%"
    )

with metric_col3:
    delta_color = "normal" if metrics['remaining'] >= 0 else "inverse"
    st.metric(
        "Remaining", 
        f"${metrics['remaining']:,.2f}",
        delta_color=delta_color
    )

with metric_col4:
    num_categories = len(current_plan.get("categories", {}))
    st.metric("Categories", str(num_categories))

# Categories management
st.subheader("💳 Spending Categories")

# Two-column layout for categories
cat_col1, cat_col2 = st.columns([2, 1])

with cat_col1:
    categories = current_plan.get("categories", {})
    
    # Display existing categories
    for i, (cat, val) in enumerate(list(categories.items())):
        with st.expander(f"💰 {cat}: ${val:,.2f}", expanded=i < 4):
            col_amount, col_delete = st.columns([4, 1])
            
            with col_amount:
                new_val = st.number_input(
                    "Amount ($)",
                    min_value=0.0,
                    step=10.0,
                    value=float(val),
                    key=f"amount_{cat}_{st.session_state.current_week}",
                    help=f"Set amount for {cat}"
                )
                
                if new_val != val:
                    st.session_state.plans[st.session_state.current_week]["categories"][cat] = new_val
                    save_data()
            
            with col_delete:
                if st.button("🗑️", key=f"delete_{cat}_{st.session_state.current_week}", help=f"Delete {cat}"):
                    del st.session_state.plans[st.session_state.current_week]["categories"][cat]
                    save_data()
                    st.rerun()
    
    # Add new category
    st.markdown("---")
    st.markdown("**➕ Add New Category**")
    new_cat_col1, new_cat_col2, new_cat_col3 = st.columns([2, 1, 1])
    
    with new_cat_col1:
        new_cat = st.text_input("Category Name", placeholder="e.g., Entertainment", key=f"new_cat_{st.session_state.current_week}")
    
    with new_cat_col2:
        new_cat_amount = st.number_input("Amount", min_value=0.0, step=10.0, value=50.0, key=f"new_amount_{st.session_state.current_week}")
    
    with new_cat_col3:
        if st.button("Add", key=f"add_cat_{st.session_state.current_week}"):
            if new_cat and new_cat not in categories:
                st.session_state.plans[st.session_state.current_week]["categories"][new_cat] = new_cat_amount
                save_data()
                st.rerun()
            elif new_cat in categories:
                st.error("Category exists!")
            else:
                st.error("Enter category name!")

with cat_col2:
    st.markdown("**📈 Allocation Breakdown**")
    
    # Show percentage breakdown
    if current_plan.get("income", 0) > 0:
        for cat, val in categories.items():
            percentage = (val / current_plan["income"]) * 100
            st.markdown(f"**{cat}**")
            st.progress(min(percentage / 100, 1.0))
            st.caption(f"{percentage:.1f}% (${val:,.2f})")
    else:
        st.info("Set income to see percentages")

# Charts section
st.markdown("---")
st.subheader("📊 Visualizations")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Sankey Chart
    if categories:
        labels = ["💰 Income"] + [f"💳 {cat}" for cat in categories.keys()]
        
        if metrics['remaining'] > 0:
            labels.append("💼 Unallocated")
        
        sources = [0] * len(categories)
        targets = list(range(1, len(categories) + 1))
        values = list(categories.values())
        
        if metrics['remaining'] > 0:
            sources.append(0)
            targets.append(len(labels) - 1)
            values.append(metrics['remaining'])
        
        sankey_fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=['rgba(31,119,180,0.3)'] * len(values)
            )
        )])
        
        sankey_fig.update_layout(
            title_text="💸 Income Flow",
            font_size=12,
            height=400
        )
        st.plotly_chart(sankey_fig, use_container_width=True)

with chart_col2:
    # Pie chart
    if categories:
        df = pd.DataFrame(list(categories.items()), columns=['Category', 'Amount'])
        
        pie_fig = px.pie(
            df, 
            values='Amount', 
            names='Category',
            title='💰 Category Distribution',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
        pie_fig.update_layout(height=400)
        st.plotly_chart(pie_fig, use_container_width=True)

# Plans overview section
if len(st.session_state.plans) > 1:
    st.markdown("---")
    st.subheader("📋 All Plans Overview")
    
    # Create summary table
    summary_data = []
    for week_key, plan in sorted(st.session_state.plans.items()):
        plan_metrics = calculate_metrics(plan)
        summary_data.append({
            'Week': get_week_display(week_key),
            'Income': f"${plan.get('income', 0):,.2f}",
            'Allocated': f"${plan_metrics['total_allocated']:,.2f}",
            'Remaining': f"${plan_metrics['remaining']:,.2f}",
            'Categories': len(plan.get('categories', {})),
            'Status': '🔴 Over Budget' if plan_metrics['over_budget'] else 
                     '🟡 Tight' if plan_metrics['remaining'] < 50 else '🟢 Good'
        })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Quick stats
        total_weeks = len(st.session_state.plans)
        avg_income = sum(plan.get('income', 0) for plan in st.session_state.plans.values()) / total_weeks
        over_budget_weeks = sum(1 for plan in st.session_state.plans.values() if calculate_metrics(plan)['over_budget'])
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric("Total Plans", total_weeks)
        with stat_col2:
            st.metric("Avg Weekly Income", f"${avg_income:,.2f}")
        with stat_col3:
            st.metric("Over Budget Weeks", over_budget_weeks)

# Footer
st.markdown("---")
st.caption("💡 Tip: Use the sidebar to navigate between weeks and copy successful plans to future weeks!")