# tools/api_explorer.py
import urllib.request
import urllib.parse
import json
import time
from typing import List, Dict, Optional

class GitHubExplorer:
    """
    Mengeksplorasi GitHub melalui API.
    """
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.headers = {
            'User-Agent': 'Arint/6.0',
            'Accept': 'application/vnd.github.v3+json'
        }
        if token:
            self.headers['Authorization'] = f'token {token}'
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Kirim request ke API GitHub."""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        if params:
            url += '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            print(f"[GitHub API] Error: {e}")
            return None
    
    def trending_repos(self, language: str = "python", limit: int = 5) -> List[Dict]:
        """Ambil repositori tren berdasarkan bahasa."""
        params = {
            'q': f'language:{language}',
            'sort': 'stars',
            'order': 'desc',
            'per_page': limit
        }
        data = self._request('search/repositories', params)
        if not data or 'items' not in data:
            return []
        items = []
        for repo in data['items']:
            items.append({
                'name': repo['full_name'],
                'description': repo['description'] or '',
                'stars': repo['stargazers_count'],
                'url': repo['html_url'],
                'language': repo['language'],
                'created_at': repo['created_at'],
                'updated_at': repo['updated_at']
            })
        return items
    
    def repo_readme(self, owner: str, repo: str) -> Optional[str]:
        """Ambil README repositori (dalam bentuk teks)."""
        endpoint = f'repos/{owner}/{repo}/readme'
        data = self._request(endpoint)
        if data and 'content' in data:
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            return content
        return None
    
    def repo_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """Ambil daftar file dalam direktori."""
        endpoint = f'repos/{owner}/{repo}/contents/{path}'
        data = self._request(endpoint)
        if isinstance(data, list):
            return data
        return []

class HuggingFaceExplorer:
    """
    Mengeksplorasi Hugging Face melalui API.
    """
    BASE_URL = "https://huggingface.co/api"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.headers = {'User-Agent': 'Arint/6.0'}
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        if params:
            url += '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            print(f"[HuggingFace API] Error: {e}")
            return None
    
    def trending_models(self, limit: int = 5) -> List[Dict]:
        """Ambil model populer (berdasarkan likes)."""
        params = {'sort': 'likes', 'direction': -1, 'limit': limit}
        data = self._request('models', params)
        if not data:
            return []
        items = []
        for model in data:
            items.append({
                'id': model['modelId'],
                'pipeline_tag': model.get('pipeline_tag', 'unknown'),
                'likes': model.get('likes', 0),
                'downloads': model.get('downloads', 0),
                'description': model.get('description', '')[:200],
                'tags': model.get('tags', [])
            })
        return items
    
    def model_card(self, model_id: str) -> Optional[str]:
        """Ambil README model (model card)."""
        # HF menyediakan raw README di https://huggingface.co/{model_id}/raw/main/README.md
        url = f"https://huggingface.co/{model_id}/raw/main/README.md"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Arint/6.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode('utf-8')
        except:
            return None
    
    def trending_datasets(self, limit: int = 5) -> List[Dict]:
        """Ambil dataset populer."""
        params = {'sort': 'likes', 'direction': -1, 'limit': limit}
        data = self._request('datasets', params)
        if not data:
            return []
        items = []
        for ds in data:
            items.append({
                'id': ds['datasetId'],
                'likes': ds.get('likes', 0),
                'downloads': ds.get('downloads', 0),
                'description': ds.get('description', '')[:200]
            })
        return items