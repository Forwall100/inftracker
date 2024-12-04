from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def parse_5ka(driver, url):
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[1]/div[2]/div[1]/p[1]"))
        )
    except Exception as e:
        print("Элемент не найден или страница не загрузилась за отведенное время", e)
        driver.quit()
        exit()

    try:
        price_without_discount = driver.find_element(
            By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[1]/div[2]/div[1]/p[1]"
        ).text

        price_with_discount = driver.find_element(
            By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[2]/p[1]"
        ).text
    except:
        price_without_discount = driver.find_element(
            By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[1]/div[2]/div/p[1]"
        ).text
        price_with_discount = None

    driver.quit()
    return {
        'price_with_discount': price_with_discount,
        'price_without_discount': price_without_discount
    }
