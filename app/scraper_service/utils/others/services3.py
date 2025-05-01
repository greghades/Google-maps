import asyncio
import gc
import json
import time
from typing import Dict, List, Optional

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from utils.XPATHs.config import *


class ServiceScraper:
    def __init__(self, url: str,location:str, service:str,ads_limit:int,social_media) -> None:
        self.url = url
        self.browser: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._setup_driver()

    async def _setup_driver(self) -> None:
        """Configura el navegador Playwright en modo no headless."""

        async with async_playwright() as playwright:
            self.playwright = playwright
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.page = await self.browser.new_page()
            await self.page.set_default_timeout(10000)
            
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()

    async def _extract_services(self, ad) -> Optional[Dict[str, str]]:
        """Extrae información de un anuncio (título, dirección, teléfono)."""
        try:
            aria_label = await ad.get_attribute("aria-label")
            print(f"Extrayendo {aria_label}")
            await ad.click()
            print("Hicimos clic en el anuncio, esperando el modal...")
            await self.page.wait_for_selector(INFO_MODAL_XPATH, timeout=5000)
            print("Modal cargado.")

            await asyncio.sleep(3)

            # Extraer título
            title = "N/A"
            title_element = await self.page.query_selector(TITLE_XPATH)
            if title_element:
                title = await title_element.inner_text()
                print(f"Título: {title}")

            # Extraer dirección
            adress = "N/A"
            adress_element = await self.page.query_selector(ADRESS_XPATH)
            if adress_element:
                adress = await adress_element.inner_text()
                print(f"Dirección: {adress}")

            # Extraer teléfono
            phone = "N/A"
            phone_element = await self.page.query_selector(PHONE_XPATH)
            if phone_element:
                phone = await phone_element.inner_text()
                print(f"Teléfono: {phone}")

            return {"title": title, "adress": adress, "phone": phone}

        except Exception as e:
            print(f"Error al extraer {aria_label}: {e}")
            return None

    async def get_services(
        self, service: str, location: str, ads_limit: int, social_links: List[str]
    ) -> str:
        """Realiza la búsqueda en Google Maps y extrae información."""
        await self._setup_driver()
        info = []

        try:
            await self.page.goto(self.url)

            # Realizar búsqueda
            await self.page.fill("#searchboxinput", f"{service} {location}")
            await self.page.click("#searchbox-searchbutton")

            # Esperar y desplazar contenedor de anuncios
            await self.page.wait_for_selector(ADS_CONTAINER_XPATH, timeout=10000)
            await self._scroll_to_element(ADS_CONTAINER_XPATH)

            # Obtener anuncios
            ads = await self.page.query_selector_all(ADS_XPATH)
            ads = ads[:ads_limit]

            for ad in ads:
                data = await self._extract_services(ad)
                if data:
                    info.append(data)

            return json.dumps(info, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"Error durante el scraping: {e}")
            return json.dumps(info, ensure_ascii=False, indent=4)

        finally:
            await self._cleanup()

    async def _scroll_to_element(self, selector: str) -> None:
        """Desplaza un contenedor hasta cargar todo el contenido dinámico."""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            element = await self.page.query_selector(selector)
            last_height = 0
            while True:
                await self.page.evaluate(
                    "el => el.scrollTop = el.scrollHeight", element
                )
                await asyncio.sleep(2)  # Espera carga de contenido dinámico
                new_height = await self.page.evaluate("el => el.scrollHeight", element)
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            print(f"Error al desplazar al elemento: {e}")


async def main():
    # Establecer la política del bucle de eventos para Windows

    services = ServiceScraper("https://www.google.com/maps")

    await services.get_services(
        "carpinteria", "barquisimeto", 3, ["instagram"]
    )
    with open("utils/services.json", "w", encoding="utf-8") as file:
        file.write(services)

    




if __name__ == "__main__":
    # Ejecutar el programa directamente con asyncio.run
    asyncio.run(main())
