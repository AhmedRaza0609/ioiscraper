import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from streamlit_autorefresh import st_autorefresh

# === Must be first Streamlit command ===
st.set_page_config(layout="wide")

# === Auto-refresh every 60 seconds ===
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")

# --- Country Code Mapping ---
country_codes = {
    'CHN': 'China', 'KOR': 'South Korea', 'CAN': 'Canada', 'ROU': 'Romania',
    'AUS': 'Australia', 'POL': 'Poland', 'HUN': 'Hungary', 'USA': 'United States',
    'VNM': 'Vietnam', 'IRN': 'Iran', 'SGP': 'Singapore', 'MYS': 'Malaysia',
    'CHE': 'Switzerland', 'KAZ': 'Kazakhstan', 'HRV': 'Croatia', 'BGR': 'Bulgaria',
    'TUR': 'Turkey', 'TWN': 'Taiwan', 'IDN': 'Indonesia', 'NLD': 'Netherlands',
    'JPN': 'Japan', 'ITA': 'Italy', 'FRA': 'France', 'GBR': 'United Kingdom',
    'MKD': 'North Macedonia', 'THA': 'Thailand', 'EGY': 'Egypt', 'FIN': 'Finland',
    'SRB': 'Serbia', 'SVK': 'Slovakia', 'MDA': 'Moldova', 'ESP': 'Spain',
    'UZB': 'Uzbekistan', 'BRA': 'Brazil', 'HKG': 'Hong Kong', 'PAK': 'Pakistan',
    'CYP': 'Cyprus', 'UKR': 'Ukraine', 'SWE': 'Sweden', 'BEL': 'Belgium',
    'CZE': 'Czech Republic', 'AZE': 'Azerbaijan', 'PHL': 'Philippines',
    'BGD': 'Bangladesh', 'ARM': 'Armenia', 'MAC': 'Macau', 'SAU': 'Saudi Arabia',
    'IND': 'India', 'CUB': 'Cuba', 'DEU': 'Germany', 'MEX': 'Mexico',
    'NZL': 'New Zealand', 'AUT': 'Austria', 'EST': 'Estonia', 'LTU': 'Lithuania',
    'KGZ': 'Kyrgyzstan', 'MNG': 'Mongolia', 'LVA': 'Latvia', 'GEO': 'Georgia',
    'SVN': 'Slovenia', 'ARG': 'Argentina', 'ZAF': 'South Africa',
    'COL': 'Colombia', 'BIH': 'Bosnia and Herzegovina', 'GRC': 'Greece',
    'IRL': 'Ireland', 'NGA': 'Nigeria', 'BOL': 'Bolivia', 'NOR': 'Norway',
    'MAR': 'Morocco', 'PER': 'Peru', 'TUN': 'Tunisia', 'DNK': 'Denmark',
    'LBY': 'Libya', 'CHL': 'Chile', 'ISL': 'Iceland', 'PRT': 'Portugal',
    'DOM': 'Dominican Republic', 'SLV': 'El Salvador', 'LUX': 'Luxembourg',
    'DZA': 'Algeria', 'ECU': 'Ecuador', 'RWA': 'Rwanda', 'GHA': 'Ghana',
}

@st.cache_data(ttl=60)
def fetch_data():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)

        url = "https://ranking.ioi2025.bo/"
        driver.get(url)
        time.sleep(3)  # Wait for JS to render

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        table = soup.find("table", id="Scoreboard")
        if not table:
            st.warning("No table with id 'Scoreboard' found.")
            return pd.DataFrame()

        headers = [th.get_text(strip=True) or f"Unnamed_{i}" for i, th in enumerate(table.find("thead").find_all("th"))]
        rows = [[td.get_text(strip=True) for td in tr.find_all("td")] for tr in table.find("tbody").find_all("tr")]
        df = pd.DataFrame(rows, columns=headers)

        if "ID" not in df.columns:
            st.error("❌ Column 'ID' not found in table.")
            return pd.DataFrame()

        df.columns = df.columns.str.strip()
        df["Country"] = df["ID"].str[:3]
        df = df[df["Country"] != "IOI"]
        df["Country"] = df["Country"].map(country_codes).fillna(df["Country"])

        score_col = [c for c in df.columns if "Global" in c or "Score" in c][-1]
        df.rename(columns={score_col: "Total Score"}, inplace=True)
        df["Total Score"] = pd.to_numeric(df["Total Score"], errors="coerce")
        df = df.dropna(subset=["Country", "Total Score"])
        return df

    except Exception as e:
        st.error(f"Exception while fetching: {e}")
        return pd.DataFrame()

def plot_top50(df):
    top50 = df.groupby("Country")["Total Score"].sum().sort_values(ascending=False).head(30)
    fig, ax = plt.subplots(figsize=(8, 10))
    top50.sort_values().plot(kind="barh", ax=ax, color="skyblue")
    ax.set_title("Top 30 Countries by Total Score")
    st.pyplot(fig)

def plot_pakistan_context(df):
    country_total = df.groupby("Country")["Total Score"].sum().sort_values(ascending=False)
    ranked = country_total.reset_index().reset_index()
    ranked.columns = ["Rank", "Country", "Total Score"]
    ranked["Rank"] += 1

    if "Pakistan" not in ranked["Country"].values:
        st.warning("Pakistan not in the ranking.")
        return

    n = ranked[ranked["Country"] == "Pakistan"]["Rank"].values[0]
    nearby = ranked[(ranked["Rank"] >= n - 5) & (ranked["Rank"] <= n + 5)]
    st.subheader("📊 Countries Near Pakistan in Ranking")
    st.dataframe(nearby, height=400)

def plot_pakistan_scores(df):
    pak = df[df["Country"] == "Pakistan"].copy()

    # Detect all problem columns dynamically
    known_cols = {"First Name", "Last Name", "ID", "Country", "Total Score"}
    all_cols = [col for col in df.columns if col not in known_cols]

    # Automatically detect up to 6 problem columns
    problem_cols = ['souvenirs','triples','worldmap','festival','migrations','obstacles']


    for col in problem_cols:
        pak[col] = pd.to_numeric(pak[col], errors="coerce")

    df_no_ioi = df[df["ID"].str[:3] != "IOI"].copy()
    df_no_ioi = df_no_ioi.sort_values("Total Score", ascending=False)
    df_no_ioi["Rank_no_ioi"] = range(1, len(df_no_ioi) + 1)
    pak = pak.merge(df_no_ioi[["ID", "Rank_no_ioi"]], on="ID", how="left")

    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(pak))
    bar_width = 0.8 / 7  # 6 problems + 1 total = 7 bars

    # Plot 6 problem bars
    for i, col in enumerate(problem_cols):
        offset = (i - 3) * bar_width  # centered around 0
        ax.bar([j + offset for j in x], pak[col], width=bar_width, label=col.capitalize())

    # Plot total score bar
    offset = (3) * bar_width
    bars_total = ax.bar([j + offset for j in x], pak["Total Score"], width=bar_width, label="Total", color="black")

    for i, bar in enumerate(bars_total):
        rank_ioi = df[df["ID"] == pak.iloc[i]["ID"]].index[0] + 1
        rank_no_ioi = pak.iloc[i].get("Rank_no_ioi", "?")
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f"{rank_ioi}/{rank_no_ioi}",
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(range(len(pak)))
    ax.set_xticklabels(pak["First Name"] + " " + pak["Last Name"])
    ax.set_title("🇵🇰 Pakistan: Problem-wise Scores (6 problems + Total)")
    ax.legend()
    st.pyplot(fig)


# === Interface ===
st.title("🌍 IOI 2025 Live Scoreboard")

df = fetch_data()
if df is None or df.empty:
    st.error("❌ Could not fetch or parse data.")
else:
    plot_top50(df)
    plot_pakistan_context(df)
    plot_pakistan_scores(df)
