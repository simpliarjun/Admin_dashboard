import pandas as pd

def most_travelled_destination(df, top_n=10):
    return df["Destination"].value_counts().head(top_n)

def most_used_transport(df):
    return df["Mode of Transport"].value_counts()

def most_used_fuel(df):
    return df["Fuel Type"].value_counts()

def most_common_purpose(df):
    return df["Purpose"].value_counts()

def average_distance_monthly(df):
    df["Month"] = df["Trip Start Date"].dt.to_period("M")
    return df.groupby("Month")["Distance (km)"].mean()

def fuel_cost_monthly(df):
    df["Month"] = df["Trip Start Date"].dt.to_period("M")
    return df.groupby("Month")["Fuel Cost (INR)"].sum()

def co2_monthly(df):
    df["Month"] = df["Trip Start Date"].dt.to_period("M")
    return df.groupby("Month")["Carbon Emission (kg)"].sum()

def distance_by_transport(df):
    return df.groupby("Mode of Transport")["Distance (km)"].sum()

def average_companions(df):
    return float(df["Companions"].mean())

def average_spent(df):
    return float(df["Total Cost (INR)"].mean())

def average_toll(df):
    if "Toll Cost (INR)" not in df.columns:
        return 0.0
    return float(df["Toll Cost (INR)"].mean())

def average_trip_duration(df):
    return float(df["_Trip Duration Seconds"].dropna().mean())

def most_travelled_routes(df, top_n=10):
    return df["Most Travelled Route"].value_counts().head(top_n)

def average_spent_on_most_travelled_routes(df, top_n=10):
    top_routes = df["Most Travelled Route"].value_counts().head(top_n).index
    return (
        df[df["Most Travelled Route"].isin(top_routes)]
        .groupby("Most Travelled Route")["Total Cost (INR)"]
        .mean()
        .sort_values(ascending=False)
    )

def calculate_trip_score(df, route=None):
    """
    Calculate a trip score for a route based on efficiency and sustainability.
    Score ranges from 0-100 (higher is better).
    Factors: CO2 emissions (40%), fuel cost efficiency (30%), distance efficiency (20%), companion ratio (10%)
    Returns both score and breakdown details.
    """
    if route is None:
        route_data = df
    else:
        route_data = df[df["Most Travelled Route"] == route]
    
    if route_data.empty:
        return 0, {}
    
    # Calculate components
    total_co2 = route_data["Carbon Emission (kg)"].sum()
    total_distance = route_data["Distance (km)"].sum()
    total_cost = route_data["Total Cost (INR)"].sum()
    avg_companions = route_data["Companions"].mean()
    
    avg_co2_per_km = total_co2 / total_distance if total_distance > 0 else 0
    avg_cost_per_km = total_cost / total_distance if total_distance > 0 else 0
    avg_distance = route_data["Distance (km)"].mean()
    
    # Normalize scores (inverse for emissions and cost - lower is better)
    # CO2 score: lower emissions is better (max 50 kg/km for normalization)
    co2_score = max(0, (50 - min(avg_co2_per_km, 50)) / 50 * 40)
    
    # Cost score: lower cost per km is better (max 100 INR/km)
    cost_score = max(0, (100 - min(avg_cost_per_km, 100)) / 100 * 30)
    
    # Distance score: longer planned routes are more efficient (max 500 km)
    distance_score = min(avg_distance / 500, 1) * 20
    
    # Companion score: more companions is better for shared trips (max 5)
    companion_score = min(avg_companions / 5, 1) * 10
    
    total_score = co2_score + cost_score + distance_score + companion_score
    
    breakdown = {
        "co2_score": round(co2_score, 2),
        "cost_score": round(cost_score, 2),
        "distance_score": round(distance_score, 2),
        "companion_score": round(companion_score, 2),
        "avg_co2_per_km": round(avg_co2_per_km, 2),
        "avg_cost_per_km": round(avg_cost_per_km, 2),
        "avg_distance": round(avg_distance, 2),
        "avg_companions": round(avg_companions, 2),
    }
    
    return round(total_score, 2), breakdown

def generate_trip_report(df, route=None):
    """
    Generate a comprehensive trip report for a specific route or entire dataset.
    Returns a dictionary with key metrics and insights.
    """
    if route is None:
        route_data = df
        route_name = "Overall"
    else:
        route_data = df[df["Most Travelled Route"] == route]
        route_name = route
    
    if route_data.empty:
        return None
    
    report = {
        "Route": route_name,
        "Trip Count": len(route_data),
        "Total Distance (km)": round(route_data["Distance (km)"].sum(), 2),
        "Avg Distance per Trip (km)": round(route_data["Distance (km)"].mean(), 2),
        "Total CO₂ Emissions (kg)": round(route_data["Carbon Emission (kg)"].sum(), 2),
        "Avg CO₂ per Trip (kg)": round(route_data["Carbon Emission (kg)"].mean(), 2),
        "Total Fuel Cost (INR)": round(route_data["Fuel Cost (INR)"].sum(), 2),
        "Avg Fuel Cost per Trip (INR)": round(route_data["Fuel Cost (INR)"].mean(), 2),
        "Total Cost (INR)": round(route_data["Total Cost (INR)"].sum(), 2),
        "Avg Cost per Trip (INR)": round(route_data["Total Cost (INR)"].mean(), 2),
        "Avg Companions": round(route_data["Companions"].mean(), 2),
        "Most Common Transport": route_data["Mode of Transport"].mode().values[0] if not route_data["Mode of Transport"].mode().empty else "N/A",
        "Most Common Fuel": route_data["Fuel Type"].mode().values[0] if not route_data["Fuel Type"].mode().empty else "N/A",
    }
    
    return report

def get_most_travelled_route(df):
    """
    Get the single most travelled route name.
    """
    routes = most_travelled_routes(df, top_n=1)
    return routes.index[0] if len(routes) > 0 else None
