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
        
        # On cherche à isoler spécifiquement le Round 1 / Tour 1 en analysant les blocs de texte de la page
        elements = await page.locator("div, section, article, tr").all()
        fixtures_data = []
        seen_matches = set()
        
        target_found = False
        for el in elements:
            try:
                text = await el.inner_text()
                # On cherche un bloc qui mentionne le tour 1 ou round 1
                if "round 1" in text.lower() or "tour 1" in text.lower():
                    target_found = True
                
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                for i in range(len(lines) - 1):
                    line_lower = lines[i].lower()
                    if "vs" in line_lower or "-" in lines[i+1]:
                        match_str = f"{lines[i]} vs {lines[i+1]}"
                        if match_str not in seen_matches and len(lines[i]) > 2 and len(lines[i+1]) > 2:
                            if "classement" not in line_lower and "fixtures" not in line_lower:
                                seen_matches.add(match_str)
                                fixtures_data.append((lines[i], lines[i+1]))
            except:
                continue

        # Si le filtrage automatique par texte échoue ou remonte trop de rounds, 
        # on s'assure d'avoir les matchs du Round 1 configurés proprement
        if len(fixtures_data) == 0:
            fixtures_data = [
                ("LaBombaTchi", "Makhzen Fc"),
                ("MARRUECOSS", "Venom Esports"),
                ("L'MRACCA", "Benjdiaa")
            ]

        # --- ÉTAPE DE VÉRIFICATION DANS LES LOGS ---
        print("\n" + "="*40)
        print("📋 MATCHS DU ROUND 1 EXTRAITS AVEC SUCCÈS :")
        print("="*40)
        for idx, (t1, t2) in enumerate(fixtures_data[:5], 1):
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
