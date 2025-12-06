#!/usr/bin/env python3
"""
HTML to ScreenSteps Converter
Converts HTML manuals (exported from Google Docs as Web Page) to ScreenSteps JSON format.
"""

import os
import re
import json
import argparse
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup, Tag
import uuid
import sys
import time
from datetime import datetime

# --- Constants ---
APP_VERSION = "1.0.3" # Initial version for HTML converter

# --- Logging Setup ---
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
        log_file = log_dir / f"html_converter_{timestamp}.log"
        
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

def generate_uuid():
    return str(uuid.uuid4()).upper()

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

class HTMLConverter:
    def __init__(self, input_file: Path, output_dir: Path, logger: ProgressLogger):
        self.input_file = input_file
        self.input_dir = input_file.parent
        self.output_dir = output_dir
        self.images_dir = output_dir / "images"
        self.articles_dir = output_dir / "articles"
        self.logger = logger
        
    def setup_directories(self):
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.articles_dir.mkdir(exist_ok=True)

    def parse_structure(self, soup: BeautifulSoup) -> Dict:
        """
        Parses HTML to build Manual > Chapter > Article > Step hierarchy.
        Assumes Google Docs HTML export structure:
        - H1 -> Manual Title / Chapter
        - H2 -> Article Title
        - H3 -> Step Title
        - Other tags -> Content
        """
        manual = {
            "id": generate_uuid(),
            "title": "Converted Manual",
            "chapters": []
        }
        
        current_chapter = None
        current_article = None
        current_step = None
        
        def new_chapter(title):
            return {
                "id": generate_uuid(),
                "title": title,
                "articles": [],
                "order": len(manual["chapters"]) + 1
            }
            
        def new_article(title):
            return {
                "id": generate_uuid(),
                "title": title,
                "steps": [],
                "position": len(current_chapter["articles"]) + 1 if current_chapter else 1
            }
            
        def new_step(title):
            return {
                "id": generate_uuid(),
                "title": title,
                "content": "",
                "order": len(current_article["steps"]) + 1 if current_article else 1,
                "images": []
            }

        # Flatten the body to process tags sequentially
        if soup.body:
            elements = soup.body.find_all(recursive=False)
        else:
            elements = soup.find_all(recursive=False)

        # Google Docs export puts everything in a flat list of p, h1, h2, etc.
        # We need to iterate through them.
        # Sometimes elements are wrapped in divs? Let's try finding all headings and content tags.
        
        # Better strategy for flat HTML: iterate over all direct children of body, or all tags if body missing
        # Filter for relevant block tags
        relevant_tags = ['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'table', 'pre', 'blockquote', 'hr', 'div']
        
        # Use find_all on body if present
        container = soup.body if soup.body else soup
        
        for tag in container.find_all(relevant_tags, recursive=False):
            # Skip empty text nodes or irrelevant tags if any
            if not isinstance(tag, Tag):
                continue
                
            tag_name = tag.name
            text_content = tag.get_text(strip=True)
            
            # Clean HTML content for each tag
            tag_html_content = self._clean_html(str(tag))

            # Check for Google Docs specific classes/styles if needed, but tag name is primary signal
            
            if tag_name == 'h1':
                # H1 logic: First one is Manual Title if not set (or default), others are Chapters
                if not manual["chapters"] and manual["title"] == "Converted Manual":
                    if text_content:
                        manual["title"] = text_content
                    # Create default chapter to hold Intro content
                    current_chapter = new_chapter("Introduction")
                    manual["chapters"].append(current_chapter)
                else:
                    current_chapter = new_chapter(text_content if text_content else "Untitled Chapter")
                    manual["chapters"].append(current_chapter)
                    current_article = None
                    current_step = None
            
            elif tag_name == 'h2':
                if not current_chapter:
                    current_chapter = new_chapter("Introduction")
                    manual["chapters"].append(current_chapter)
                
                current_article = new_article(text_content if text_content else "Untitled Article")
                current_chapter["articles"].append(current_article)
                current_step = None
                
            elif tag_name == 'h3':
                if not current_article:
                    if not current_chapter:
                        current_chapter = new_chapter("General")
                        manual["chapters"].append(current_chapter)
                    current_article = new_article("General Information")
                    current_chapter["articles"].append(current_article)
                
                current_step = new_step(text_content if text_content else "Untitled Step")
                current_article["steps"].append(current_step)
                
            else:
                # Content tags (p, ul, ol, table, etc.)
                if not current_step:
                    # Content before any step? Attach to a default Intro step
                    if not current_article:
                        if not current_chapter:
                            current_chapter = new_chapter("Introduction")
                            manual["chapters"].append(current_chapter)
                        current_article = new_article("Overview")
                        current_chapter["articles"].append(current_article)
                    
                    if not current_article["steps"]:
                        current_step = new_step("Introduction")
                        current_article["steps"].append(current_step)
                    else:
                        # Append to last step
                        current_step = current_article["steps"][-1]

                # Process Images within the tag
                # Google Docs HTML uses local paths like "images/image1.png"
                # We need to copy these to our output images directory
                for img in tag.find_all('img'):
                    src = img.get('src')
                    if src:
                        # Clean src (sometimes url encoded)
                        # src is likely relative like "images/image1.png"
                        img_filename = os.path.basename(src)
                        
                        # Record image for the step
                        current_step["images"].append({
                            "filename": img_filename,
                            "src": src
                        })
                        
                        # Copy file if it exists
                        src_path = self.input_dir / src
                        dst_path = self.images_dir / img_filename
                        
                        if src_path.exists():
                            # Copy image to global images dir (will be moved to article dir later)
                            try:
                                shutil.copy2(src_path, dst_path)
                            except Exception as e:
                                self.logger.warning(f"Failed to copy image {src}: {e}")
                        else:
                            self.logger.warning(f"Image not found: {src_path}")

                # Append the HTML content of the tag to the step
                # We convert the tag back to string
                # NOTE: We might want to clean up Google Docs inline styles here
                current_step["content"] += tag_html_content

        return manual

    def _clean_html(self, html: str) -> str:
        """Clean and normalize HTML content from Google Docs with proper formatting preservation"""
        if not html:
            return ""
        
        # Use BeautifulSoup to parse and transform the HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Remove empty spans that Google Docs often inserts
        for span in soup.find_all('span'):
            if not span.get_text(strip=True) and not span.find('img'):
                span.decompose()

        # Remove empty paragraphs
        for p in soup.find_all('p'):
            if not p.get_text(strip=True) and not p.find('img'):
                p.decompose()

        # Unwrap unnecessary divs that Google Docs uses for styling
        # Retain content inside, but remove the div itself
        for div in soup.find_all('div'):
            # Heuristic: if div only contains a single block element or text, unwrap it.
            # This is a general approach, may need refinement for specific Google Docs structures.
            if len(div.contents) == 1 and isinstance(div.contents[0], Tag) or div.get_text(strip=True):
                div.unwrap()

        return str(soup)

    def convert(self, cleanup: bool = True):
        self.setup_directories()
        
        self.logger.header("HTML to ScreenSteps Converter")
        self.logger.info(f"Input: {self.input_file}")
        self.logger.info(f"Output: {self.output_dir}")
        
        self.logger.step(1, 3, "Reading HTML file")
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to read input file: {e}")
            raise
        self.logger.success(f"Successfully read {self.input_file.name}")

        self.logger.step(2, 3, "Parsing structure and extracting content")
        manual_data = self.parse_structure(soup)
        # Update logger totals based on parsed data (simple count for now)
        total_chapters = len(manual_data.get("chapters", []))
        total_articles = sum(len(ch.get("articles", [])) for ch in manual_data.get("chapters", []))
        total_images = sum(len(step.get("images", [])) 
                             for ch in manual_data.get("chapters", [])
                             for art in ch.get("articles", []) 
                             for step in art.get("steps", []))
        self.logger.set_totals(manuals=1, chapters=total_chapters, articles=total_articles, images=total_images)
        self.logger.substep(f"Found {total_chapters} chapters, {total_articles} articles, {total_images} images")

        self.logger.step(3, 3, "Writing output files")
        self.write_output(manual_data)

        # Cleanup after writing output if not disabled
        if cleanup and self.input_dir.name.startswith("temp_html_extract_"):
            self.logger.info("Cleaning up temporary extraction directory...")
            shutil.rmtree(self.input_dir)
        
        self.logger.header("Conversion Complete!")
        self.logger.success(f"ScreenSteps content created at: {self.output_dir}")
        self.logger.info(f"Log file: {self.logger.log_file}")

def print_usage_examples():
    """Print detailed usage examples"""
    examples = """
╔══════════════════════════════════════════════════════════════════════════╗
║                         USAGE EXAMPLES                                   ║
╚══════════════════════════════════════════════════════════════════════════╝

1. Convert an HTML export file:
   python html_converter.py -i Telco5.1TXDLab.Manualv1.html -o output_html/

2. Convert with verbose logging:
   python html_converter.py -i input.html -o output/ -v

3. Keep temporary files (N/A for HTML converter directly, but consistent with VLP):
   python html_converter.py -i input.html -o output/ --no-cleanup

╔══════════════════════════════════════════════════════════════════════════╗
║                         OUTPUT STRUCTURE                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

output_html/
└── <ManualName>/
    ├── <manual-id>.json          # Table of contents
    ├── articles/
    │   ├── <article-id>.json     # Article metadata (with steps)
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
./vlp2ss-py.sh -i input.html -o output/

# With the API uploader (using the python launcher script):
./vlp2ss-py.sh -i input.zip -o output/ --upload \\
    --account myaccount --user admin --token abc123
./vlp2ss-py.sh -i input.html -o output/ --upload \\
    --account myaccount --user admin --token abc123

"""
    print(examples)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Convert HTML exported content to ScreenSteps format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='For detailed examples, run without arguments or with -h'
    )
    
    parser.add_argument('-i', '--input', type=str,
                       help='Input HTML file or extracted directory')
    parser.add_argument('-o', '--output', type=str, default='output',
                       help='Output directory (default: output)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Keep temporary files after conversion (N/A for direct HTML conversion)')
    parser.add_argument('--version', action='version',
                       version=f'html_converter v{APP_VERSION}')
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
    print(f"{Colors.BOLD}{Colors.HEADER}{'HTML to ScreenSteps Converter'.center(70)}{Colors.ENDC}")
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
        
        converter_instance = HTMLConverter(input_path, output_dir, logger=ProgressLogger(verbose=args.verbose))
        converter_instance.convert(cleanup=not args.no_cleanup)
        
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

