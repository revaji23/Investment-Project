import requests
from bs4 import BeautifulSoup
import math

API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
headers = {"Authorization": "Bearer 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"}

url = "https://www.cnn.com/2025/06/25/investing/stock-market-record-dow"
max_words = 1000

def fetch_page_text(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page: {response.status_code}")
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    article_content = soup.find_all(class_="article__content")
    if not article_content:
        print("No article content found.")
        return ""
    return article_content[0].getText(strip=True)

def summarize(text):
    print(f"Summarizing text... ({len(text.split())} words)")
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": text}, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result[0]['summary_text']
    except Exception as e:
        print("Error:", e)
        return None
    
def seperate_sections(text):
    words = text.split()
    sections = []
    num = math.ceil(len(words) / max_words)
    for i in range(num):
        if i + 1 == num:
            sections.append(words[i * max_words: len(words)])
            break
        sections.append(words[i * max_words:(i + 1) * max_words])
    return sections

page_text = fetch_page_text(url)
text_sections = seperate_sections(page_text)
total_summary = ""

if page_text:
    for iter, section in enumerate(text_sections):
        print(f"Processing section {iter + 1}...")
        summary = summarize(" ".join(section)).replace(" .", ".")
        total_summary += summary
    print("Final Summary: ", total_summary)
else:
    print("Text couldn't be fetched or is empty.") 