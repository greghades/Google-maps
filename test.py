"""
OBJETIVO:
    - Hacer una extracción compleja en Selenium
    - Hacer una extracción de datos de una red social
CREADO POR: LEONARDO KUFFO
ULTIMA VEZ EDITADO: 03 OCTUBRE 2024
"""

from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import (
    ChromeDriverManager,
)  # pip install webdriver-manager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.XPATHs.config import *  # Cambia la ruta según tu estructura de carpetas
opts = Options()
opts.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
)
# Agregar a todos sus scripts de selenium para que no aparezca la ventana de seleccionar navegador por defecto: (desde agosto 2024)
opts.add_argument("--disable-search-engine-choice-screen")


driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=opts
)
wait = WebDriverWait(driver, timeout=5)


driver.get(
    "https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwitoOn69qOMAxUIEzQIHWkJKIMQFnoECAoQAQ&url=https%3A%2F%2Fmaps.google.com%2Fmaps&usg=AOvVaw1nQWRIQz9dBndHi5i2aVaW&opi=89978449"
)  # Cambia la URL a la que necesites

info = []


search_input = driver.find_element(By.ID, "searchboxinput")
search_input.send_keys(f"carpinteria barquisimeto")

search_button = driver.find_element(By.ID, "searchbox-searchbutton")
search_button.click()
sleep(2)

wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='feed']")))

ads = driver.find_elements(By.XPATH, "//a[@class='hfpxzc']")


def extract_services(ad):
    try:
        print(f"Extrayendo {ad.get_attribute('aria-label')}")
        driver.execute_script("arguments[0].click();", ad)
        sleep(5)

        info_modal = driver.find_element(By.XPATH, INFO_MODAL_XPATH)
        scroll_to_element(info_modal)

        try:
            title = driver.find_element(By.XPATH, TITLE_XPATH).text
        except Exception as e:
            print(f"Error al obtener el título: {e}")
            title = "N/A"

        try:
            adress = driver.find_element(By.XPATH, ADRESS_XPATH).text
        except Exception as e:
            print(f"Error al obtener la dirección: {e}")
            adress = "N/A"

        try:
            phone = driver.find_element(By.XPATH, PHONE_XPATH).text
        except Exception as e:
            print(f"Error al obtener el teléfono: {e}")
            phone = "N/A"

        return {
            "title": title,
            "adress": adress,
            "phone": phone,
            "social_media_links": extract_social_links(),
        }

    except Exception as e:
        print(f"Hubo un error con {ad.get_attribute('aria-label')} {e}")
        return None

def scroll_to_element(element):

    last_height = 0
    while True:
        # Desplazar al final
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight", element
            )
        sleep(2)  # Dar tiempo para que cargue el contenido dinámico

        # Verificar la nueva altura del panel
        new_height = driver.execute_script(
            "return arguments[0].scrollHeight", element
        )
        if new_height == last_height:  # Si no cambia, hemos llegado al final
            break
        last_height = new_height


def extract_social_links():

    social_media_urls = []

    try:
        iframe = driver.find_element(By.TAG_NAME, "iframe")
        driver.switch_to.frame(iframe)
    except Exception as e:
        print("No se encontró el iframe:", e)
        return []

    try:
        wait.until(
            EC.presence_of_all_elements_located((By.XPATH, SOCIAL_MEDIA_LINK_XPATH))
        )
        links = driver.find_elements(By.XPATH, SOCIAL_MEDIA_LINK_XPATH)

        for link in links:
            try:
                link.click()
                sleep(2)

                driver.switch_to.window(driver.window_handles[1])
                social_media_urls.append(driver.current_url)

                driver.close()  # Cierra la nueva ventana
                driver.switch_to.window(
                    driver.window_handles[0]
                )  # Regresa a la ventana principal
                driver.switch_to.frame(iframe)  # Cambia de nuevo al iframe
                sleep(1)
            except Exception as e:
                print(f"Error al procesar el enlace {link}: {e}")
                break

           
        print(f"Se encontraron {len(links)} enlaces de redes sociales")
        return social_media_urls

    except Exception as e:
        driver.switch_to.default_content()
        print(
            "No se encontraron enlaces de redes sociales después del desplazamiento:",
            e,
        )
        return []

    finally:
        driver.switch_to.default_content()


for ad in ads[:5]:
    data = extract_services(ad)
    if data:
        info.append(data)

import json
print(json.dumps(info, indent=4, ensure_ascii=False))
