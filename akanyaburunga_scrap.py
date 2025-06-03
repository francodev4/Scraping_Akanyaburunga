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
        article = soup.find('div', class_='post')
        if not article:
            print(f"No article found at {url}")
            return None
        
        # Get title from h2 > a
        title = article.find('h2').find('a')
        title_text = title.text.strip() if title else "No title"
        
        # Get date from first link in entry-meta
        meta = article.find('p', class_='entry-meta')
        date = meta.find('a') if meta else None
        date_text = date.text.strip() if date else "No date"
        
        # Get content from entry-summary first
        paragraphs = []
        entry_summary = article.find('div', class_='entry-summary')
        if entry_summary:
            # Look for paragraphs with class="has-text-align-left" and strong tags
            for p in entry_summary.find_all('p', class_='has-text-align-left'):
                strong = p.find('strong')
                if strong:
                    text = strong.text.strip()
                    if text and not text.startswith(('Share this:', 'Like Loading')):
                        paragraphs.append(text)
        
        # If we don't have content yet, try getting from full article
        if not paragraphs:
            more_link = article.find('a', class_='more-link')
            if more_link:
                full_url = more_link['href']
                full_response = requests.get(full_url, headers=headers)
                full_soup = BeautifulSoup(full_response.content, 'html.parser')
                
                content = full_soup.find('div', class_='entry-content')
                if content:
                    # Remove social sharing buttons
                    for share in content.find_all('div', class_='sharedaddy'):
                        share.decompose()
                    
                    # Get paragraphs with text-align:justify
                    for p in content.find_all('p', style='text-align:justify'):
                        text = p.text.strip()
                        if text and not text.startswith(('Share this:', 'Like Loading')):
                            paragraphs.append(text)
        
        print(f"Found {len(paragraphs)} paragraphs for {title_text}")
        
        return {
            'title': title_text,
            'date': date_text,
            'content': paragraphs
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
            
            # Find all posts
            posts = soup.find_all('div', class_='post')
            print(f"Found {len(posts)} posts on this page")
            
            for post in posts:
                try:
                    # Get title from h2 > a
                    title_elem = post.find('h2').find('a')
                    if not title_elem:
                        continue
                    title_text = title_elem.text.strip()
                    article_url = title_elem['href']
                    
                    # Get date from first link in entry-meta
                    meta = post.find('p', class_='entry-meta')
                    date = meta.find('a') if meta else None
                    date_text = date.text.strip() if date else "No date"
                    
                    print(f"\nScraping article: {article_url}")
                    print(f"Title: {title_text}")
                    print(f"Date: {date_text}")
                    
                    # Get full article content
                    article_response = requests.get(article_url, headers=headers)
                    article_response.raise_for_status()
                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                    
                    # Get content
                    content = article_soup.find('div', class_='entry-content')
                    paragraphs = []
                    if content:
                        # Remove social sharing buttons
                        for share in content.find_all('div', class_='sharedaddy'):
                            share.decompose()
                        
                        # Get paragraphs with justified text
                        for p in content.find_all('p', style="text-align:justify"):
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
                time.sleep(2)
            
        except Exception as e:
            print(f"Error processing category page {current_url}: {e}")
            break
    
    return articles

def save_structured_articles(all_articles):
    """Save articles structured by categories"""
    # Create dictionary to hold articles by category
    categories_dict = {}
    
    # Group articles by category
    for article in all_articles:
        for category in article['categories']:
            category_name = category['name']
            category_url = category['url']
            
            if category_name not in categories_dict:
                categories_dict[category_name] = {
                    'Articles': {},
                    'url_of_category': category_url
                }
            
            # Find next article number
            article_num = len(categories_dict[category_name]['Articles']) + 1
            article_key = f'Article{article_num}'
            
            # Add article with simplified structure
            categories_dict[category_name]['Articles'][article_key] = {
                'title': article['title'],
                'date': article['date'],
                'content': article['content']
            }
    
    # Save to JSON with the new structure
    with open('Articles.json', 'w', encoding='utf-8') as f:
        json.dump(categories_dict, f, ensure_ascii=False, indent=4)
    print("Saved articles to Articles.json")

def scrape_mada_actus():
    articles = []
    url = "https://actus.mg/"
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for article in soup.find_all('article'):
            # Get title
            title = article.find('h2', class_='entry-title')
            title_text = title.text.strip() if title else "No title"
            
            # Get date
            date = article.find('time', class_='entry-date')
            date_text = date.text.strip() if date else "No date"
            
            # Get "More..." link
            more_link = article.find('a', class_='more-link')
            if more_link:
                article_url = more_link['href']
                article_response = requests.get(article_url)
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                # Get content
                content = article_soup.find('div', class_='entry-content')
                content_text = ""
                if content:
                    # Exclure les boutons de partage social
                    social_buttons = content.find_all('div', class_='sharedaddy')
                    for button in social_buttons:
                        button.decompose()
                    
                    content_text = content.get_text(strip=True)
                
                articles.append({
                    'title': title_text,
                    'date': date_text,
                    'content': content_text
                })
    
    except Exception as e:
        print(f"Une erreur s'est produite : {str(e)}")
    
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
    
    # After scraping is complete, save structured version
    save_structured_articles(all_articles)

if __name__ == "__main__":
    main()

