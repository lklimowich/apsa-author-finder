
import streamlit as st
import pandas as pd
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- Helper Functions ---

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def scrape_apsa_program(url):
    driver = setup_driver()
    driver.get(url)
    time.sleep(5)  # wait for page to load

    presenters = []

    try:
        sessions = driver.find_elements(By.CLASS_NAME, "Papers")
        for session in sessions:
            try:
                title = session.find_element(By.CLASS_NAME, "title").text
                people = session.find_elements(By.CLASS_NAME, "people")
                for person in people:
                    name = person.find_element(By.CLASS_NAME, "name").text
                    affiliation = person.find_element(By.CLASS_NAME, "affiliation").text
                    presenters.append({
                        "Name": name,
                        "Affiliation": affiliation,
                        "Session Title": title
                    })
            except:
                continue
    except:
        st.error("Could not find session data on the page.")
    driver.quit()
    return pd.DataFrame(presenters)

def filter_presenters(df):
    ranks = ["Associate Professor", "Professor", "Chair", "Director", "Senior Researcher"]
    countries = ["University", "College", "Canada", "USA", "United States"]

    def is_valid(row):
        return any(rank in row["Affiliation"] for rank in ranks) and any(loc in row["Affiliation"] for loc in countries)

    return df[df.apply(is_valid, axis=1)]

def check_openalex_books(name):
    base_url = "https://api.openalex.org/authors"
    params = {"search": name}
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            for result in data.get("results", []):
                if result.get("works_count", 0) > 0:
                    return True
    except:
        return False
    return False

def enrich_with_books(df):
    df["Has Academic Book"] = df["Name"].apply(check_openalex_books)
    return df

# --- Streamlit Interface ---

st.title("APSA 2025 Academic Book Author Finder")

url = st.text_input("Enter APSA Conference Program URL", "https://convention2.allacademic.com/one/apsa/apsa25/")

if st.button("Scrape and Analyze"):
    with st.spinner("Scraping conference program..."):
        data = scrape_apsa_program(url)
        st.success(f"Found {len(data)} presenters.")
        st.dataframe(data)

        st.write("Filtering by academic rank and location...")
        filtered = filter_presenters(data)
        st.success(f"{len(filtered)} presenters match the criteria.")
        st.dataframe(filtered)

        st.write("Checking for prior academic book authorship...")
        enriched = enrich_with_books(filtered)
        st.success("Book authorship check complete.")
        st.dataframe(enriched)

        csv = enriched.to_csv(index=False).encode("utf-8")
        st.download_button("Download Results as CSV", csv, "apsa_presenters.csv", "text/csv")
