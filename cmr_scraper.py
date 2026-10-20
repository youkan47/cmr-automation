import asyncio
import os
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

async def generate_fixtures_graphic():
    round_number = 1 
    base_url = "https://zone212.cmrankings.com"
    
    standings_url = f"{base_url}/competition/21?tab=standings"
    fixtures_url = f"{base_url}/competition/21?tab=fixtures"
    
    competition_logo_url = "https://zone212.cmrankings.com/tenancy/assets/competitions/logos/competition-21-ed4d38e3-a842-4c11-9d00-79b94db30ed7.webp"
    
    print(f"🚀 [Pro Design Linux Font] Connexion au classement pour récupérer les logos...")
    
    team_logos = {}
    extracted_fixtures = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # --- ÉTAPE 1 : Récupérer les logos depuis l'onglet STANDINGS ---
        await page.goto(standings_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)
        
        team_logos = await page.evaluate("""() => {
            const logosMap = {};
            const rows = document.querySelectorAll('tr, tbody tr');
            rows.forEach(row => {
                const text = row.innerText;
                const img = row.querySelector('img');
                if (text && img) {
                    const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                    for (let l of lines) {
                        if (l.length > 2 && l.length < 30 && !/^[0-9]+$/.test(l)) {
                            logosMap[l.toUpperCase()] = img.src;
                            break;
                        }
                    }
                }
            });
            return logosMap;
        }""")
        
        print(f"✅ Logos récupérés pour {len(team_logos)} équipes.")

        # --- ÉTAPE 2 : Récupérer les matchs du Round depuis l'onglet FIXTURES ---
        print(f"🚀 Connexion aux matchs du Round {round_number}...")
        await page.goto(fixtures_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)
        
        extracted_fixtures = await page.evaluate("""(roundNum) => {
            const fixtures = [];
            const targetText = 'League · Round ' + roundNum;
            const cards = document.querySelectorAll('div');
            
            cards.forEach(card => {
                const text = card.innerText;
                if (text && text.includes(targetText) && (text.includes('SCHEDULED') || text.includes('0/2 played'))) {
                    const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                    const cleaned = [];
                    const skipWords = ['2 legs', 'scheduled', '0/2 played', 'tue', 'oct', 'nov', '2026', 'crest', 'today', 'matches', 'played', 'league', 'round', String(roundNum), 'active'];
                    
                    for (let l of lines) {
                        const lower = l.toLowerCase();
                        if (!skipWords.some(w => lower.includes(w)) && l.length > 2 && l.length < 30) {
                            cleaned.push(l);
                        }
                    }
                    
                    if (cleaned.length >= 2) {
                        const t1 = cleaned[0];
                        const t2 = cleaned[1];
                        if (!fixtures.some(f => f[0] === t1 && f[1] === t2) && t1 !== t2) {
                            fixtures.push([t1, t2]);
                        }
                    }
                }
            });
            return fixtures;
        }""", round_number)

        await browser.close()

    if not extracted_fixtures or len(extracted_fixtures) < 5:
        print("⚠️ Utilisation de la liste officielle des 5 matchs du Round 1.")
        extracted_fixtures = [
            ("Viltrumites ES", "BLUE LOCK1"),
            ("VNM Esports", "AUREUS ES"),
            ("INFIRNO FC", "AJAX CASABLANCA"),
            ("TEMARA FC", "FC L HOKOMA"),
            ("LMRARCCA", "fc energy")
        ]

    fixtures_to_render = extracted_fixtures[:5]

    final_fixtures_with_logos = []
    for t1, t2 in fixtures_to_render:
        logo1 = team_logos.get(t1.upper(), "")
        logo2 = team_logos.get(t2.upper(), "")
        final_fixtures_with_logos.append((t1, t2, logo1, logo2))

    # --- CRÉATION DE L'AFFICHE HD CARRÉE (1080x1080) ---
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), color="#050913")
    draw = ImageDraw.Draw(img)
    
    # Cadre esport premium (Or et Bleu)
    draw.rectangle([30, 30, W-30, H-30], outline="#d4af37", width=4)
    draw.rectangle([38, 38, W-38, H-38], outline="#00b4db", width=2)
    
    # Logo de la compétition centré en haut
    if competition_logo_url:
        try:
            res = requests.get(competition_logo_url, timeout=5)
            comp_logo = Image.open(BytesIO(res.content)).convert("RGBA")
            comp_logo = comp_logo.resize((120, 120), Image.Resampling.LANCZOS)
            img.paste(comp_logo, (W//2 - 60, 42), comp_logo)
        except Exception as e:
            print(f"Erreur chargement logo compétition : {e}")

    # Utilisation d'une police Linux standard (DejaVu Sans Bold) garantie sur GitHub Actions
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font_title = ImageFont.truetype(font_path, 64) # Gros titre lisible
        font_match = ImageFont.truetype(font_match_path := font_path, 34) # Noms d'équipes bien visibles
    except:
        font_title = ImageFont.load_default()
        font_match = ImageFont.load_default()
        
    # En-tête : MATCHDAY 1
    draw.text((W/2, 185), "MATCHDAY 1", fill="#d4af37", anchor="mm", font=font_title)
    
    # --- INSERTION DES CARTES DE MATCHS ---
    start_y = 235
    row_height = 150
    
    for i, (team_a, team_b, logo1_url, logo2_url) in enumerate(final_fixtures_with_logos):
        y = start_y + (i * row_height)
        
        # Fond de la carte de match
        draw.rectangle([70, y, W-70, y + 132], fill="#0d1930", outline="#d4af37", width=2)
        
        if logo1_url and not logo1_url.startswith("http"):
            logo1_url = base_url + logo1_url
        if logo2_url and not logo2_url.startswith("http"):
            logo2_url = base_url + logo2_url

        # Insertion Logo Équipe 1
        if logo1_url:
            try:
                response = requests.get(logo1_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((70, 70), Image.Resampling.LANCZOS)
                img.paste(logo_img, (95, y + 31), logo_img)
            except Exception as e:
                print(f"Erreur logo 1: {e}")
                
        # Insertion Logo Équipe 2
        if logo2_url:
            try:
                response = requests.get(logo2_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((70, 70), Image.Resampling.LANCZOS)
                img.paste(logo_img, (W - 165, y + 31), logo_img)
            except Exception as e:
                print(f"Erreur logo 2: {e}")

        # Noms des équipes et VS
        draw.text((185, y + 66), team_a.upper()[:12], fill="#ffffff", anchor="lm", font=font_match)
        draw.text((W/2, y + 66), "VS", fill="#00b4db", anchor="mm", font=font_match)
        draw.text((W - 185, y + 66), team_b.upper()[:12], fill="#ffffff", anchor="rm", font=font_match)
        
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Affiche avec vraie police HD générée avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
