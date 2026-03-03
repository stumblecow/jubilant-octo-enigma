import streamlit as st
import pandas as pd
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Donation Dashboard",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Campaign Donation Dashboard")
st.markdown("---")

# ─────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────
uploaded_file = st.sidebar.file_uploader(
    "📁 Upload Donation CSV",
    type=["csv", "xlsx"]
)

@st.cache_data
def load_data(file):
    if file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Convert amount
    if 'Amount' in df.columns:
        df['Amount'] = (
            df['Amount']
            .astype(str)
            .str.replace('[$,]', '', regex=True)
            .str.strip()
        )
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

    # Convert date
    if 'Paid At' in df.columns:
        df['Paid At'] = pd.to_datetime(df['Paid At'], errors='coerce')
        df['Month'] = df['Paid At'].dt.to_period('M').astype(str)
        df['Year'] = df['Paid At'].dt.year

    # Clean tracker/district columns
    for col in ['In Tracker?', 'In District']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    return df

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
if uploaded_file is None:
    st.info("👈 Upload a CSV or Excel file in the sidebar to get started.")
    st.markdown("""
    ### Expected Columns:

| Column | Description |
| --- | --- |
| `Amount` | Donation amount |
| `Paid At` | Date of donation |
| `Full Name` | Donor full name |
| `Donor First Name` | First name |
| `Donor Last Name` | Last name |
| `Donor City` | City |
| `Donor State` | State |
| `Donor ZIP` | ZIP code |
| `In Tracker?` | Y/N — in tracker |
| `In District` | Y/N — in district |
| `Donor Occupation` | Occupation |
| `Donor Employer` | Employer |

    """)
    st.stop()

df = load_data(uploaded_file)

# ─────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────
st.sidebar.markdown("## 🔽 Filters")

# Date range filter
if 'Paid At' in df.columns and df['Paid At'].notna().any():
    min_date = df['Paid At'].min().date()
    max_date = df['Paid At'].max().date()
    date_range = st.sidebar.date_input(
        "📅 Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    if len(date_range) == 2:
        df = df[
            (df['Paid At'].dt.date >= date_range[0]) &
            (df['Paid At'].dt.date <= date_range[1])
        ]

# State filter
if 'Donor State' in df.columns:
    states = ['All'] + sorted(df['Donor State'].dropna().unique().tolist())
    selected_state = st.sidebar.selectbox("🗺️ State", states)
    if selected_state != 'All':
        df = df[df['Donor State'] == selected_state]

# In District filter
if 'In District' in df.columns:
    district_options = ['All'] + sorted(df['In District'].dropna().unique().tolist())
    selected_district = st.sidebar.selectbox("🏘️ In District", district_options)
    if selected_district != 'All':
        df = df[df['In District'] == selected_district]

# In Tracker filter
if 'In Tracker?' in df.columns:
    tracker_options = ['All'] + sorted(df['In Tracker?'].dropna().unique().tolist())
    selected_tracker = st.sidebar.selectbox("📋 In Tracker", tracker_options)
    if selected_tracker != 'All':
        df = df[df['In Tracker?'] == selected_tracker]

# Amount range filter
if 'Amount' in df.columns:
    min_amt = float(df['Amount'].min())
    max_amt = float(df['Amount'].max())
    amt_range = st.sidebar.slider(
        "💵 Amount Range ($)",
        min_value=min_amt,
        max_value=max_amt,
        value=(min_amt, max_amt)
    )
    df = df[
        (df['Amount'] >= amt_range[0]) &
        (df['Amount'] <= amt_range[1])
    ]

st.sidebar.markdown(f"**Showing {len(df):,} records**")

# ─────────────────────────────────────────
# KPI METRICS ROW
# ─────────────────────────────────────────
st.markdown("## 📊 Summary Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

total_raised = df['Amount'].sum() if 'Amount' in df.columns else 0
total_donors = df['Full Name'].nunique() if 'Full Name' in df.columns else 0
total_donations = len(df)
avg_donation = df['Amount'].mean() if 'Amount' in df.columns else 0
median_donation = df['Amount'].median() if 'Amount' in df.columns else 0

col1.metric("💰 Total Raised", f"${total_raised:,.2f}")
col2.metric("👥 Unique Donors", f"{total_donors:,}")
col3.metric("🔢 Total Donations", f"{total_donations:,}")
col4.metric("📈 Average Donation", f"${avg_donation:,.2f}")
col5.metric("📊 Median Donation", f"${median_donation:,.2f}")

# In District / In Tracker metrics
st.markdown("---")
col6, col7, col8, col9 = st.columns(4)

if 'In District' in df.columns:
    in_district = (df['In District'] == 'Y').sum()
    pct_district = (in_district / len(df) * 100) if len(df) > 0 else 0
    col6.metric("🏘️ In-District Donors", f"{in_district:,}")
    col7.metric("📍 % In-District", f"{pct_district:.1f}%")

if 'In Tracker?' in df.columns:
    in_tracker = (df['In Tracker?'] == 'Y').sum()
    pct_tracker = (in_tracker / len(df) * 100) if len(df) > 0 else 0
    col8.metric("📋 In Tracker", f"{in_tracker:,}")
    col9.metric("✅ % In Tracker", f"{pct_tracker:.1f}%")

st.markdown("---")

# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Timeline",
    "🏆 Top Donors",
    "🗺️ Geography",
    "🏢 Employer/Occupation",
    "🔍 Data Explorer",
    "🚨 Data Quality"
])

# ══════════════════════════════════════════
# TAB 1 — TIMELINE
# ══════════════════════════════════════════
with tab1:
    st.markdown("### 📅 Donations Over Time")

    if 'Paid At' in df.columns and df['Paid At'].notna().any():

        # Monthly totals
        monthly = (
            df.groupby('Month')['Amount']
            .agg(['sum', 'count'])
            .reset_index()
            .rename(columns={'sum': 'Total', 'count': 'Count'})
        )

        col_a, col_b = st.columns(2)

        with col_a:
            fig1 = px.bar(
                monthly,
                x='Month',
                y='Total',
                title='💰 Total Raised Per Month',
                labels={'Total': 'Amount ($)', 'Month': ''},
                color='Total',
                color_continuous_scale='Blues'
            )
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)

        with col_b:
            fig2 = px.line(
                monthly,
                x='Month',
                y='Count',
                title='🔢 Number of Donations Per Month',
                labels={'Count': '# Donations', 'Month': ''},
                markers=True
            )
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)

        # Cumulative
        df_sorted = df.sort_values('Paid At')
        df_sorted['Cumulative'] = df_sorted['Amount'].cumsum()
        fig3 = px.area(
            df_sorted,
            x='Paid At',
            y='Cumulative',
            title='📈 Cumulative Fundraising Over Time',
            labels={'Cumulative': 'Total Raised ($)', 'Paid At': 'Date'}
        )
        st.plotly_chart(fig3, use_container_width=True)

    else:
        st.warning("No valid date data found.")

# ══════════════════════════════════════════
# TAB 2 — TOP DONORS
# ══════════════════════════════════════════
with tab2:
    st.markdown("### 🏆 Top Donors")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        top_n = st.slider("Show Top N Donors", 5, 50, 10)

    if 'Full Name' in df.columns and 'Amount' in df.columns:
        top_donors = (
            df.groupby('Full Name')['Amount']
            .agg(['sum', 'count'])
            .reset_index()
            .rename(columns={'sum': 'Total Donated', 'count': 'Donations'})
            .sort_values('Total Donated', ascending=False)
            .head(top_n)
        )

        col_a, col_b = st.columns(2)

        with col_a:
            st.dataframe(
                top_donors.style.format({'Total Donated': '${:,.2f}'}),
                use_container_width=True
            )

        with col_b:
            fig4 = px.bar(
                top_donors.sort_values('Total Donated'),
                x='Total Donated',
                y='Full Name',
                orientation='h',
                title=f'Top {top_n} Donors by Total Amount',
                color='Total Donated',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig4, use_container_width=True)

        # Repeat donors
        st.markdown("### 🔄 Repeat Donors")
        repeat = top_donors[top_donors['Donations'] > 1].sort_values(
            'Donations', ascending=False
        )
        st.dataframe(
            repeat.style.format({'Total Donated': '${:,.2f}'}),
            use_container_width=True
        )

        # Donation size distribution
        st.markdown("### 📊 Donation Amount Distribution")
        fig5 = px.histogram(
            df,
            x='Amount',
            nbins=30,
            title='Distribution of Donation Amounts',
            labels={'Amount': 'Donation ($)', 'count': 'Frequency'}
        )
        st.plotly_chart(fig5, use_container_width=True)

# ══════════════════════════════════════════
# TAB 3 — GEOGRAPHY
# ══════════════════════════════════════════
with tab3:
    st.markdown("### 🗺️ Geographic Breakdown")

    if 'Donor State' in df.columns:
        state_totals = (
            df.groupby('Donor State')['Amount']
            .agg(['sum', 'count'])
            .reset_index()
            .rename(columns={'sum': 'Total', 'count': 'Donors'})
            .sort_values('Total', ascending=False)
        )

        col_a, col_b = st.columns(2)

        with col_a:
            fig6 = px.bar(
                state_totals.head(15),
                x='Donor State',
                y='Total',
                title='💰 Top States by Amount Raised',
                color='Total',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig6, use_container_width=True)

        with col_b:
            # Choropleth map
            fig7 = px.choropleth(
                state_totals,
                locations='Donor State',
                locationmode='USA-states',
                color='Total',
                scope='usa',
                title='🗺️ Donation Heatmap by State',
                color_continuous_scale='Blues',
                labels={'Total': 'Amount ($)'}
            )
            st.plotly_chart(fig7, use_container_width=True)

    # City breakdown
    if 'Donor City' in df.columns:
        st.markdown("### 🏙️ Top Cities")
        city_totals = (
            df.groupby(['Donor City', 'Donor State'])['Amount']
            .agg(['sum', 'count'])
            .reset_index()
            .rename(columns={'sum': 'Total', 'count': 'Donations'})
            .sort_values('Total', ascending=False)
            .head(15)
        )
        fig8 = px.bar(
            city_totals,
            x='Donor City',
            y='Total',
            color='Donor State',
            title='Top 15 Cities by Donations',
            labels={'Total': 'Amount ($)'}
        )
        fig8.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig8, use_container_width=True)

    # In District pie chart
    if 'In District' in df.columns:
        st.markdown("### 🏘️ In-District vs Out-of-District")
        district_counts = df['In District'].value_counts().reset_index()
        district_counts.columns = ['In District', 'Count']
        fig9 = px.pie(
            district_counts,
            names='In District',
            values='Count',
            title='In District vs Out of District',
            color_discrete_map={'Y': '#2ecc71', 'N': '#e74c3c'}
        )
