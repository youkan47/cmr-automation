import asyncio
from playwright.async_api import async_playwright

async def scrape_cmr_competition(competition_id, tab="standings"):
    url = f"https://zone212.cmrankings.com/competition/{competition_id}?tab={tab}"
    print(f"🚀 Connexion à la plateforme CMR pour la compétition {competition_id} ({tab})...")
    
    async with async_playwright() as p:
        # Lancement d'un navigateur headless dans le cloud
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Accès à la page et attente du chargement complet du JavaScript
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(3)
        
        extracted_data = []
        
        if tab == "standings":
            rows = await page.locator("table tbody tr, tr").all()
            for idx, row in enumerate(rows):
                text_content = await row.inner_text()
                lines = [line.strip() for line in text_content.split("\n") if line.strip()]
                
                img_element = row.locator("img")
                logo_url = ""
                if await img_element.count() > 0:
                    logo_url = await img_element.first.get_attribute("src") or ""
                
                if lines:
                    extracted_data.append({
                        "rang": idx + 1,
                        "details": lines,
                        "logo": logo_url
                    })
        else:
            match_cards = await page.locator(".match-card, tr, [class*='fixture'], [class*='match']").all()
            for idx, card in enumerate(match_cards):
                text_content = await card.inner_text()
                lines = [line.strip() for line in text_content.split("\n") if line.strip()]
                
                imgs = await card.locator("img").all()
                logos = [await img.get_attribute("src") for img in imgs]
                
                if len(lines) >= 2:
                    extracted_data.append({
                        "match": idx + 1,
                        "details": lines,
                        "logos": logos
                    })
                    
        await browser.close()
        print(f"✅ Extraction réussie ! {len(extracted_data)} éléments trouvés.")
        print(extracted_data)
        return extracted_data

if __name__ == "__main__":
    # Test avec la compétition 21 (onglets fixtures / matchs)
    asyncio.run(scrape_cmr_competition(21, tab="fixtures"))
