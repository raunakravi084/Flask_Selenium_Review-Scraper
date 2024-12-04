from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import re
import urllib.parse as urlparse
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from urllib.request import urlopen as uReq

app = Flask(__name__)


@app.route('/', methods=['GET'])  # route to display the homepage
@cross_origin()
def homepage():
    return render_template("index.html")


# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless=new")  # Use the latest headless mode for Chrome
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)  # Add explicit wait


@app.route('/review', methods=['POST', 'GET'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")

            # Step 1: Search for "iPhone 15" on Flipkart
            # search_text = "iPhone 15"
            search_url = "https://www.flipkart.com/search?q=" + searchString
            driver.get(search_url)
            time.sleep(5)  # Wait for the page to load

            # Step 2: Find and click on the first product link
            first_product_element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "tUxRFH"))
            )
            first_product_link = first_product_element.find_element(By.TAG_NAME, "a")
            first_product_link.click()
            time.sleep(5)  # Wait for the product page to load

            # Switch to the new tab if opened in a new tab
            driver.switch_to.window(driver.window_handles[-1])

            # Step 3: Find and click on the reviews link
            try:
                # Wait for the reviews section to be visible
                reviews_section = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "pPAw9M"))
                )

                # Find the reviews link within the section
                reviews_link = reviews_section.find_element(By.TAG_NAME, "a")

                # Get the href attribute
                reviews_url = reviews_link.get_attribute("href")

                # Clean the URL to get only the main reviews (remove additional parameters)
                base_reviews_url = re.match(r'(.*?)\?', reviews_url).group(1)
                if not base_reviews_url:
                    base_reviews_url = reviews_url.split('?')[0]

                # Navigate to the main reviews page
                driver.get(base_reviews_url)

                # print("Successfully navigated to reviews page!")
                # print("Reviews page URL:", driver.current_url)

                # Wait for the reviews to load
                time.sleep(5)

            except Exception as e:
                print("Error accessing reviews:", str(e))

            # Extracting the review

            try:
                # Open the URL
                driver.get(base_reviews_url)
                time.sleep(5)  # Wait for the page to load

                # Get page source
                page_source = driver.page_source

                # Parse the page source with BeautifulSoup
                soup = BeautifulSoup(page_source, "html.parser")

                commentboxes = soup.find_all("div", class_="cPHDOP col-12-12")

                # create csv to store values
                filename = searchString + ".csv"
                fw = open(filename, "w")
                headers = "Name, Date, Place, Comment, Heading, Rating \n"
                fw.write(headers)

                # Initialize a list to store extracted reviews
                reviews = []

                # Extracting review details
                for review in commentboxes:
                    try:
                        name = review.find("p", class_="_2NsDsF AwS1CA").get_text(strip=True)
                        date = review.find('div', class_="row gHqwa8").div.find_all('p', class_="_2NsDsF")[-1].get_text(
                            strip=True)
                        place = review.find('p', class_="MztJPv").find_all('span')[-1].get_text(strip=True).strip(', ')
                        comment = review.find("div", class_="ZmyHeo").div.div.get_text(strip=True, separator='.')
                        heading = review.find("p", class_="z9E0IG").get_text(strip=True)
                        rating = review.find("div", class_="XQDdHH Ga3i8K").get_text(strip=True)

                        my_dict = {
                            "Name": name,
                            "Date": date,
                            "Place": place,
                            "Comment": comment,
                            "Heading": heading,
                            "Rating": rating
                        }
                        reviews.append(my_dict)

                    except AttributeError:
                        # Skip if any detail is missing
                        continue

                return render_template('results.html', reviews=reviews[0:(len(reviews) - 1)])


            except Exception as e:
                print("Error accessing reviews:", str(e))


        except Exception as e:
            print("Error accessing reviews:", str(e))

    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8001, debug=True)
    app.run(debug=True)