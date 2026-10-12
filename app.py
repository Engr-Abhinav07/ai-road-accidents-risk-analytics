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
                if deaths_col:
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


# ---------------------------------------------------------------------------
# Automatic visual analytics for ANY uploaded CSV/XLSX dataset.
# This runs independently of the road-accident schema detector above.
# ---------------------------------------------------------------------------
if uploaded is not None:
    st.divider()
    st.subheader("✨ Automatic data visualization")
    st.caption(
        "Charts are selected from the columns found in your uploaded file. "
        "These exploratory charts describe the uploaded data; they do not verify its source."
    )
    try:
        file_bytes = uploaded.getvalue()
        if uploaded.name.lower().endswith(".csv"):
            # Try common encodings and let pandas infer the delimiter.
            try:
                auto_df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding="utf-8-sig")
            except UnicodeDecodeError:
                auto_df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding="latin-1")
        else:
            auto_df = pd.read_excel(io.BytesIO(file_bytes))

        if auto_df.empty or len(auto_df.columns) == 0:
            st.warning("The uploaded file has no data rows or columns to visualize.")
        else:
            import re

            def _auto_norm(value):
                return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")

            # Convert object columns to numeric only when most non-empty values parse.
            plot_df = auto_df.copy()
            for col in plot_df.columns:
                if not pd.api.types.is_numeric_dtype(plot_df[col]) and not pd.api.types.is_datetime64_any_dtype(plot_df[col]):
                    non_null = plot_df[col].dropna()
                    if len(non_null):
                        converted = pd.to_numeric(
                            non_null.astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False),
                            errors="coerce"
                        )
                        if converted.notna().mean() >= 0.85:
                            plot_df[col] = pd.to_numeric(
                                plot_df[col].astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False),
                                errors="coerce"
                            )

            # Detect date-like columns without blindly converting every text field.
            date_cols = [c for c in plot_df.columns if pd.api.types.is_datetime64_any_dtype(plot_df[c])]
            for col in plot_df.columns:
                if col in date_cols or plot_df[col].dtype != "object":
                    continue
                name = _auto_norm(col)
                if any(token in name for token in ("date", "time", "timestamp", "datetime")):
                    parsed = pd.to_datetime(plot_df[col], errors="coerce")
                    if parsed.notna().mean() >= 0.60:
                        plot_df[col] = parsed
                        date_cols.append(col)

            # Global filters: expose every year and every district/police unit present
            # in the uploaded data. These filters affect all automatic charts below.
            year_candidates = [c for c in plot_df.columns if _auto_norm(c) in {
                "year", "accident_year", "crash_year", "report_year", "calendar_year"
            }]
            year_filter_col = year_candidates[0] if year_candidates else None
            if year_filter_col is None and date_cols:
                year_filter_col = date_cols[0]

            district_name_tokens = {
                "district", "district_name", "districts", "revenue_district",
                "police_unit", "unit_name", "city", "city_name", "town", "region", "state", "state_ut"
            }
            district_candidates = [c for c in plot_df.columns if _auto_norm(c) in district_name_tokens
                                   or "district" in _auto_norm(c)]
            district_filter_col = district_candidates[0] if district_candidates else None

            filtered_df = plot_df.copy()
            st.markdown("#### Dataset filters")
            filter_cols = st.columns(2)
            if year_filter_col is not None:
                if year_filter_col in date_cols or pd.api.types.is_datetime64_any_dtype(filtered_df[year_filter_col]):
                    years_available = sorted(pd.to_datetime(filtered_df[year_filter_col], errors="coerce").dt.year.dropna().astype(int).unique().tolist())
                    chosen_years = filter_cols[0].multiselect(
                        f"Select year(s) — {year_filter_col}", years_available,
                        default=years_available, key="auto_all_year_filter"
                    )
                    date_years = pd.to_datetime(filtered_df[year_filter_col], errors="coerce").dt.year
                    filtered_df = filtered_df[date_years.isin(chosen_years)]
                else:
                    numeric_years = pd.to_numeric(filtered_df[year_filter_col], errors="coerce")
                    years_available = sorted(numeric_years.dropna().unique().tolist())
                    chosen_years = filter_cols[0].multiselect(
                        f"Select year(s) — {year_filter_col}", years_available,
                        default=years_available, key="auto_all_year_filter"
                    )
                    filtered_df = filtered_df[numeric_years.isin(chosen_years)]
            else:
                filter_cols[0].caption("No year/date column detected; all rows are included.")

            if district_filter_col is not None:
                districts_available = sorted(filtered_df[district_filter_col].dropna().astype(str).unique().tolist())
                chosen_districts = filter_cols[1].multiselect(
                    f"Select district / location — {district_filter_col}",
                    options=districts_available, default=districts_available,
                    key="auto_all_district_filter", help="All values in this column are available; clear selections to inspect a subset."
                )
                filtered_df = filtered_df[filtered_df[district_filter_col].astype(str).isin(chosen_districts)]
            else:
                filter_cols[1].caption("No district/location column detected in this file.")

            # Optional filter for any other categorical field, not only districts.
            categorical_filter_candidates = [c for c in filtered_df.columns
                if not pd.api.types.is_numeric_dtype(filtered_df[c])
                and not pd.api.types.is_datetime64_any_dtype(filtered_df[c])
                and 1 < filtered_df[c].nunique(dropna=True) <= 500]
            if categorical_filter_candidates:
                other_filter_col = st.selectbox(
                    "Optional filter for any other category", ["(No extra filter)"] + categorical_filter_candidates,
                    key="auto_extra_filter_column"
                )
                if other_filter_col != "(No extra filter)":
                    extra_values = sorted(filtered_df[other_filter_col].dropna().astype(str).unique().tolist())
                    selected_extra_values = st.multiselect(
                        f"Select values — {other_filter_col}", extra_values,
                        default=extra_values, key="auto_extra_filter_values"
                    )
                    filtered_df = filtered_df[filtered_df[other_filter_col].astype(str).isin(selected_extra_values)]

            st.caption(f"Charts use {len(filtered_df):,} of {len(auto_df):,} uploaded rows after filtering.")
            # All charts and column selectors below use the filtered data.
            plot_df = filtered_df.copy()

            numeric_cols_all = plot_df.select_dtypes(include=np.number).columns.tolist()
            id_tokens = ("id", "index", "serial", "sr_no", "s_no", "phone", "mobile", "postal", "pincode", "zip")
            numeric_cols = [
                c for c in numeric_cols_all
                if not any(token == part for token in id_tokens for part in _auto_norm(c).split("_"))
                and plot_df[c].nunique(dropna=True) > 1
            ]
            categorical_cols = [
                c for c in plot_df.columns
                if c not in numeric_cols_all and c not in date_cols
                and 1 < plot_df[c].nunique(dropna=True) <= min(100, max(20, int(len(plot_df) * 0.5)))
            ]
            # Low-cardinality numeric columns can also represent categories.
            for c in numeric_cols_all:
                if plot_df[c].nunique(dropna=True) <= 12 and c not in categorical_cols:
                    categorical_cols.append(c)

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Rows", f"{len(auto_df):,}")
            k2.metric("Columns", f"{len(auto_df.columns):,}")
            k3.metric("Missing cells", f"{int(auto_df.isna().sum().sum()):,}")
            k4.metric("Duplicate rows", f"{int(auto_df.duplicated().sum()):,}")

            with st.expander("Detected data types and missing values"):
                profile = pd.DataFrame({
                    "Column": [str(c) for c in auto_df.columns],
                    "Detected type": [str(plot_df[c].dtype) for c in auto_df.columns],
                    "Missing values": [int(auto_df[c].isna().sum()) for c in auto_df.columns],
                    "Unique values": [int(auto_df[c].nunique(dropna=True)) for c in auto_df.columns],
                })
                st.dataframe(profile, use_container_width=True, hide_index=True)

            # Explicit full-column selector: make every source column available for exploration.
            all_column_labels = [str(c) for c in plot_df.columns]
            with st.expander("All available columns (for manual chart selection)", expanded=False):
                st.multiselect(
                    "Columns in this dataset", options=all_column_labels,
                    default=all_column_labels, key="auto_all_columns_selector",
                    help="Every uploaded column is listed here. Numeric, category and date selectors below are used to build compatible charts."
                )

            # Let users choose which numeric fields to focus on, without requiring it.
            if numeric_cols:
                chosen_numeric = st.multiselect(
                    "Numeric columns to visualize",
                    options=numeric_cols,
                    default=numeric_cols[:min(6, len(numeric_cols))],
                    key="auto_numeric_columns"
                )
            else:
                chosen_numeric = []

            if categorical_cols:
                chosen_category = st.selectbox(
                    "Category column (for comparisons)",
                    options=categorical_cols,
                    index=0,
                    key="auto_category_column"
                )
            else:
                chosen_category = None

            if date_cols:
                chosen_date = st.selectbox("Date/time column (for trends)", options=date_cols, key="auto_date_column")
            else:
                chosen_date = None

            # Build a compact responsive chart grid.
            if chosen_date and chosen_numeric:
                trend_source = plot_df.dropna(subset=[chosen_date]).copy()
                trend_source["_trend_period"] = trend_source[chosen_date]
                if pd.api.types.is_datetime64_any_dtype(trend_source[chosen_date]):
                    trend_source["_trend_period"] = trend_source[chosen_date].dt.to_period("M").astype(str)
                    trend_source["_trend_period"] = pd.Categorical(
                        trend_source["_trend_period"],
                        categories=sorted(trend_source["_trend_period"].dropna().unique()),
                        ordered=True
                    )
                trend_metric = st.selectbox(
                    "Metric for trend chart",
                    options=chosen_numeric,
                    key="auto_trend_metric"
                )
                trend = trend_source.groupby("_trend_period", observed=False)[trend_metric].agg(["mean", "sum", "count"]).reset_index()
                trend_stat = st.radio(
                    "Trend aggregation",
                    options=["Sum", "Average", "Count"],
                    horizontal=True,
                    key="auto_trend_aggregation"
                )
                stat_col = {"Sum": "sum", "Average": "mean", "Count": "count"}[trend_stat]
                fig = px.line(
                    trend, x="_trend_period", y=stat_col, markers=True,
                    title=f"{trend_stat} of {trend_metric} over time",
                    labels={"_trend_period": str(chosen_date), stat_col: trend_stat}
                )
                fig.update_traces(line=dict(color=CYAN, width=3))
                st.plotly_chart(chart_layout(fig, 420), use_container_width=True)

            if chosen_category:
                cat_source = plot_df[[chosen_category] + chosen_numeric].copy() if chosen_numeric else plot_df[[chosen_category]].copy()
                cat_source[chosen_category] = cat_source[chosen_category].astype("string").fillna("Missing")
                cat_counts = cat_source[chosen_category].value_counts().head(20).sort_values()
                c1, c2 = st.columns(2)
                with c1:
                    count_frame = cat_counts.rename_axis("Category").reset_index(name="Records")
                    fig = px.bar(
                        count_frame, x="Records", y="Category", orientation="h",
                        title=f"Records by {chosen_category} (top 20)",
                        color="Records", color_continuous_scale=["#164E63", CYAN, PURPLE]
                    )
                    st.plotly_chart(chart_layout(fig, max(380, min(700, 24 * len(count_frame)))), use_container_width=True)
                with c2:
                    pie_frame = cat_source[chosen_category].value_counts().head(8).rename_axis("Category").reset_index(name="Records")
                    if len(pie_frame) >= 2:
                        fig = px.pie(pie_frame, names="Category", values="Records", hole=0.55,
                                     title=f"Category share: {chosen_category}")
                        st.plotly_chart(chart_layout(fig, 390), use_container_width=True)

                if chosen_numeric:
                    cat_metric = st.selectbox(
                        "Numeric metric for category comparison",
                        options=chosen_numeric,
                        key="auto_category_metric"
                    )
                    compare = plot_df[[chosen_category, cat_metric]].copy()
                    compare[chosen_category] = compare[chosen_category].astype("string").fillna("Missing")
                    compare = compare.groupby(chosen_category, dropna=False)[cat_metric].mean().nlargest(20).sort_values().reset_index()
                    fig = px.bar(
                        compare, x=cat_metric, y=chosen_category, orientation="h",
                        title=f"Average {cat_metric} by {chosen_category} (top 20)",
                        color=cat_metric, color_continuous_scale=["#164E63", CYAN, AMBER]
                    )
                    st.plotly_chart(chart_layout(fig, max(390, min(720, 26 * len(compare)))), use_container_width=True)

            if chosen_numeric:
                st.markdown("#### Numeric distributions")
                distribution_cols = st.columns(2)
                for idx, col in enumerate(chosen_numeric[:6]):
                    with distribution_cols[idx % 2]:
                        values = plot_df[col].replace([np.inf, -np.inf], np.nan).dropna()
                        if values.empty:
                            st.info(f"No usable numeric values in {col}.")
                            continue
                        fig = px.histogram(
                            pd.DataFrame({col: values}), x=col, nbins=30,
                            title=f"Distribution of {col}", marginal="box"
                        )
                        fig.update_traces(marker_line_width=0.5)
                        st.plotly_chart(chart_layout(fig, 350), use_container_width=True)

                if len(chosen_numeric) >= 2:
                    scatter_x = st.selectbox("Scatter plot — X axis", chosen_numeric, index=0, key="auto_scatter_x")
                    scatter_y = st.selectbox("Scatter plot — Y axis", chosen_numeric, index=1, key="auto_scatter_y")
                    scatter_df = plot_df[[scatter_x, scatter_y] + ([chosen_category] if chosen_category else [])].dropna().head(10000)
                    fig = px.scatter(
                        scatter_df, x=scatter_x, y=scatter_y,
                        color=chosen_category if chosen_category and chosen_category != scatter_x and chosen_category != scatter_y else None,
                        opacity=0.7, title=f"{scatter_y} vs {scatter_x}"
                    )
                    st.plotly_chart(chart_layout(fig, 430), use_container_width=True)

                if len(chosen_numeric) >= 2:
                    corr = plot_df[chosen_numeric].corr(numeric_only=True)
                    fig = px.imshow(
                        corr, text_auto=".2f", aspect="auto",
                        color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                        title="Correlation heatmap"
                    )
                    st.plotly_chart(chart_layout(fig, 430), use_container_width=True)

                if chosen_category and chosen_numeric:
                    box_metric = st.selectbox("Box plot metric", chosen_numeric, key="auto_box_metric")
                    box_data = plot_df[[chosen_category, box_metric]].dropna().copy()
                    box_data[chosen_category] = box_data[chosen_category].astype(str)
                    top_categories = box_data[chosen_category].value_counts().head(12).index
                    box_data = box_data[box_data[chosen_category].isin(top_categories)]
                    fig = px.box(box_data, x=chosen_category, y=box_metric, points="outliers",
                                 title=f"{box_metric} spread by {chosen_category} (top 12 categories)")
                    st.plotly_chart(chart_layout(fig, 430), use_container_width=True)

            if not numeric_cols and not categorical_cols and not date_cols:
                st.info("This file has no columns suitable for automatic charts. Review the detected data types above.")
            elif not chosen_numeric and not chosen_category and not chosen_date:
                st.info("Choose one or more columns above to generate charts.")
            st.download_button(
                "Download uploaded dataset as CSV",
                auto_df.to_csv(index=False).encode("utf-8"),
                file_name="uploaded_dataset.csv",
                mime="text/csv",
                key="auto_download_dataset"
            )
    except Exception as auto_error:
        st.error(f"Automatic visualization could not process this file: {auto_error}")

st.divider()
st.subheader("Data integrity & limitations")
st.markdown("""
- The statewide annual chart uses **published official aggregate values**, not the 200,000-row sample.
- A district or highway ranking is only as reliable as the uploaded underlying records. This app will not fabricate missing districts, highways, crash locations, or yearly counts.
- The official 2024 police-unit report uses **police units**, which do not always map one-to-one to civil districts.
- A risk-prediction model should only be trained on verified incident-level data with a documented target, train/test split, and validation. Do not report model accuracy from synthetic data as real-world performance.
""")
st.caption("Sources: Maharashtra Highway Traffic Police · Maharashtra Transport Department. Verify revisions and provisional figures against the linked source pages before publication.")
