# Web Scraping Examples in Python

# Method 1: Using requests and BeautifulSoup (Most Common)
import requests
from bs4 import BeautifulSoup
import json
import time
import os

def load_progress():
    """Load previously scraped articles if any"""
    if os.path.exists('Articles.json'):
        with open('Articles.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_progress(articles):
    """Save current progress"""
    with open('Articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    print(f"Progress saved: {len(articles)} articles")

def get_next_page_url(soup):
    """Get the next page URL if it exists"""
    next_link = soup.find('a', class_='next')
    return next_link.get('href') if next_link else None

def scrape_akanyaburunga(start_url):
    """Scrape articles from Akanyaburunga blog with pagination"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Load existing progress
        articles = load_progress()
        existing_titles = {article['title'] for article in articles}
        
        current_url = start_url
        page_num = 1
        
        while current_url:
            print(f"\nProcessing page {page_num}: {current_url}")
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all post divs
            all_posts = soup.find_all('div', class_='post')
            print(f"Found {len(all_posts)} posts on this page")
            
            for post in all_posts:
                # Get title
                title = post.find('h2').find('a')
                title_text = title.text.strip() if title else "No title"
                
                # Skip if already scraped
                if title_text in existing_titles:
                    print(f"Skipping already scraped article: {title_text}")
                    continue
                
                print(f"Processing article: {title_text}")
                
                # Get date
                date = post.find('p', class_='entry-meta').find('a')
                date_text = date.text.strip() if date else "No date"
                
                # Get content
                content = post.find('div', class_='entry-summary')
                paragraphs = []
                if content:
                    for p in content.find_all('p'):
                        text = p.text.strip()
                        if text:
                            paragraphs.append(text)
                
                article_data = {
                    'title': title_text,
                    'date': date_text,
                    'content': paragraphs,
                    'page_number': page_num,
                    'url': current_url
                }
                
                articles.append(article_data)
                existing_titles.add(title_text)
                
                # Save progress after each article
                save_progress(articles)
            
            # Get next page URL
            current_url = get_next_page_url(soup)
            page_num += 1
            
            # Add delay between pages to be polite
            time.sleep(2)
            
        print("\nScraping completed!")
        return articles
        
    except requests.RequestException as e:
        print(f"\nError on page {page_num}: {e}")
        print(f"Last URL processed: {current_url}")
        return articles

if __name__ == "__main__":
    url = "https://akanyaburunga.wordpress.com/"
    results = scrape_akanyaburunga(url)
    print(f"\nTotal articles scraped: {len(results)}")