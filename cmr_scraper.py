import asyncio
import os
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

async def generate_fixtures_graphic():
    round_number = 1 
    url = "https://zone212.cmrankings.com/competition/21?tab=fixtures"
    print(f"🚀 [Chirurgical] Extraction ciblée du Round {round_number} : {url}")
    
    extracted_fixtures = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        # Extraction ultra-précise par carte de match individuelle (corrigée sans f-string)
        extracted_fixtures = await page.evaluate("""(roundNum) => {
            const fixtures = [];
            const targetText = 'League · Round ' + roundNum;
            
            const cards = document.querySelectorAll('div');
            
            cards.forEach(card => {
                const text = card.innerText;
                const imgs = card.querySelectorAll('img');
                
                if (text && text.includes(targetText) && imgs.length >= 2) {
                    const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                    const cleaned = [];
                    const skipWords = ['2 legs', 'scheduled', '0/2 played', 'tue', 'oct', 'nov', '2026', 'crest', 'today', 'matches', 'played', 'league', 'round', String(roundNum)];
                    
                    for (let l of lines) {
                        const lower = l.toLowerCase();
                        if (!skipWords.some(w => lower.includes(w)) && l.length > 2 && l.length < 30) {
                            cleaned.push(l);
                        }
                    }
                    
                    if (cleaned.length >= 2) {
                        const t1 = cleaned[0];
                        const t2 = cleaned[1];
                        
                        let logo1 = imgs[0] ? imgs[0].src : '';
                        let logo2 = imgs[1] ? imgs[1].src : '';
                        
                        if (!fixtures.some(f => f[0] === t1 && f[1] === t2) && t1 !== t2) {
                            fixtures.push([t1, t2, logo1, logo2]);
                        }
                    }
                }
            });
            return fixtures;
        }""", round_number)

        print(f"🔍 Nombre de vraies cartes de matchs extraites : {len(extracted_fixtures)}")
        await browser.close()

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
    print(f"📋 VÉRIFICATION FINALE DES MATCHS ET LOGOS (ROUND {round_number}) :")
    print("="*50)
    for idx, match in enumerate(fixtures_to_render, 1):
        print(f"Match {idx} :")
        print(f"  - Équipe 1 : {match[0]} | Logo : {match[2] if match[2] else '❌ AUCUN URL'}")
        print(f"  - Équipe 2 : {match[1]} | Logo : {match[3] if match[3] else '❌ AUCUN URL'}")
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
    
    base_url = "https://zone212.cmrankings.com"
    
    for i, (team_a, team_b, logo1_url, logo2_url) in enumerate(fixtures_to_render):
        y = start_y + (i * row_height)
        
        draw.rectangle([80, y, W-80, y + 160], fill="#0d1930", outline="#d4af37", width=2)
        
        if logo1_url and not logo1_url.startswith("http"):
            logo1_url = base_url + logo1_url
        if logo2_url and not logo2_url.startswith("http"):
            logo2_url = base_url + logo2_url

        if logo1_url:
            try:
                response = requests.get(logo1_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
                img.paste(logo_img, (110, y + 40), logo_img)
            except Exception as e:
                print(f"Erreur logo 1: {e}")
                
        if logo2_url:
            try:
                response = requests.get(logo2_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
                img.paste(logo_img, (W - 190, y + 40), logo_img)
            except Exception as e:
                print(f"Erreur logo 2: {e}")

        draw.text((210, y + 80), team_a.upper()[:15], fill="#ffffff", anchor="lm", font=font_match)
        draw.text((W/2, y + 80), "VS", fill="#00b4db", anchor="mm", font=font_match)
        draw.text((W - 210, y + 80), team_b.upper()[:15], fill="#ffffff", anchor="rm", font=font_match)
        
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Affiche parfaite générée avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
