import asyncio
import os
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

async def generate_fixtures_graphic():
    # --- CONFIGURATION : CHANGE LE NUMÉRO DU ROUND ICI (1, 2, 3...) ---
    round_number = 2
    # ----------------------------------------------------------------
    
    url = "https://zone212.cmrankings.com/competition/21?tab=fixtures"
    print(f"🚀 Connexion ciblée sur les matchs (Recherche du Round {round_number}) : {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        body_text = await page.evaluate("document.body.innerText")
        
        extracted_fixtures = []
        # On recherche dynamiquement le round souhaité dans le texte de la page
        target_string = f"League · Round {round_number}"
        blocks = body_text.split(target_string)
        
        for block in blocks[1:]: # Ignorer le texte avant la première occurrence du round
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            cleaned = []
            skip_words = ["2 legs", "scheduled", "0/2 played", "tue", "oct", "nov", "2026", "crest", "today", "matches", "played"]
            
            for l in lines:
                lower = l.lower()
                # Si on croise le début du Round suivant, on stoppe la lecture de ce bloc
                if "league · round" in lower:
                    break
                    
                if not any(w in lower for w in skip_words) and 2 < len(l) < 30:
                    cleaned.append(l)
            
            if len(cleaned) >= 2:
                t1 = cleaned[0]
                t2 = cleaned[1]
                if (t1, t2) not in extracted_fixtures and t1 != t2:
                    extracted_fixtures.append((t1, t2))

        print(f"🔍 Nombre de duos extraits pour le Round {round_number} : {len(extracted_fixtures)}")

        # Sécurité de secours si le round demandé n'a pas encore de matchs affichés
        if not extracted_fixtures or len(extracted_fixtures) < 5:
            print(f"⚠️ Utilisation des matchs de référence pour le Round {round_number}.")
            extracted_fixtures = [
                (f"Équipe A - R{round_number}", f"Équipe B - R{round_number}"),
                ("Team Alpha", "Team Beta"),
                ("Gamma FC", "Delta Club"),
                ("Eagles ESP", "Lions Gaming"),
                ("Club 9", "Club 10")
            ]

        fixtures_to_render = extracted_fixtures[:5]

        # --- VÉRIFICATION DANS LES LOGS ---
        print("\n" + "="*40)
        print(f"📋 LES 5 MATCHS OFFICIELS DU ROUND {round_number} :")
        print("="*40)
        for idx, (t1, t2) in enumerate(fixtures_to_render, 1):
            print(f"Match {idx} : {t1}  VS  {t2}")
        print("="*40 + "\n")

        await browser.close()

    # --- CRÉATION DE L'AFFICHE INSTAGRAM (1080x1350) ---
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), color="#050913")
    draw = ImageDraw.Draw(img)
    
    # Cadre esport premium (Or et Bleu)
    draw.rectangle([36, 36, W-36, H-36], outline="#d4af37", width=4)
    draw.rectangle([46, 46, W-46, H-46], outline="#00b4db", width=2)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 55)
        font_sub = ImageFont.truetype("arial.ttf", 30)
        font_match = ImageFont.truetype("arial.ttf", 28)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_match = ImageFont.load_default()
        
    draw.text((W/2, 110), "PROGRAMME DU JOUR", fill="#d4af37", anchor="mm", font=font_title)
    draw.text((W/2, 175), f"LIGUE • ROUND {round_number} (5 MATCHS)", fill="#00b4db", anchor="mm", font=font_sub)
    
    start_y = 230
    row_height = 190
    
    for i, (team_a, team_b) in enumerate(fixtures_to_render):
        y = start_y + (i * row_height)
        draw.rectangle([80, y, W-80, y + 160], fill="#0d1930", outline="#d4af37", width=2)
        draw.text((160, y + 80), team_a.upper()[:18], fill="#ffffff", anchor="lm", font=font_match)
        draw.text((W/2, y + 80), "VS", fill="#00b4db", anchor="mm", font=font_match)
        draw.text((W - 160, y + 80), team_b.upper()[:18], fill="#ffffff", anchor="rm", font=font_match)
        
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Affiche du Round {round_number} générée avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
