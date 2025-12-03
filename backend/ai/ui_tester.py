import asyncio
import argparse
import os
from typing import List, Set, Dict, Any
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Page
from PIL import Image
import io
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add backend directory to path so we can import ai.client
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.ai.client import get_ai_client

class UITesterAgent:
    def __init__(self, start_url: str, max_pages: int = 5):
        self.start_url = start_url
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.queue: List[str] = [start_url]
        self.results: List[Dict[str, Any]] = []
        self.ai_client = get_ai_client()
        self.domain = urlparse(start_url).netloc

    async def run(self):
        """Run the UI tester agent."""
        print(f"Starting UI Tester Agent on {self.start_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            
            while self.queue and len(self.visited_urls) < self.max_pages:
                url = self.queue.pop(0)
                
                if url in self.visited_urls:
                    continue
                
                # Skip external links
                if urlparse(url).netloc != self.domain:
                    continue

                try:
                    await self.process_page(context, url)
                except Exception as e:
                    print(f"Error processing {url}: {e}")
                
                self.visited_urls.add(url)

            await browser.close()
        
        self.generate_report()

    async def process_page(self, context, url: str):
        """Visit a page, take a screenshot, and assess it."""
        print(f"Visiting: {url}")
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            
            # Extract links for crawling
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a')).map(a => a.href)
            """)
            
            for link in links:
                # Normalize and filter links
                full_url = urljoin(url, link)
                parsed = urlparse(full_url)
                if parsed.netloc == self.domain and full_url not in self.visited_urls:
                    self.queue.append(full_url)

            # Take screenshot
            screenshot_bytes = await page.screenshot(full_page=True)
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Assess with AI
            assessment = self.assess_page(url, image)
            self.results.append({
                "url": url,
                "assessment": assessment,
                "links_found": len(links)
            })
            
        finally:
            await page.close()

    def assess_page(self, url: str, image: Image.Image) -> str:
        """Use VLM to assess the page."""
        print(f"Assessing {url} with AI...")
        
        system_prompt = """
        You are an expert UI/UX Tester and QA Engineer.
        Your goal is to analyze the provided screenshot of a web page and identify:
        1. Visual bugs (layout issues, overlapping text, broken images).
        2. Usability issues (confusing navigation, poor contrast, hard to read text).
        3. Aesthetic improvements (inconsistent styling, spacing issues).
        4. Functional concerns (if visible, e.g., error messages).
        
        Be concise and specific. If the page looks good, say so.
        Format your response as a markdown list of findings.
        """
        
        prompt = f"Analyze this screenshot of the page at {url}. Identify any UI/UX issues."
        
        response = self.ai_client.generate_with_image(
            prompt=prompt,
            image=image,
            system_prompt=system_prompt
        )
        return response

    def generate_report(self):
        """Generate a markdown report of the findings."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_lines = [
            f"# UI Test Report",
            f"**Date:** {timestamp}",
            f"**Start URL:** {self.start_url}",
            f"**Pages Scanned:** {len(self.visited_urls)}",
            "",
            "## Findings",
            ""
        ]
        
        for result in self.results:
            report_lines.append(f"### Page: {result['url']}")
            report_lines.append(f"**Links Found:** {result['links_found']}")
            report_lines.append("")
            report_lines.append("#### AI Assessment")
            report_lines.append(result['assessment'])
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")

        report_content = "\n".join(report_lines)
        
        output_file = "ui_test_report.md"
        with open(output_file, "w") as f:
            f.write(report_content)
        
        print(f"Report generated: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI UI Tester Agent")
    parser.add_argument("--url", required=True, help="Starting URL to crawl")
    parser.add_argument("--max-pages", type=int, default=5, help="Maximum number of pages to crawl")
    
    args = parser.parse_args()
    
    agent = UITesterAgent(args.url, args.max_pages)
    asyncio.run(agent.run())
