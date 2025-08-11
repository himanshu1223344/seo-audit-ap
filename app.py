import streamlit as st
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- UI Styling ---
st.markdown("""
    <style>
        .stApp { background-color: black !important; }
        footer {visibility: hidden;}
        .custom-footer {
            position: fixed; left: 0; bottom: 0; width: 100vw;
            background-color: #1976d2 !important; color: white !important;
            font-weight: bold; text-align: center; padding: 12px 0;
            font-size: 17px; opacity: 0.97; z-index: 9999;
        }
    </style>
    <div class="custom-footer">
        Developed by Himanshu &amp; Ahezam
    </div>
""", unsafe_allow_html=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SEO-AnalyzerBot/1.0; +https://yourdomain.com/bot)"
}

def get_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc.replace("www.", "")

def get_page_info(url):
    try:
        t0 = time.time()
        response = requests.get(url, timeout=10, headers=HEADERS)
        load_time = round(time.time() - t0, 2)
        status = response.status_code
        if status >= 400:
            return None, None
        soup = BeautifulSoup(response.content, "lxml")
        schema_jsonld = soup.find_all("script", type="application/ld+json")
        has_jsonld = len(schema_jsonld) > 0
        has_microdata = bool(soup.find(attrs={"itemscope": True}))
        has_rdfa = bool(soup.find(attrs={"typeof": True}))
        title = soup.title.string.strip() if soup.title else "No Title"
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta_desc['content'].strip() if meta_desc and 'content' in meta_desc.attrs else "No Meta Description"
        canonical = soup.find("link", rel="canonical")
        canonical = canonical['href'] if canonical and 'href' in canonical.attrs else "No Canonical"
        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
        word_count = len(soup.get_text().split())
        imgs = soup.find_all("img")
        image_count = len(imgs)
        missing_alt = sum(1 for img in imgs if not img.get("alt"))
        robots_tag = soup.find("meta", attrs={"name": "robots"})
        robots_value = robots_tag['content'].strip() if robots_tag and 'content' in robots_tag.attrs else "None"
        external_links = []
        for a_tag in soup.find_all("a", href=True):
            href = urljoin(url, a_tag['href'])
            parsed = urlparse(href)
            if parsed.scheme in ["http", "https"]:
                if get_domain(url) not in parsed.netloc:
                    external_links.append(href)
        external_link_count = len(external_links)
        return {
            "URL": url,
            "Status Code": status,
            "Title": title,
            "Meta Description": meta_desc,
            "Canonical": canonical,
            "H1 Count": len(h1_tags),
            "Word Count": word_count,
            "Image Count": image_count,
            "Missing ALT Count": missing_alt,
            "Meta Robots": robots_value,
            "External Link Count": external_link_count,
            "Page Load Time (sec)": load_time,
            "Has JSON-LD Schema": has_jsonld,
            "Has Microdata Schema": has_microdata,
            "Has RDFa Schema": has_rdfa,
        }, soup
    except Exception as e:
        return None, None

st.title("SEO Bulk Audit Web Tool")
st.write("Paste your page URLs below (one per line) and click 'Run Audit'.")

url_input = st.text_area("Page URLs (one per line)", height=200)
run_button = st.button("Run Audit")

if run_button and url_input.strip():
    raw_urls = [line.strip() for line in url_input.strip().split('\n') if line.strip()]
    st.info(f"Crawling {len(raw_urls)} URLs. Please wait (takes 1–2 seconds per page)...")
    results = []
    visited = set()
    progress = st.progress(0)
    for i, url in enumerate(raw_urls, 1):
        if url in visited:
            continue
        visited.add(url)
        page_data, _ = get_page_info(url)
        if page_data:
            results.append(page_data)
        else:
            st.error(f"Failed to crawl: {url}")
        progress.progress(i / len(raw_urls))
        time.sleep(1)
    df = pd.DataFrame(results)
    st.success("Audit complete! Use the buttons below to download your reports.")
    if df.empty:
        st.warning("No pages were successfully audited. Please check your URLs and try again.")
    else:
        st.dataframe(df)
        st.download_button("Download All Results as CSV", df.to_csv(index=False), file_name="seo_audit_report.csv")
