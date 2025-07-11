import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import os
import yfinance as yf
import spacy
import pandas as pd

df = pd.read_csv("companies.csv")
nlp = spacy.load("en_core_web_sm")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml"
}

def empty_return():
    return {
        "content": "",
        "title": "",
        "datetime": "",
        "url": "",
        "domain": "",
        "summary": "",
        "tickers": [],
        "indexes": [],
        "companies": []
    }

def hg_summarize_article(section):
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    hf_api_key = os.getenv("HF_API_KEY")
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    payload = {
        "inputs": section,
        "parameters": {
            "max_length": 500,
            "min_length": 50,
            "do_sample": False
        }
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"].strip()
        else:
            return "⚠️ Hugging Face API did not return a summary."
    except Exception as e:
        return f"❌ Hugging Face API error: {e}"

def content_extract(soup, class_names):
    paragraphs = soup.find_all("p")
    if paragraphs:
        temp_page_text = " ".join(p.get_text(strip=True) for p in paragraphs)
        temp_page_text = temp_page_text.replace("Oops, something went wrong ", "") if "Oops, something went wrong " in temp_page_text else temp_page_text
    else:
        temp_page_text = ""
    
    for class_name in class_names:
        article_content = soup.find_all(class_=class_name)
        if article_content:
            for a in article_content.find_all("a"):
                print(f"\nA: {a}\n")
            temp_page_text = article_content[0].get_text(strip=True)
            break
    return temp_page_text

def get_domain(url):
    return urlparse(url).netloc

def get_datetime(soup):
    datetime_tag = soup.find("time", attrs={"datetime": True}) if soup.find("time", attrs={"datetime": True}) else ""
    return datetime_tag.get("datetime") if datetime_tag else ""

def get_title(soup):
    return max([tag.get_text(strip=True) for tag in soup.find_all("h1", limit=2)], key=len)

def validate_ticker(ticker):
    try:
        yf.Ticker(ticker).info
        return True
    except Exception:
        return False

def extract_tickers(text, company_list, company_to_ticker):
    ticker_patterns = [
        r'\$[A-Z]{1,5}',
        r'\([A-Z]{1,5}\)', 
        r'\b[A-Z]{2,5}\b(?=\s+(stock|shares))',
        r'\b([A-Z]{1,5}=F)\b', 
    ]
    index_pattern = r'\(\^[A-Z0-9]{1,6}\)'
    found_tickers = []

    found_indexes = re.findall(index_pattern, text)
    if found_indexes:
        found_indexes = [index.strip("()").strip("^") for index in found_indexes]
    for pattern in ticker_patterns:
        matches = re.findall(pattern, text)
        found_tickers.extend([ticker.strip("()").strip("$") for ticker in matches])
    found_tickers = [ticker for ticker in found_tickers if validate_ticker(ticker) and 
                     ticker in company_to_ticker.values() and 
                     ticker not in found_indexes]
    if company_list:
        new_tickers = []
        for company in company_list:
            key = company.lower().replace(" corp", "")
            if key in company_to_ticker:
                new_tickers.append(company_to_ticker[key])
            if key == "meta":
                new_tickers.append("META")
        found_tickers.extend(new_tickers)
        
    return list(set(found_tickers)), list(set(found_indexes))

def extract_companies(text): 
    company_to_ticker = dict(zip(df["short name"].str.lower().str.replace(" communications", "").str.replace(".com", "").str.strip(), df["ticker"]))
    parsed = f" {text.replace("'s", "").replace(".", "").replace(",", "")} "
    companies = []
    for name in company_to_ticker:
        name = "aMD" if name == "advanced micro devices" else name
        if f" {name.title()} " in parsed:
            companies.append(name.lower())
    return [companies, company_to_ticker]

def get_all_company_names(tickers, company_map):
    new_company_list = [name for name, tckr in company_map.items() if tckr in tickers]
    return new_company_list

def fetch_page_metadata(url):
    COMMON_CLASSES = [
        "article__content", "article-content", "main-content",
        "post-content", "entry-content", "story-body", "content__article-body",
        "article-body__content__17Yit", "atoms-wrapper", "ArticleBody-articleBody"
    ]
    info_dict = {}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch page: {response.status_code}")
            return empty_return
        soup = BeautifulSoup(response.text, "html.parser")

        info_dict["content"] = content_extract(soup, COMMON_CLASSES)
        article_content = info_dict["content"]
        info_dict["title"] = get_title(soup)
        info_dict["datetime"] = get_datetime(soup)
        info_dict["url"] = url
        info_dict["domain"] = get_domain(url)
        info_dict["summary"] = hg_summarize_article(article_content)
        company_info = extract_companies(article_content)
        company_list, company_map = company_info[0], company_info[1]
        info_dict["tickers"], info_dict["indexes"] = extract_tickers(article_content, company_list, company_map)
        info_dict["companies"] = get_all_company_names(info_dict["tickers"], company_map)
        
        return info_dict
    
    except requests.exceptions.RequestException:
        print("❌ Connection Error")
        return empty_return()

def main():
    url = input("Enter the article URL: ")
    total_info = fetch_page_metadata(url)
    if not total_info["content"]:
        print("⚠️ Couldn't fetch article content.")
        return
    print(f"Article Content: {total_info['content']}\n")
    print(f"Article Title: {total_info['title']}\n")
    print(f"Article DateTime: {total_info['datetime']}\n")
    print(f"Article Domain: {total_info['domain']}\n")
    print(f"Article Tickers: {total_info['tickers']}\n")
    print(f"Article Indexes: {total_info['indexes']}\n")
    print(f"Article Companies {total_info["companies"]}\n")

if __name__ == "__main__":  
    main()
