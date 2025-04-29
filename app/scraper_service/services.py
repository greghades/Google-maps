import asyncio
import json
import random
from typing import Dict, List, Optional
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from utils.XPATHs.config import (
    URL_MAPS,
    ADS_CONTAINER_XPATH,
    ADS_XPATH,
    TITLE_XPATH,
    PHONE_XPATH,
    ADRESS_XPATH,
    INFO_MODAL_XPATH,
    SOCIAL_MEDIA_LINK_XPATH
)


global url
url = URL_MAPS

async def search_page(page: Page, service: str, location: str) -> None:
    """Navega a la URL y realiza la búsqueda con el servicio y ubicación proporcionados."""
    try:
        await page.goto(url, wait_until="domcontentloaded")
        await page.fill("#searchboxinput", f"{service} {location}")
        await page.click("#searchbox-searchbutton")
        await page.wait_for_selector(ADS_CONTAINER_XPATH, timeout=10000)
    except Exception as e:
        print(f"Error al buscar en la página: {e}")
        raise


async def extract_ad_data(page: Page, context: BrowserContext, social_links:List[str]) -> Dict:
    """Extrae los datos de un anuncio (título, teléfono, dirección)."""

    await scroll_to_element(page,INFO_MODAL_XPATH)

    try:
        title = await page.query_selector(TITLE_XPATH)
        title_text = await title.inner_text() if title else "N/A"
        print(f"Extrayendo: {title_text}")

        phone = await page.query_selector(PHONE_XPATH)
        phone_number = await phone.inner_text() if phone else "N/A"

        address = await page.query_selector(ADRESS_XPATH)
        address_text = await address.inner_text() if address else "N/A"
       

        return {
            "title": title_text,
            "phone": phone_number,
            "address": address_text,
            "social_media": await extract_social_media_links(
                page, context, social_links
            ),
        }
    except Exception as e:
        print(f"Error extrayendo datos del anuncio: {e}")
        return {"title": "N/A", "phone": "N/A", "address": "N/A"}


async def extract_social_media_links(page: Page, context: BrowserContext,social_links:List[str]) -> List[str]:

    try:
        await page.wait_for_selector("//iframe", timeout=10000)
        iframe = await page.query_selector("//iframe")
        
        frame = await iframe.content_frame()

        if frame:
            social_media_links = await frame.query_selector_all(SOCIAL_MEDIA_LINK_XPATH)
            links = []

            for link in social_media_links:

                if await is_valid_link(link,social_links):
                    await asyncio.sleep(
                        random.uniform(1, 2)
                    )  # Espera para cargar el enlace

                    try:
                        async with context.expect_page() as new_page_info:
                            # Espera a que se abra el enlace
                            await link.click()
                        new_page = await new_page_info.value

                        await new_page.wait_for_load_state("load", timeout=15000)
                        current_url = new_page.url
                        links.append(current_url)

                        await new_page.close()
                    except Exception as e:
                        print(f"Error al abrir el enlace: {e}")
               
            return links
        else:
            print("No se pudo acceder al iframe de redes sociales.")
            return []

    except Exception as e:  
        print(f"Error al encontrar frame: {e}")
        return []


async def is_valid_link(link, social_links) -> bool:

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
        query_selector = await link.query_selector("//img")
        if not query_selector:
            return False
        alt_text = await query_selector.get_attribute("alt")
        alt_text = alt_text.split(".")[1].lower() if alt_text else "N/A"


        # Si el dominio está en social_links, es válido
        if alt_text in social_links:
            print(f"Dominio extraído: {alt_text}")
            return True
        # Si "others" está en social_links, verifica que no sea una red social conocida
        if "others" in social_links and alt_text not in known_social_media:
            print(f"Dominio extraído: {alt_text}")
            return True

        return False
    except Exception as e:
        print(f"Error al procesar el enlace {link}: {e}")
        return False

async def scrape_ads(page: Page, context: BrowserContext, social_links:List[str], ads_limit: int = 5) -> List[Dict]:
    """Extrae datos de los anuncios en la página."""
    results = []
    try:
        ads = await page.query_selector_all(ADS_XPATH)
        print(f"Cantidad de anuncios encontrados: {len(ads)}")
        for ad in ads[:ads_limit]:
            await ad.click()
            await asyncio.sleep(random.uniform(1, 2))
            ad_data = await extract_ad_data(page, context, social_links)
            results.append(ad_data)
        if results:
            await save_results(results, "scraped_data.json")
            return results
        else:
            print("No se obtuvieron resultados.")
            return []
    except Exception as e:
        print(f"Error al procesar anuncios: {e}")


async def save_results(data: List[Dict], output_file: str) -> None:
    """Guarda los datos extraídos en un archivo JSON."""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Datos guardados en {output_file}")
    except Exception as e:
        print(f"Error al guardar los datos: {e}")


async def scrape_page(service: str, location: str,ads_limit: str, social_links: List[str]) -> Optional[List[Dict]]:
    """Orquesta el proceso de scraping para una página dada."""
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await search_page(page, service, location)
            await scroll_to_element(page, ADS_CONTAINER_XPATH, ads_limit)
            results = await scrape_ads(page, context,social_links, ads_limit)

            await page.close()
            await context.close()
            await browser.close()
            return results
        except Exception as e:
            print(f"Error en el proceso de scraping: {e}")
            return None


async def scroll_to_element(page: Page, selector: str,ads_limit:int=0) -> None:
    """Desplaza un contenedor hasta cargar todo el contenido dinámico."""
    try:
        await page.wait_for_selector(selector, timeout=10000)
        element = await page.query_selector(selector)

        last_height = 0

        while True:
            await page.evaluate("el => el.scrollTop = el.scrollHeight", element)
            await asyncio.sleep(random.uniform(1,2))  # Espera carga de contenido dinámico
            new_height = await page.evaluate("el => el.scrollHeight", element)

            ads_quantity = await page.query_selector_all(ADS_XPATH)

            if len(ads_quantity) >= ads_limit:
                break
            if new_height == last_height:
                break
            last_height = new_height
       

    except Exception as e:
        print(f"Error al desplazar al elemento: {e}")

import time

if __name__ == "__main__":
    tiempo_inicial = time.time()
    asyncio.run(scrape_page("hoteles", "valencia", 20, ["instagram", "others"]))
    tiempo_final = time.time()
    tiempo_total = tiempo_final - tiempo_inicial

    horas, resto = divmod(tiempo_total, 3600)
    minutos, segundos = divmod(resto, 60)

    print(f"Tiempo total de ejecución: {int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}")