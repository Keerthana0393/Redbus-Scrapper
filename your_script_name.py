import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import streamlit as st
import pandas as pd

# Initialize WebDriver
driver = webdriver.Chrome()
driver.get("https://www.redbus.in/")
driver.maximize_window()

# Step 1: Search for bus details
try:
    # Enter source and destination
    source = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "src"))
    )
    source.send_keys("Chennai")
    time.sleep(2)
    source.send_keys(Keys.ENTER)

    destination = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "dest"))
    )
    destination.send_keys("Bangalore")
    time.sleep(2)
    destination.send_keys(Keys.ENTER)

        # Select travel date
    date_picker = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "onwardCal"))
    )
    date_picker.click()

    # Select date from the active calendar
    date_to_select = "25"  # Example date, change as needed

    calendar_day_xpath = f"//div[contains(@class, 'DayPicker-Day') and not(contains(@class, 'outside')) and text()='{date_to_select}']"

    try:
        calendar_day = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, calendar_day_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", calendar_day)  # Ensures visibility
        calendar_day.click()
    except Exception as e:
       print(f"Date selection error: {e}")


    # Click on Search Buses
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "search_button"))
    )
    search_button.click()

    # Step 2: Scrape Bus Details
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "bus-item")))

    buses = driver.find_elements(By.CLASS_NAME, "bus-item")
    print(f"Found {len(buses)} buses.")

    # Database setup
    conn = sqlite3.connect("bus_data.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS buses (
                  bus_name TEXT,
                  departure_time TEXT,
                  arrival_time TEXT,
                  price TEXT)''')

    data = []

    for bus in buses:
        try:
            bus_name = bus.find_element(By.CLASS_NAME, "travels.lh-24.f-bold.d-color").text
            departure_time = bus.find_element(By.CLASS_NAME, "dp-time").text
            arrival_time = bus.find_element(By.CLASS_NAME, "bp-time").text
            price = bus.find_element(By.CLASS_NAME, "fare.d-block").text

            data.append((bus_name, departure_time, arrival_time, price))
            c.execute("INSERT INTO buses VALUES (?, ?, ?, ?)", (bus_name, departure_time, arrival_time, price))
        except:
            print("Skipping one entry due to missing details.")

    conn.commit()
    conn.close()

except Exception as e:
    print(f"Error during bus search or scraping: {e}")

# Close the driver
driver.quit()

# Step 3: Streamlit App
st.title("Redbus Data Filtering App")
df = pd.read_sql("SELECT * FROM buses", sqlite3.connect("bus_data.db"))

filter_price = st.slider("Filter by Maximum Price", 0, 5000, 2000)
df_filtered = df[df['price'].apply(
    lambda x: int(''.join(filter(str.isdigit, x))) if x.strip() else 0
) <= filter_price]


st.dataframe(df_filtered)
