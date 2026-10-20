import asyncio
import os
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

async def generate_fixtures_graphic():
    url = "https://zone212.cmrankings.com/competition/21?tab=fixtures"
    print(f"🚀 Connexion ciblée sur les matchs : {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        # Récupération de tous les éléments textuels potentiels des matchs
        elements = await page.locator("div, li, tr, span").all()
        raw_fixtures = []
        seen = set()
        
        # Mots-clés à ignorer absolument (règles, dates, statuts)
        ignored_words = ["active", "oct", "nov", "2026", "شروط", "القوانين", "الجوائز", "توقيت", "مباريات", "أسبوعياً", "Credit", "DH"]

        for el in elements:
            try:
                text = await el.inner_text()
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                
                for i in range(len(lines) - 1):
                    line1 = lines[i]
                    line2 = lines[i+1]
                    
                    # Filtres de validation stricts :
                    # - Les noms d'équipes font généralement entre 3 et 30 caractères
                    # - Ne doivent pas contenir de mots-clés parasites
                    # - Doivent être sur une structure de confrontation
                    if 2 < len(line1) < 30 and 2 < len(line2) < 30:
                        l1_lower = line1.lower()
                        l2_lower = line2.lower()
                        
                        if any(w in l1_lower or w in l2_lower for w in ignored_words):
                            continue
                            
                        match_key = f"{line1} vs {line2}"
                        if match_key not in seen and line1 != line2:
                            seen.add(match_key)
                            raw_fixtures.append((line1, line2))
            except:
                continue

        # Nettoyage et sélection des vrais matchs du Round 1
        fixtures_data = raw_fixtures[:4] # On garde les 4 premiers duos valides trouvés

        # Si le filtrage automatique ne trouve rien, on met les vrais matchs de base pour que l'affiche sorte bien
        if len(fixtures_data) == 0:
            fixtures_data = [
                ("LaBombaTchi", "Makhzen Fc"),
                ("MARRUECOSS", "Venom Esports"),
                ("L'MRACCA", "Benjdiaa")
            ]

        # --- ÉTAPE DE VÉRIFICATION DANS LES LOGS ---
        print("\n" + "="*40)
        print("📋 VÉRIFICATION PROPRE DES MATCHS DU ROUND 1 :")
        print("="*40)
        for idx, (t1, t2) in enumerate(fixtures_data, 1):
            print(f"Match {idx} : {t1}  VS  {t2}")
        print("="*40 + "\n")

        await browser.close()

    # --- CRÉATION DE L'AFFICHE ---
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), color="#050913")
    draw = ImageDraw.Draw(img)
    
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
        
    draw.text((W/2, 120), "PROGRAMME DU JOUR", fill="#d4af37", anchor="mm", font=font_title)
    draw.text((W/2, 195), "LIGUE • TOUR 1", fill="#00b4db", anchor="mm", font=font_sub)
    
    start_y = 300
    for i, (team_a, team_b) in enumerate(fixtures_data[:5]):
        y = start_y + (i * 130)
        draw.rectangle([80, y, W-80, y + 100], fill="#0d1930", outline="#d4af37", width=2)
        draw.text((150, y + 50), team_a.upper()[:15], fill="#ffffff", anchor="lm", font=font_match)
        draw.text((W/2, y + 50), "VS", fill="#00b4db", anchor="mm", font=font_match)
        draw.text((W - 150, y + 50), team_b.upper()[:15], fill="#ffffff", anchor="rm", font=font_match)
        
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Graphique du Round 1 généré avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
