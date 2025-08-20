import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Function to extract presenter data from uploaded HTML
def extract_presenters(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    presenters = []

    for div in soup.find_all('div'):
        text = div.get_text(separator=' ', strip=True)
        if any(rank in text for rank in ['Professor', 'Associate Professor', 'Chair', 'Director']):
            if any(country in text for country in ['University', 'College']):
                presenters.append(text)

    return presenters

# Function to check OpenAlex for prior academic book authorship
def check_openalex_author(name):
    url = f"https://api.openalex.org/authors?search={name}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['meta']['count'] > 0:
                return "Likely Author"
        return "Not Found"
    except:
        return "Error"

# Streamlit UI
st.title("APSA 2025 Academic Book Author Finder")

uploaded_file = st.file_uploader("Upload saved HTML file of APSA conference program", type=["html"])

if uploaded_file:
    html_content = uploaded_file.read()
    presenters = extract_presenters(html_content)

    st.write(f"Found {len(presenters)} potential presenters.")

    results = []
    for presenter in presenters:
        name = presenter.split(',')[0]  # crude name extraction
        status = check_openalex_author(name)
        results.append({"Presenter": presenter, "Book Authorship": status})

    df = pd.DataFrame(results)
    st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Results as CSV", data=csv, file_name="apsa_presenters.csv", mime="text/csv")

