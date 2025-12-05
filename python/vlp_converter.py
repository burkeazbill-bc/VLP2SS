#!/usr/bin/env python3
"""
VLP to ScreenSteps Converter
Converts VMware Lab Platform (VLP) exported content to ScreenSteps format

Author: Burke Azbill
Version: 1.0.3
"""

import sys
import os
import json
import zipfile
import shutil
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import re
from html import unescape
import uuid
from bs4 import BeautifulSoup
from PIL import Image
from bs4 import Tag # Added this import for Tag type hinting

# --- Constants ---
APP_VERSION = "1.0.3"

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

class ProgressLogger:
    """Enhanced logging with progress indicators"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.setup_logging()
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
    
    def setup_logging(self):
        """Configure logging with file and console handlers"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"vlp_converter_{timestamp}.log"
        
        # File handler - detailed logs
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler - user-friendly output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if not self.verbose else logging.DEBUG)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.log_file = log_file
    
    def header(self, message: str):
        """Print a header message"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{message.center(70)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        logging.info(f"HEADER: {message}")
    
    def success(self, message: str):
        """Print a success message"""
        print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")
        logging.info(f"SUCCESS: {message}")
    
    def info(self, message: str):
        """Print an info message"""
        if self.verbose:
            print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")
        logging.info(message)
    
    def warning(self, message: str):
        """Print a warning message"""
        print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")
        logging.warning(message)
    
    def error(self, message: str):
        """Print an error message"""
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")
        logging.error(message)
    
    def step(self, step_num: int, total_steps: int, message: str):
        """Print a step progress message"""
        print(f"{Colors.OKBLUE}[{step_num}/{total_steps}] {message}{Colors.ENDC}")
        logging.info(f"STEP [{step_num}/{total_steps}]: {message}")
    
    def substep(self, message: str, indent: int = 1):
        """Print a sub-step message"""
        if self.verbose:
            indent_str = "  " * indent
            print(f"{indent_str}→ {message}")
        logging.debug(f"SUBSTEP: {message}")
    
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
        logging.info(f"{progress_str} {message} [ETA: {time_est}]")

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
            # Extract filename from path like './images/filename.png'
            # Remove query parameters (e.g., '?X-Amz-Algorithm=...')
            # Ensure src is a string
            src_str = str(src) if not isinstance(src, str) else src
            filename = src_str.split('/')[-1].split('?')[0]
            images.append({
                'src': src_str,
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
        div_classes = div.get('class')
        if div_classes:
            for class_name in div_classes:
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

class VLPParser:
    """Parser for VLP XML content"""
    
    def __init__(self, logger: ProgressLogger):
        self.logger = logger
    
    def parse_xml(self, xml_path: Path) -> Dict:
        """Parse VLP content.xml file"""
        self.logger.info(f"Parsing VLP XML: {xml_path}")
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            manual_data = {
                'id': root.get('id'),
                'name': root.findtext('name', ''),
                'language': root.findtext('defaultLanguageCode', 'en'),
                'format': root.findtext('dataFormat', 'default'),
                'chapters': []
            }
            
            # Parse content nodes (chapters and articles)
            content_nodes = root.find('contentNodes')
            if content_nodes is not None:
                for node in content_nodes.findall('ContentNode'):
                    parsed_node = self._parse_content_node(node)
                    if parsed_node:
                        manual_data['chapters'].append(parsed_node)
            
            self.logger.success(f"Parsed manual: {manual_data['name']}")
            self.logger.substep(f"Found {len(manual_data['chapters'])} top-level sections")
            
            return manual_data
            
        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error parsing XML: {e}")
            raise
    
    def _parse_content_node(self, node: ET.Element, level: int = 0) -> Optional[Dict]:
        """Recursively parse content nodes (chapters/articles)"""
        node_data = {
            'id': node.get('id'),
            'title': node.findtext('title', ''),
            'order': int(node.findtext('orderIndex', '0')),
            'content': '',
            'images': [],
            'children': []
        }
        
        # Parse localizations
        localizations = node.find('localizations')
        if localizations is not None:
            locale_content = localizations.find('LocaleContent')
            if locale_content is not None:
                node_data['title'] = locale_content.findtext('title', node_data['title'])
                node_data['language'] = locale_content.findtext('languageCode', 'en')
                node_data['content'] = locale_content.findtext('content', '')
                
                # Parse images
                images = locale_content.find('images')
                if images is not None:
                    for img in images.findall('img'):
                        node_data['images'].append({
                            'src': img.get('src', ''),
                            'filename': img.get('filename', ''),
                            'width': img.get('width', ''),
                            'height': img.get('height', '')
                        })
        
        # Parse children recursively
        children = node.find('children')
        if children is not None:
            for child_node in children.findall('ContentNode'):
                child_data = self._parse_content_node(child_node, level + 1)
                if child_data:
                    node_data['children'].append(child_data)
        
        return node_data
    
    def flatten_structure(self, manual_data: Dict) -> List[Dict]:
        """
        Flatten VLP hierarchical structure into ScreenSteps format:
        - Level 1 nodes become chapters
        - Level 2 nodes become articles  
        - Level 3 nodes become steps (content_blocks) within articles
        """
        # First pass: count totals for progress tracking
        total_chapters = len(manual_data['chapters'])
        total_articles = 0
        total_images = 0
        
        for chapter_node in manual_data['chapters']:
            if chapter_node.get('children'):
                total_articles += len(chapter_node['children'])
                for article_node in chapter_node['children']:
                    # Count images in article
                    total_images += len(article_node.get('images', []))
                    # Count images in steps
                    if article_node.get('children'):
                        for step_node in article_node['children']:
                            total_images += len(step_node.get('images', []))
        
        # Set totals for progress tracking
        self.logger.set_totals(manuals=1, chapters=total_chapters, articles=total_articles, images=total_images)
        self.logger.current_manual = 1
        
        chapters = []
        
        for chapter_idx, chapter_node in enumerate(manual_data['chapters'], 1):
            self.logger.current_chapter = chapter_idx
            
            chapter = {
                'id': chapter_node['id'],
                'title': chapter_node['title'],
                'order': chapter_node['order'],
                'description': self._clean_html(chapter_node['content']),
                'articles': []
            }
            
            # Process level 2 children as articles
            if chapter_node.get('children'):
                # Sort articles by VLP order, then assign sequential positions
                sorted_articles = sorted(chapter_node['children'], key=lambda x: x['order'])
                
                for position, article_node in enumerate(sorted_articles, start=1):
                    self.logger.current_article += 1
                    self.logger.progress(f"Processing article: {article_node['title']}")
                    
                    article = {
                        'id': article_node['id'],
                        'title': article_node['title'],
                        'vlp_order': article_node['order'],  # Keep VLP order for reference
                        'position': position,  # Sequential position for ScreenSteps
                        'steps': []  # Store level 3 as steps
                    }
                    
                    # Process level 3 children as steps
                    if article_node.get('children'):
                        # Sort steps by VLP order
                        sorted_steps = sorted(article_node['children'], key=lambda x: x['order'])
                        for step_node in sorted_steps:
                            step = {
                                'id': step_node['id'],
                                'title': step_node['title'],
                                'order': step_node['order'],
                                'content': self._clean_html(step_node['content']),
                                'images': step_node.get('images', [])
                            }
                            article['steps'].append(step)
                            # Count processed images
                            self.logger.processed_images += len(step_node.get('images', []))
                    else:
                        # If no level 3, treat article content as single step
                        step = {
                            'id': article_node['id'],
                            'title': article_node['title'],
                            'order': 0,
                            'content': self._clean_html(article_node['content']),
                            'images': article_node.get('images', [])
                        }
                        article['steps'].append(step)
                        # Count processed images
                        self.logger.processed_images += len(article_node.get('images', []))
                    
                    chapter['articles'].append(article)
                    self.logger.processed_articles += 1
            
            chapters.append(chapter)
        
        return chapters
    
    def _node_to_article(self, node: Dict, parent: Dict) -> Dict:
        """Convert a VLP node to a ScreenSteps article"""
        return {
            'id': node['id'],
            'title': node['title'],
            'order': node['order'],
            'content': self._clean_html(node['content']),
            'html_body': node['content'],
            'images': node.get('images', []),
            'parent_title': parent.get('title', ''),
            'meta_title': node['title'],
            'meta_description': self._extract_description(node['content']),
            'created_at': datetime.now().isoformat(),
            'last_edited_at': datetime.now().isoformat()
        }
    
    def _clean_html(self, html: str) -> str:
        """Clean and normalize HTML content with proper formatting preservation"""
        if not html:
            return ""
        
        # First unescape HTML entities (may need multiple passes for double-encoding)
        html = unescape(html)
        # Second pass to handle double-encoded entities like &amp;gt; -> &gt; -> >
        html = unescape(html)
        
        # Parse and convert VLP-specific formatting to standard HTML
        html = self._convert_vlp_formatting(html)
        
        # Fix image paths - remove ./ prefix
        html = re.sub(r'src=["\']\./', 'src="', html)
        
        return html.strip()
    
    def _convert_vlp_formatting(self, html: str) -> str:
        """Convert VLP-specific span classes to proper HTML formatting tags"""
        if not html:
            return ""
        
        try:
            # Use BeautifulSoup to parse and transform the HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Convert YouTube embeds first (before other transformations)
            self._convert_youtube_embeds(soup)
            
            # Map of VLP CSS classes to HTML tags
            # c5 is commonly used for bold/strong text in VLP exports
            class_to_tag_map = {
                'c0': 'strong',
                'c3': 'strong',
                'c5': 'strong',
                'c6': 'code',
                'c7': 'strong',
            }
            
            # Find all span elements with class attributes
            for span in soup.find_all('span', class_=True):
                classes = span.get('class')
                if not classes:
                    continue
                
                # Check if any class matches our mapping
                replacement_tag = None
                # Prioritize 'c5' (strong) over other classes if present
                if 'c5' in classes:
                    replacement_tag = 'strong'
                else:
                    for cls in classes:
                        if cls in class_to_tag_map:
                            replacement_tag = class_to_tag_map[cls]
                            break
                
                if replacement_tag:
                    # Create new tag with the same content
                    new_tag = soup.new_tag(replacement_tag)
                    # Preserve the inner content (including nested tags and text)
                    new_tag.extend(span.contents)
                    # Replace the span with the new tag
                    span.replace_with(new_tag)
                else:
                    # If no mapping found, unwrap the span but keep its content
                    # This handles spans like <span class="c0"> that are just containers
                    if span.string:
                        span.unwrap()
            
            # Convert back to string first
            html = str(soup)
            
            # Convert VLP paragraph classes to ScreenSteps formatted blocks
            html = self._convert_vlp_paragraph_styles(html)
            
            # Use the result from paragraph styles conversion
            result = html
            
            # Clean up any remaining empty spans
            result = re.sub(r'<span[^>]*>\s*</span>', '', result)
            
            # Normalize <ol> start attributes and handle nested lists
            soup = BeautifulSoup(result, 'html.parser')
            for ol_tag in soup.find_all('ol'):
                if ol_tag.has_attr('start'):
                    del ol_tag['start']
                
                # Handle nested list types based on Google Docs classes (lst-kix_...-N)
                # Level 0 is default (1, 2, 3...)
                # Level 1 should be alpha (a, b, c...)
                # Level 2 should be roman (i, ii, iii...)
                classes = ol_tag.get('class')
                if classes:
                    for cls in classes:
                        if 'lst-kix_' in cls:
                            if cls.endswith('-1'):
                                ol_tag['type'] = 'a'
                                # Add margin to simulate nesting since they are often separate blocks
                                # Force list style type via CSS as HTML attribute is often overridden
                                ol_tag['style'] = 'margin-left: 40px; list-style-type: lower-latin;'
                            elif cls.endswith('-2'):
                                ol_tag['type'] = 'i'
                                ol_tag['style'] = 'margin-left: 80px; list-style-type: upper-latin;'
            result = str(soup)

            return result
            
        except Exception as e:
            # If parsing fails, return original HTML
            self.logger.warning(f"Failed to parse HTML for formatting conversion: {e}")
            return html
    
    def _convert_vlp_paragraph_styles(self, html_content: str) -> str:
        """Convert VLP paragraph classes to ScreenSteps formatted blocks."""
        if not html_content:
            return ""

        p_class_to_style_map = {
            'c10': 'introduction',
            'c44': 'introduction',
            'c48': 'info',
            'c28': 'info',
            'c39': 'info',
            # Add other mappings here as they are identified
        }

        soup = BeautifulSoup(html_content, 'html.parser')
        # Use a copy of the list of tags to iterate over, as we are modifying the tree
        # Filter to ensure only valid Tag objects are included
        all_p_tags = [p for p in soup.find_all('p') if p is not None and isinstance(p, Tag)]
        processed_tags = set()

        for p_class, style in p_class_to_style_map.items():
            # Find all tags with the current class
            tags_with_class = [
                p for p in all_p_tags 
                if (p_classes := p.get('class')) and p_class in p_classes and p not in processed_tags
            ]
            
            i = 0
            while i < len(tags_with_class):
                start_tag = tags_with_class[i]
                if start_tag in processed_tags:
                    i += 1
                    continue

                group = [start_tag]
                processed_tags.add(start_tag)
                
                # Find consecutive siblings with the same class
                next_sibling = start_tag.find_next_sibling()
                while next_sibling and isinstance(next_sibling, Tag) and next_sibling.has_attr('class'):
                    sibling_classes = next_sibling.get('class')
                    if sibling_classes and p_class in sibling_classes:
                        if next_sibling in processed_tags:
                            break # Stop if we hit a tag that's already part of another group
                        group.append(next_sibling)
                        processed_tags.add(next_sibling)
                        next_sibling = next_sibling.find_next_sibling()
                    else:
                        break

                # Filter out empty paragraphs and paragraphs that contain ONLY images (no text)
                # Styled blocks should only contain text content, not standalone images
                content_tags = [p for p in group if p and p.get_text(strip=True)]
                
                if content_tags:
                    # Create the styled div and insert it into the tree *before* the start tag.
                    styled_div = soup.new_tag('div')
                    styled_div['class'] = 'screensteps-styled-block'
                    styled_div['data-style'] = style
                    start_tag.insert_before(styled_div)

                    # Move the content tags into the new div
                    for tag in content_tags:
                        if tag and tag.parent:  # Only extract if tag is valid and still in tree
                            styled_div.append(tag.extract())
                
                # Decompose only truly empty tags (no text and no images)
                # Leave image-only paragraphs in place so they can be processed as separate content blocks
                for tag in group:
                    if tag and tag.parent and tag not in content_tags:
                        # Only decompose if the tag has no images
                        if not tag.find('img'):
                            tag.decompose()
                
                # Move to the next unprocessed tag
                i += len(group)
                
        return str(soup)
    
    def _convert_youtube_embeds(self, soup: BeautifulSoup) -> None:
        """Convert VLP YouTube embed divs to ScreenSteps iframe format"""
        # Find all YouTube embed divs
        youtube_divs = soup.find_all('div', class_='mediatag-thumb youtube-thumb')
        
        for youtube_div in youtube_divs:
            # Extract the YouTube video ID from data-media-id attribute
            video_id = youtube_div.get('data-media-id')
            
            if not video_id:
                # Try to extract from data-thumb-url as fallback
                thumb_url = youtube_div.get('data-thumb-url')
                if thumb_url:
                    thumb_url_str = str(thumb_url) if not isinstance(thumb_url, str) else thumb_url
                    match = re.search(r'youtube\.com/vi/([^/]+)/', thumb_url_str)
                    if match:
                        video_id = match.group(1)
            
            if video_id:
                # Create the ScreenSteps-compatible HTML embed structure
                # Outer div with html-embed class (no tabindex, no wrapper div)
                outer_div = soup.new_tag('div')
                outer_div['class'] = 'html-embed'
                
                # Create the iframe directly inside html-embed div
                iframe = soup.new_tag('iframe')
                iframe['width'] = '560'
                iframe['height'] = '315'
                iframe['src'] = f'https://www.youtube.com/embed/{video_id}'
                iframe['title'] = 'YouTube video player'
                iframe['frameborder'] = '0'
                iframe['allow'] = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share'
                iframe['referrerpolicy'] = 'strict-origin-when-cross-origin'
                iframe['allowfullscreen'] = ''
                
                # Assemble the structure
                outer_div.append(iframe)
                
                # Replace the VLP YouTube div with the ScreenSteps format
                youtube_div.replace_with(outer_div)
                
                self.logger.substep(f"Converted YouTube embed: {video_id}")
            else:
                self.logger.warning("Found YouTube embed div but could not extract video ID")
    
    def _extract_description(self, html: str, max_length: int = 200) -> str:
        """Extract plain text description from HTML"""
        if not html:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text

class ScreenStepsConverter:
    """Converter from VLP to ScreenSteps format"""
    
    def __init__(self, logger: ProgressLogger):
        self.logger = logger
    
    def convert(self, vlp_data: Dict, chapters: List[Dict], 
                output_dir: Path, images_dir: Path) -> Dict:
        """Convert VLP data to ScreenSteps format"""
        
        self.logger.info("Converting to ScreenSteps format...")
        
        # Create ScreenSteps manual structure
        manual = {
            'manual': {
                'id': vlp_data['id'],
                'title': vlp_data['name'],
                'language': vlp_data['language'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'chapters': []
            }
        }
        
        # Convert chapters
        for chapter in chapters:
            ss_chapter = {
                'id': chapter['id'],
                'title': chapter['title'],
                'order': chapter['order'],
                'description': chapter.get('description', ''),
                'articles': []
            }
            
            # Convert articles (with steps)
            for article in chapter['articles']:
                ss_article = {
                    'id': article['id'],
                    'title': article['title'],
                    'position': article['position'],  # Sequential position for ScreenSteps
                    'vlp_order': article.get('vlp_order'),  # Keep VLP order for reference
                    'steps': article.get('steps', [])  # Include steps
                }
                ss_chapter['articles'].append(ss_article)
            
            manual['manual']['chapters'].append(ss_chapter)
        
        self.logger.success(f"Converted {len(chapters)} chapters with articles")
        
        return manual
    
    def write_output(self, manual: Dict, chapters: List[Dict], 
                     output_dir: Path, images_source: Path) -> Tuple[int, int]:
        """Write ScreenSteps formatted output and return counts"""
        
        self.logger.info("Writing ScreenSteps output files...")
        
        # Create directory structure
        articles_dir = output_dir / "articles"
        images_dir = output_dir / "images"
        articles_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Write table of contents
        toc_file = output_dir / f"{manual['manual']['id']}.json"
        with open(toc_file, 'w', encoding='utf-8') as f:
            json.dump(manual, f, indent=2, ensure_ascii=False)
        self.logger.substep(f"Created TOC: {toc_file.name}")
        
        # Write individual articles and count images
        article_count = 0
        image_count = 0
        for chapter in manual['manual']['chapters']:
            for article in chapter['articles']:
                article_id = article['id']
                
                # Write article JSON (with steps)
                article_file = articles_dir / f"{article_id}.json"
                with open(article_file, 'w', encoding='utf-8') as f:
                    json.dump(article, f, indent=2, ensure_ascii=False)
                
                # Copy article images from steps
                article_images_dir = images_dir / article_id
                article_images_dir.mkdir(exist_ok=True)
                
                for step in article.get('steps', []):
                    for img_info in step.get('images', []):
                        src_image = images_source / img_info['filename']
                        if src_image.exists():
                            dst_image = article_images_dir / src_image.name
                            shutil.copy2(src_image, dst_image)
                            image_count += 1
                
                article_count += 1
        
        self.logger.substep(f"Created {article_count} article files with {image_count} images")
        self.logger.success(f"Output written to: {output_dir}")
        
        return article_count, image_count

class VLPToScreenStepsConverter:
    """Main converter class"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = ProgressLogger(verbose)
        self.parser = VLPParser(self.logger)
        self.converter = ScreenStepsConverter(self.logger)
    
    def convert_zip(self, zip_path: Path, output_dir: Path, 
                    cleanup: bool = True) -> Path:
        """Convert a VLP ZIP export to ScreenSteps format"""
        
        self.logger.header("VLP to ScreenSteps Converter")
        self.logger.info(f"Input: {zip_path}")
        self.logger.info(f"Output: {output_dir}")
        
        # Step 1: Extract ZIP
        self.logger.step(1, 5, "Extracting VLP ZIP file")
        temp_dir = self._extract_zip(zip_path)
        
        # Step 2: Parse VLP XML
        self.logger.step(2, 5, "Parsing VLP content")
        xml_file = temp_dir / "content.xml"
        if not xml_file.exists():
            raise FileNotFoundError(f"content.xml not found in {temp_dir}")
        
        vlp_data = self.parser.parse_xml(xml_file)
        
        # Step 3: Flatten structure
        self.logger.step(3, 5, "Flattening content structure")
        chapters = self.parser.flatten_structure(vlp_data)
        self.logger.substep(f"Created {len(chapters)} chapters")
        total_articles = sum(len(ch['articles']) for ch in chapters)
        self.logger.substep(f"Created {total_articles} articles")
        
        # Step 4: Convert to ScreenSteps format
        self.logger.step(4, 5, "Converting to ScreenSteps format")
        manual = self.converter.convert(vlp_data, chapters, output_dir, 
                                       temp_dir / "images")
        
        # Step 5: Write output
        self.logger.step(5, 5, "Writing output files")
        output_path = output_dir / vlp_data['name']
        output_path.mkdir(parents=True, exist_ok=True)
        
        images_source = temp_dir / "images"
        article_count, image_count = self.converter.write_output(manual, chapters, output_path, images_source)
        
        # Cleanup
        if cleanup:
            self.logger.info("Cleaning up temporary files...")
            shutil.rmtree(temp_dir)
        
        self.logger.header("Conversion Complete!")
        self.logger.success(f"ScreenSteps content created at: {output_path}")
        self.logger.success(f"Converted {len(chapters)} chapters, {article_count} articles, {image_count} images")
        self.logger.info(f"Log file: {self.logger.log_file}")
        
        return output_path
    
    def convert_directory(self, dir_path: Path, output_dir: Path) -> Path:
        """Convert an extracted VLP directory to ScreenSteps format"""
        
        self.logger.header("VLP to ScreenSteps Converter")
        self.logger.info(f"Input: {dir_path}")
        self.logger.info(f"Output: {output_dir}")
        
        # Parse VLP XML
        self.logger.step(1, 4, "Parsing VLP content")
        xml_file = dir_path / "content.xml"
        if not xml_file.exists():
            raise FileNotFoundError(f"content.xml not found in {dir_path}")
        
        vlp_data = self.parser.parse_xml(xml_file)
        
        # Flatten structure
        self.logger.step(2, 4, "Flattening content structure")
        chapters = self.parser.flatten_structure(vlp_data)
        self.logger.substep(f"Created {len(chapters)} chapters")
        total_articles = sum(len(ch['articles']) for ch in chapters)
        self.logger.substep(f"Created {total_articles} articles")
        
        # Convert to ScreenSteps format
        self.logger.step(3, 4, "Converting to ScreenSteps format")
        manual = self.converter.convert(vlp_data, chapters, output_dir, 
                                       dir_path / "images")
        
        # Write output
        self.logger.step(4, 4, "Writing output files")
        output_path = output_dir / vlp_data['name']
        output_path.mkdir(parents=True, exist_ok=True)
        
        images_source = dir_path / "images"
        article_count, image_count = self.converter.write_output(manual, chapters, output_path, images_source)
        
        self.logger.header("Conversion Complete!")
        self.logger.success(f"ScreenSteps content created at: {output_path}")
        self.logger.success(f"Converted {len(chapters)} chapters, {article_count} articles, {image_count} images")
        self.logger.info(f"Log file: {self.logger.log_file}")
        
        return output_path
    
    def _extract_zip(self, zip_path: Path) -> Path:
        """Extract ZIP file to temporary directory"""
        temp_dir = Path("temp") / zip_path.stem
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.substep(f"Extracting to: {temp_dir}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the actual content directory (may be nested)
        content_xml = None
        for root, dirs, files in os.walk(temp_dir):
            if 'content.xml' in files:
                content_xml = Path(root)
                break
        
        if content_xml and content_xml != temp_dir:
            # Move contents up if nested
            for item in content_xml.iterdir():
                shutil.move(str(item), str(temp_dir / item.name))
        
        self.logger.substep(f"Extracted {len(list(temp_dir.rglob('*')))} files")
        
        return temp_dir

def print_usage_examples():
    """Print detailed usage examples"""
    examples = """
╔══════════════════════════════════════════════════════════════════════════╗
║                         USAGE EXAMPLES                                   ║
╚══════════════════════════════════════════════════════════════════════════╝

1. Convert a VLP ZIP file:
   python vlp_converter.py -i HOL-2601-03-VCF-L_en.zip -o output/

2. Convert an extracted VLP directory:
   python vlp_converter.py -i VLP-Export-Samples/HOL-2601-03-VCF-L-en/ -o output/

3. Convert with verbose logging:
   python vlp_converter.py -i input.zip -o output/ -v

4. Keep temporary files for debugging:
   python vlp_converter.py -i input.zip -o output/ --no-cleanup

5. Batch convert multiple files:
   for file in *.zip; do
       python vlp_converter.py -i "$file" -o output/
   done

╔══════════════════════════════════════════════════════════════════════════╗
║                         OUTPUT STRUCTURE                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

output/
└── HOL-2601-03-VCF-L/
    ├── <manual-id>.json          # Table of contents
    ├── articles/
    │   ├── <article-id>.json     # Article metadata
    │   └── <article-id>.html     # Article content
    └── images/
        └── <article-id>/
            └── *.png             # Article images

╔══════════════════════════════════════════════════════════════════════════╗
║                         BASH SCRIPT USAGE                                ║
╚══════════════════════════════════════════════════════════════════════════╝

# Using the bash wrapper:
# This bash script is intended to be a launcher for the python scripts,
# NOT a standalone converter and uploader.
./vlp2ss-py.sh -i input.zip -o output/

# With the API uploader (using the python launcher script):
./vlp2ss-py.sh -i input.zip -o output/ --upload \\
    --account myaccount --user admin --token abc123

"""
    print(examples)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Convert VLP exported content to ScreenSteps format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='For detailed examples, run without arguments or with -h'
    )
    
    parser.add_argument('-i', '--input', type=str,
                       help='Input VLP ZIP file or extracted directory')
    parser.add_argument('-o', '--output', type=str, default='output',
                       help='Output directory (default: output)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Keep temporary files after conversion')
    parser.add_argument('--version', action='version',
                       version=f'vlp2ss-py v{APP_VERSION}')
    parser.add_argument('--examples', action='store_true',
                       help='Show detailed usage examples')
    
    args = parser.parse_args()
    
    # Show examples if no input or --examples flag
    if not args.input or args.examples:
        if args.examples:
            print_usage_examples()
            return 0
        parser.print_help()
        print("\n" + "="*70)
        print_usage_examples()
        return 0
    
    # --- Print Header ---
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'VLP to ScreenSteps Converter'.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{f'Version: {APP_VERSION}'.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")
    
    try:
        start_time = time.time()
        
        input_path = Path(args.input)
        output_dir = Path(args.output)
        
        if not input_path.exists():
            print(f"{Colors.FAIL}Error: Input path does not exist: {input_path}{Colors.ENDC}")
            return 1
        
        # Clean logs and output directories at startup
        logs_dir = Path("logs")
        if logs_dir.exists():
            shutil.rmtree(logs_dir)
        logs_dir.mkdir(exist_ok=True)
        
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        converter = VLPToScreenStepsConverter(verbose=args.verbose)
        
        if input_path.is_file() and input_path.suffix == '.zip':
            converter.convert_zip(input_path, output_dir, 
                                 cleanup=not args.no_cleanup)
        elif input_path.is_dir():
            converter.convert_directory(input_path, output_dir)
        else:
            print(f"{Colors.FAIL}Error: Input must be a ZIP file or directory{Colors.ENDC}")
            return 1
        
        elapsed = time.time() - start_time
        minutes, seconds = divmod(int(elapsed), 60)
        if minutes > 0:
            print(f"{Colors.OKCYAN}ℹ Total execution time: {minutes}m {seconds}s{Colors.ENDC}")
        else:
            print(f"{Colors.OKCYAN}ℹ Total execution time: {seconds}s{Colors.ENDC}")
        
        return 0
        
    except Exception as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        logging.exception("Conversion failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

