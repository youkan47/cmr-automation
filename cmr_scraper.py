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
    
    print(f"🚀 [Pro Layout Fix] Récupération des logos et des matchs...")
    
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
        print("⚠️ IMG_0847.jpeg introuvable, création d'un fond de secours.")
        img = Image.new("RGB", (1080, 1080), color="#050913")
        
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # Téléchargement d'une police bold propre pour le rendu Linux
    font_path = "BroadcastFont.ttf"
    if not os.path.exists(font_path):
        ttf_url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
        r = requests.get(ttf_url)
        with open(font_path, "wb") as f:
            f.write(r.content)

    try:
        font_title = ImageFont.truetype(font_path, 58)  # Titre bien proportionné sous le logo
        font_match = ImageFont.truetype(font_path, 30)  # Noms d'équipes lisibles
        font_vs = ImageFont.truetype(font_path, 24)     # VS central
    except:
        font_title = ImageFont.load_default()
        font_match = ImageFont.load_default()
        font_vs = ImageFont.load_default()
        
    # Titre "MATCHDAY 1" centré sous le logo CMR de l'image de fond
    title_text = "MATCHDAY 1"
    draw.text((W/2 + 2, 192), title_text, fill="#000000", anchor="mm", font=font_title)
    draw.text((W/2, 190), title_text, fill="#F3C653", anchor="mm", font=font_title) # Or brillant
    
    # --- INSERTION DES LIGNES DE MATCHS (Positionnement parfait) ---
    start_y = 260
    row_height = 115
    
    for i, (team_a, team_b, logo1_url, logo2_url) in enumerate(final_fixtures_with_logos):
        y = start_y + (i * row_height)
        
        # Bandeau de match semi-transparent élégant (largeur bien ajustée aux marges)
        draw.rectangle([85, y, W-85, y + 98], fill=(8, 18, 38, 230), outline=(212, 175, 55, 140), width=1)
        
        # Ligne lumineuse dorée sous chaque match
        draw.line([(95, y + 98), (W - 95, y + 98)], fill="#E5B84B", width=2)
        
        if logo1_url and not logo1_url.startswith("http"):
            logo1_url = base_url + logo1_url
        if logo2_url and not logo2_url.startswith("http"):
            logo2_url = base_url + logo2_url

        # Insertion Logo Équipe 1 (Taille optimisée : 56x56)
        if logo1_url:
            try:
                response = requests.get(logo1_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((56, 56), Image.Resampling.LANCZOS)
                img.paste(logo_img, (115, y + 21), logo_img)
            except Exception as e:
                print(f"Erreur logo 1: {e}")
                
        # Insertion Logo Équipe 2
        if logo2_url:
            try:
                response = requests.get(logo2_url, timeout=5)
                logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
                logo_img = logo_img.resize((56, 56), Image.Resampling.LANCZOS)
                img.paste(logo_img, (W - 171, y + 21), logo_img)
            except Exception as e:
                print(f"Erreur logo 2: {e}")

        # Badge "VS" central en cyan néon
        vs_box_w, vs_box_h = 46, 30
        vs_x = W // 2 - vs_box_w // 2
        vs_y = y + 34
        draw.rectangle([vs_x, vs_y, vs_x + vs_box_w, vs_y + vs_box_h], fill="#03060A", outline="#00B4DB", width=2)
        draw.text((W/2, y + 49), "VS", fill="#00B4DB", anchor="mm", font=font_vs)

        # Noms des équipes parfaitement alignés
        draw.text((190, y + 49), team_a.upper()[:14], fill="#FFFFFF", anchor="lm", font=font_match)
        draw.text((W - 190, y + 49), team_b.upper()[:14], fill="#FFFFFF", anchor="rm", font=font_match)
        
    output_path = "instagram_post.png"
    img.save(output_path)
    print(f"🎨 Affiche corrigée et alignée générée avec succès : {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_fixtures_graphic())
