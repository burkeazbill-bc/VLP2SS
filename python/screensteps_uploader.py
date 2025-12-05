#!/usr/bin/env python3
"""
ScreenSteps API Uploader
Uploads converted VLP content to ScreenSteps via API

Author: Burke Azbill
Version: 1.0.3
"""

import sys
import os
import json
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import requests
from requests.auth import HTTPBasicAuth
import uuid
import re
from bs4 import BeautifulSoup
from PIL import Image
from html import unescape

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Helper functions for content block generation
def generate_uuid():
    """Generate a UUID v4 for content blocks"""
    return str(uuid.uuid4()).upper()

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def extract_images_from_html(html_content):
    """Extract image references from HTML"""
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    images = []
    
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src:
            # Extract filename and remove query parameters (e.g., '?X-Amz-Algorithm=...')
            filename = src.split('/')[-1].split('?')[0]
            images.append({
                'src': src,
                'filename': filename,
                'alt': img.get('alt', '')
            })
    
    return images

def remove_images_from_html(html_content):
    """Remove img tags from HTML"""
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    for img in soup.find_all('img'):
        img.decompose()
    return str(soup)

def extract_styled_blocks_from_html(html_content: str) -> List[Dict]:
    """Extract ScreenSteps-styled HTML blocks and their content."""
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    styled_blocks = []
    
    # Find all divs with class 'screensteps-styled-block'
    for div in soup.find_all('div', class_='screensteps-styled-block'):
        style = div.get('data-style')
        if style:
            styled_blocks.append({
                'style': style,
                'html': str(div.decode_contents()) # Get inner HTML
            })
    
    return styled_blocks

def remove_styled_blocks_from_html(html_content: str) -> str:
    """Remove ScreenSteps-styled HTML blocks from HTML."""
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    for div in soup.find_all('div', class_='screensteps-styled-block'):
        div.decompose()
    return str(soup)

def extract_youtube_embeds(html_content):
    """Extract YouTube embed divs from HTML and return list of video IDs"""
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    youtube_embeds = []
    
    # Find all YouTube embed divs
    youtube_divs = soup.find_all('div', class_='html-embed')
    
    for div in youtube_divs:
        # Look for iframe with YouTube embed URL
        iframe = div.find('iframe')
        if iframe:
            src = iframe.get('src', '')
            # Extract video ID from YouTube embed URL
            # Format: https://www.youtube.com/embed/VIDEO_ID
            match = re.search(r'youtube\.com/embed/([^/?]+)', src)
            if match:
                video_id = match.group(1)
                youtube_embeds.append({
                    'video_id': video_id,
                    'html': str(div)
                })
    
    return youtube_embeds

def remove_youtube_embeds_from_html(html_content):
    """Remove YouTube embed divs from HTML"""
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove html-embed divs (YouTube embeds)
    for div in soup.find_all('div', class_='html-embed'):
        div.decompose()
    return str(soup)

def detect_style_from_html(html_content):
    """Detect ScreenSteps style from VLP HTML"""
    if not html_content:
        return None
    
    style_map = {
        'block-style-introduction': 'introduction',
        'block-style-tip': 'tip',
        'block-style-info': 'info',
        'block-style-alert': 'alert',
        'block-style-warning': 'warning'
    }
    
    soup = BeautifulSoup(html_content, 'html.parser')
    for div in soup.find_all('div', class_=True):
        for class_name in div.get('class', []):
            if class_name in style_map:
                return style_map[class_name]
    
    return None

def remove_style_divs(html_content):
    """Remove block-style div wrappers but keep content"""
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    for div in soup.find_all('div', class_=re.compile(r'block-style-')):
        div.unwrap()
    return str(soup)

class ScreenStepsAPI:
    """ScreenSteps API client"""
    
    def __init__(self, account: str, user: str, token: str, logger):
        self.account = account
        self.user = user
        self.token = token
        self.logger = logger
        self.base_url = f"https://{account}.screenstepslive.com/api/v2"
        self.auth = HTTPBasicAuth(user, token)
        self.session = requests.Session()
        self.session.auth = self.auth
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make API request with rate limiting and retry logic"""
        url = f"{self.base_url}/{endpoint}"
        
        # Log request details in verbose mode
        if hasattr(self, 'verbose') and self.verbose:
            self.logger.info("=" * 70)
            self.logger.info("API REQUEST DETAILS:")
            self.logger.info(f"  Endpoint: {method} {url}")
            self.logger.info(f"  Username: {self.user}")
            if 'json' in kwargs:
                self.logger.info(f"  JSON Data: {json.dumps(kwargs['json'], indent=2)}")
            if 'data' in kwargs:
                self.logger.info(f"  Form Data: {kwargs['data']}")
            if 'files' in kwargs:
                self.logger.info(f"  Files: {list(kwargs['files'].keys())}")
            self.logger.info("=" * 70)
        
        while True:
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Log response details in verbose mode
                if hasattr(self, 'verbose') and self.verbose:
                    self.logger.info("API RESPONSE:")
                    self.logger.info(f"  Status Code: {response.status_code}")
                    self.logger.info(f"  Headers: {dict(response.headers)}")
                    try:
                        self.logger.info(f"  Body: {response.json()}")
                    except:
                        self.logger.info(f"  Body: {response.text[:500]}")
                    self.logger.info("=" * 70)
                
                if response.status_code == 200 or response.status_code == 201:
                    # Add delay between successful API calls to avoid rate limiting
                    time.sleep(0.25)
                    return response
                elif response.status_code == 429:
                    # Rate limit exceeded - check for retry_in value
                    try:
                        retry_info = response.json()
                        retry_in = retry_info.get('retry_in', 60)
                        self.logger.warning(f"Rate limit exceeded. Retrying in {retry_in} seconds...")
                        time.sleep(retry_in)                    
                    except ValueError:
                        self.logger.warning("Rate limit exceeded. Retrying in 60 seconds...")
                        time.sleep(60)
                else:
                    self.logger.error("=" * 70)
                    self.logger.error("API REQUEST FAILED:")
                    self.logger.error(f"  Endpoint: {method} {url}")
                    self.logger.error(f"  Username: {self.user}")
                    self.logger.error(f"  Status Code: {response.status_code}")
                    if 'json' in kwargs:
                        self.logger.error(f"  Request JSON: {json.dumps(kwargs['json'], indent=2)}")
                    self.logger.error(f"  Response: {response.text}")
                    self.logger.error("=" * 70)
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                self.logger.error("=" * 70)
                self.logger.error("REQUEST EXCEPTION:")
                self.logger.error(f"  Endpoint: {method} {url}")
                self.logger.error(f"  Username: {self.user}")
                if 'json' in kwargs:
                    self.logger.error(f"  Request JSON: {json.dumps(kwargs['json'], indent=2)}")
                self.logger.error(f"  Error: {e}")
                self.logger.error("=" * 70)
                raise
    
    def get_sites(self) -> List[Dict]:
        """Get all sites"""
        response = self._request('GET', 'sites')
        return response.json().get('sites', [])
    
    def get_site(self, site_id: str) -> Dict:
        """Get site details"""
        response = self._request('GET', f'sites/{site_id}')
        return response.json().get('site', {})
    
    def create_manual(self, site_id: str, title: str, chapters: List[Dict] = None, 
                     published: bool = True) -> Dict:
        """Create a new manual with chapters"""
        data = {
            'manual': {
                'title': title,
                'published': published
            }
        }
        
        # Add chapters array if provided
        if chapters:
            data['manual']['chapters'] = chapters
        
        response = self._request('POST', f'sites/{site_id}/manuals', json=data)
        return response.json().get('manual', {})
    
    def create_chapter(self, site_id: str, manual_id: str, title: str, 
                      position: int, description: str = "") -> Dict:
        """Create a new chapter"""
        data = {
            'chapter': {
                'position': position,
                'title': title,
                'published': True,
                'manual_id': int(manual_id)
            }
        }
        response = self._request('POST', f'sites/{site_id}/chapters', 
                                json=data)
        return response.json().get('chapter', {})
    
    def create_article(self, site_id: str, chapter_id: str, title: str, 
                      position: int) -> Dict:
        """Create a new article (placeholder - content added separately)"""
        data = {
            'article': {
                'position': position,
                'title': title,
                'published': True,
                'chapter_id': int(chapter_id)
            }
        }
        response = self._request('POST', f'sites/{site_id}/articles', 
                                json=data)
        return response.json().get('article', {})
    
    def upload_image(self, site_id: str, article_id: str, 
                   image_path: Path) -> Dict:
        """
        Upload an image using the ScreenSteps Files API
        Reference: https://help.screensteps.com/a/1540764-creating-images-or-file-attachments-via-the-public-api
        
        Equivalent curl command:
        curl -X POST -u user:token https://account_name.screenstepslive.com/api/v2/sites/site_id/files \
             -H "Accept: application/json" \
             -F "type=ImageAsset" \
             -F "file=@image.png"
        """
        with open(image_path, 'rb') as f:
            # Prepare multipart form data (equivalent to curl -F flags)
            files = {
                'type': (None, 'ImageAsset'),  # -F "type=ImageAsset"
                'file': (image_path.name, f, 'image/png')  # -F "file=@image.png"
            }
            
            # Use the _request method which handles rate limiting
            response = self._request('POST', f'sites/{site_id}/files', 
                                   files=files)
            
            # Add delay after successful upload
            # ScreenSteps rate limit: 8 files per 10 seconds for image uploads
            time.sleep(1.25)
            return response.json()
    
    def update_article_contents(self, site_id: str, article_id: str, 
                               title: str, content_blocks: List[Dict], 
                               publish: bool = True) -> Dict:
        """Update article contents with content blocks"""
        data = {
            'article': {
                'title': title,
                'content_blocks': content_blocks,
                'publish': publish
            }
        }
        response = self._request('POST', f'sites/{site_id}/articles/{article_id}/contents', 
                                json=data)
        return response.json().get('article', {})
    
    def generate_content_blocks(self, article_data: Dict, images_dir: Path, 
                               site_id: str, article_id: str, article_vlp_id: str,
                               chapter_title: str = "Unknown", skipped_images: list = None,
                               uploaded_images_count: list = None) -> List[Dict]:
        """Generate ScreenSteps content_blocks from VLP article data"""
        if skipped_images is None:
            skipped_images = []
        if uploaded_images_count is None:
            uploaded_images_count = [0]
        
        content_blocks = []
        sort_order = 1
        
        # Images are stored in article-specific subdirectories
        article_images_dir = images_dir / article_vlp_id
        
        for step in article_data.get('steps', []):
            # Create StepContent block
            step_uuid = generate_uuid()
            step_block = {
                'uuid': step_uuid,
                'type': 'StepContent',
                'title': step['title'],
                'depth': 0,
                'sort_order': sort_order,
                'content_block_ids': [],
                'anchor_name': slugify(step['title']),
                'auto_numbered': False,
                'foldable': False
            }
            content_blocks.append(step_block)
            sort_order += 1

            # New sequential parsing logic to preserve content order
            html_content = step.get('content', '')
            
            block_regex = re.compile(r'(<div class="html-embed">.*?</div>|<div class="screensteps-styled-block".*?>.*?</div>|<img[^>]+src="[^"]+"[^>]*>)', re.DOTALL)
            
            last_index = 0
            
            for match in block_regex.finditer(html_content):
                start, end = match.span()
                
                # 1. Process text before the special block
                text_before = html_content[last_index:start]
                plain_text_before = re.sub(r'<[^>]+>', '', text_before).strip()
                if plain_text_before:
                    text_uuid = generate_uuid()
                    text_block = {
                        'uuid': text_uuid, 'type': 'TextContent', 'body': text_before, 'depth': 1, 
                        'sort_order': sort_order, 'style': None, 'show_copy_clipboard': False
                    }
                    content_blocks.append(text_block)
                    step_block['content_block_ids'].append(text_uuid)
                    sort_order += 1
                
                # 2. Process the special block itself
                block_html = match.group(0)
                
                if block_html.startswith('<img'):
                    img_match = re.search(r'<img[^>]+src="([^"]+)"', block_html)
                    if img_match:
                        src = unescape(img_match.group(1))
                        filename = src.split('/')[-1].split('?')[0]
                        image_path = article_images_dir / filename
                        
                        image_processed = False
                        if image_path.exists():
                            try:
                                image_response = self.upload_image(site_id, article_id, image_path)
                                if image_response and 'file' in image_response and 'id' in image_response['file']:
                                    # ... (code to create image_block) ...
                                    image_asset_id = image_response['file']['id']
                                    image_uuid = generate_uuid()
                                    image_block = {
                                        'uuid': image_uuid, 'type': 'ImageContentBlock', 'asset_file_name': filename,
                                        'image_asset_id': image_asset_id, 'width': image_response['file'].get('width', 800),
                                        'height': image_response['file'].get('height', 600), 'depth': 1, 'sort_order': sort_order,
                                        'alt_tag': "", 'url': image_response['file'].get('url', '')
                                    }
                                    content_blocks.append(image_block)
                                    step_block['content_block_ids'].append(image_uuid)
                                    sort_order += 1
                                    uploaded_images_count[0] += 1
                                    image_processed = True
                                else:
                                    self.logger.warning(f"Invalid API response for image {filename}")
                            except Exception as e:
                                self.logger.warning(f"Failed to upload image {filename}: {e}")
                        else:
                             self.logger.warning(f"Image not found, skipping: {image_path}")

                        if not image_processed:
                            # Add placeholder alert block if image failed to process
                            skipped_images.append({
                                'image_path': str(image_path), 'chapter_title': chapter_title, 
                                'article_title': article_data.get('title', 'Unknown'), 'step_title': step.get('title', 'Unknown')
                            })
                            placeholder_uuid = generate_uuid()
                            placeholder_block = {
                                'uuid': placeholder_uuid, 'type': 'TextContent', 'body': '<p>ERROR IMPORTING IMAGE - PLEASE RE-CREATE SCREENSHOT</p>',
                                'style': 'alert', 'depth': 1, 'sort_order': sort_order, 'anchor_name': '', 
                                'auto_numbered': False, 'foldable': False
                            }
                            content_blocks.append(placeholder_block)
                            step_block['content_block_ids'].append(placeholder_uuid)
                            sort_order += 1

                elif block_html.startswith('<div class="html-embed"'):
                    embed_uuid = generate_uuid()
                    embed_block = {
                        'uuid': embed_uuid, 'type': 'TextContent', 'body': block_html, 'depth': 1,
                        'sort_order': sort_order, 'style': 'html-embed', 'show_copy_clipboard': False
                    }
                    content_blocks.append(embed_block)
                    step_block['content_block_ids'].append(embed_uuid)
                    sort_order += 1
                    
                elif block_html.startswith('<div class="screensteps-styled-block"'):
                    style_match = re.search(r'data-style="([^"]+)"[^>]*>(.*)</div>', block_html, re.DOTALL)
                    if style_match:
                        style = style_match.group(1)
                        inner_body = style_match.group(2)
                        block_uuid = generate_uuid()
                        block = {
                            'uuid': block_uuid, 'type': 'TextContent', 'body': inner_body, 'depth': 1,
                            'sort_order': sort_order, 'style': style, 'show_copy_clipboard': False
                        }
                        content_blocks.append(block)
                        step_block['content_block_ids'].append(block_uuid)
                        sort_order += 1

                last_index = end

            # 3. Process any remaining text after the last special block
            remaining_text = html_content[last_index:]
            plain_remaining_text = re.sub(r'<[^>]+>', '', remaining_text).strip()
            if plain_remaining_text:
                text_uuid = generate_uuid()
                text_block = {
                    'uuid': text_uuid, 'type': 'TextContent', 'body': remaining_text, 'depth': 1,
                    'sort_order': sort_order, 'style': None, 'show_copy_clipboard': False
                }
                content_blocks.append(text_block)
                step_block['content_block_ids'].append(text_uuid)
                sort_order += 1
        
        return content_blocks

class ScreenStepsUploader:
    """Upload converted content to ScreenSteps"""
    
    def __init__(self, account: str, user: str, token: str, verbose: bool = False, suffix: bool = False):
        self.verbose = verbose
        self.setup_logging(verbose)
        self.logger = logging.getLogger(__name__)
        self.api = ScreenStepsAPI(account, user, token, self)
        self.api.verbose = verbose  # Pass verbose flag to API client
        self.image_map = {}  # Map old image paths to new URLs
        # Progress tracking
        self.start_time = time.time()
        self.total_manuals = 0
        self.total_chapters = 0
        self.total_articles = 0
        self.total_images = 0
        self.current_manual = 0
        self.current_chapter = 0
        self.current_article = 0
        self.processed_articles = 0
        self.processed_images = 0
        self.suffix = suffix
    
    def setup_logging(self, verbose: bool):
        """Configure logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"screensteps_upload_{timestamp}.log"
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if not verbose else logging.DEBUG)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Configure logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.log_file = log_file
    
    def header(self, message: str):
        """Print header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{message.center(70)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        self.logger.info(f"HEADER: {message}")
    
    def success(self, message: str):
        """Print success"""
        print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")
        self.logger.info(f"SUCCESS: {message}")
    
    def info(self, message: str):
        """Print info"""
        if self.verbose:
            print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")
        self.logger.info(message)
    
    def warning(self, message: str):
        """Print warning"""
        print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")
        self.logger.warning(message)
    
    def error(self, message: str):
        """Print error"""
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")
        self.logger.error(message)
    
    def step(self, step_num: int, total_steps: int, message: str):
        """Print step"""
        print(f"{Colors.OKBLUE}[{step_num}/{total_steps}] {message}{Colors.ENDC}")
        self.logger.info(f"STEP [{step_num}/{total_steps}]: {message}")
    
    def substep(self, message: str, indent: int = 1):
        """Print substep"""
        if self.verbose:
            indent_str = "  " * indent
            print(f"{indent_str}→ {message}")
        self.logger.debug(f"SUBSTEP: {message}")
    
    def set_totals(self, manuals: int = 1, chapters: int = 0, articles: int = 0, images: int = 0):
        """Set total counts for progress tracking"""
        self.total_manuals = manuals
        self.total_chapters = chapters
        self.total_articles = articles
        self.total_images = images
    
    def get_progress_string(self) -> str:
        """Generate progress percentage string"""
        manual_pct = (self.current_manual / self.total_manuals * 100) if self.total_manuals > 0 else 0
        chapter_pct = (self.current_chapter / self.total_chapters * 100) if self.total_chapters > 0 else 0
        article_pct = (self.current_article / self.total_articles * 100) if self.total_articles > 0 else 0
        return f"[ Manual: {manual_pct:.0f}%, Chapter: {chapter_pct:.0f}%, Article: {article_pct:.0f}% ]"
    
    def estimate_time_remaining(self) -> str:
        """Estimate remaining time based on progress"""
        if self.processed_articles == 0:
            return "Calculating..."
        
        elapsed = time.time() - self.start_time
        
        # Use weighted formula: articles are primary driver, images add time
        # Based on user data: ~10-15 seconds per article + ~2 seconds per image
        avg_time_per_article = 12.5  # seconds
        avg_time_per_image = 2.0     # seconds
        
        # Calculate estimated total time
        estimated_total = (self.total_articles * avg_time_per_article) + (self.total_images * avg_time_per_image)
        
        # Calculate progress-based estimate
        articles_remaining = self.total_articles - self.processed_articles
        images_remaining = self.total_images - self.processed_images
        
        estimated_remaining = (articles_remaining * avg_time_per_article) + (images_remaining * avg_time_per_image)
        
        # Format time
        minutes, seconds = divmod(int(estimated_remaining), 60)
        if minutes > 0:
            return f"~{minutes}m {seconds}s"
        else:
            return f"~{seconds}s"
    
    def progress(self, message: str):
        """Print a progress message with percentages and time estimate"""
        progress_str = self.get_progress_string()
        time_est = self.estimate_time_remaining()
        print(f"{Colors.OKBLUE}{progress_str} {message} {Colors.OKCYAN}[ETA: {time_est}]{Colors.ENDC}")
        self.logger.info(f"{progress_str} {message} [ETA: {time_est}]")
    
    def _html_to_content_blocks(self, html_content: str) -> List[Dict]:
        """Convert HTML content to ScreenSteps content blocks"""
        import uuid
        import re
        
        if not html_content:
            return []
        
        content_blocks = []
        
        # Split by paragraphs and headers
        # This is a simple conversion - for complex content, may need more sophisticated parsing
        parts = re.split(r'(<h[1-6][^>]*>.*?</h[1-6]>|<p[^>]*>.*?</p>)', html_content, flags=re.DOTALL)
        
        step_number = 1
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Check if it's a header (treat as step)
            header_match = re.match(r'<h([1-6])[^>]*>(.*?)</h\1>', part, re.DOTALL)
            if header_match:
                level = int(header_match.group(1))
                title = re.sub(r'<[^>]+>', '', header_match.group(2)).strip()
                
                content_blocks.append({
                    'uuid': str(uuid.uuid4()),
                    'type': 'StepContent',
                    'title': title,
                    'depth': 0,
                    'sort_order': step_number
                })
                step_number += 1
            # Check if it's a paragraph (treat as text content)
            elif part.startswith('<p') or part.startswith('<'):
                content_blocks.append({
                    'uuid': str(uuid.uuid4()),
                    'type': 'TextContent',
                    'body': part,
                    'depth': 1,
                    'sort_order': step_number
                })
                step_number += 1
        
        # If no content blocks were created, create a single text block
        if not content_blocks:
            content_blocks.append({
                'uuid': str(uuid.uuid4()),
                'type': 'TextContent',
                'body': html_content,
                'depth': 0,
                'sort_order': 1
            })
        
        return content_blocks
    
    def upload(self, content_dir: Path, site_id: str, 
               create_new: bool = True) -> Dict:
        """Upload content to ScreenSteps"""
        
        # Track skipped images
        skipped_images = []
        
        # Track uploaded images
        uploaded_images_count = [0]  # Use list to allow modification in nested function
        
        self.header("ScreenSteps Content Uploader")
        self.info(f"Content directory: {content_dir}")
        self.info(f"Target site ID: {site_id}")
        
        # Step 1: Verify connection
        self.step(1, 6, "Verifying ScreenSteps connection")
        try:
            sites = self.api.get_sites()
            site_found = any(s['id'] == int(site_id) for s in sites)
            if not site_found:
                raise ValueError(f"Site ID {site_id} not found")
            self.success(f"Connected to ScreenSteps account: {self.api.account}")
        except Exception as e:
            self.error(f"Connection failed: {e}")
            raise
        
        # Step 2: Load content
        self.step(2, 6, "Loading converted content")
        toc_file = self._find_toc_file(content_dir)
        if not toc_file:
            raise FileNotFoundError("No TOC file found in content directory")
        
        with open(toc_file, 'r', encoding='utf-8') as f:
            manual_data = json.load(f)
        
        manual_info = manual_data['manual']
        self.substep(f"Manual: {manual_info['title']}")
        self.substep(f"Chapters: {len(manual_info['chapters'])}")
        
        # Count totals for progress tracking
        total_chapters = len(manual_info['chapters'])
        total_articles = sum(len(ch['articles']) for ch in manual_info['chapters'])
        total_images = 0
        for chapter_data in manual_info['chapters']:
            for article_data in chapter_data['articles']:
                for step in article_data.get('steps', []):
                    total_images += len(step.get('images', []))
        
        self.set_totals(manuals=1, chapters=total_chapters, articles=total_articles, images=total_images)
        self.current_manual = 1
        
        # Step 3: Create manual with chapters
        self.step(3, 5, "Creating manual with chapters in ScreenSteps")
        chapter_map = {}
        
        if create_new:
            # Prepare chapters array for manual creation
            chapters_array = []
            for idx, chapter_data in enumerate(manual_info['chapters'], 1):
                chapters_array.append({
                    'position': chapter_data.get('order', idx),
                    'title': chapter_data['title'],
                    'published': True
                })
            
            # Create manual with all chapters in one call
            # Manual is unpublished, but chapters remain published
            manual_title = manual_info['title']
            if self.suffix:
                manual_title += "-python"
            manual = self.api.create_manual(
                site_id,
                manual_title,
                chapters=chapters_array,
                published=False  # Manual unpublished for review
            )
            manual_id = str(manual['id'])
            self.success(f"Created manual: {manual['title']} (ID: {manual_id})")
            
            # Map old chapter IDs to new chapter IDs from response
            if 'chapters' in manual:
                for idx, chapter_data in enumerate(manual_info['chapters']):
                    if idx < len(manual['chapters']):
                        chapter_map[chapter_data['id']] = str(manual['chapters'][idx]['id'])
                        self.substep(f"Created chapter: {manual['chapters'][idx]['title']}")
        else:
            # Use existing manual ID from file
            manual_id = str(manual_info['id'])
            self.info(f"Using existing manual ID: {manual_id}")
            
            # Still need to create chapters individually if using existing manual
            self.step(4, 5, "Creating chapters")
            for idx, chapter_data in enumerate(manual_info['chapters'], 1):
                chapter = self.api.create_chapter(
                    site_id,
                    manual_id,
                    chapter_data['title'],
                    position=chapter_data.get('order', idx),
                    description=chapter_data.get('description', '')
                )
                chapter_map[chapter_data['id']] = str(chapter['id'])
                self.substep(f"Created: {chapter['title']}")
        
        # Step 4: Create articles and add content
        self.step(4, 5, "Creating articles and adding content")
        images_dir = content_dir / "images"  # Images are in content_dir/images/article_id/
        
        for chapter_idx, chapter_data in enumerate(manual_info['chapters'], 1):
            self.current_chapter = chapter_idx
            chapter_id = chapter_map.get(chapter_data['id'])
            if not chapter_id:
                continue
            
            for article_data in chapter_data['articles']:
                self.current_article += 1
                article_vlp_id = article_data['id']  # VLP article ID for finding images
                
                # Show progress
                self.progress(f"Creating article: {article_data['title']}")
                
                # Create article placeholder
                article = self.api.create_article(
                    site_id,
                    chapter_id,
                    article_data['title'],
                    position=article_data.get('position', self.current_article)
                )
                article_id_new = str(article['id'])
                
                # Generate content blocks (uploads images internally)
                content_blocks = self.api.generate_content_blocks(
                    article_data,
                    images_dir,
                    site_id,
                    article_id_new,
                    article_vlp_id,  # Pass VLP ID to find images
                    chapter_title=chapter_data.get('title', 'Unknown'),
                    skipped_images=skipped_images,
                    uploaded_images_count=uploaded_images_count
                )
                
                # Update article contents
                if content_blocks:
                    try:
                        self.api.update_article_contents(
                            site_id,
                            article_id_new,
                            article_data['title'],
                            content_blocks,
                            publish=True
                        )
                        if self.verbose:
                            self.substep(f"  Updated content with {len(content_blocks)} blocks")
                    except Exception as e:
                        self.warning(f"Failed to update article contents: {e}")
                
                # Track processed articles and images
                self.processed_articles += 1
                # Count images in this article
                for step in article_data.get('steps', []):
                    self.processed_images += len(step.get('images', []))
        
        # Final progress update
        self.progress("Upload complete!")
        
        self.header("Upload Complete!")
        self.success(f"Manual: {manual_info['title']}")
        self.success(f"Manual created with {self.processed_articles} articles")
        self.success(f"Images uploaded: {uploaded_images_count[0]}")
        if skipped_images:
            self.warning(f"Images skipped: {len(skipped_images)}")
        else:
            self.success("Images skipped: 0")
        self.info(f"Log file: {self.log_file}")
        
        # Display skipped images summary
        if skipped_images:
            self.header("Skipped Images Summary")
            self.warning(f"Total images skipped: {len(skipped_images)}")
            self.info("Images were replaced with alert: ERROR IMPORTING IMAGE - PLEASE RE-CREATE SCREENSHOT")
            print()
            
            # Group by chapter
            from collections import defaultdict
            chapter_map = defaultdict(list)
            for img in skipped_images:
                chapter_map[img['chapter_title']].append(img)
            
            # Display grouped by chapter and article
            for chapter_title, images in chapter_map.items():
                self.info(f"Chapter: {chapter_title}")
                
                # Group by article within chapter
                article_map = defaultdict(list)
                for img in images:
                    article_map[img['article_title']].append(img)
                
                for article_title, article_images in article_map.items():
                    self.substep(f"  Article: {article_title}")
                    for img in article_images:
                        self.substep(f"    Step: {img['step_title']}")
                        self.substep(f"      Image: {Path(img['image_path']).name}")
                print()
        
        return {
            'manual_id': manual_id,
            'chapters': len(chapter_map),
            'articles': self.processed_articles
        }
    
    def _find_toc_file(self, content_dir: Path) -> Optional[Path]:
        """Find the TOC JSON file"""
        for file in content_dir.glob('*.json'):
            if file.stem != 'manifest':  # Exclude manifest files
                return file
        return None

def print_usage_examples():
    """Print detailed usage examples"""
    examples = """
╔══════════════════════════════════════════════════════════════════════════╗
║                         USAGE EXAMPLES                                   ║
╚══════════════════════════════════════════════════════════════════════════╝

1. Upload converted content to ScreenSteps:
   python screensteps_uploader.py \\
       --content output/HOL-2601-03-VCF-L \\
       --account myaccount \\
       --user admin \\
       --token abc123xyz \\
       --site 12345

2. Upload with verbose logging:
   python screensteps_uploader.py \\
       --content output/HOL-2601-03-VCF-L \\
       --account myaccount \\
       --user admin \\
       --token abc123xyz \\
       --site 12345 \\
       --verbose

3. Use existing manual (don't create new):
   python screensteps_uploader.py \\
       --content output/HOL-2601-03-VCF-L \\
       --account myaccount \\
       --user admin \\
       --token abc123xyz \\
       --site 12345 \\
       --no-create

╔══════════════════════════════════════════════════════════════════════════╗
║                    GENERATING API TOKEN                                  ║
╚══════════════════════════════════════════════════════════════════════════╝

1. Log in to your ScreenSteps account
2. Go to Account Settings > API Tokens
3. Click "Generate New Token"
4. Give it "Full Access" permission
5. Copy the token and use it with --token parameter

╔══════════════════════════════════════════════════════════════════════════╗
║                         BASH SCRIPT USAGE                                ║
╚══════════════════════════════════════════════════════════════════════════╝

# Complete workflow: Convert and upload
./vlp2ss.sh -i input.zip -o output/ \\
    --upload \\
    --account myaccount \\
    --user admin \\
    --token abc123xyz \\
    --site 12345

"""
    print(examples)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Upload converted VLP content to ScreenSteps via API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='For detailed examples, run with --examples'
    )
    
    parser.add_argument('--content', type=str,
                       help='Path to converted content directory')
    parser.add_argument('--account', type=str, default=os.environ.get('SS_ACCOUNT'),
                       help='ScreenSteps account name (or SS_ACCOUNT env var)')
    parser.add_argument('--user', type=str, default=os.environ.get('SS_USER'),
                       help='ScreenSteps user ID (or SS_USER env var)')
    parser.add_argument('--token', type=str, default=os.environ.get('SS_TOKEN'),
                       help='ScreenSteps API token (or SS_TOKEN env var)')
    parser.add_argument('--site', type=str, default=os.environ.get('SS_SITE'),
                       help='ScreenSteps site ID (or SS_SITE env var)')
    parser.add_argument('--no-create', action='store_true',
                       help='Use existing manual (don\'t create new)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--version', action='version',
                       version='VLP2SS - The VLP to ScreenSteps Uploader\nVersion: 1.0.3\nAuthor: Burke Azbill\nLicense: MIT')
    parser.add_argument('--examples', action='store_true',
                       help='Show detailed usage examples')
    parser.add_argument('--suffix', action='store_true',
                       help='Append -python suffix to manual titles')
    
    args = parser.parse_args()
    
    # Show examples
    if args.examples or not args.content:
        if args.examples:
            print_usage_examples()
            return 0
        parser.print_help()
        print("\n" + "="*70)
        print_usage_examples()
        return 0
    
    # Validate required arguments
    if not all([args.account, args.user, args.token, args.site]):
        print(f"{Colors.FAIL}Error: --account, --user, --token, and --site are required, or set SS_ACCOUNT, SS_USER, SS_TOKEN, and SS_SITE environment variables.{Colors.ENDC}")
        return 1
    
    try:
        start_time = time.time()
        
        content_dir = Path(args.content)
        if not content_dir.exists():
            print(f"{Colors.FAIL}Error: Content directory does not exist: {content_dir}{Colors.ENDC}")
            return 1
        
        uploader = ScreenStepsUploader(
            args.account,
            args.user,
            args.token,
            verbose=args.verbose,
            suffix=args.suffix
        )
        
        uploader.upload(
            content_dir,
            args.site,
            create_new=not args.no_create
        )
        
        elapsed = time.time() - start_time
        minutes, seconds = divmod(int(elapsed), 60)
        if minutes > 0:
            print(f"{Colors.OKCYAN}ℹ Total execution time: {minutes}m {seconds}s{Colors.ENDC}")
        else:
            print(f"{Colors.OKCYAN}ℹ Total execution time: {seconds}s{Colors.ENDC}")
        
        return 0
        
    except Exception as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        logging.exception("Upload failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

