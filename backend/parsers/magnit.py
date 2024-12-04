from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


def clean_string(input_string):
    if input_string is None:
        return None
    return re.sub(r'[^0-9.,]', '', input_string)


def parse_magnit(driver, url):
    driver.get(url)

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div/div/div/main/div/div[1]/section/div/div/div/div[2]/section[1]/section/div[1]/span[1]"))
        )
    except Exception as e:
        print("Элемент не найден или страница не загрузилась за отведенное время", e)
        driver.quit()
        exit()

    try:
        print('Парсим со скидкой')
        price_without_discount = driver.find_element(
            By.XPATH, "/html/body/div[1]/div/div/div/main/div/div[1]/section/div/div/div/div[2]/section[1]/section/div[1]/span[1]/span"
        ).text

        price_with_discount = driver.find_element(
            By.XPATH, "/html/body/div[1]/div/div/div/main/div/div[1]/section/div/div/div/div[2]/section[1]/section/div[1]/div[1]/span/span"
        ).text
    except:
        print('Парсим без скидки')
        price_without_discount = driver.find_element(
            By.XPATH, "/html/body/div[1]/div/div/div/main/div/div[1]/section/div/div/div/div[2]/section[1]/section/div[1]/span[1]/span"
        ).text
        price_with_discount = None
    print('Спарсили все')

    driver.quit()
    return {
        'price_with_discount': clean_string(price_with_discount),
        'price_without_discount': clean_string(price_without_discount)
    }
