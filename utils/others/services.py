import json
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from utils.XPATHs.config import *


class ServiceScraper:
    def __init__(self, url) -> None:
        self.url = url
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, timeout=5)
        self.action = ActionChains(self.driver)

    def _setup_driver(self):

        options = Options()
        # options.add_argument(
        #     f"user-agent={self._get_user_agents()}"
        # )
        options.add_argument("--headless")  # Ejecutar en modo headless (sin GUI)
        options.add_argument("--disable-search-engine-choice-screen")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--enable-unsafe-swiftshader")
        service = Service(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()

        return driver

    def _get_user_agents(self):
        with open("utils/user-agents.txt", "r", encoding="utf-8") as archivo:
            user_agent = [linea.strip() for linea in archivo]

            return user_agent[random.randint(0, len(user_agent))]

    def _scroll_to_element(self, element):

        last_height = 0
        while True:
            # Desplazar al final
            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", element
            )
            time.sleep(2)  # Dar tiempo para que cargue el contenido dinámico

            # Verificar la nueva altura del panel
            new_height = self.driver.execute_script(
                "return arguments[0].scrollHeight", element
            )
            if new_height == last_height:  # Si no cambia, hemos llegado al final
                break
            last_height = new_height

    def _extract_services(self, ad):
        try:
            print(f"Extrayendo {ad.get_attribute('aria-label')}")
            self.action.move_to_element(ad).perform()
            self.driver.execute_script("arguments[0].click();", ad)
            time.sleep(5)

            info_modal = self.driver.find_element(By.XPATH, INFO_MODAL_XPATH)
            self._scroll_to_element(info_modal)

            try:
                title = self.driver.find_element(By.XPATH, TITLE_XPATH).text
            except Exception as e:
                print(f"Error al obtener el título")
                title = "N/A"

            try:
                adress = self.driver.find_element(By.XPATH, ADRESS_XPATH).text
            except Exception as e:
                print(f"Error al obtener la dirección")
                adress = "N/A"

            try:
                phone = self.driver.find_element(By.XPATH, PHONE_XPATH).text
            except Exception as e:
                print(f"Error al obtener el teléfono")
                phone = "N/A"

            return {"title": title, "adress": adress, "phone": phone}

        except Exception as e:
            print(f"Hubo un error con {ad.get_attribute('aria-label')} {e}")
            return None

    def get_services(
        self, service: str, location: str, ads_limit: int, social_links: list[str]
    ) -> str:

        self.driver.get(self.url)
        info = []

        try:

            search_input = self.driver.find_element(By.ID, "searchboxinput")
            search_input.send_keys(f"{service} {location}")

            search_button = self.driver.find_element(By.ID, "searchbox-searchbutton")
            search_button.click()
            time.sleep(2)

            self.wait.until(
                EC.presence_of_element_located((By.XPATH, ADS_CONTAINER_XPATH))
            )
            ads_container = self.driver.find_element(By.XPATH, ADS_CONTAINER_XPATH)

            self._scroll_to_element(ads_container)

            self.wait.until(EC.presence_of_element_located((By.XPATH, ADS_XPATH)))

            ads = self.driver.find_elements(By.XPATH, ADS_XPATH)[:ads_limit]

            for ad in ads:
                data: dict[str, str] | None = self._extract_services(ad)

                if data:
                    info.append(data)
                    if len(social_links) > 0:
                        data["social_links"] = json.dumps(
                            self.extract_social_links(social_links), ensure_ascii=False
                        )
            return json.dumps(info, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"Error during scraping: {e}")
            return json.dumps(info, ensure_ascii=False, indent=4)

        finally:
            self.driver.quit()

    def _is_valid_link(self, link, social_links) -> bool:

        known_social_media = [
            "facebook",
            "twitter",
            "instagram",
            "linkedin",
            "youtube",
            "tiktok",
        ]
        try:
            # Extrae el dominio del enlace (ejemplo: "facebook" de "www.facebook.com")
            alt_text = (
                link.find_element(By.XPATH, ".//img")
                .get_attribute("alt")
                .split(".")[1]
                .lower()
            )

            # Si el dominio está en social_links, es válido
            if alt_text in social_links:
                return True
            # Si "others" está en social_links, verifica que no sea una red social conocida
            if "others" in social_links and alt_text not in known_social_media:
                return True
            return False
        except Exception as e:
            print(f"Error al procesar el enlace {link}: {e}")
            return False

    def extract_social_links(self, social_links: list[str]) -> list[str]:

        social_media_urls = []

        try:
            iframe = self.driver.find_element(By.TAG_NAME, "iframe")
            self.driver.switch_to.frame(iframe)
        except Exception as e:
            print("No se encontró el iframe:", e)
            return []

        try:

            self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, SOCIAL_MEDIA_LINK_XPATH))
            )
            links = self.driver.find_elements(By.XPATH, SOCIAL_MEDIA_LINK_XPATH)

            for link in links:
                if self._is_valid_link(link, social_links):
                    try:
                        link.click()
                        time.sleep(2)

                        self.driver.switch_to.window(self.driver.window_handles[1])
                        social_media_urls.append(self.driver.current_url)

                        self.driver.close()  # Cierra la nueva ventana
                        self.driver.switch_to.window(
                            self.driver.window_handles[0]
                        )  # Regresa a la ventana principal
                        self.driver.switch_to.frame(iframe)  # Cambia de nuevo al iframe
                        time.sleep(1)
                    except Exception as e:
                        print(f"Error al procesar el enlace {link}: {e}")
                        break

            print(f"Se encontraron {len(links)} enlaces de redes sociales")
            return social_media_urls

        except Exception as e:
            self.driver.switch_to.default_content()
            print(
                "No se encontraron enlaces de redes sociales después del desplazamiento:",
                e,
            )
            return []

        finally:
            self.driver.switch_to.default_content()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()


with ServiceScraper(URL_MAPS) as scraper:
    with open("utils/services.json", "w", encoding="utf-8") as file:
        services = scraper.get_services("carpinteria", "barquisimeto", 6, ["instagram"])
        file.write(services)
