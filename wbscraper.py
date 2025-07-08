import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import os
import yfinance as yf

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml"
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

def extract_tickers(text):
    ticker_patterns = [
        r'\$[A-Z]{1,5}',
        r'([A-Z]{1,5})\)',
        r'\b[A-Z]{2,5}\b(?=\s+(stock|shares))'
    ]
    index_pattern = r'\(\^[A-Z0-9]{1,6}\)'
    found_tickers = []

    found_indexes = re.findall(index_pattern, text)
    if found_indexes:
        found_indexes = [index.strip("()").strip("^") for index in found_indexes]
    for pattern in ticker_patterns:
        matches = re.findall(pattern, text)
        found_tickers.extend([ticker.strip("()").strip("$") for ticker in matches])
    found_tickers = [ticker for ticker in found_tickers if validate_ticker(ticker) and ticker not in found_indexes]
    return list(set(found_tickers)), list(set(found_indexes))

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
            return {"content": "", "title": "", 
                    "datetime": "", "url": "", 
                    "domain": "", "summary": "",
                    "tickers": [], "indexes": []}
        soup = BeautifulSoup(response.text, "html.parser")
        
        # page content
        article_content = content_extract(soup, COMMON_CLASSES)
        # page title
        title_tag = get_title(soup)
        # page datetime
        datetime_tag = get_datetime(soup)
        # page domain
        domain_tag = get_domain(url)
        # page summary
        article_summary = hg_summarize_article(article_content)
        # page tickers, indexes
        tickers, indexes = extract_tickers(article_content)

        info_dict["content"] = article_content
        info_dict["title"] = title_tag
        info_dict["datetime"] = datetime_tag
        info_dict["url"] = url
        info_dict["domain"] = domain_tag
        info_dict["summary"] = article_summary
        info_dict["tickers"] = tickers
        info_dict["indexes"] = indexes

        return info_dict
    except requests.exceptions.RequestException:
        print("❌ Connection Error")
        return {"content": "", "title": "",
                "datetime": "", "url": "", 
                "domain": "", "summary": "",
                "tickers": [], "indexes": []}

def main():
    url = input("Enter the article URL: ")
    total_info = fetch_page_metadata(url)
    if not total_info["content"]:
        print("⚠️ Couldn't fetch article content.")
        return
    print(f"Article Content: \n{total_info['content']}\n")
    print(f"Article Title: \n{total_info['title']}\n")
    print(f"Article DateTime: \n{total_info['datetime']}\n")
    print(f"Article Domain: \n{total_info['domain']}\n")
    print(f"Article Tickers: \n{total_info['tickers']}\n")
    print(f"Article Indexes: \n{total_info['indexes']}\n")

if __name__ == "__main__":
    main()