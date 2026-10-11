"""
Maharashtra Road Accident Risk Analytics — Streamlit app
IMPORTANT:
- Statewide annual figures below are transcribed from Maharashtra Highway Traffic Police
  (2019–2025; 2025 is provisional).
- A real district/highway incident-level dashboard requires an official incident-level
  dataset. This app does NOT convert synthetic/example rows into real statistics.
- Upload an official CSV/XLSX with one row per accident to enable district/highway analysis.
Run:
    pip install streamlit pandas numpy plotly openpyxl
    streamlit run app.py
"""
from pathlib import Path
import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Maharashtra Road Safety Intelligence", page_icon="🚦",
                   layout="wide", initial_sidebar_state="expanded")

BG = "#0B1220"
CARD = "#121C2F"
CYAN = "#22D3EE"
RED = "#F43F5E"
PURPLE = "#8B5CF6"
AMBER = "#F59E0B"
TEXT = "#E6EDF7"
MUTED = "#8EA0BC"

st.markdown(f"""
<style>
.stApp {{background:{BG}; color:{TEXT}}}
[data-testid="stSidebar"] {{background:#101A2B}}
.block-container {{padding-top:1.5rem; max-width:1600px}}
div[data-testid="stMetric"] {{background:{CARD}; padding:18px 20px; border-top:3px solid {CYAN}; border-radius:9px}}
div[data-testid="stMetricLabel"] p {{color:{MUTED} !important}}
div[data-testid="stMetricValue"] div {{color:{TEXT} !important}}
div[data-testid="stMetricDelta"] {{color:{TEXT} !important}}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] small {{color:{TEXT} !important}}
[data-testid="stFileUploader"] {{background:#FFFFFF; border-radius:10px; padding:8px}}
[data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label,
[data-testid="stCheckbox"] label {{color:{TEXT} !important}}
h1,h2,h3 {{color:{TEXT} !important}}
.small-note {{color:{MUTED}; font-size:0.9rem}}
</style>
""", unsafe_allow_html=True)

# Official statewide aggregate statistics from Maharashtra Highway Traffic Police.
# Counts are accidents by severity category; "total_killed" is people killed.
STATE = pd.DataFrame([
    [2019,11787,12788,12197,19152,5473,9476,3468,32925,False],
    [2020,10773,11569,9094,13971,3432,5943,1672,24971,False],
    [2021,12554,13528,10867,16073,4009,6998,2047,29477,False],
    [2022,14058,15224,12250,19540,4442,7699,2633,33383,False],
    [2023,14119,15366,13836,21446,4796,8318,2492,35243,False],
    [2024,14565,15715,14559,22051,4716,8484,2278,36118,False],
    [2025,14440,15549,15449,23756,4389,8391,2172,36450,True],
], columns=["year","fatal_accidents","total_killed","serious_accidents","seriously_injured",
            "minor_accidents","minor_injured","no_injury_accidents","total_accidents","provisional"])

EXPRESSWAYS = pd.DataFrame([
    ["Mumbai–Pune Expressway",2019,353,92],["Mumbai–Pune Expressway",2020,161,66],
    ["Mumbai–Pune Expressway",2021,200,88],["Mumbai–Pune Expressway",2022,198,92],
    ["Mumbai–Pune Expressway",2023,154,65],["Mumbai–Pune Expressway",2024,191,90],
    ["Mumbai–Pune Expressway",2025,187,68],
    ["Samruddhi Mahamarg",2022,21,1],["Samruddhi Mahamarg",2023,134,151],
    ["Samruddhi Mahamarg",2024,137,126],["Samruddhi Mahamarg",2025,185,152],
], columns=["highway","year","accidents","deaths"])
SOURCE_URL = "https://highwaypolice.maharashtra.gov.in/statics/"
TRANSPORT_URL = "https://transport.maharashtra.gov.in/1297/Statistics"
PUBLICATIONS_URL = "https://highwaypolice.maharashtra.gov.in/publication-page/"

def chart_layout(fig, height=390):
    fig.update_layout(
        height=height, paper_bgcolor=CARD, plot_bgcolor=CARD,
        font=dict(color=TEXT, family="Inter, Arial"),
        margin=dict(l=20,r=20,t=55,b=30),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.12),
        xaxis=dict(gridcolor="#243149", zerolinecolor="#243149"),
        yaxis=dict(gridcolor="#243149", zerolinecolor="#243149"),
    )
    return fig

def kpi_row(df):
    total = int(df["total_accidents"].sum())
    deaths = int(df["total_killed"].sum())
    fatal = int(df["fatal_accidents"].sum())
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Reported accidents", f"{total:,}")
    c2.metric("People killed", f"{deaths:,}")
    c3.metric("Fatal accidents", f"{fatal:,}")
    c4.metric("Deaths per fatal accident", f"{deaths/max(fatal,1):.2f}")

st.title("🚦 MAHARASHTRA ROAD SAFETY INTELLIGENCE")
st.caption("Official aggregate trends • District & highway explorer • transparent data provenance")

with st.sidebar:
    st.header("Dashboard controls")
    st.write("The statewide trend uses published official aggregate figures.")
    years = st.multiselect("Year", STATE.year.tolist(), default=STATE.year.tolist())
    st.divider()
    st.subheader("District / highway data")
    uploaded = st.file_uploader("Upload official accident-level CSV or Excel", type=["csv","xlsx"])
    user_confirms_official = st.checkbox(
        "I verified the uploaded file is from an official source and is not synthetic/demo data.",
        value=False
    )
    st.caption("Do not tick this for the provided 200,000-row synthetic sample.")

state = STATE[STATE.year.isin(years)].copy()
if state.empty:
    state = STATE.copy()

st.subheader("Statewide official annual statistics")
st.markdown(f'<p class="small-note">Source: <a href="{SOURCE_URL}">Maharashtra Highway Traffic Police</a>. '
            '2025 is marked provisional on the source page.</p>', unsafe_allow_html=True)
kpi_row(state)

left,right = st.columns([1.45,1])
with left:
    fig = px.line(state, x="year", y="total_accidents", markers=True,
                  title="Reported road accidents by year", labels={"year":"Year","total_accidents":"Accidents"})
    fig.update_traces(line=dict(color=CYAN,width=4), marker=dict(size=9))
    st.plotly_chart(chart_layout(fig), use_container_width=True)
with right:
    severity = pd.DataFrame({
        "Severity":["Fatal accidents","Serious-injury accidents","Minor-injury accidents","No-injury accidents"],
        "Count":[state.fatal_accidents.sum(),state.serious_accidents.sum(),
                 state.minor_accidents.sum(),state.no_injury_accidents.sum()]
    })
    fig = px.bar(severity, x="Severity", y="Count", color="Severity",
                 color_discrete_sequence=[RED,AMBER,CYAN,PURPLE], title="Accident severity categories")
    st.plotly_chart(chart_layout(fig), use_container_width=True)

fig = go.Figure()
fig.add_trace(go.Bar(x=state.year, y=state.total_killed, name="People killed", marker_color=RED))
fig.add_trace(go.Bar(x=state.year, y=state.seriously_injured, name="Seriously injured", marker_color=AMBER))
fig.add_trace(go.Bar(x=state.year, y=state.minor_injured, name="Minor injuries", marker_color=CYAN))
fig.update_layout(barmode="group", title="Human impact by year", xaxis_title="Year", yaxis_title="People")
st.plotly_chart(chart_layout(fig, 420), use_container_width=True)

st.subheader("Expressway statistics")
st.caption("Mumbai–Pune Expressway figures transcribed from the same official Highway Traffic Police page. These are expressway-specific and should not be added to statewide totals.")
ex_years = st.multiselect("Expressway year", EXPRESSWAYS.year.tolist(),
                          default=[y for y in EXPRESSWAYS.year.tolist() if y in years],
                          key="ex_years")
ex = EXPRESSWAYS[EXPRESSWAYS.year.isin(ex_years)]
if not ex.empty:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=ex.year, y=ex.accidents, name="Accidents", marker_color=CYAN))
    fig.add_trace(go.Scatter(x=ex.year, y=ex.deaths, name="Deaths", mode="lines+markers",
                             line=dict(color=RED,width=3), yaxis="y2"))
    fig.update_layout(title="Mumbai–Pune Expressway: accidents vs deaths",
                      yaxis=dict(title="Accidents"), yaxis2=dict(title="Deaths",overlaying="y",side="right"))
    st.plotly_chart(chart_layout(fig), use_container_width=True)
st.dataframe(ex, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Official uploaded data explorer")
st.caption("The uploader accepts official statewide aggregates, expressway summaries, or incident-level district/highway records. Each format is handled separately so aggregate rows are not miscounted as individual crashes.")
if uploaded is None:
    st.info("Upload one of the official CSV/XLSX formats to explore it here. The statewide and expressway charts above already use the published official figures.")
    st.markdown(f"""
- [Official Highway Traffic Police annual statistics]({SOURCE_URL})
- [Official Maharashtra Transport Department statistics]({TRANSPORT_URL})
- [Official road-accident reports / publications]({PUBLICATIONS_URL})
""")
else:
    try:
        raw = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)
        st.write(f"Uploaded file: **{uploaded.name}** · {len(raw):,} rows · {len(raw.columns)} columns")
        st.dataframe(raw.head(10), use_container_width=True)
        if not user_confirms_official:
            st.warning("Analysis is paused until you confirm the file is from an official source and is not synthetic/demo data.")
        else:
            df = raw.copy()
            # Normalize labels for flexible matching (spaces, punctuation, and case).
            def norm_col(value):
                import re
                return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
            lower_to_original = {norm_col(c): c for c in df.columns}
            def find_col(*names):
                for n in names:
                    if n in lower_to_original:
                        return lower_to_original[n]
                return None

            year_col = find_col("year", "accident_year")
            date_col = find_col("date", "accident_date", "crash_date")
            district_col = find_col("district", "district_name", "revenue_district", "police_unit", "unit_name")
            highway_col = find_col("road_name", "highway", "highway_name", "road", "nh_name", "route", "expressway")
            accidents_col = find_col("total_accidents", "reported_accidents", "accidents", "number_of_accidents", "no_of_accident", "no_of_accidents", "total_accident", "total_no_of_accidents")
            deaths_col = find_col("people_killed", "total_killed", "fatalities", "deaths", "persons_killed", "killed", "total_deaths", "total_killed_persons")
            fatal_col = find_col("fatal_accidents", "fatal_accident", "number_fatal_accidents", "no_of_fatal_accidents", "fatal_accident_count")
            serious_col = find_col("serious_injury_accidents", "serious_accidents", "seriously_injured_accidents", "serious_injury_accident", "no_of_serious_injury_accidents")
            minor_col = find_col("minor_injury_accidents", "minor_accidents", "minor_injury_accident", "no_of_minor_injury_accidents")
            noinjury_col = find_col("no_injury_accidents", "without_injury_accidents", "accidents_without_injury", "no_injury_accident")
            injured_col = find_col("total_casualties", "injured", "total_injured", "persons_injured", "people_seriously_injured", "total_seriously_injured", "total_minor_injured")

            if year_col is None and date_col:
                df["_parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
                df["_year"] = df["_parsed_date"].dt.year
                year_col = "_year"

            # Official statewide annual aggregate format (like the provided 2019–2025 CSV).
            if year_col and accidents_col and (deaths_col or fatal_col) and (fatal_col or serious_col or minor_col or noinjury_col or accidents_col) and district_col is None and highway_col is None:
                st.success("Detected official statewide annual aggregate data. Showing aggregate analysis (not incident-level district rankings).")
                df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
                df[accidents_col] = pd.to_numeric(df[accidents_col], errors="coerce")
                df[deaths_col] = pd.to_numeric(df[deaths_col], errors="coerce")
                available_years = sorted(df[year_col].dropna().astype(int).unique().tolist())
                selected_years = st.multiselect("Uploaded aggregate year filter", available_years, default=available_years, key="aggregate_year_filter")
                aggdf = df[df[year_col].isin(selected_years)].copy()
                m1,m2,m3 = st.columns(3)
                m1.metric("Reported accidents in uploaded file", f"{aggdf[accidents_col].sum():,.0f}")
                m2.metric("People killed in uploaded file", "Not available" if not deaths_col else f"{pd.to_numeric(aggdf[deaths_col], errors='coerce').fillna(0).sum():,.0f}")
                m3.metric("Years included", f"{aggdf[year_col].nunique():,.0f}")
                fig = px.line(aggdf, x=year_col, y=accidents_col, markers=True, title="Uploaded official annual accident trend")
                fig.update_traces(line=dict(color=CYAN, width=4), marker=dict(size=9))
                st.plotly_chart(chart_layout(fig), use_container_width=True)
                impact_cols = [c for c in [fatal_col, serious_col, minor_col, noinjury_col] if c]
                if impact_cols:
                    sev = pd.DataFrame({"Severity": [str(c).replace("_", " ").title() for c in impact_cols],
                                        "Accidents": [pd.to_numeric(aggdf[c], errors="coerce").fillna(0).sum() for c in impact_cols]})
                    fig = px.bar(sev, x="Severity", y="Accidents", title="Uploaded accident categories", color="Severity",
                                 color_discrete_sequence=[RED, AMBER, CYAN, PURPLE])
                    st.plotly_chart(chart_layout(fig), use_container_width=True)
                st.download_button("Download uploaded aggregate data", aggdf.to_csv(index=False).encode("utf-8"),
                                   "filtered_official_aggregate.csv", "text/csv")
                st.info("These figures are already aggregated by year. They cannot produce district or highway rankings unless those fields exist in the source data.")

            # Official road/expressway aggregate format.
            elif year_col and highway_col and accidents_col:
                st.success("Detected road/highway summary data. Each row is treated as an aggregate, not as one accident.")
                df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
                df[accidents_col] = pd.to_numeric(df[accidents_col], errors="coerce")
                if deaths_col:
                    df[deaths_col] = pd.to_numeric(df[deaths_col], errors="coerce")
                available_years = sorted(df[year_col].dropna().astype(int).unique().tolist())
                selected_years = st.multiselect("Uploaded road-data year filter", available_years, default=available_years, key="road_year_filter")
                roads = sorted(df[highway_col].dropna().astype(str).unique().tolist())
                selected_roads = st.multiselect("Road / highway filter", roads, default=roads, key="road_filter")
                road_df = df[df[year_col].isin(selected_years) & df[highway_col].astype(str).isin(selected_roads)].copy()
                m1,m2,m3 = st.columns(3)
                m1.metric("Reported accidents", f"{road_df[accidents_col].sum():,.0f}")
                m2.metric("People killed", "Not available" if not deaths_col else f"{road_df[deaths_col].sum():,.0f}")
                m3.metric("Roads included", f"{road_df[highway_col].nunique():,.0f}")
                fig = px.bar(road_df, x=year_col, y=accidents_col, color=highway_col, barmode="group", title="Accidents by road and year")
                st.plotly_chart(chart_layout(fig), use_container_width=True)
                if deaths_col:
                    fig = px.line(road_df, x=year_col, y=deaths_col, color=highway_col, markers=True, title="Deaths by road and year")
                    st.plotly_chart(chart_layout(fig), use_container_width=True)
                st.dataframe(road_df, use_container_width=True, hide_index=True)
                st.download_button("Download filtered road summary", road_df.to_csv(index=False).encode("utf-8"),
                                   "filtered_official_road_summary.csv", "text/csv")

            # Incident-level data with district and/or road labels.
            elif district_col or highway_col:
                st.success("Detected district/highway-labelled data. Review the source definition to confirm whether each row is one accident or an aggregate.")
                if year_col:
                    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
                    yr_vals = sorted(df[year_col].dropna().astype(int).unique().tolist())
                    yr_filter = st.multiselect("Uploaded-data year filter", yr_vals, default=yr_vals, key="incident_year_filter")
                    df = df[df[year_col].isin(yr_filter)]
                elif date_col:
                    df["_parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
                else:
                    st.warning("No year/date column detected; year filtering is unavailable.")
                dcol, hcol = st.columns(2)
                if district_col:
                    districts = sorted(df[district_col].dropna().astype(str).unique().tolist())
                    chosen_d = dcol.multiselect("District / police unit", districts, default=districts)
                    df = df[df[district_col].astype(str).isin(chosen_d)]
                if highway_col:
                    highways = sorted(df[highway_col].dropna().astype(str).unique().tolist())
                    chosen_h = hcol.multiselect("Highway / road", highways, default=highways)
                    df = df[df[highway_col].astype(str).isin(chosen_h)]
                count_col = find_col("accident_id", "fir_number", "case_id")
                n_acc = len(df) if count_col is None else df[count_col].nunique()
                n_deaths = pd.to_numeric(df[deaths_col], errors="coerce").fillna(0).sum() if deaths_col else np.nan
                n_injured = pd.to_numeric(df[injured_col], errors="coerce").fillna(0).sum() if injured_col else np.nan
                a,b,c = st.columns(3)
                a.metric("Rows / reported cases", f"{n_acc:,.0f}")
                b.metric("Deaths (if supplied)", "Not available" if pd.isna(n_deaths) else f"{n_deaths:,.0f}")
                c.metric("Injuries (if supplied)", "Not available" if pd.isna(n_injured) else f"{n_injured:,.0f}")
                if district_col:
                    agg = df.groupby(district_col, dropna=False).size().reset_index(name="records").sort_values("records",ascending=False)
                    fig = px.bar(agg.head(36).sort_values("records"), x="records", y=district_col, orientation="h",
                                 title="Records by district / police unit", color="records", color_continuous_scale=["#164E63",CYAN,RED])
                    st.plotly_chart(chart_layout(fig, max(400, min(900, 22*len(agg)))), use_container_width=True)
                if highway_col:
                    agg = df.groupby(highway_col, dropna=False).size().reset_index(name="records").sort_values("records",ascending=False)
                    fig = px.bar(agg.head(25).sort_values("records"), x="records", y=highway_col, orientation="h",
                                 title="Top 25 highways / roads by records", color="records", color_continuous_scale=["#164E63",CYAN,AMBER])
                    st.plotly_chart(chart_layout(fig, max(420, min(850, 25*min(len(agg),25)))), use_container_width=True)
                if district_col and highway_col:
                    st.markdown("**District × highway matrix**")
                    st.dataframe(pd.crosstab(df[district_col], df[highway_col]), use_container_width=True)
                if date_col and deaths_col:
                    temp = df.copy()
                    temp["_date"] = pd.to_datetime(temp[date_col], errors="coerce")
                    temp["_deaths_numeric"] = pd.to_numeric(temp[deaths_col], errors="coerce").fillna(0)
                    trend = temp.dropna(subset=["_date"]).groupby(temp["_date"].dt.to_period("M").astype(str)).agg(
                        records=("_date","size"), deaths=("_deaths_numeric","sum")).reset_index(names="month")
                    fig = px.line(trend, x="month", y="records", markers=True, title="Monthly accident records")
                    fig.update_traces(line=dict(color=CYAN,width=3))
                    st.plotly_chart(chart_layout(fig), use_container_width=True)
                st.download_button("Download filtered data as CSV", df.to_csv(index=False).encode("utf-8"),
                                   "filtered_maharashtra_road_accidents.csv", "text/csv")
            else:
                st.error("This file does not contain recognizable aggregate, road/highway, district, or incident-level columns. Check the column headers or download the official templates linked above.")
    except Exception as e:
        st.error(f"Could not read or analyse the uploaded file: {e}")

st.divider()
st.subheader("Data integrity & limitations")
st.markdown("""
- The statewide annual chart uses **published official aggregate values**, not the 200,000-row sample.
- A district or highway ranking is only as reliable as the uploaded underlying records. This app will not fabricate missing districts, highways, crash locations, or yearly counts.
- The official 2024 police-unit report uses **police units**, which do not always map one-to-one to civil districts.
- A risk-prediction model should only be trained on verified incident-level data with a documented target, train/test split, and validation. Do not report model accuracy from synthetic data as real-world performance.
""")
st.caption("Sources: Maharashtra Highway Traffic Police · Maharashtra Transport Department. Verify revisions and provisional figures against the linked source pages before publication.")
