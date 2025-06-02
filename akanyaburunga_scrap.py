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
    next_link = soup.find('a', class_='next page-numbers')
    return next_link.get('href') if next_link else None

def scrape_article(url, headers):
    """Scrape a single article page"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find article content
        article = soup.find('article') or soup.find('div', class_='post')
        if not article:
            print(f"No article found at {url}")
            return None
            
        # Get title
        title = article.find('h1', class_='entry-title') or article.find('h2', class_='entry-title')
        title_text = title.text.strip() if title else "No title"
        print(f"Found title: {title_text}")
        
        # Get date
        date = article.find('time', class_='entry-date published') or article.find('span', class_='posted-on')
        date_text = date.text.strip() if date else "No date"
        
        # Get content
        content = article.find('div', class_='entry-content') or article.find('div', class_='entry-summary')
        paragraphs = []
        if content:
            for p in content.find_all('p'):
                text = p.text.strip()
                if text:
                    paragraphs.append(text)
        
        # Get categories
        categories = []
        category_links = article.find_all('a', rel='category tag')
        for cat in category_links:
            categories.append({
                'name': cat.text.strip(),
                'url': cat.get('href', '')
            })
            print(f"Found category: {categories[-1]['name']}")
            
        return {
            'title': title_text,
            'date': date_text,
            'content': paragraphs,
            'categories': categories,
            'url': url
        }
    except Exception as e:
        print(f"Error scraping article {url}: {e}")
        return None

def scrape_category(category_url, headers):
    """Scrape all articles from a category"""
    articles = []
    current_url = category_url
    
    while current_url:
        print(f"\nProcessing category page: {current_url}")
        try:
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug the HTML structure
            print("Debug: HTML structure of first post")
            first_post = soup.find('div', class_='post') or soup.find('article')
            if first_post:
                print(first_post.prettify()[:500])  # Print first 500 chars
            
            # Find all posts
            posts = soup.find_all('div', id=lambda x: x and x.startswith('post-'))
            print(f"Found {len(posts)} posts on this page")
            
            for post in posts:
                try:
                    # Get article URL from title link
                    title_link = post.find('a', href=True)
                    if not title_link:
                        continue
                        
                    article_url = title_link['href']
                    print(f"\nScraping article: {article_url}")
                    
                    # Get the full article
                    article_response = requests.get(article_url, headers=headers)
                    article_response.raise_for_status()
                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                    
                    # Get title
                    title = article_soup.find('h1', class_='entry-title')
                    title_text = title.text.strip() if title else "No title"
                    
                    # Get date
                    date = article_soup.find('time', class_='entry-date published')
                    date_text = date.text.strip() if date else "No date"
                    
                    # Get content
                    content = article_soup.find('div', class_='entry-content')
                    paragraphs = []
                    if content:
                        for p in content.find_all('p'):
                            text = p.text.strip()
                            if text:
                                paragraphs.append(text)
                    
                    # Get categories
                    categories = []
                    for cat_link in article_soup.find_all('a', rel='category tag'):
                        categories.append({
                            'name': cat_link.text.strip(),
                            'url': cat_link['href']
                        })
                    
                    article_data = {
                        'title': title_text,
                        'date': date_text,
                        'content': paragraphs,
                        'categories': categories,
                        'url': article_url
                    }
                    
                    articles.append(article_data)
                    print(f"Successfully scraped: {title_text}")
                    
                    # Save progress after each article
                    save_progress(articles)
                    time.sleep(1)  # Be polite
                    
                except Exception as e:
                    print(f"Error scraping article {article_url}: {e}")
                    continue
            
            # Get next page
            next_link = soup.find('a', class_='next page-numbers')
            current_url = next_link['href'] if next_link else None
            if current_url:
                print(f"\nFound next page: {current_url}")
                time.sleep(2)  # Be polite between pages
            
        except Exception as e:
            print(f"Error processing category page {current_url}: {e}")
            break
    
    return articles

def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # List of all category URLs
    categories = [
        'https://akanyaburunga.wordpress.com/category/amadini/',
        'https://akanyaburunga.wordpress.com/category/amayagwa/',
        'https://akanyaburunga.wordpress.com/category/imibano/',
        'https://akanyaburunga.wordpress.com/category/imigani-ibitito/',
        'https://akanyaburunga.wordpress.com/category/imyibutsa/',
        'https://akanyaburunga.wordpress.com/category/indimburo/',
        'https://akanyaburunga.wordpress.com/category/inkuru-zigezweho/',
        'https://akanyaburunga.wordpress.com/category/kahise/',
        'https://akanyaburunga.wordpress.com/category/menya-akahise-kawe/',
        'https://akanyaburunga.wordpress.com/category/uncategorized/',
        'https://akanyaburunga.wordpress.com/category/utugenegene/',
        'https://akanyaburunga.wordpress.com/category/yaga-akaranga/'
    ]
    
    all_articles = []
    existing_urls = set()
    
    # Load existing progress
    if os.path.exists('Articles.json'):
        all_articles = load_progress()
        existing_urls = {article['url'] for article in all_articles}
    
    # Scrape each category
    for category_url in categories:
        print(f"\nProcessing category: {category_url}")
        category_articles = scrape_category(category_url, headers)
        
        # Add only new articles
        for article in category_articles:
            if article['url'] not in existing_urls:
                all_articles.append(article)
                existing_urls.add(article['url'])
                save_progress(all_articles)
    
    print(f"\nTotal articles scraped: {len(all_articles)}")

if __name__ == "__main__":
    main()