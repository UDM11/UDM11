#!/usr/bin/env python3
"""
GitHub README Featured Projects Updater

This script fetches repositories with the 'showcase' topic from a GitHub account
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
    if not username:
        print("Error: GITHUB_ACTOR environment variable not set")
        print("Please provide username via --username flag or set GITHUB_ACTOR")
        sys.exit(1)
    return username


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variable or command line."""
    return os.getenv('GITHUB_TOKEN')


def fetch_showcase_repositories(username: str, token: Optional[str] = None) -> List[Dict]:
    """
    Fetch top repositories from GitHub (sorted by stars and updated date).

    Args:
        username: GitHub username
        token: Optional GitHub token for authentication

    Returns:
        List of repository dictionaries
    """
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
    
    if token:
        headers['Authorization'] = f'token {token}'
    
    # Fetch user's repositories directly
    url = f'https://api.github.com/users/{username}/repos'
    params = {
        'sort': 'updated',
        'order': 'desc',
        'per_page': 20,
        'type': 'owner'  # Only get repositories owned by the user
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        repos = response.json()
        
        if not isinstance(repos, list):
            print(f"Warning: Unexpected API response format")
            return []
        
        # Filter out forks and sort by stars (descending)
        non_forks = [repo for repo in repos if not repo.get('fork', False)]
        sorted_repos = sorted(non_forks, key=lambda x: x.get('stargazers_count', 0), reverse=True)
        
        return sorted_repos
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repositories: {e}")
        sys.exit(1)


def format_repository(repo: Dict) -> str:
    """
    Format a single repository for display in README.

    Args:
        repo: Repository dictionary from GitHub API

    Returns:
        Formatted markdown string
    """
    name = repo.get('name', 'Unknown')
    description = repo.get('description') or 'No description available'
    language = repo.get('language') or 'Unknown'
    stars = repo.get('stargazers_count', 0)
    url = repo.get('html_url', '#')
    
    # Escape special characters in description
    description = description.replace('<', '&lt;').replace('>', '&gt;')
    
    return f"""
### [{name}]({url})

{description}

**Language:** {language} · **⭐ Stars:** {stars}

---"""


def update_readme(repositories: List[Dict], readme_path: str = 'README.md') -> bool:
    """
    Update README.md with featured projects section.

    Args:
        repositories: List of repository dictionaries
        readme_path: Path to README.md file

    Returns:
        True if README was updated, False otherwise
    """
    if not os.path.exists(readme_path):
        print(f"Error: {readme_path} not found")
        sys.exit(1)
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate projects section
    if repositories:
        projects_section = "\n".join([format_repository(repo) for repo in repositories[:6]])
    else:
        projects_section = """
No repositories found yet. Once you create repositories, they will appear here automatically.
"""
    
    # Find and replace the projects section
    pattern = r'<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->'
    replacement = f'<!-- PROJECTS:START -->{projects_section}\n<!-- PROJECTS:END -->'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content == content:
        print("No changes needed - README is already up to date")
        return False
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Updated {readme_path} with {len(repositories[:6])} featured projects")
    return True


def main():
    """Main function to update README with featured projects."""
    # Parse command line arguments
    username = None
    token = None
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == '--username' and i + 1 <= len(sys.argv) - 1:
            username = sys.argv[i + 1]
        elif arg == '--token' and i + 1 <= len(sys.argv) - 1:
            token = sys.argv[i + 1]
    
    # Get username from environment if not provided
    if not username:
        username = get_github_username()
    
    # Get token from environment if not provided
    if not token:
        token = get_github_token()
    
    print(f"Fetching top repositories for user: {username}")
    
    # Fetch repositories
    repositories = fetch_showcase_repositories(username, token)
    
    if not repositories:
        print("No repositories found")
        # Still update README with "no projects" message
        update_readme([])
        return
    
    print(f"Found {len(repositories)} repositories")
    
    # Update README
    updated = update_readme(repositories)
    
    if updated:
        print("README updated successfully")
    else:
        print("No changes made to README")


if __name__ == '__main__':
    main()
