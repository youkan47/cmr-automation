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
        
        # Extraction précise basée sur la structure exacte que tu as partagée
        extracted_fixtures = await page.evaluate("""() => {
            const fixtures = [];
            const textContent = document.body.innerText;
            
            // On cherche à découper par les blocs "League · Round 1"
            const blocks = textContent.split('League · Round 1');
            
            blocks.forEach(block => {
                const lines = block.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                
                // Dans ton texte type, les équipes se trouvent autour de "0/2 played" ou avant/après les mots "SCHEDULED" / "crest"
                // On filtre les lignes pour trouver les vrais noms d'équipes
                const cleanedLines = [];
                const skipWords = ['2 legs', 'scheduled', '0/2 played', 'tue', 'oct', 'nov', '2026', 'crest', 'today', 'matches'];
                
                for (let l of lines) {
                    const lower = l.toLowerCase();
                    if (!skipWords.some(w => lower.includes(w)) && l.length > 2 && l.length < 30) {
                        cleanedLines.push(l);
                    }
                }
                
                // Si on a au moins 2 équipes valides dans ce bloc de round 1
                if (cleanedLines.length >= 2) {
                    const t1 = cleanedLines[0];
                    const t2 = cleanedLines[1];
                    if (!fixtures.some(f => f[0] === t1 && f[1] === t2) && t1 !== t2) {
                        fixtures.push([t1, t2]);
                    }
                }
            });
            
            return fixtures;
        """)

        print(f"🔍 Nombre de duos extraits : {len(extracted_fixtures)}")

        # Si le scraping automatique a un souci, on intègre directement tes 5 vrais matchs exacts
        if not extracted_fixtures or len(extracted_fixtures) < 5:
            print("⚠️ Utilisation des 5 vrais matchs officiels du Round 1.")
            extracted_fixtures = [
                ("Viltrumites ES", "BLUE LOCK1"),
                ("VNM Esports", "AUREUS ES"),
                ("INFIRNO FC", "AJAX CASABLANCA"),
                ("TEMARA FC", "FC L HOKOMA"),
                ("LMRARCCA", "fc energy")
            ]

        fixtures_to_render = extracted_fixtures[:5]

        # --- VÉRIFICATION DANS LES LOGS ---
        print("\n" + "="*40)
        print("📋 LES 5 VRAIS MATCHS DU ROUND 1 :")
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
    draw.text((W/2, 175), "LIGUE • ROUND 1 (5 MATCHS)", fill="#00b4db", anchor="mm", font=font_sub)
    
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
    print(f"🎨 Affiche parfaite générée avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
