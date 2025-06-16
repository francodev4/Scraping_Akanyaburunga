import os
import requests
from typing import Dict, List
from pathlib import Path
from datetime import datetime

# Configuration
UPLOAD_URL = "http://172.233.123.71:8080/api/upload"
CONTRIBUTOR_ID = "46293"  # ID du contributeur

def extract_metadata_from_markdown(file_path: Path) -> Dict:
    """
    Extrait les métadonnées d'un fichier Markdown au format YAML.
    Exemple :
    ---
    title: Titre de l'article
    author: Nom de l'auteur
    source: URL de la source
    date: Date au format RFC3339 (ex: 2025-04-05T12:00:00Z)
    category: Catégorie de l'article
    ---
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    metadata = {}
    if len(lines) >= 2 and lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            line = lines[i].strip()
            if line and ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"')
            i += 1
    
    return metadata


def upload_article_content(file_path: Path, article: Dict) -> bool:
    """
    Effectue l'upload d'un article vers l'API.
    """
    try:
        # Récupération ou génération des métadonnées
        title = article.get('title') or file_path.stem
        author = article.get('author') or 'Anonyme'
        source = article.get('source') or 'local'
        category = article.get('category') or 'Religion'

        # Génération de la date au format RFC3339
        date = article.get('date')
        if not date:
            date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')  # Date actuelle en UTC

        form_data = {
            'contributor_id': CONTRIBUTOR_ID,
            'title': title,
            'author': author,
            'source': source,
            'date': date,
            'category': category,
        }

        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'text/markdown')
            }

            response = requests.post(UPLOAD_URL, data=form_data, files=files)

        if response.status_code == 201:
            print(f"✅ Article uploadé avec succès : {title}")
            return True
        elif response.status_code == 208:
            print(f"⚠️ L'article a déjà été uploadé : {title}")
            return False
        else:
            print(f"❌ Échec de l'upload de l'article : {title}. Code de statut : {response.status_code}")
            print("Réponse détaillée :", response.text)
            return False

    except Exception as e:
        print(f"💥 Erreur lors de l'upload de {file_path}: {e}")
        return False


def main():
    """
    Fonction principale pour uploader tous les fichiers Markdown.
    """
    # MODIFICATION À FAIRE :
    # Remplace "chemin d'acces vers ama article yawe" par le chemin du dossier où se trouvent tes fichiers Markdown.
    # Par exemple : Path("articles_markdown") si tes fichiers sont dans un dossier "articles_markdown" à la racine du projet.
    markdown_directory = Path("articles_markdown")

    # Vérification si le répertoire existe
    if not markdown_directory.exists():
        print(f"❌ Le répertoire {markdown_directory} n'existe pas.")
        return

    # Parcours des fichiers Markdown
    # MODIFICATION À FAIRE :
    # Si tes fichiers sont directement dans le dossier, utilise : markdown_directory.glob("*.md")
    # Si tes fichiers sont dans des sous-dossiers, utilise : markdown_directory.glob("**/*.md")
    markdown_files = list(markdown_directory.glob("*.md"))
    if not markdown_files:
        print("❌ Aucun fichier Markdown trouvé.")
        return

    # Upload des fichiers
    for file_path in markdown_files:
        print(f"\n📎 Traitement du fichier : {file_path}")

        # Extraction des métadonnées
        metadata = extract_metadata_from_markdown(file_path)

        # Upload de l'article
        upload_article_content(file_path, metadata)


if __name__ == "__main__":
    main() 