import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from deep_translator import GoogleTranslator
from collections import Counter
import urllib3
from textblob import TextBlob  # For sentiment analysis
import logging
from browserstack.local import Local
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, TimeoutException, JavascriptException
import threading

# Suppress SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging for errors and missing images
logging.basicConfig(filename="scraper_errors.log", level=logging.ERROR)

# Function to handle cookies consent pop-up
def handle_cookies(driver):
    try:
        consent_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#didomi-notice-agree-button"))
        )
        consent_button.click()
    except Exception as e:
        logging.error(f"Error handling cookies consent: {e}")

# Function to click an element with retries
def click_element(driver, by, value):
    attempts = 3
    while attempts > 0:
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((by, value)))
            element.click()
            return
        except (StaleElementReferenceException, ElementClickInterceptedException, JavascriptException) as e:
            handle_cookies(driver)
            attempts -= 1
            logging.error(f"Retry clicking element due to {e}: {value}")
        except TimeoutException as e:
            logging.error(f"Timeout while waiting for element: {value}")
            break
    logging.error(f"Failed to click element: {value}")

# Function to scrape articles and perform translations and analysis
def scrape_and_analyze(driver):
    driver.get("https://elpais.com/")
    handle_cookies(driver)

    # Click the Opinion section link
    click_element(driver, By.CSS_SELECTOR, "a[href*='opinion']")
    time.sleep(3)  # Wait for the page to load

    # Scrape Articles
    articles = driver.find_elements(By.CSS_SELECTOR, "article")[:5]
    titles = []
    contents = []
    image_urls = []

    for article in articles:
        try:
            title = article.find_element(By.CSS_SELECTOR, "h2").text
            content = article.find_element(By.CSS_SELECTOR, "p").text
            titles.append(title)
            contents.append(content)

            # Print title and content in Spanish
            print(f"Title: {title}")
            print(f"Content: {content}\n")

            # Download cover image if available
            img_element = article.find_elements(By.CSS_SELECTOR, "img")
            if img_element:
                img_url = img_element[0].get_attribute("src")
                image_urls.append(img_url)
                img_data = requests.get(img_url, verify=False).content  # Disable SSL verification
                with open(f"{title}.jpg", "wb") as handler:
                    handler.write(img_data)
            else:
                logging.error(f"No image found for '{title}'")
                image_urls.append(None)
        except Exception as e:
            logging.error(f"Error processing article '{title}': {e}")

    # Translate Article Headers
    translator = GoogleTranslator(source='auto', target='en')
    translated_titles = [translator.translate(title) for title in titles]

    # Print Translated Headers
    print("\nTranslated Titles:")
    for title in translated_titles:
        print(title)

    # Save Translated Titles to a File
    with open("translated_titles.txt", "w", encoding="utf-8") as file:
        for title in translated_titles:
            file.write(title + "\n")

    # Analyze Translated Headers
    words = " ".join(translated_titles).split()
    word_counts = Counter(words)
    repeated_words = {word: count for word, count in word_counts.items() if count > 2}

    # Print Repeated Words
    print("\nRepeated Words:")
    for word, count in repeated_words.items():
        print(f"{word}: {count}")

    # Save Repeated Words to a File
    with open("repeated_words.txt", "w", encoding="utf-8") as file:
        for word, count in repeated_words.items():
            file.write(f"{word}: {count}\n")

    # Sentiment Analysis of Titles
    print("\nSentiment Analysis:")
    for title in translated_titles:
        sentiment = TextBlob(title).sentiment.polarity
        if sentiment > 0:
            sentiment_label = "Positive"
        elif sentiment < 0:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"

        print(f"Title: {title}\nSentiment: {sentiment_label}")

    # Save Sentiment Analysis to a File
    with open("sentiment_analysis.txt", "w", encoding="utf-8") as file:
        for title in translated_titles:
            sentiment = TextBlob(title).sentiment.polarity
            if sentiment > 0:
                sentiment_label = "Positive"
            elif sentiment < 0:
                sentiment_label = "Negative"
            else:
                sentiment_label = "Neutral"

            file.write(f"Title: {title}\nSentiment: {sentiment_label}\n")

    # Translation and Analytics Summary
    print("\nTranslation Summary:")
    print(f"Total Articles Scraped: {len(titles)}")
    print(f"Valid Titles Scraped: {len(translated_titles)}")
    print(f"Total Words in Translated Titles: {len(' '.join(translated_titles).split())}")
    print(f"Unique Words: {len(set(' '.join(translated_titles).split()))}")
    print(f"Most Common Words: {repeated_words}")

# Function to run tests on BrowserStack
def run_browserstack_test(capabilities, test_name):
    try:
        # BrowserStack Hub URL
        browserstack_url = f"https://{USERNAME}:{ACCESS_KEY}@hub.browserstack.com/wd/hub"
        
        # Set up the WebDriver
        options = ChromeOptions() if capabilities['browserName'] == 'Chrome' else (
            SafariOptions() if capabilities['browserName'] == 'Safari' else FirefoxOptions()
        )
        for key, value in capabilities.items():
            options.set_capability(key, value)
        
        driver = webdriver.Remote(
            command_executor=browserstack_url,
            options=options
        )
        
        # Example Test Actions
        scrape_and_analyze(driver)
        
        # End the session
        driver.quit()
    except Exception as e:
        print(f"Error in test {test_name}: {e}")

# Cross-Browser Testing on BrowserStack
USERNAME = 'vinitshah_cSI85W'
ACCESS_KEY = 'ou5hpexVaZiipBWXRAqy'

# Define capabilities for different browsers
capabilities_list = [
    {
        'bstack:options': {
            'os': 'Windows',
            'osVersion': '10',
            'local': 'false',
            'seleniumVersion': '4.0.0',
            'userName': USERNAME,
            'accessKey': ACCESS_KEY,
            'buildName': 'Parallel Build',
            'projectName': 'Demo Project',
            'sessionName': 'Windows-Chrome Test'
        },
        'browserName': 'Chrome',
        'browserVersion': 'latest'
    },
    {
        'bstack:options': {
            'os': 'OS X',
            'osVersion': 'Ventura',
            'local': 'false',
            'seleniumVersion': '4.0.0',
            'userName': USERNAME,
            'accessKey': ACCESS_KEY,
            'buildName': 'Parallel Build',
            'projectName': 'Demo Project',
            'sessionName': 'Mac-Safari Test'
        },
        'browserName': 'Safari',
        'browserVersion': 'latest'
    },
    {
        'bstack:options': {
            'os': 'Android',
            'deviceName': 'Samsung Galaxy S22',
            'realMobile': 'true',
            'local': 'false',
            'seleniumVersion': '4.0.0',
            'userName': USERNAME,
            'accessKey': ACCESS_KEY,
            'buildName': 'Parallel Build',
            'projectName': 'Demo Project',
            'sessionName': 'Android Mobile Test'
        },
        'browserName': 'Chrome'
    }
]

# Run tests in parallel using threading
threads = []
for i, capabilities in enumerate(capabilities_list):
    test_name = f"Test-{i + 1}"
    thread = threading.Thread(target=run_browserstack_test, args=(capabilities, test_name))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

print("All tests completed.")