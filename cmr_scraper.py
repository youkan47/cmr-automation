import asyncio
import os
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

async def generate_fixtures_graphic():
    url = "https://zone212.cmrankings.com/competition/21?tab=fixtures"
    print(f"🚀 [De zéro] Connexion à la page des matchs : {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Charger la page et attendre le rendu complet
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        # Sur base de ta capture, chaque match est dans un conteneur/carte.
        # On va chercher tous les blocs de texte ou de cartes sur la page.
        match_cards = await page.locator("div, article").all()
        extracted_fixtures = []
        seen = set()

        for card in match_cards:
            try:
                text = await card.inner_text()
                # On vérifie si la carte concerne bien le "Round 1" (comme vu sur ton screen)
                if "round 1" in text.lower() or "tour 1" in text.lower():
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    
                    # Nettoyage pour trouver les noms d'équipes potentiels dans la carte
                    # Généralement, les noms d'équipes sont des lignes courtes situées autour des logos ou du statut
                    clean_lines = [l for l in lines if len(l) > 2 and len(l) < 25 and not any(w in l.lower() for w in ["league", "round", "scheduled", "played", "legs", "oct", "nov", "2026"])]
                    
                    if len(clean_lines) >= 2:
                        team_a = clean_lines[0]
                        team_b = clean_lines[1]
                        match_id = f"{team_a} vs {team_b}"
                        
                        if match_id not in seen and team_a != team_b:
                            seen.add(match_id)
                            extracted_fixtures.append((team_a, team_b))
            except:
                continue

        # Sécurité de secours si le DOM change subtilement
        if len(extracted_fixtures) == 0:
            print("⚠️ Aucun match détecté dynamiquement, utilisation des données par défaut du Round 1.")
            extracted_fixtures = [
                ("Viltrumites ES", "BLUE LOCK1"),
                ("VNM Esports", "AUREUS ES")
            ]

        # --- VÉRIFICATION DANS LES LOGS ---
        print("\n" + "="*40)
        print("📋 MATCHS DU ROUND 1 TROUVÉS :")
        print("="*40)
        for idx, (t1, t2) in enumerate(extracted_fixtures[:4], 1):
            print(f"Match {idx} : {t1}  VS  {t2}")
        print("="*40 + "\n")

        await browser.close()

    # --- CRÉATION DE L'AFFICHE INSTAGRAM (1080x1350) ---
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), color="#050913")
    draw = ImageDraw.Draw(img)
    
    # Cadre esport (Or et Bleu)
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
    draw.text((W/2, 195), "LIGUE • ROUND 1", fill="#00b4db", anchor="mm", font=font_sub)
    
    start_y = 300
    for i, (team_a, team_b) in enumerate(extracted_fixtures[:4]):
        y = start_y + (i * 140)
        draw.rectangle([80, y, W-80, y + 110], fill="#0d1930", outline="#d4af37", width=2)
        draw.text((150, y + 55), team_a.upper()[:15], fill="#ffffff", anchor="lm", font=font_match)
        draw.text((W/2, y + 55), "VS", fill="#00b4db", anchor="mm", font=font_match)
        draw.text((W - 150, y + 55), team_b.upper()[:15], fill="#ffffff", anchor="rm", font=font_match)
        
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Affiche générée avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
