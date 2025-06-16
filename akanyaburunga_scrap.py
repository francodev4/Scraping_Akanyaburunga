import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re

def get_article_content(url, headers):
    """Get the full content of an article"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the article content
        content_div = soup.find('div', class_='entry-content')
        if not content_div:
            return ""
        
        # Get all paragraphs
        paragraphs = []
        for p in content_div.find_all('p'):
            text = p.text.strip()
            if text:
                paragraphs.append(text)
        
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"Error getting article content from {url}: {e}")
        return ""

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
                    # Get title and URL
                    title_elem = post.find('h2').find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    article_url = title_elem['href']
                    
                    # Get date
                    meta = post.find('p', class_='entry-meta')
                    date = meta.find('a') if meta else None
                    date_text = date.text.strip() if date else "No date"
                    
                    print(f"\nScraping article: {title}")
                    
                    # Get full article content
                    content = get_article_content(article_url, headers)
                    
                    article_data = {
                        'title': title,
                        'date': date_text,
                        'content': content,
                        'url': article_url
                    }
                    
                    articles.append(article_data)
                    print(f"Successfully scraped: {title}")
                    
                    # Be polite to the server
                    time.sleep(1)
                    
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

def save_articles(categories_data):
    """Save articles to JSON file"""
    with open('akanyaburunga_articles.json', 'w', encoding='utf-8') as f:
        json.dump(categories_data, f, ensure_ascii=False, indent=4)
    print(f"Saved all articles to akanyaburunga_articles.json")

def sanitize_filename(text):
    """Nettoie le texte pour l'utiliser dans un nom de fichier."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\-_ ]', '', text)
    text = text.replace(' ', '-')
    return text

def save_articles_markdown(categories_data):
    """Crée un fichier Markdown pour chaque article dans le dossier articles_markdown."""
    output_dir = "articles_markdown"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for category, data in categories_data.items():
        cat_slug = sanitize_filename(category)
        for article in data.get('articles', []):
            title_slug = sanitize_filename(article.get('title', 'sans-titre'))
            filename = f"akanyaburunga_{cat_slug}_{title_slug}.md"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {article.get('title', 'Sans titre')}\n\n")
                f.write(f"**Catégorie :** {category}\n\n")
                f.write(f"**Date :** {article.get('date', 'Inconnue')}  \n")
                f.write(f"**URL :** {article.get('url', '')}\n\n")
                f.write(f"{article.get('content', '').strip()}\n")
            print(f"Fichier généré : {filepath}")

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
        'https://akanyaburunga.wordpress.com/category/utugenegene/',
        'https://akanyaburunga.wordpress.com/category/yaga-akaranga/'
    ]
    
    # Dictionary to store all categories and their articles
    all_categories = {}
    
    # Scrape each category
    for category_url in categories:
        category_name = category_url.split('/')[-2]  # Get category name from URL
        print(f"\nScraping category: {category_name}")
        
        articles = scrape_category(category_url, headers)
        all_categories[category_name] = {
            'url': category_url,
            'articles': articles
        }
        
        # Save progress after each category
        save_articles(all_categories)
        save_articles_markdown(all_categories)
        
        # Be polite to the server
        time.sleep(3)
    
    print("\nScraping completed!")

if __name__ == "__main__":
    main()