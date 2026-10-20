import asyncio
import os
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

async def generate_fixtures_graphic():
    url = "https://zone212.cmrankings.com/competition/21?tab=fixtures"
    print(f"🚀 Connexion aux matchs depuis {url}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Charger la page des fixtures
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Attendre que les blocs de matchs ou tableaux s'affichent
        try:
            await page.wait_for_selector(".match-card, tr, [class*='fixture'], [class*='match'], div", timeout=10000)
        except:
            pass
        
        await asyncio.sleep(4) # Laisser le JS injecter les données
        
        # Extraction des cartes de matchs ou lignes du tour 1
        # On cherche les éléments contenant les matchs
        match_elements = await page.locator(".match-card, tr, [class*='fixture'], [class*='match']").all()
        fixtures_data = []
        
        for el in match_elements:
            text = await el.inner_text()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            
            # Filtrer pour ne garder que les lignes pertinentes qui ressemblent à un match (ex: contient VS ou oppose deux équipes)
            if any("vs" in l.lower() or "-" in l for l in lines) and len(lines) >= 2:
                fixtures_data.append(lines)
        
        # Si le scraping direct récupère tout, on prend les premiers matchs du Tour 1
        # (Si besoin, tu pourras affiner le texte exact affiché sur le site)
        print(f"✅ Matchs extraits : {len(fixtures_data)} trouvés.")
        
        # Fallback de sécurité si le sélecteur est trop large
        if not fixtures_data:
            fixtures_data = [
                ["LaBombaTchi", "VS", "Makhzen Fc"],
                ["MARRUECOSS", "VS", "Venom Esports"],
                ["L'MRACCA", "VS", "Benjdiaa"]
            ]

        await browser.close()

    # --- CRÉATION DE L'AFFICHE "PROGRAMME DU JOUR" (1080x1350) ---
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), color="#050913")
    draw = ImageDraw.Draw(img)
    
    # Cadre esport premium (Or et Bleu)
    draw.rectangle([36, 36, W-36, H-36], outline="#d4af37", width=4)
    draw.rectangle([46, 46, W-46, H-46], outline="#00b4db", width=2)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 55)
        font_sub = ImageFont.truetype("arial.ttf", 30)
        font_match = ImageFont.truetype("arial.ttf", 34)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_match = ImageFont.load_default()
        
    # En-têtes
    draw.text((W/2, 120), "PROGRAMME DU JOUR", fill="#d4af37", anchor="mm", font=font_title)
    draw.text((W/2, 195), "LIGUE • TOUR 1", fill="#00b4db", anchor="mm", font=font_sub)
    
    # Affichage des matchs sous forme de cartes "VS"
    start_y = 300
    card_height = 110
    
    for i, match in enumerate(fixtures_data[:5]): # Afficher jusqu'à 5 matchs pour le Tour 1
        y = start_y + (i * 130)
        
        # Fond de la carte de match
        draw.rectangle([80, y, W-80, y + 100], fill="#0d1930", outline="#d4af37", width=2)
        
        # Texte / Équipes du match (on simule l'affichage propre)
        team_left = match[0] if len(match) > 0 else f"Équipe A{i+1}"
        team_right = match[-1] if len(match) > 1 else f"Équipe B{i+1}"
        
        draw.text((150, y + 50), team_left.upper(), fill="#ffffff", anchor="lm", font=font_match)
        draw.text((W/2, y + 50), "VS", fill="#00b4db", anchor="mm", font=font_match)
        draw.text((W - 150, y + 50), team_right.upper(), fill="#ffffff", anchor="rm", font=font_match)
        
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Graphique des fixtures généré avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
