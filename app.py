import streamlit as st
import json
import math
import textwrap
from openai import OpenAI
from fpdf import FPDF

# ==========================================
# 1. CONFIGURATION
# ==========================================
MA_CLE_SECRETE = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="EndurIA", page_icon="⚡", layout="wide")

# CSS "SPORT & PERFORMANCE"
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 800; letter-spacing: -1px; }
    h1 { color: #FF4B4B; }
    
    .seance-card {
        background-color: #ffffff;
        border-left: 5px solid #FF4B4B;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .seance-title { font-weight: bold; font-size: 1.1em; color: #1e1e1e; }
    .seance-meta { font-size: 0.9em; color: #666; margin-bottom: 5px; }
    
    .seance-steps ul { padding-left: 20px; margin-top: 5px; }
    .seance-steps li { margin-bottom: 8px; color: #333; font-family: 'Verdana', sans-serif; font-size: 0.95em; line-height: 1.4; }
    
    .zone-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.9em; }
    .zone-table th { background-color: #f0f2f6; padding: 8px; text-align: left; border-bottom: 2px solid #ddd; }
    .zone-table td { padding: 8px; border-bottom: 1px solid #eee; }
    
    /* Couleurs des Zones */
    .z1 { border-left: 4px solid #808080; } 
    .z2 { border-left: 4px solid #32CD32; } 
    .z3 { border-left: 4px solid #FFD700; } 
    .z4 { border-left: 4px solid #FF8C00; } 
    .z5 { border-left: 4px solid #FF0000; } 
    .z6 { border-left: 4px solid #8B0000; } 
    .z7 { border-left: 4px solid #800080; } 

    .preambule-box {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 30px;
    }
    .lexique { font-size: 0.85em; color: #555; background: #fff; padding: 10px; border-radius: 5px; border: 1px solid #eee; margin-top: 10px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR
# ==========================================
with st.sidebar:
    st.title("EndurIA")
    st.markdown("---")
    
    sport_principal = st.radio("Quel est votre sport ?", ["Cyclisme", "Course à pied"])
    st.markdown("---")
    
    if sport_principal == "Cyclisme":
        sport = st.selectbox("Discipline", ["Cyclisme sur route", "Gravel", "VTT XC", "Cyclocross"])
        sexe = st.radio("Sexe", ["Homme", "Femme"])
        
        st.markdown("### ⚡ Profil de Puissance")
        avec_capteur = st.toggle("J'ai un Capteur de Puissance", value=True)
        
        if avec_capteur:
            ftp = st.number_input("FTP (Watts)", value=250, step=5)
            poids = st.number_input("Poids (kg)", value=70, step=1)
            wkg = round(ftp/poids, 2)
            st.metric("Rapport Poids/Puissance à FTP", f"{wkg} W/kg")
        else:
            ftp = None
            st.info("Le plan sera basé sur vos sensations (1-10).")
            
    else:  
        sport = st.selectbox("Discipline", ["Course sur route", "Trail", "Ultra trail"])
        sexe = st.radio("Sexe", ["Homme", "Femme"])
        
        st.markdown("### 🏃 Profil VMA")
        avec_vma = st.toggle("Je connais ma VMA", value=True)
        
        if avec_vma:
            vma = st.number_input("VMA (Vitesse Maximale Aérobie en km/h)", value=15.0, step=0.5)
        else:
            vma = None
            st.info("Le plan sera basé sur les niveaux d'intensité (i1 à i7) et vos sensations (RPE 1-10).")

    st.markdown("---")
    
    niveau = st.selectbox("Niveau d'entraînement avant le plan", [
        "Je m'entraînais moins de 2h par semaine", 
        "Je m'entraînais entre 3h et 5h par semaine", 
        "Je m'entraînais entre 5h et 10h par semaine", 
        "Je m'entraînais entre 10h et 15h par semaine", 
        "Je m'entraînais entre 15h et 20h par semaine"
    ])
    
    st.markdown("### 📅 Disponibilités")
    st.caption("Indiquez le nombre d'heures où vous êtes disponible chaque jour.")
    
    jours_dispos = {}
    cols_d = st.columns(2)
    with cols_d[0]:
        jours_dispos["Lundi"] = st.number_input("Lun (h)", 0.0, 10.0, 0.0, 0.5)
        jours_dispos["Mardi"] = st.number_input("Mar (h)", 0.0, 10.0, 1.0, 0.5)
        jours_dispos["Mercredi"] = st.number_input("Mer (h)", 0.0, 10.0, 0.0, 0.5)
        jours_dispos["Jeudi"] = st.number_input("Jeu (h)", 0.0, 10.0, 1.0, 0.5)
    with cols_d[1]:
        jours_dispos["Vendredi"] = st.number_input("Ven (h)", 0.0, 10.0, 0.0, 0.5)
        jours_dispos["Samedi"] = st.number_input("Sam (h)", 0.0, 10.0, 2.0, 0.5)
        jours_dispos["Dimanche"] = st.number_input("Dim (h)", 0.0, 10.0, 2.0, 0.5)

    volume_dispo_total = sum(jours_dispos.values())
    st.write(f"**Total heures disponibles : {volume_dispo_total}h / semaine**")
    
    st.markdown("### 🎯 Objectif")
    duree_plan = st.slider("Durée plan (semaines)", 4, 52, 6)

# ==========================================
# 3. PAGE PRINCIPALE & PAIEMENT STRIPE
# ==========================================

st.title(f"PLANIFICATION {sport.upper()}")

TOKEN_SECRET = "PROCOACH2026SECURE" 
parametres_url = st.query_params
a_paye = parametres_url.get("token") == TOKEN_SECRET

if a_paye:
    st.success("✅ Accès débloqué ! Configurez votre objectif ci-dessous pour générer votre plan.")
    
    if sport_principal == "Cyclisme":
        label_objectif = "Objectif (Exemples : \"Gagner une course open 3 FFC\", \"Faire la meilleure performance possible à l'étape du Tour 2026 (Cyclosportive)\"...)"
        default_objectif = "Faire la meilleure performance possible à ma prochaine cyclosportive"
    else:
        label_objectif = "Objectif (Exemples : \"Faire moins de 40min au 10km\", \"Pouvoir courir 1h sans m'arrêter\"...)"
        default_objectif = "Faire un semi-marathon en moins d'1h30"

    objectif = st.text_input(label_objectif, default_objectif)
    generer = st.button("⚡ GÉNÉRER LA STRUCTURE DU PLAN", type="primary", use_container_width=True)

else:
    st.info("💡 Pour générer votre plan d'entraînement sur-mesure, vous devez débloquer l'accès.")
    st.markdown("""
    **Ce que vous obtenez (4,99€) :**
    * 🎯 Un plan ultra-personnalisé de 4 à 52 semaines généré par IA.
    * ⏱️ Une adaptation parfaite à vos disponibilités et votre niveau.
    * 🍎 Des conseils nutritionnels précis pour chaque séance.
    * 📥 Un fichier PDF complet de votre programme prêt à être téléchargé.
    """)
    
    LIEN_STRIPE = "https://buy.stripe.com/test_28E14oco2gZvaTN8l17Re00" 
    st.link_button("💳 DÉBLOQUER MON PLAN (4,99€) - Paiement Sécurisé", LIEN_STRIPE, type="primary", use_container_width=True)
    st.caption("🔒 Paiement 100% sécurisé via Stripe. Vous serez redirigé automatiquement ici après le paiement.")
    generer = False

# ==========================================
# 4. LOGIQUE MÉTIER & DONNÉES ZONES/LEXIQUE
# ==========================================

if generer:
    client = OpenAI(api_key=MA_CLE_SECRETE)
    
    # --- PRÉPARATION DES DONNÉES (POUR WEB ET PDF) ---
    if sport_principal == "Cyclisme":
        if avec_capteur:
            z1 = [0, int(ftp * 0.55)]; z2 = [int(ftp * 0.56), int(ftp * 0.75)]
            z3 = [int(ftp * 0.76), int(ftp * 0.90)]; z4 = [int(ftp * 0.91), int(ftp * 1.05)]
            z5 = [int(ftp * 1.06), int(ftp * 1.20)]; z6 = [int(ftp * 1.21), int(ftp * 1.50)]
            z7 = [int(ftp * 1.51), 9999]

            headers_zones = ["Zone", "Nom", "Vos Watts", "Durée Tenable", "Sensations"]
            data_zones = [
                ["Z1", "Récup Active", f"< {z1[1]} W", "sans limite", "Très facile ; respiration uniquement par le nez sans souci, tu peux parler en phrase longue sans souci, jambes légères."],
                ["Z2", "Endurance", f"{z2[0]} - {z2[1]} W", "3h à 10h", "Aisance respiratoire, tu peux tenir une discussion facilement, effort facile mais concentré."],
                ["Z3", "Tempo", f"{z3[0]} - {z3[1]} W", "45min à 3h", "Respiration clairement marquée, les phrases doivent être courtes, tu sens les jambes travailler. Exemple : ascension d'un long col."],
                ["Z4", "Seuil", f"{z4[0]} - {z4[1]} W", "20min à 60min", "Conversation impossible, juste 'oui' ou 'non', brûlure musculaire mais pas à fond. Exemple : col court."],
                ["Z5", "PMA", f"{z5[0]} - {z5[1]} W", "3min à 8min", "Respiration haletante. Compte à rebours mental. Exemple : bosse à bloc en course."],
                ["Z6", "Anaérobie", f"{z6[0]} - {z6[1]} W", "30sec à 3min", "Effort violent, attaque prolongée, clairement à fond sur plus ou moins 1 minute."],
                ["Z7", "Sprint", f"> {z7[0]} W", "< 30sec", "Explosivité pure. Sprint très court. Force maximum sur durée extrêmement courte."]
            ]
            data_lexique = [
                ("FTP", "Puissance maximale tenable sur 1 heure."),
                ("PMA", "Puissance Maximale Aérobie (effort max de 5 min)."),
                ("RPM", "Tours de pédale par minute (Cadence).")
            ]
            prompt_style_instruction = "UTILISE LA NOTATION 'Z' (Z1, Z2, Z3...). EXEMPLE : '3 séries de (10 min en Z3 puis 5 min de récup en Z1)'."

        else:
            headers_zones = ["Zone", "Intensité", "RPE (1-10)", "Durée Tenable", "Sensations"]
            data_zones = [
                ["i1", "Récupération", "1-2", "sans limite", "Très facile ; respiration uniquement par le nez sans souci, tu peux parler en phrase longue sans souci, jambes légères."],
                ["i2", "Endurance", "3-4", "3h à 10h", "Aisance respiratoire, tu peux tenir une discussion facilement, effort facile mais concentré."],
                ["i3", "Tempo", "5-6", "45min à 3h", "Respiration clairement marquée, les phrases doivent être courtes, tu sens les jambes travailler. Exemple : ascension d'un long col."],
                ["i4", "Seuil", "7-8", "20min à 60min", "Conversation impossible, juste 'oui' ou 'non', brûlure musculaire mais pas à fond. Exemple : col court."],
                ["i5", "PMA", "9", "3min à 8min", "Respiration haletante. Compte à rebours mental. Exemple : bosse à bloc en course."],
                ["i6", "Anaérobie", "9.5", "30sec à 3min", "Effort violent, attaque prolongée, clairement à fond sur plus ou moins 1 minute."],
                ["i7", "Sprint", "10", "< 30 sec", "Explosivité pure. Sprint très court. Force maximum sur durée extrêmement courte."]
            ]
            data_lexique = [
                ("RPE", "Ressenti de l'effort (1 = Facile, 10 = Extrême)."),
                ("FC", "Fréquence Cardiaque (BPM)."),
                ("RPM", "Cadence de pédalage.")
            ]
            prompt_style_instruction = "INTERDICTION D'UTILISER 'Z'. UTILISE UNIQUEMENT 'i' (i1 à i7). EXEMPLE : '3 séries de (10 min en i3 puis 5 min de récup en i1)'."

    else:
        if avec_vma:
            # AJOUT DU " km/h" ICI 👇
            z1 = f"<{round(vma*0.65, 1)} km/h"; z2 = f"{round(vma*0.65, 1)} - {round(vma*0.75, 1)} km/h"
            z3 = f"{round(vma*0.75, 1)} - {round(vma*0.85, 1)} km/h"; z4 = f"{round(vma*0.85, 1)} - {round(vma*0.90, 1)} km/h"
            z5 = f"{round(vma*0.90, 1)} - {round(vma*1.0, 1)} km/h"; z6 = f"{round(vma*1.0, 1)} - {round(vma*1.10, 1)} km/h"
            z7 = f">{round(vma*1.10, 1)} km/h"

            headers_zones = ["Zone", "Nom", "% VMA", "Vitesse (km/h)", "Sensations"]
            data_zones = [
                ["Z1", "Récupération", "< 65%", z1, "Trot très lent, aucune fatigue, respiration nasale aisée."],
                ["Z2", "Endurance Fondamentale", "65-75%", z2, "Aisance respiratoire totale, conversation parfaitement fluide."],
                ["Z3", "Tempo / Allure Marathon", "75-85%", z3, "Respiration plus rythmée, phrases courtes possibles, foulée dynamique."],
                ["Z4", "Seuil Anaérobie", "85-90%", z4, "Allure semi-marathon/10km. Conversation impossible (mots isolés), effort difficile mais constant."],
                ["Z5", "VMA Longue", "90-100%", z5, "Effort très dur, hyperventilation, tenable sur des fractions de 3 à 6 minutes."],
                ["Z6", "VMA Courte", "100-110%", z6, "Allure maximale sur des fractions courtes (30s à 1min30)."],
                ["Z7", "Sprint", "> 110%", z7, "Sprint pur, vitesse maximale sur quelques secondes."]
            ]
            data_lexique = [
                ("VMA", "Vitesse Maximale Aérobie. Allure tenable sur environ 6 minutes."),
                ("EF", "Endurance Fondamentale (Z2). L'allure de base de la plupart des footings."),
                ("Trot / Récup", "Allure très lente pour récupérer entre deux efforts intenses.")
            ]
            prompt_style_instruction = "UTILISE LES % VMA ET ALLURES CIBLES. EXEMPLE : '3 séries de (3 min à 90% VMA puis 1 min30 de trot lent)'."

        else:
            headers_zones = ["Niveau", "Intensité", "RPE (1-10)", "Durée Tenable", "Sensations (Test de la parole)"]
            data_zones = [
                ["i1", "Récupération", "1-2", "sans limite", "Trot très lent, aucune fatigue, on peut chanter ou parler sans problème."],
                ["i2", "Endurance Fondamentale", "3-4", "plusieurs heures", "Aisance respiratoire totale, conversation fluide avec d'autres coureurs."],
                ["i3", "Tempo / Allure modérée", "5-6", "1h à 3h", "Respiration rythmée, on ne peut dire que des phrases courtes."],
                ["i4", "Seuil Anaérobie", "7-8", "30min à 1h", "Effort 'confortablement difficile'. On ne dit que des mots isolés ('Oui', 'Non')."],
                ["i5", "Fractionné Long", "9", "3min à 6min", "Très difficile. Souffle court, hyperventilation."],
                ["i6", "Fractionné Court", "9.5", "30sec à 2min", "Effort quasi-maximal."],
                ["i7", "Sprint", "10", "< 20 sec", "Vitesse maximale absolue."]
            ]
            data_lexique = [
                ("RPE", "Ressenti de l'effort (1 = Facile, 10 = Sprint max)."),
                ("Fractionné", "Entraînement alternant périodes d'efforts intenses et récupérations."),
                ("EF", "Endurance Fondamentale (i2). L'allure de base.")
            ]
            prompt_style_instruction = "INTERDICTION D'UTILISER 'Z'. UTILISE UNIQUEMENT LES NIVEAUX 'i' (i1 à i7) OU L'ÉCHELLE RPE. EXEMPLE : '3 séries de (3 min à i4 puis 1 min30 de trot en i1)'."

    # --- GÉNÉRATION HTML POUR LE WEB ---
    html_zones = '<table class="zone-table"><tr>'
    for h in headers_zones: html_zones += f"<th>{h}</th>"
    html_zones += "</tr>"
    for i, row in enumerate(data_zones):
        html_zones += f'<tr class="z{i+1}">'
        for j, cell in enumerate(row):
            html_zones += f"<td><strong>{cell}</strong></td>" if j==0 else f"<td>{cell}</td>"
        html_zones += "</tr>"
    html_zones += "</table>"

    html_lexique = '<div class="lexique"><strong>📚 GLOSSAIRE :</strong><br>'
    for item in data_lexique:
        html_lexique += f"<strong>{item[0]}</strong> : {item[1]}<br>"
    html_lexique += "</div>"

    # --- APPEL OPENAI ---
    dispos_str = ", ".join([f"{j}: {h}h" for j, h in jours_dispos.items() if h > 0])
    full_plan = {"titre": f"Prépa {objectif}", "weeks": []}
    taille_bloc = 4 
    nombre_blocs = math.ceil(duree_plan / taille_bloc)
    progress_bar = st.progress(0)
    status = st.status("🧠 Analyse des disponibilités et rédaction du plan...", expanded=True)
    
    try:
        for i in range(nombre_blocs):
            start_w = i * taille_bloc + 1
            end_w = min((i + 1) * taille_bloc, duree_plan)
            
            status.write(f"Rédaction du bloc semaines {start_w} à {end_w}...")
            
            prompt = f"""
            Tu es un coach expert en {sport_principal} ({sport}).
            Athlète : {sexe}, Niveau : {niveau}.
            Disponibilités EXACTES : {dispos_str}. Objectif : {objectif}.
            
            MISSION : Génère un plan pour les semaines {start_w} à {end_w}.
            1. DÉTERMINISME ABSOLU : Temps, intensité et répétitions précis.
            2. FORMAT : La liste 'details' contient des phrases.
            3. NOMENCLATURE : {prompt_style_instruction}
            4. REPOS : Génère une séance pour chaque jour dispo. Si repos nécessaire, titre "Repos" avec nutrition "Hydratation".
            
            JSON ATTENDU :
            {{
              "weeks": [
                {{
                  "numero": {start_w},
                  "seances": [
                     {{
                       "jour": "Mardi", "titre": "Endurance", "duree_totale": "1h30",
                       "nutrition": "60g glucides/h", "details": ["Echauffement...", "Corps...", "Retour..."]
                     }}
                  ]
                }}
              ]
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            data_chunk = json.loads(response.choices[0].message.content)
            if "weeks" in data_chunk:
                full_plan["weeks"].extend(data_chunk["weeks"])
            
            progress_bar.progress((i + 1) / nombre_blocs)

        status.update(label="✅ Terminé !", state="complete", expanded=False)
        
        # ==========================================
        # 5. GÉNÉRATION DU PDF PRO (Arrière-plan)
        # ==========================================
        class PDF(FPDF):
            def header(self):
                self.set_fill_color(255, 75, 75)
                self.rect(0, 0, 210, 18, 'F')
                self.set_y(6)
                self.set_font('Arial', 'B', 14)
                self.set_text_color(255, 255, 255)
                self.cell(0, 6, "ENDURIA - PLAN D'ENTRAINEMENT SUR-MESURE", 0, 1, 'C')
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

            def clean(self, txt):
                if not txt: return ""
                txt = str(txt).replace("⏱️", "").replace("🍎", "").replace("⚡", "").replace("🎯", "")
                return txt.encode('latin-1', 'replace').decode('latin-1')

        pdf = PDF()
        pdf.add_page()
        
        # --- En-tête Titre ---
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 10, pdf.clean(f"OBJECTIF : {objectif.upper()}"), 0, 1, 'C')
        
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(100, 100, 100)
        infos = f"FTP : {ftp}W" if (sport_principal=="Cyclisme" and avec_capteur) else (f"VMA : {vma} km/h" if (sport_principal=="Course à pied" and avec_vma) else "Sensations (RPE)")
        pdf.cell(0, 6, pdf.clean(f"{sport_principal} | {sport} | {infos}"), 0, 1, 'C')
        pdf.ln(8)
        
        # --- Bloc Zones COMPLET (Identique au site) ---
        pdf.set_fill_color(240, 240, 240)
        pdf.set_draw_color(200, 200, 200)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, "  VOS ZONES DE TRAVAIL", border=1, ln=1, fill=True)
        pdf.ln(2)

        for row in data_zones:
            # Ligne avec fond gris clair (Zone | Nom | Valeur | Durée)
            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(250, 250, 250)
            pdf.set_text_color(255, 75, 75)
            pdf.cell(15, 6, pdf.clean(row[0]), border="LTB", align='C', fill=True)
            
            pdf.set_text_color(40, 40, 40)
            info_str = f" {row[1]}   |   {row[2]}   |   {row[3]}"
            pdf.cell(0, 6, pdf.clean(info_str), border="RTB", ln=1, fill=True)
            
            # Ligne descriptive en dessous (Sensations)
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 5, pdf.clean(f"Sensations : {row[4]}"), border="LBR")
            pdf.ln(2)

        # --- Bloc Lexique COMPLET (Identique au site) ---
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, "  GLOSSAIRE", border=1, ln=1, fill=True)
        pdf.ln(2)
        
        for item in data_lexique:
            pdf.set_font("Arial", "B", 9)
            pdf.cell(30, 6, pdf.clean(item[0]), 0, 0)
            pdf.set_font("Arial", "", 9)
            pdf.multi_cell(0, 6, pdf.clean(f": {item[1]}"))
        pdf.ln(8)
        
        # --- Boucle des Semaines ---
        for week in full_plan['weeks']:
            if pdf.get_y() > 250: pdf.add_page()
            
            num_pdf = week.get('numero', '?')
            pdf.set_fill_color(50, 50, 50)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, pdf.clean(f"  SEMAINE {num_pdf}"), 0, 1, 'L', fill=True)
            pdf.ln(3)
            
            for seance in week.get('seances', []):
                if pdf.get_y() > 240: pdf.add_page()
                
                pdf.set_fill_color(245, 245, 245)
                pdf.set_font("Arial", "B", 10)
                
                jour_txt = pdf.clean(seance.get('jour', '').upper())
                duree_txt = pdf.clean(seance.get('duree_totale', ''))
                titre_txt = pdf.clean(seance.get('titre', ''))
                
                pdf.set_text_color(255, 75, 75)
                pdf.cell(30, 8, f" {jour_txt} ", 0, 0, 'L', fill=True)
                pdf.set_text_color(40, 40, 40)
                pdf.cell(0, 8, f"{titre_txt}  |  Durée : {duree_txt}", 0, 1, 'L', fill=True)
                
                pdf.set_text_color(230, 120, 0)
                pdf.set_font("Arial", "B", 9)
                pdf.cell(30, 6, "", 0, 0) 
                pdf.cell(0, 6, pdf.clean(f"Nutrition : {seance.get('nutrition', '')}"), 0, 1)
                
                pdf.set_text_color(60, 60, 60)
                pdf.set_font("Arial", "", 9)
                details_pdf = seance.get('details', ["Non spécifié"])
                
                if isinstance(details_pdf, list):
                    for step in details_pdf:
                        pdf.set_x(40)
                        pdf.multi_cell(0, 5, pdf.clean(f"- {step}"))
                else:
                    pdf.set_x(40)
                    pdf.multi_cell(0, 5, pdf.clean(details_pdf))
                    
                pdf.ln(4)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        # ==========================================
        # 6. AFFICHAGE DU BOUTON TÉLÉCHARGEMENT (EN HAUT)
        # ==========================================
        st.divider()
        st.warning("⚠️ ATTENTION : Téléchargez votre PDF maintenant. Si vous fermez ou rafraîchissez cette page, votre plan sera perdu.")
        st.download_button(
            label="📥 TÉLÉCHARGER LE PDF DU PLAN",
            data=pdf_bytes,
            file_name=f"EndurIA_Plan_{sport_principal}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        st.divider()

        # ==========================================
        # 7. AFFICHAGE WEB (EN BAS)
        # ==========================================
        st.markdown(f"""
        <div class="preambule-box">
            <h3 style="margin-top:0;">📊 VOS ZONES & LEXIQUE</h3>
            {html_zones}
            {html_lexique}
        </div>
        """, unsafe_allow_html=True)
        
        for week in full_plan['weeks']:
            num = week.get('numero', '?')
            with st.expander(f"SEMAINE {num}", expanded=(num==1)):
                seances = week.get('seances', [])
                cols = st.columns(len(seances)) if len(seances) <= 4 and len(seances) > 0 else st.columns(3)
                
                for i, seance in enumerate(seances):
                    if len(seances) > 0:
                        col_to_use = cols[i % 3] if len(seances) > 4 else cols[i]
                        with col_to_use:
                            details_raw = seance.get('details', ["Détails non générés."])
                            steps_html = "".join([f"<li>{step}</li>" for step in details_raw]) if isinstance(details_raw, list) else details_raw
                            st.markdown(f"""
                            <div class="seance-card">
                                <div class="seance-meta">{seance.get('jour', 'Jour ?').upper()} • ⏱️ {seance.get('duree_totale', 'N/A')}</div>
                                <div class="seance-title">{seance.get('titre', 'Séance')}</div>
                                <div style="font-size: 0.85em; color: #d35400; margin-bottom: 8px; font-weight: bold;">🍎 Nutrition : {seance.get('nutrition', 'Non spécifiée')}</div>
                                <div class="seance-steps"><ul>{steps_html}</ul></div>
                            </div>
                            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
