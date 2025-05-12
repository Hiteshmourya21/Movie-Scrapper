from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time
import re

def get_imdb_reviews(movie_title):
    print(f"[DEBUG] Searching for movie: {movie_title}")

    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless")  # Uncomment for headless mode

    driver = webdriver.Chrome(options=options)

    try:
        search_url = f"https://www.imdb.com/find?q={movie_title.replace(' ', '+')}&s=tt&ttype=ft"
        driver.get(search_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href^='/title/tt']"))
        )
        links = driver.find_elements(By.CSS_SELECTOR, "a[href^='/title/tt']")

        movie_url = None
        for link in links:
            href = link.get_attribute("href")
            if "/title/tt" in href:
                movie_url = href
                print(f"[DEBUG] Found movie URL: {movie_url}")
                break

        if not movie_url:
            return [], "Movie not found."

        movie_id = re.search(r'tt\d+', movie_url).group()
        print(f"[DEBUG] Found movie ID: {movie_id}")

        review_url = f"https://www.imdb.com/title/{movie_id}/reviews"
        driver.get(review_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="review"]'))
        )

        # Scroll and click "Load More" if available
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            try:
                load_more_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-qa="load-more-button"]'))
                )
                load_more_button.click()
                print("[DEBUG] Clicked 'Load More'")
                time.sleep(2)
            except (TimeoutException, NoSuchElementException):
                break
            except StaleElementReferenceException:
                continue  # retry if button was refreshed

        # Extract reviews
        review_blocks = driver.find_elements(By.CSS_SELECTOR, '[data-testid="review"]')
        reviews = []

        for block in review_blocks:
            try:
                review_text = block.text.strip()
                if review_text:
                    reviews.append(review_text)
            except Exception as e:
                print(f"[WARN] Could not extract a review block: {e}")
                continue

        if not reviews:
            print("[DEBUG] No reviews extracted.")
            return [], "No reviews found."

        print(f"[DEBUG] Extracted {len(reviews)} reviews.")
        return reviews, None

    except Exception as e:
        print(f"[EXCEPTION] {str(e)}")
        return [], f"Error occurred: {str(e)}"

    finally:
        driver.quit()
