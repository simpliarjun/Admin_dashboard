import pandas as pd

EXPECTED_COLUMNS = [
    "Origin",
    "Trip Start Date",
    "Trip Start Time",
    "Destination",
    "Trip End Date",
    "Trip End Time",
    "Mode of Transport",
    "Fuel Type",
    "Distance (km)",
    "Purpose",
    "Companions",
    "Frequency",
    "Total Cost (INR)",
    "Toll Cost (INR)",
    "Most Travelled Route",
    "Carbon Emission (kg)",
    "Fuel Cost (INR)",
    "Most Travelled Month",
]

NUMERIC_COLUMNS = [
    "Distance (km)",
    "Companions",
    "Total Cost (INR)",
    "Toll Cost (INR)",
    "Carbon Emission (kg)",
    "Fuel Cost (INR)",
]

STRING_COLUMNS = [
    "Origin",
    "Destination",
    "Mode of Transport",
    "Fuel Type",
    "Purpose",
    "Frequency",
    "Most Travelled Route",
    "Most Travelled Month",
]

def clean_travel_data(xlsx_file):
    df = pd.read_excel(xlsx_file) if not isinstance(xlsx_file, pd.DataFrame) else xlsx_file.copy()
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[EXPECTED_COLUMNS]
    for col in STRING_COLUMNS:
        df[col] = df[col].astype(str).str.strip().replace({"nan": None, "None": None, "" : None})
    df["Trip Start Date"] = pd.to_datetime(df["Trip Start Date"], errors="coerce")
    df["Trip End Date"] = pd.to_datetime(df["Trip End Date"], errors="coerce")
    df["Trip Start Time"] = pd.to_datetime(df["Trip Start Time"], errors="coerce").dt.time
    df["Trip End Time"] = pd.to_datetime(df["Trip End Time"], errors="coerce").dt.time
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Companions"] = df["Companions"].round().fillna(0)
    df["Toll Cost (INR)"] = df["Toll Cost (INR)"].fillna(0)
    df["Most Travelled Route"] = df["Most Travelled Route"].fillna(df["Origin"] + " - " + df["Destination"])
    start_dt = pd.to_datetime(df["Trip Start Date"].astype(str) + " " + df["Trip Start Time"].astype(str), errors="coerce")
    end_dt = pd.to_datetime(df["Trip End Date"].astype(str) + " " + df["Trip End Time"].astype(str), errors="coerce")
    df["_Trip Duration Seconds"] = (end_dt - start_dt).dt.total_seconds()
    return df
