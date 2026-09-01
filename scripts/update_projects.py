#!/usr/bin/env python3
"""
GitHub README Featured Projects Updater

This script fetches top repositories from a GitHub account
and updates the README.md file with the featured projects section.

Requirements:
- GitHub username via GITHUB_ACTOR environment variable or --username flag
- GitHub token via GITHUB_TOKEN environment variable or --token flag
- README.md must contain <!-- PROJECTS:START --> and <!-- PROJECTS:END --> markers
"""

import os
import sys
import re
from typing import List, Dict, Optional
import requests


def get_github_username() -> str:
    """Get GitHub username from environment variable or command line."""
    username = os.getenv('GITHUB_ACTOR')
    if not username or username.lower() in ('github-actions[bot]', 'github-actions'):
        username = 'UDM11'
    return username


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variable or command line."""
    return os.getenv('GITHUB_TOKEN')


def fetch_showcase_repositories(username: str, token: Optional[str] = None) -> List[Dict]:
    """
    Fetch top repositories from GitHub, prioritizing real full projects with rich descriptions over empty learning repos.
    """
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
    
    if token:
        headers['Authorization'] = f'token {token}'
    
    url = f'https://api.github.com/users/{username}/repos'
    params = {
        'sort': 'updated',
        'order': 'desc',
        'per_page': 100,
        'type': 'owner'
    }
    
    # Generic practice/learning repos to de-prioritize
    generic_repo_names = {'python', 'c-programming', 'dsa-in-c', 'html-and-css', 'java-script', 'basic-java-program', 'genai', 'mern', 'reactproject', username.lower()}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        repos = response.json()
        
        if not isinstance(repos, list):
            print("Warning: Unexpected API response format")
            return []
        
        # Filter out forks and profile config repo
        non_forks = [repo for repo in repos if not repo.get('fork', False) and repo.get('name', '').lower() != username.lower()]
        
        # Score repositories based on completeness (has description, not generic, has stars, recently updated)
        def score_repo(r: Dict) -> tuple:
            name_lower = r.get('name', '').lower()
            has_desc = bool(r.get('description'))
            is_generic = name_lower in generic_repo_names
            stars = r.get('stargazers_count', 0)
            updated_at = r.get('pushed_at') or r.get('updated_at') or ''
            
            # Highest priority: has description and not generic
            priority = 2 if (has_desc and not is_generic) else (1 if has_desc else 0)
            return (priority, stars, updated_at)
        
        sorted_repos = sorted(non_forks, key=score_repo, reverse=True)
        top_repos = sorted_repos[:6]
        
        # Fetch detailed languages for top repositories
        for repo in top_repos:
            try:
                lang_url = repo.get('languages_url')
                if lang_url:
                    lang_res = requests.get(lang_url, headers=headers)
                    if lang_res.status_code == 200:
                        repo['languages_data'] = list(lang_res.json().keys())
                    else:
                        repo['languages_data'] = []
                else:
                    repo['languages_data'] = []
            except Exception:
                repo['languages_data'] = []
        
        return top_repos
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repositories: {e}")
        sys.exit(1)


def get_project_icon(name: str, description: str) -> str:
    """Return an appropriate emoji icon based on project keywords."""
    text = (name + ' ' + description).lower()
    if 'nepse' in text or 'trading' in text or 'market' in text or 'stock' in text:
        return '📈'
    if 'car' in text or 'showroom' in text or 'vehicle' in text:
        return '🚗'
    if 'travel' in text or 'tour' in text or 'trip' in text or 'itinerary' in text:
        return '✈️'
    if 'agent' in text or 'agentic' in text:
        return '🤖'
    if 'ims' in text or 'intern' in text or 'management' in text or 'portal' in text:
        return '👥'
    if 'react' in text:
        return '⚛️'
    if 'ai' in text or 'ml' in text or 'llm' in text or 'rag' in text:
        return '🧠'
    return '🚀'


def get_tech_badges(repo: Dict) -> str:
    """Detect and return rich shields.io tech badges from repo languages, topics, and description."""
    name = repo.get('name', '')
    desc = repo.get('description') or ''
    primary_lang = repo.get('language') or ''
    topics = repo.get('topics', [])
    repo_languages = repo.get('languages_data', [])
    
    all_text = (name + ' ' + desc + ' ' + primary_lang + ' ' + ' '.join(topics) + ' ' + ' '.join(repo_languages)).lower()
    
    # Pre-defined badge catalogue with official logos & brand colors
    badge_catalog = [
        ('fastapi', 'FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white', 'FastAPI'),
        ('react', 'React-20232A?style=flat-square&logo=react&logoColor=61DAFB', 'React'),
        ('typescript', 'TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white', 'TypeScript'),
        ('python', 'Python-3776AB?style=flat-square&logo=python&logoColor=white', 'Python'),
        ('supabase', 'Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=white', 'Supabase'),
        ('langchain', 'LangChain-1C3C3C?style=flat-square&logo=chainlink&logoColor=white', 'LangChain'),
        ('chromadb', 'ChromaDB-FF4F00?style=flat-square', 'ChromaDB'),
        ('openai', 'OpenAI-412991?style=flat-square&logo=openai&logoColor=white', 'OpenAI'),
        ('xgboost', 'XGBoost-111111?style=flat-square', 'XGBoost'),
        ('pytorch', 'PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white', 'PyTorch'),
        ('tensorflow', 'TensorFlow-FF6F00?style=flat-square&logo=tensorflow&logoColor=white', 'TensorFlow'),
        ('scikit', 'Scikit--Learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white', 'Scikit-Learn'),
        ('jwt', 'JWT-black?style=flat-square&logo=JSON%20web%20tokens', 'JWT'),
        ('tailwind', 'TailwindCSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white', 'TailwindCSS'),
        ('vite', 'Vite-646CFF?style=flat-square&logo=vite&logoColor=white', 'Vite'),
        ('next', 'Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white', 'Next.js'),
        ('node', 'Node.js-6DA55F?style=flat-square&logo=node.js&logoColor=white', 'Node.js'),
        ('express', 'Express.js-404D59?style=flat-square&logo=express&logoColor=61DAFB', 'Express.js'),
        ('postgres', 'PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white', 'PostgreSQL'),
        ('redis', 'Redis-DC382D?style=flat-square&logo=redis&logoColor=white', 'Redis'),
        ('firebase', 'Firebase-FFCA28?style=flat-square&logo=firebase&logoColor=black', 'Firebase'),
        ('docker', 'Docker-2496ED?style=flat-square&logo=docker&logoColor=white', 'Docker'),
        ('javascript', 'JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black', 'JavaScript'),
        ('html', 'HTML5-E34F26?style=flat-square&logo=html5&logoColor=white', 'HTML5'),
        ('css', 'CSS3-1572B6?style=flat-square&logo=css3&logoColor=white', 'CSS3'),
        ('php', 'PHP-777BB4?style=flat-square&logo=php&logoColor=white', 'PHP'),
        ('java', 'Java-ED8B00?style=flat-square&logo=openjdk&logoColor=white', 'Java'),
        ('c++', 'C%2B%2B-00599C?style=flat-square&logo=c%2B%2B&logoColor=white', 'C++'),
    ]
    
    selected_badges = []
    seen = set()
    
    for key, slug, alt in badge_catalog:
        if key in all_text and alt not in seen:
            selected_badges.append(f'<img src="https://img.shields.io/badge/{slug}" alt="{alt}"/>')
            seen.add(alt)
            if len(selected_badges) >= 4:
                break
    
    # Fallback to primary language if no badges matched
    if not selected_badges and primary_lang:
        selected_badges.append(f'<img src="https://img.shields.io/badge/{primary_lang}-3178C6?style=flat-square" alt="{primary_lang}"/>')
    
    # Append star count if > 0
    stars = repo.get('stargazers_count', 0)
    if stars > 0:
        selected_badges.append(f'<img src="https://img.shields.io/badge/⭐_{stars}-yellow?style=flat-square" alt="Stars"/>')
        
    return "\n        ".join(selected_badges)


def format_repository_card(repo: Dict) -> str:
    """Format a single repository card for display in table."""
    name = repo.get('name', 'Unknown')
    description = repo.get('description') or 'Full-stack software engineering project.'
    url = repo.get('html_url', '#')
    icon = get_project_icon(name, description)
    badges = get_tech_badges(repo)
    
    description = description.replace('<', '&lt;').replace('>', '&gt;')
    
    return f"""    <td width="50%" valign="top">
      <h3>{icon} <a href="{url}">{name}</a></h3>
      <p>{description}</p>
      <p>
        {badges}
      </p>
    </td>"""


def generate_projects_table(repositories: List[Dict]) -> str:
    """Generate a responsive 2-column table grid for projects."""
    if not repositories:
        return "\n<p align=\"center\">No repositories found yet.</p>\n"
    
    rows = []
    for i in range(0, len(repositories), 2):
        pair = repositories[i:i+2]
        cells = [format_repository_card(repo) for repo in pair]
        if len(cells) == 1:
            cells.append('    <td width="50%" valign="top"></td>')
        row_content = "\n".join(cells)
        rows.append(f"  <tr>\n{row_content}\n  </tr>")
    
    table_content = "\n".join(rows)
    return f"\n<table>\n{table_content}\n</table>\n"


def update_readme(repositories: List[Dict], readme_path: str = 'README.md') -> bool:
    """
    Update README.md with featured projects section.
    """
    if not os.path.exists(readme_path):
        print(f"Error: {readme_path} not found")
        sys.exit(1)
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate projects section
    projects_section = generate_projects_table(repositories)
    
    # Find and replace the projects section
    pattern = r'<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->'
    replacement = f'<!-- PROJECTS:START -->{projects_section}<!-- PROJECTS:END -->'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content == content:
        print("No changes needed - README is already up to date")
        return False
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Updated {readme_path} with {len(repositories)} featured projects")
    return True


def main():
    """Main function to update README with featured projects."""
    username = None
    token = None
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == '--username' and i + 1 <= len(sys.argv) - 1:
            username = sys.argv[i + 1]
        elif arg == '--token' and i + 1 <= len(sys.argv) - 1:
            token = sys.argv[i + 1]
    
    if not username:
        username = get_github_username()
    if not token:
        token = get_github_token()
    
    print(f"Fetching top repositories for user: {username}")
    repositories = fetch_showcase_repositories(username, token)
    
    if not repositories:
        print("No repositories found")
        update_readme([], 'README.md')
        return
    
    print(f"Found {len(repositories)} repositories with language data")
    updated = update_readme(repositories, 'README.md')
    
    if updated:
        print("README updated successfully with real tech badges")
    else:
        print("No changes made to README")


if __name__ == '__main__':
    main()
