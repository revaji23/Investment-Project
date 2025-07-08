import requests
from bs4 import BeautifulSoup
import math

API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
headers = {"Authorization": "Bearer API KEY HERE"}

def fetch_page_text(url):
    COMMON_CLASSES = [
        "article__content", "article-content", "main-content",
        "post-content", "entry-content", "story-body", "content__article-body"
    ]
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        print("You Are Offline...\nError:", e)
        return ""
    if response.status_code != 200:
        print(f"Failed to retrieve the page: {response.status_code}")
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    for class_name in COMMON_CLASSES:
        article_content = soup.find_all(class_=class_name)
        if article_content:
            return article_content[0].get_text(strip=True)
    paragraphs = soup.find_all("p")
    if paragraphs:
        return "\n".join(p.get_text(strip=True) for p in paragraphs)
    print("No article content found.")
    return ""

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
    
def seperate_sections(text, maxWords):
    words = text.split()
    sections = []
    num = math.ceil(len(words) / maxWords)
    for i in range(num):
        if i + 1 == num:
            sections.append(words[i * maxWords: len(words)])
            break
        sections.append(words[i * maxWords:(i + 1) * maxWords])
    return sections

def summarize_article_main(website_link, word_limit):
    page_text = fetch_page_text(website_link)
    text_sections = seperate_sections(page_text, word_limit)
    total_summary = ""
        
    if page_text:
        for iter, section in enumerate(text_sections):
            print(f"Processing section {iter + 1}...")
            summary = summarize(" ".join(section)).replace(" .", ".")
            if summary:
                total_summary += summary
        print("Final Summary: ", total_summary)
    else:
        print("Text couldn't be fetched or is empty.")

url = "https://www.cnn.com/2025/06/26/politics/immigration-deportations-trump-asylum-seekers"
max_words = 200

summarize_article_main(url, max_words)
