import asyncio
import os
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
import requests

async def generate_cmr_graphic():
    url = "https://zone212.cmrankings.com/competition/21?tab=standings"
    print(f"🚀 Connexion et extraction des données depuis {url}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(3)
        
        # Extraction des lignes du tableau de classement
        rows = await page.locator("table tbody tr, tr").all()
        extracted_data = []
        
        for idx, row in enumerate(rows):
            text_content = await row.inner_text()
            lines = [line.strip() for line in text_content.split("\n") if line.strip()]
            img_element = row.locator("img")
            logo_url = ""
            if await img_element.count() > 0:
                logo_url = await img_element.first.get_attribute("src") or ""
            
            if lines and idx < 10: # Top 10 clubs
                extracted_data.append({
                    "rang": str(idx + 1),
                    "name": lines[0] if len(lines) > 0 else f"Club {idx+1}",
                    "logo": logo_url
                })
        await browser.close()

    print(f"✅ Données extraites : {len(extracted_data)} clubs trouvés.")
    
    # --- CRÉATION DU GRAPHIQUE INSTAGRAM (1080x1350) ---
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), color="#050913")
    draw = ImageDraw.Draw(img)
    
    # Cadre et bordures esport (Or et Bleu)
    draw.rectangle([36, 36, W-36, H-36], outline="#d4af37", width=4)
    draw.rectangle([46, 46, W-46, H-46], outline="#00b4db", width=2)
    
    # Polices par défaut (évite les erreurs si les fichiers de police manquent)
    try:
        font_title = ImageFont.truetype("arial.ttf", 60)
        font_sub = ImageFont.truetype("arial.ttf", 32)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        
    # Titres de l'affiche
    draw.text((W/2, 120), "CLASSEMENT OFFICIEL", fill="#d4af37", anchor="mm", font=font_title)
    draw.text((W/2, 200), "CMR LEAGUE • SAISON 4", fill="#00b4db", anchor="mm", font=font_sub)
    
    # Dessin des lignes de classement
    start_y = 300
    row_height = 85
    
    for i, club in enumerate(extracted_data[:8]):
        y = start_y + (i * row_height)
        # Fond de chaque ligne
        draw.rectangle([70, y, W-70, y + 70], fill="#0d1930", outline="#00b4db" if i>2 else "#d4af37", width=2)
        # Rang
        draw.text((110, y + 35), str(club["rang"]), fill="#d4af37", anchor="mm", font=font_sub)
        # Nom du club
        draw.text((200, y + 35), club["name"].upper(), fill="#ffffff", anchor="lm", font=font_sub)
        
    # Sauvegarde du fichier image final
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Graphique Instagram généré avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_cmr_graphic())
