import streamlit as st
import pandas as pd
import psycopg2
import subprocess
import os
import platform
import shutil

from data_cleaner import clean_travel_data

from analytics.stats import (
    most_travelled_destination,
    most_used_transport,
    most_used_fuel,
    most_common_purpose,
    average_distance_monthly,
    fuel_cost_monthly,
    co2_monthly,
    distance_by_transport,
    average_companions,
    average_spent,
    average_toll,
    average_trip_duration,
    most_travelled_routes,
    average_spent_on_most_travelled_routes,
    calculate_trip_score,
    generate_trip_report,
    get_most_travelled_route,
)

from analytics.charts import plot_pie, plot_bar, plot_line

st.set_page_config(page_title="Travel Analytics Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("✈️ Travel Analytics Dashboard")
st.caption("Operational & Cost Insights Across Trips")

st.sidebar.header("Data Source")

data_source = st.sidebar.radio(
    "Choose data source",
    ["Excel Upload", "PostgreSQL Database", "Encrypted Container (VeraCrypt)"]
)

uploaded_file = None
df = None

DEFAULT_VERACRYPT_DIR = r"C:\\Users\\Arjun Gupta\\Desktop\\VeraCrypt"
DEFAULT_VERACRYPT_EXE = os.path.join(DEFAULT_VERACRYPT_DIR, "VeraCrypt.exe")
VERACRYPT_CLI = shutil.which("veracrypt") or shutil.which("veracrypt.exe") or (DEFAULT_VERACRYPT_EXE if os.path.exists(DEFAULT_VERACRYPT_EXE) else None)

def is_veracrypt_available():
    return VERACRYPT_CLI is not None

def mount_container_windows(container_path, drive_letter, password=None, keyfile=None, timeout=30):
    veracrypt = VERACRYPT_CLI
    if not veracrypt:
        return False, "VeraCrypt binary not found."
    drive = drive_letter.strip().rstrip(":").upper()
    cmd = [veracrypt, "/v", container_path, "/l", drive, "/q", "/s"]
    if password:
        cmd += ["/p", password]
    if keyfile:
        cmd += ["/k", keyfile]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return proc.returncode == 0, proc.stdout
    except Exception as e:
        return False, str(e)

def dismount_volume_windows(drive_letter, timeout=20):
    veracrypt = VERACRYPT_CLI
    if not veracrypt:
        return False, "VeraCrypt binary not found."
    drive = drive_letter.strip().rstrip(":").upper()
    target = drive if drive else drive_letter
    cmd = [veracrypt, "/d", target, "/q", "/s"]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return proc.returncode == 0, proc.stdout
    except Exception as e:
        return False, str(e)

def is_drive_mounted(drive_letter):
    drive = drive_letter.strip().rstrip(":").upper()
    path = f"{drive}:\\"
    return os.path.exists(path)

if data_source == "Excel Upload":
    uploaded_file = st.sidebar.file_uploader("Upload Travel Dataset (.xlsx)", type=["xlsx"])
    if not uploaded_file:
        st.info("Please upload an Excel file to view analytics.")
        st.stop()
    df = clean_travel_data(uploaded_file)

elif data_source == "PostgreSQL Database":
    st.sidebar.subheader("PostgreSQL Configuration")

    db_host = st.sidebar.text_input("Host", "localhost")
    db_port = st.sidebar.text_input("Port", "5432")
    db_name = st.sidebar.text_input("Database Name")
    db_user = st.sidebar.text_input("User")
    db_password = st.sidebar.text_input("Password", type="password")
    table_name = st.sidebar.text_input("Table Name", "travel_trip")

    if st.sidebar.button("Connect to Database"):
        try:
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password,
            )
            raw_df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            conn.close()
            df = clean_travel_data(raw_df)
            st.success("Connected to PostgreSQL successfully")
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            st.stop()

    if df is None:
        st.stop()

else:
    st.sidebar.subheader("VeraCrypt Encrypted Container")

    if not is_veracrypt_available():
        st.sidebar.error("VeraCrypt not found.")
        st.stop()

    container_path = st.sidebar.text_input("Container filepath", "")
    mount_point = st.sidebar.text_input("Drive letter", "X")

    use_keyfile = st.sidebar.checkbox("Use keyfile", True)
    keyfile_path = None
    password = None

    if use_keyfile:
        keyfile_path = st.sidebar.text_input("Keyfile path", "")
        password = st.sidebar.text_input("Password (optional)", type="password")
    else:
        password = st.sidebar.text_input("Password", type="password")
        keyfile_path = st.sidebar.text_input("Optional keyfile", "")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("Mount Container"):
            success, out = mount_container_windows(container_path, mount_point, password or None, keyfile_path or None)
            if success:
                st.sidebar.success("Mounted container.")
            else:
                st.sidebar.error(out)

    with col2:
        if st.button("Dismount Container"):
            target = mount_point if mount_point else container_path
            success, out = dismount_volume_windows(target)
            if success:
                st.sidebar.success("Dismounted container.")
            else:
                st.sidebar.error(out)

    inside_path = st.sidebar.text_input("File inside mounted container (full path)")

    if not inside_path:
        st.info("Provide spreadsheet path inside mounted container.")
        st.stop()

    if not os.path.exists(inside_path):
        st.error("File not found.")
        st.stop()

    try:
        if inside_path.lower().endswith(".csv"):
            raw_df = pd.read_csv(inside_path)
        else:
            raw_df = pd.read_excel(inside_path)
        df = clean_travel_data(raw_df)
    except Exception as e:
        st.error(f"Failed to read: {e}")
        st.stop()

def format_duration(seconds):
    seconds = int(seconds or 0)
    return f"{seconds//86400}d {(seconds%86400)//3600}h {seconds%60}s"

st.subheader("Key Performance Indicators")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Avg Spend (INR)", f"{average_spent(df):,.0f}")
c2.metric("Avg Toll (INR)", f"{average_toll(df):,.0f}")
c3.metric("Avg Companions", f"{average_companions(df):.2f}")
c4.metric("Avg Trip Duration", format_duration(average_trip_duration(df)))

st.divider()

st.subheader("Travel Distribution Insights")

# FIX: Avoid pie-pie combination
c5, c6 = st.columns(2)
with c5:
    st.plotly_chart(plot_pie(most_travelled_destination(df), "Most Travelled Destinations"), use_container_width=True)
with c6:
    st.plotly_chart(plot_bar(most_used_transport(df), "Transport Usage", "Mode", "Count"), use_container_width=True)

c7, c8 = st.columns(2)
with c7:
    st.plotly_chart(plot_pie(most_used_fuel(df), "Fuel Type Distribution"), use_container_width=True)
with c8:
    st.plotly_chart(plot_bar(most_common_purpose(df), "Trip Purpose Distribution", "Purpose", "Count"), use_container_width=True)

st.divider()

st.subheader("Time-Based Trends")

c9, c10 = st.columns(2)
with c9:
    st.plotly_chart(plot_line(average_distance_monthly(df), "Average Distance Per Month", "Month", "Distance (km)"), use_container_width=True)
with c10:
    st.plotly_chart(plot_line(fuel_cost_monthly(df), "Fuel Cost Over Time", "Month", "Cost (INR)"), use_container_width=True)

c11, c12 = st.columns(2)
with c11:
    st.plotly_chart(plot_line(co2_monthly(df), "CO₂ Emissions Over Time", "Month", "kg"), use_container_width=True)
with c12:
    st.plotly_chart(plot_bar(distance_by_transport(df), "Total Distance by Transport", "Transport", "Distance"), use_container_width=True)

st.divider()

st.subheader("Route Insights")

# Trip Score and Report for Most Travelled Route
most_travelled = get_most_travelled_route(df)
if most_travelled:
    trip_score, score_breakdown = calculate_trip_score(df, most_travelled)
    trip_report = generate_trip_report(df, most_travelled)
    
    col_score, col_report = st.columns([1, 2])
    
    with col_score:
        st.metric("📊 Trip Score (Most Travelled Route)", f"{trip_score}/100")
        st.caption(f"Route: {most_travelled}")
        
        # Score interpretation
        if trip_score >= 80:
            st.success("🟢 Excellent - Highly efficient and sustainable route")
        elif trip_score >= 60:
            st.info("🟡 Good - Reasonably efficient route")
        else:
            st.warning("🔴 Fair - Consider optimizing this route")
    
    with col_report:
        st.markdown("**Brief Trip Report**")
        if trip_report:
            report_text = f"""
- **Trips Count:** {trip_report['Trip Count']} trips
- **Total Distance:** {trip_report['Total Distance (km)']} km
- **CO₂ Emissions:** {trip_report['Total CO₂ Emissions (kg)']} kg
- **Total Cost:** ₹{trip_report['Total Cost (INR)']:,.0f}
- **Avg Cost per Trip:** ₹{trip_report['Avg Cost per Trip (INR)']:,.0f}
- **Avg Companions:** {trip_report['Avg Companions']}
- **Primary Transport:** {trip_report['Most Common Transport']}
- **Primary Fuel:** {trip_report['Most Common Fuel']}
            """
            st.markdown(report_text)
    
    # Score Breakdown Details
    with st.expander("📋 View Score Breakdown & Rating Logic"):
        st.markdown("### Trip Score Calculation Logic")
        st.markdown("The overall trip score is calculated from **4 key efficiency factors**:")
        
        breakdown_cols = st.columns(4)
        
        with breakdown_cols[0]:
            st.metric(
                "🌍 CO₂ Efficiency",
                f"{score_breakdown['co2_score']}/40",
                delta=f"{score_breakdown['avg_co2_per_km']} kg/km"
            )
            st.caption("Lower emissions = higher score")
        
        with breakdown_cols[1]:
            st.metric(
                "💰 Cost Efficiency", 
                f"{score_breakdown['cost_score']}/30",
                delta=f"₹{score_breakdown['avg_cost_per_km']}/km"
            )
            st.caption("Lower cost per km = higher score")
        
        with breakdown_cols[2]:
            st.metric(
                "📏 Distance Efficiency",
                f"{score_breakdown['distance_score']}/20",
                delta=f"{score_breakdown['avg_distance']} km avg"
            )
            st.caption("Longer routes = higher score")
        
        with breakdown_cols[3]:
            st.metric(
                "👥 Companion Ratio",
                f"{score_breakdown['companion_score']}/10",
                delta=f"{score_breakdown['avg_companions']} avg"
            )
            st.caption("More companions = higher score")
        
        st.divider()
        st.markdown("### Scoring Methodology")
        
        methodology = f"""
**Factor Weightage:**
- 🌍 **CO₂ Emissions (40%)** - Environmental impact
  - Baseline: 50 kg/km (maximum acceptable)
  - Current: {score_breakdown['avg_co2_per_km']} kg/km
  - Score: {score_breakdown['co2_score']}/40 points
  
- 💰 **Cost Efficiency (30%)** - Economic efficiency  
  - Baseline: 100 INR/km (maximum acceptable)
  - Current: ₹{score_breakdown['avg_cost_per_km']}/km
  - Score: {score_breakdown['cost_score']}/30 points
  
- 📏 **Distance Efficiency (20%)** - Route planning efficiency
  - Baseline: 500 km (optimal average distance)
  - Current: {score_breakdown['avg_distance']} km per trip
  - Score: {score_breakdown['distance_score']}/20 points
  
- 👥 **Companion Share (10%)** - Resource utilization
  - Baseline: 5 companions (optimal sharing)
  - Current: {score_breakdown['avg_companions']} companions avg
  - Score: {score_breakdown['companion_score']}/10 points

**Final Score: {trip_score}/100**
        """
        st.markdown(methodology)
        
        st.info("""
**Score Interpretation:**
- **80-100:** 🟢 Excellent - Route is highly optimized for sustainability and cost efficiency
- **60-79:** 🟡 Good - Route is reasonably efficient with room for optimization
- **Below 60:** 🔴 Fair - Consider reviewing transport mode, route planning, or trip consolidation
        """)


st.divider()

st.subheader("Top Routes Analysis")

st.markdown("**Routes by Trip Frequency**")
st.dataframe(most_travelled_routes(df), use_container_width=True)

st.markdown("**Average Spend by Route**")
st.dataframe(
    average_spent_on_most_travelled_routes(df).to_frame("Average Spend (INR)"),
    use_container_width=True,
)

with st.expander("View Cleaned Dataset"):
    st.dataframe(df.head(50), use_container_width=True)
