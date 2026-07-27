import time
from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            record_video_dir="videos/"
        )
        page = context.new_page()

        # Wait for dev server to start
        max_retries = 10
        for i in range(max_retries):
            try:
                page.goto('http://localhost:5173')
                break
            except Exception as e:
                if i == max_retries - 1:
                    raise
                time.sleep(2)

        # Wait for the main app structure to load
        page.wait_for_selector('.bento-grid')

        # Take a screenshot
        page.screenshot(path="frontend_bento_grid.png")

        context.close()
        browser.close()

if __name__ == '__main__':
    verify_frontend()
