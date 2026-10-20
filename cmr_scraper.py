import asyncio
import os
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

async def generate_fixtures_graphic():
    round_number = 1 
    url = f"https://zone212.cmrankings.com/competition/21?tab=fixtures"
    print(f"🚀 [Playwright] Connexion ciblée sur le Round {round_number} : {url}")
    
    extracted_fixtures = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigation et attente du chargement réseau complet
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        # Utilisation des locators Playwright pour cibler les conteneurs de matchs
        # On recherche les éléments contenant la mention du round
        target_text = f"League · Round {round_number}"
        
        # Récupération de tous les blocs de texte / cartes via Playwright
        cards = await page.locator("div").all()
        
        for card in cards:
            try:
                text = await card.inner_text()
                if text and target_text in text and ("SCHEDULED" in text or "0/2 played" in text):
                    # Extraire les lignes propres du bloc
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    cleaned = []
                    skip_words = ['2 legs', 'scheduled', '0/2 played', 'tue', 'oct', 'nov', '2026', 'crest', 'today', 'matches', 'played', 'league', 'round', str(round_number)]
                    
                    for l in lines:
                        lower = l.lower()
                        if not any(w in lower for w in skip_words) and 2 < len(l) < 30:
                            cleaned.append(l)
                    
                    if len(cleaned) >= 2:
                        t1 = cleaned[0]
                        t2 = cleaned[1]
                        
                        # Extraction robuste des URLs des logos via le locator Playwright
                        img_locators = card.locator("img")
                        img_count = await img_locators.count()
                        
                        logo1 = await img_locators.nth(0).get_attribute("src") if img_count > 0 else ""
                        logo2 = await img_locators.nth(1).get_attribute("src") if img_count > 1 else ""
                        
                        # Si les URLs sont relatives, on les complète avec le domaine de base
                        base_url = "https://zone212.cmrankings.com"
                        if logo1 and not logo1.startswith("http"):
                            logo1 = base_url + logo1
                        if logo2 and not logo2.startswith("http"):
                            logo2 = base_url + logo2
                            
                        match_tuple = (t1, t2, logo1, logo2)
                        if match_tuple not in extracted_fixtures and t1 != t2:
                            extracted_fixtures.append(match_tuple)
            except Exception as e:
                continue

        print(f"🔍 Nombre de duos extraits via Playwright : {len(extracted_fixtures)}")
        await browser.close()

    # Sécurité si l'extraction échoue
    if not extracted_fixtures or len(extracted_fixtures) == 0:
        print(f"⚠️ Utilisation des données de secours pour le Round {round_number}.")
        extracted_fixtures = [
            ("Viltrumites ES", "BLUE LOCK1", "", ""),
            ("VNM Esports", "AUREUS ES", "", ""),
            ("INFIRNO FC", "AJAX CASABLANCA", "", ""),
            ("TEMARA FC", "FC L HOKOMA", "", ""),
            ("LMRARCCA", "fc energy", "", "")
        ]

    fixtures_to_render = extracted_fixtures[:5]

    # --- VÉRIFICATION DÉTAILLÉE DANS LES LOGS ---
    print("\n" + "="*50)
    print(f"📋 VÉRIFICATION PLAYWRIGHT (ROUND {round_number}) :")
    print("="*50)
    for idx, match in enumerate(fixtures_to_render, 1):
        print(f"Match {idx} :")
        print(f"  - Équipe 1 : {match[0]} | Logo : {match[2] if match[2] else '❌ URL INTrouvable'}")
        print(f"  - Équipe 2 : {match[1]} | Logo : {match[3] if match[3] else '❌ URL INTrouvable'}")
    print("="*50 + "\n")

    # --- CRÉATION DE L'AFFICHE INSTAGRAM (1080x1350) ---
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), color="#050913")
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([36, 36, W-36, H-36], outline="#d4af37", width=4)
    draw.rectangle([46, 46, W-46, H-46], outline="#00b4db", width=2)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 55)
        font_sub = ImageFont.truetype("arial.ttf", 30)
        font_match = ImageFont.truetype("arial.ttf", 26)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_match = ImageFont.load_default()
        
    draw.text((W/2, 110), "PROGRAMME DU JOUR", fill="#d4af37", anchor="mm", font=font_title)
    draw.text((W/2, 175), f"LIGUE • ROUND {round_number} ({len(fixtures_to_render)} MATCHS)", fill="#00b4db", anchor="mm", font=font_sub)
    
    start_y = 230
    row_height = 190
    
    for i, (team_a, team_b, logo1_url, logo2_url) in enumerate(fixtures_to_render):
        y = start_y + (i * row_height)
        
        draw.rectangle([80, y, W-80, y + 160], fill="#0d1930", outline="#d4af37", width=2)
        
        # Téléchargement et collage du Logo 1
        if logo1_url:
            try:
                response = requests.get(logo1_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
                img.paste(logo_img, (110, y + 40), logo_img)
            except Exception as e:
                print(f"Erreur image logo 1: {e}")
                
        # Téléchargement et collage du Logo 2
        if logo2_url:
            try:
                response = requests.get(logo2_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
                img.paste(logo_img, (W - 190, y + 40), logo_img)
            except Exception as e:
                print(f"Erreur image logo 2: {e}")

        draw.text((210, y + 80), team_a.upper()[:15], fill="#ffffff", anchor="lm", font=font_match)
        draw.text((W/2, y + 80), "VS", fill="#00b4db", anchor="mm", font=font_match)
        draw.text((W - 210, y + 80), team_b.upper()[:15], fill="#ffffff", anchor="rm", font=font_match)
        
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Affiche avec logos Playwright générée avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
