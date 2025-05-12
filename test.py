from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.get("https://www.imdb.com/title/tt0499549/reviews")

# Bypass 'navigator.webdriver' detection
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

print("Page title:", driver.title)
print("First 500 characters of HTML:")
print(driver.page_source[:500])

driver.quit()
