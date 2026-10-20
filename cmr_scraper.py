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
    
    print(f"🚀 [Pro Taille XXL] Récupération des logos et des matchs...")
    
    team_logos = {}
    extracted_fixtures = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # --- ÉTAPE 1 : Récupérer les logos depuis STANDINGS ---
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

        # --- ÉTAPE 2 : Récupérer les matchs du Round depuis FIXTURES ---
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

    # --- CHARGEMENT DU MASTER BACKGROUND (IMG_0847.jpeg) ---
    bg_path = "IMG_0847.jpeg"
    if os.path.exists(bg_path):
        img = Image.open(bg_path).convert("RGB")
        print("✅ IMG_0847.jpeg chargé avec succès !")
    else:
        print("⚠️ IMG_0847.jpeg introuvable, création d'un fond de secours 2000x2000.")
        img = Image.new("RGB", (2000, 2000), color="#050913")
        
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # Téléchargement de la police
    font_path = "BroadcastFont.ttf"
    if not os.path.exists(font_path):
        ttf_url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
        r = requests.get(ttf_url)
        with open(font_path, "wb") as f:
            f.write(r.content)

    # TAILLES XXL ADAPTÉES À LA HAUTE RÉSOLUTION DE TON IMAGE DE FOND
    title_font_size = int(W * 0.08)   # 8% de la largeur pour le titre
    match_font_size = int(W * 0.038)  # 3.8% de la largeur pour les équipes (très grand et visible)

    try:
        font_title = ImageFont.truetype(font_path, title_font_size)
        font_match = ImageFont.truetype(font_path, match_font_size)
    except:
        font_title = ImageFont.load_default()
        font_match = ImageFont.load_default()
        
    # Titre "MATCHDAY 1" positionné sous le logo
    title_text = "MATCHDAY 1"
    title_y = int(H * 0.22)
    draw.text((W/2 + 6, title_y + 6), title_text, fill="#000000", anchor="mm", font=font_title)
    draw.text((W/2, title_y), title_text, fill="#F3C653", anchor="mm", font=font_title)
    
    # --- INSERTION DES LIGNES DE MATCHS (Taille massive, sans VS) ---
    start_y = int(H * 0.30)
    available_height = H * 0.63
    row_height = int(available_height / 5)
    bar_height = int(row_height * 0.80)
    
    margin_x = int(W * 0.06)
    
    for i, (team_a, team_b, logo1_url, logo2_url) in enumerate(fixtures_to_render):
        y = start_y + (i * row_height)
        
        # Bandeau de match semi-transparent
        draw.rectangle([margin_x, y, W - margin_x, y + bar_height], fill=(8, 18, 38, 235), outline=(212, 175, 55, 160), width=3)
        
        # Ligne lumineuse dorée sous chaque match
        draw.line([(margin_x + 15, y + bar_height), (W - margin_x - 15, y + bar_height)], fill="#E5B84B", width=4)
        
        if logo1_url and not logo1_url.startswith("http"):
            logo1_url = base_url + logo1_url
        if logo2_url and not logo2_url.startswith("http"):
            logo2_url = base_url + logo2_url

        logo_size = int(bar_height * 0.75)
        logo_y = y + (bar_height - logo_size) // 2

        # Insertion Logo Équipe 1
        if logo1_url:
            try:
                response = requests.get(logo1_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                img.paste(logo_img, (margin_x + int(40), logo_y), logo_img)
            except Exception as e:
                print(f"Erreur logo 1: {e}")
                
        # Insertion Logo Équipe 2
        if logo2_url:
            try:
                response = requests.get(logo2_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                img.paste(logo_img, (W - margin_x - int(40) - logo_size, logo_y), logo_img)
            except Exception as e:
                print(f"Erreur logo 2: {e}")

        # Noms des équipes en format XXL, bien lisibles des deux côtés
        text_y = y + bar_height / 2
        draw.text((margin_x + logo_size + int(65), text_y), team_a.upper()[:14], fill="#FFFFFF", anchor="lm", font=font_match)
        draw.text((W - margin_x - logo_size - int(65), text_y), team_b.upper()[:14], fill="#FFFFFF", anchor="rm", font=font_match)
        
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Affiche XXL avec gros textes générée avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
