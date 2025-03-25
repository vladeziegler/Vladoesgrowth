from brave_search import BraveSearch
from sequential_thinking import SequentialThinking
from puppeteer import Puppeteer
import asyncio
import json
import os
from datetime import datetime

async def analyze_ai_news():
    # Initialize MCP tools
    thinking = SequentialThinking()
    brave_search = BraveSearch()
    puppeteer = Puppeteer()
    
    # Create results directory
    results_dir = "ai_news_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        print(f"Created results directory: {results_dir}")
    
    # Document the process with Sequential Thinking
    thinking.add_step("Search Setup", "Preparing to search for latest AI news")
    thinking.add_step("Execute Search", "Searching for recent AI developments and news")
    
    # Perform the search using Brave Search
    results = await brave_search.search("latest artificial intelligence news developments 2024")
    print(f"Found {len(results)} search results")
    
    # Analysis categories
    categories = {
        "generative_ai": ["gpt", "llm", "large language model", "chatgpt", "claude", "gemini", "dall-e", "midjourney", "stable diffusion"],
        "ai_ethics": ["ethics", "bias", "fairness", "transparency", "regulation", "governance"],
        "ai_research": ["research", "paper", "study", "breakthrough", "algorithm"],
        "business_ai": ["business", "startup", "funding", "investment", "enterprise", "commercial"],
        "ai_applications": ["healthcare", "finance", "education", "autonomous", "robotics"]
    }
    
    # Analyze results
    thinking.add_step("Result Analysis", "Categorizing and analyzing AI news results")
    categorized_results = {category: [] for category in categories}
    
    for result in results:
        title = result.get('title', '').lower()
        description = result.get('description', '').lower()
        content = title + " " + description
        
        # Categorize each result
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in content:
                    categorized_results[category].append(result)
                    break
    
    # Identify trending topics
    thinking.add_step("Trend Identification", "Identifying trending topics in AI news")
    trending = {}
    for category, results in categorized_results.items():
        trending[category] = len(results)
    
    # Display analysis
    print("=== AI NEWS ANALYSIS ===")
    print(f"Total results analyzed: {len(results)}")
    print("\nTrending Categories:")
    for category, count in sorted(trending.items(), key=lambda x: x[1], reverse=True):
        print(f"- {category.replace('_', ' ').title()}: {count} articles")
    
    print("\nTop Stories by Category:")
    for category, category_results in categorized_results.items():
        if category_results:
            print(f"\n{category.replace('_', ' ').title()}:")
            for result in category_results[:2]:  # Top 2 per category
                print(f"- {result.get('title')}")
                print(f"  {result.get('url')}")
    
    # Save results to JSON
    thinking.add_step("Save Results", "Saving analysis results to JSON file")
    results_file = os.path.join(results_dir, f"ai_news_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_date": datetime.now().isoformat(),
            "total_results": len(results),
            "categories": {k: len(v) for k, v in categorized_results.items()},
            "categorized_results": categorized_results,
            "thinking_process": thinking.get_steps()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"Saved analysis results to {results_file}")
    
    # Use Puppeteer to take screenshots of top news sites
    thinking.add_step("Visual Capture", "Taking screenshots of top AI news websites")
    browser = await puppeteer.launch({
        "headless": False,
        "defaultViewport": {"width": 1366, "height": 768}
    })
    
    page = await browser.newPage()
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Get top URLs across all categories
    top_urls = []
    for category_results in categorized_results.values():
        for result in category_results:
            url = result.get('url')
            if url and url not in top_urls and url.startswith('http'):
                top_urls.append(url)
                if len(top_urls) >= 5:  # Limit to 5 screenshots
                    break
        if len(top_urls) >= 5:
            break
    
    # Take screenshots
    for i, url in enumerate(top_urls):
        try:
            thinking.add_step(f"Screenshot {i+1}", f"Taking screenshot of {url}")
            print(f"Taking screenshot of {url}")
            
            await page.goto(url, {"waitUntil": "networkidle0", "timeout": 30000})
            await page.waitForTimeout(2000)  # Wait for page to fully load
            
            # Generate a safe filename from the URL
            safe_filename = url.replace("://", "_").replace("/", "_").replace(".", "_")[:100]
            screenshot_path = os.path.join(results_dir, f"ai_news_{i+1}_{safe_filename}.png")
            
            await page.screenshot({"path": screenshot_path, "fullPage": True})
            print(f"Saved screenshot to {screenshot_path}")
        except Exception as e:
            print(f"Error taking screenshot of {url}: {str(e)}")
    
    # Close browser
    await browser.close()
    
    # Return summary
    return {
        "status": "success",
        "total_results": len(results),
        "categories_analyzed": len(categories),
        "screenshots_taken": len(top_urls),
        "results_directory": results_dir,
        "results_file": results_file,
        "thinking_process": thinking.get_steps()
    }

async def main():
    result = await analyze_ai_news()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())