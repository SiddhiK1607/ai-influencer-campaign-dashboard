import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. SETTINGS ---
st.set_page_config(page_title="AI Influencer Campaign Tool: Vetting & Decision Dashboard", layout="wide")

st.title("🚀AI Influencer Campaign Tool: Vetting & Decision Dashboard")
st.info("Live Sync enabled with Google Sheets Backend")
st.divider()

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; padding: 15px; border-radius: 8px; }
    h1, h2, h3 { color: #58a6ff !important; }
    .stButton>button { background-color: #238636; color: white; border: none; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING ---
# New URL from your previous message
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTNNVXIp0kWpiCdq_L74i3HUVd1cdGeiaAnp5vAQzUPOgoTib3NAidpSl_en0vK-A/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(sheet_url)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        
        # Mapping specific column names from the new sheet
        df.rename(columns={'engagement_rate_%': 'engagement_rate', 'cost_per_post': 'cost'}, inplace=True)
        
        num_cols = ['followers', 'avg_views', 'engagement_rate', 'cost', 'creator_score']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

# --- 3. SESSION STATE ---
if "campaigns" not in st.session_state:
    st.session_state.campaigns = {}

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🎯 Campaign Manager", "📈 Insights"])

# ============================
# 📊 TAB 1: EXECUTIVE SUMMARY
# ============================
with tab1:
    st.subheader("Global Creator Database")
    if not df.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Talent Pool", len(df))
        m2.metric("Avg Quality Score", f"{df['creator_score'].mean():.1f}/5")
        m3.metric("Database Reach", f"{df['avg_views'].sum():,.0f} Views")
        st.divider()
        st.write("### Data Preview")
        st.dataframe(df.head(15), use_container_width=True)

# ============================
# 🎯 TAB 2: CAMPAIGN WORKFLOW (PDF REQUIREMENTS)
# ============================
with tab2:
    # Requirement 1: Select Action
    flow = st.radio("Step 1: Campaign Flow", ["Create New Campaign", "Select Existing Campaign"], horizontal=True)
    st.divider()

    if flow == "Create New Campaign":
        st.subheader("📝 Step 2: New Campaign Setup")
        
        # Requirement 2: Mandatory Fields
        next_id = len(st.session_state.campaigns) + 1
        c_code = st.text_input("Campaign Code (Mandatory) *", value=f"CMP{next_id:03d}")
        c_name = st.text_input("Campaign Name (Mandatory) *")
        
        niche_options = df['primary_niche'].dropna().unique() if not df.empty else []
        selected_niches = st.multiselect("Select Target Niches (Mandatory) *", niche_options)

        if st.button("Initialize & Save Campaign"):
            if c_name and selected_niches and c_code:
                if c_code in st.session_state.campaigns:
                    st.error("Campaign Code already exists. Please use a unique code.")
                else:
                    st.session_state.campaigns[c_code] = {
                        "name": c_name,
                        "niches": selected_niches,
                        "mappings": [] # Storage for vetted creators
                    }
                    st.success(f"Campaign '{c_name}' saved successfully!")
            else:
                st.error("Please fill all mandatory fields.")

    else:
        campaign_list = list(st.session_state.campaigns.keys())
        if not campaign_list:
            st.info("No active campaigns. Please create one first.")
        else:
            selected_id = st.selectbox("Step 2: Choose Campaign to Manage", campaign_list)
            camp_data = st.session_state.campaigns[selected_id]
            
            st.subheader(f"⚙️ Managing: {camp_data['name']} ({selected_id})")
            st.write(f"**Target Niches:** {', '.join(camp_data['niches'])}")
            
            # Requirement 3: Creator Filtering based on niches
            filtered_creators = df[df['primary_niche'].isin(camp_data['niches'])]
            
            st.divider()
            st.write(f"### Relevant Creators for {', '.join(camp_data['niches'])}")
            
            for i, row in filtered_creators.iterrows():
                with st.expander(f"👤 {row['name']} | Score: {row['creator_score']}/5", expanded=True):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"Niche: {row['primary_niche']} | Engagement: {row['engagement_rate']}%")
                        st.progress(min(float(row['creator_score'])/5, 1.0))
                    with col_b:
                        action = st.selectbox("Action", ["Pending", "Shortlist", "Reject","Backup"], key=f"sel_{selected_id}_{i}")
                        if st.button("Log Mapping", key=f"btn_{selected_id}_{i}"):
                            # Save to Mappings
                            mapping_entry = {
                                "Campaign_Code": selected_id,
                                "Creator_Name": row['name'],
                                "Status": action,
                                "Niche": row['primary_niche'],
                                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            st.session_state.campaigns[selected_id]['mappings'].append(mapping_entry)
                            st.toast(f"Mapped {row['name']} as {action}")

            # FINAL EXPORT
            if camp_data['mappings']:
                st.divider()
                st.subheader("📥 Final Campaign Mapping Log")
                mapping_df = pd.DataFrame(camp_data['mappings'])
                st.dataframe(mapping_df, use_container_width=True)
                
                csv = mapping_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Campaign Results (CSV)", csv, f"{selected_id}_results.csv", "text/csv")

# ============================
# 📈 TAB 3: INSIGHTS
# ============================
with tab3:
   # ============================
# 📈 TAB 3: INSIGHTS
# ============================

    st.subheader("Statistical Correlations")
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Reach vs Engagement**")
            st.scatter_chart(df, x='avg_views', y='engagement_rate', color='primary_niche')
        with c2:
            st.write("**Cost vs Quality ROI**")
            st.scatter_chart(df, x='cost', y='creator_score', color='ai_rank')
        
        st.divider()
        st.write("**Metric Correlation Matrix**")
        corr = df[['engagement_rate', 'creator_score', 'avg_views', 'cost']].corr()
        st.dataframe(corr.style.background_gradient(cmap='Blues'), use_container_width=True)