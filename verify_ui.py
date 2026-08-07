from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(record_video_dir=".")
    page = context.new_page()
    page.goto("http://localhost:5173") # wait for initial load
    page.wait_for_timeout(5000) # give time to render layout
    page.screenshot(path="dashboard.png")
    context.close()
    browser.close()
