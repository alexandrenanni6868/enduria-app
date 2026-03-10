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
    
    # SÉLECTION DU SPORT PRINCIPAL
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
            
    else:  # Course à pied
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
    st.caption("Indiquez le nombre d'heures où vous êtes disponible chaque jour (Laissez 0 si indisponible).")
    
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

# --- VÉRIFICATION DU PAIEMENT SÉCURISÉ ---
TOKEN_SECRET = "PROCOACH2026SECURE" 

parametres_url = st.query_params
a_paye = parametres_url.get("token") == TOKEN_SECRET

if a_paye:
    st.success("✅ Accès débloqué ! Configurez votre objectif ci-dessous pour générer votre plan.")
    
    if sport_principal == "Cyclisme":
        label_objectif = "Objectif (Exemples : \"Gagner une course open 3 FFC\", \"Faire la meilleure performance possible à l'étape du Tour 2026 (Cyclosportive)\", \"Pouvoir faire une sortie de 4h\"...)"
        default_objectif = "Faire la meilleure performance possible à ma prochaine cyclosportive"
    else:
        label_objectif = "Objectif (Exemples : \"Faire moins de 40min au 10km\", \"Pouvoir courir 1h sans m'arrêter\", \"Faire un marathon en moins de 3h30\"...)"
        default_objectif = "Faire un semi-marathon en moins d'1h30"

    objectif = st.text_input(label_objectif, default_objectif)

    generer = st.button("⚡ GÉNÉRER LA STRUCTURE DU PLAN", type="primary", use_container_width=True)

else:
    st.info("💡 Pour générer votre plan d'entraînement sur-mesure, vous devez débloquer l'accès.")
    
    st.markdown("""
    **Ce que vous obtenez (19€) :**
    * 🎯 Un plan ultra-personnalisé de 4 à 52 semaines généré par IA.
    * ⏱️ Une adaptation parfaite à vos disponibilités et votre niveau.
    * 🍎 Des conseils nutritionnels précis pour chaque séance.
    * 📥 Un fichier PDF complet de votre programme prêt à être téléchargé.
    """)
    
    # REMPLACE CETTE URL PAR TON VRAI LIEN DE PAIEMENT STRIPE QUAND TU ES PRET
    LIEN_STRIPE = "https://buy.stripe.com/TON_LIEN_STRIPE_ICI" 
    
    st.link_button("💳 DÉBLOQUER MON PLAN (19€) - Paiement Sécurisé", LIEN_STRIPE, type="primary", use_container_width=True)
    st.caption("🔒 Paiement 100% sécurisé via Stripe. Vous serez redirigé automatiquement ici après le paiement.")
    
    generer = False

# ==========================================
# 4. LOGIQUE MÉTIER & GÉNÉRATION PDF
# ==========================================

if generer:
    client = OpenAI(api_key=MA_CLE_SECRETE)
    
    # --- DÉFINITION DES ZONES SELON LE SPORT ET LE MODE ---
    if sport_principal == "Cyclisme":
        if avec_capteur:
            z1 = [0, int(ftp * 0.55)]
            z2 = [int(ftp * 0.56), int(ftp * 0.75)]
            z3 = [int(ftp * 0.76), int(ftp * 0.90)]
            z4 = [int(ftp * 0.91), int(ftp * 1.05)]
            z5 = [int(ftp * 1.06), int(ftp * 1.20)]
            z6 = [int(ftp * 1.21), int(ftp * 1.50)]
            z7 = [int(ftp * 1.51), 9999]

            html_zones = textwrap.dedent(f"""
                <table class="zone-table">
                <tr><th>Zone</th><th>Nom</th><th>Vos Watts</th><th>Durée Tenable</th><th>Sensations</th></tr>
                <tr class="z1"><td><strong>Z1</strong></td><td>Récup Active</td><td>< {z1[1]} W</td><td>sans limite</td><td>Très facile ; respiration uniquement par le nez sans souci.</td></tr>
                <tr class="z2"><td><strong>Z2</strong></td><td>Endurance</td><td>{z2[0]} - {z2[1]} W</td><td>3h à 10h selon le niveau</td><td>Aisance respiratoire, tu peux tenir une discussion facilement.</td></tr>
                <tr class="z3"><td><strong>Z3</strong></td><td>Tempo</td><td>{z3[0]} - {z3[1]} W</td><td>45min à 3h selon le niveau</td><td>Respiration clairement marqué, les phrases doivent être courtes.</td></tr>
                <tr class="z4"><td><strong>Z4</strong></td><td>Seuil</td><td>{z4[0]} - {z4[1]} W</td><td>20min à 60min</td><td>Conversation impossible, juste "oui" ou "non", brûlure musculaire.</td></tr>
                <tr class="z5"><td><strong>Z5</strong></td><td>PMA</td><td>{z5[0]} - {z5[1]} W</td><td>3min à 8min</td><td>Respiration haletante. Compte à rebours mental.</td></tr>
                <tr class="z6"><td><strong>Z6</strong></td><td>Anaérobie</td><td>{z6[0]} - {z6[1]} W</td><td>30sec à 3min</td><td>Effort violent, attaque prolongée, clairement à fond.</td></tr>
                <tr class="z7"><td><strong>Z7</strong></td><td>Sprint</td><td>> {z7[0]} W</td><td>< 5 à 30sec</td><td>Explosivité pure. Sprint très court. Force maximum.</td></tr>
                </table>
            """)
            pdf_zones_text = f"Z1: <{z1[1]}W  |  Z2: {z2[0]}-{z2[1]}W  |  Z3: {z3[0]}-{z3[1]}W  |  Z4: {z4[0]}-{z4[1]}W  |  Z5: {z5[0]}-{z5[1]}W  |  Z6: {z6[0]}-{z6[1]}W"
            prompt_style_instruction = "UTILISE LA NOTATION 'Z' (Z1, Z2, Z3...). EXEMPLE : '3 séries de (10 min en Z3 puis 5 min de récup en Z1)'."
            html_lexique = "<div class='lexique'><strong>📚 GLOSSAIRE:</strong> FTP: Puissance max sur 1h | PMA: Puissance Max Aérobie (5 min) | RPM: Cadence.</div>"

        else:
            html_zones = textwrap.dedent("""
                <table class="zone-table">
                <tr><th>Zone</th><th>Intensité</th><th>RPE (1-10)</th><th>Durée Tenable</th><th>Sensations</th></tr>
                <tr class="z1"><td><strong>i1</strong></td><td>Récupération</td><td>1-2</td><td>sans limite</td><td>Très facile ; respiration uniquement par le nez sans souci.</td></tr>
                <tr class="z2"><td><strong>i2</strong></td><td>Endurance</td><td>3-4</td><td>3h à 10h</td><td>Aisance respiratoire, tu peux tenir une discussion facilement.</td></tr>
                <tr class="z3"><td><strong>i3</strong></td><td>Tempo</td><td>5-6</td><td>45min à 3h</td><td>Respiration clairement marqué, les phrases doivent être courtes.</td></tr>
                <tr class="z4"><td><strong>i4</strong></td><td>Seuil</td><td>7-8</td><td>20min à 60min</td><td>Conversation impossible, juste "oui" ou "non".</td></tr>
                <tr class="z5"><td><strong>i5</strong></td><td>PMA</td><td>9</td><td>3min à 8min</td><td>Respiration haletante. Compte à rebours mental.</td></tr>
                <tr class="z6"><td><strong>i6</strong></td><td>Anaérobie</td><td>9.5</td><td>30sec à 3min</td><td>Effort violent, attaque prolongée, clairement à fond.</td></tr>
                <tr class="z7"><td><strong>i7</strong></td><td>Sprint</td><td>10</td><td>< 30 sec</td><td>Explosivité pure. Sprint très court. Force maximum.</td></tr>
                </table>
            """)
            pdf_zones_text = "i1: RPE 1-2 | i2: RPE 3-4 | i3: RPE 5-6 | i4: RPE 7-8 | i5: RPE 9 | i6: RPE 9.5 | i7: RPE 10"
            prompt_style_instruction = "INTERDICTION D'UTILISER 'Z'. UTILISE UNIQUEMENT 'i' (i1 à i7). EXEMPLE : '3 séries de (10 min en i3 puis 5 min de récup en i1)'."
            html_lexique = "<div class='lexique'><strong>📚 GLOSSAIRE:</strong> RPE: Ressenti de l'effort (1=Facile, 10=Max) | FC: Fréquence Cardiaque | RPM: Cadence.</div>"

    else:
        if avec_vma:
            z1 = f"<{round(vma*0.65, 1)}"
            z2 = f"{round(vma*0.65, 1)} - {round(vma*0.75, 1)}"
            z3 = f"{round(vma*0.75, 1)} - {round(vma*0.85, 1)}"
            z4 = f"{round(vma*0.85, 1)} - {round(vma*0.90, 1)}"
            z5 = f"{round(vma*0.90, 1)} - {round(vma*1.0, 1)}"
            z6 = f"{round(vma*1.0, 1)} - {round(vma*1.10, 1)}"
            z7 = f">{round(vma*1.10, 1)}"

            html_zones = textwrap.dedent(f"""
                <table class="zone-table">
                <tr><th>Zone</th><th>Nom</th><th>% VMA</th><th>Vitesse (km/h)</th><th>Sensations</th></tr>
                <tr class="z1"><td><strong>Z1</strong></td><td>Récupération</td><td>< 65%</td><td>{z1}</td><td>Trot très lent, aucune fatigue, respiration nasale aisée.</td></tr>
                <tr class="z2"><td><strong>Z2</strong></td><td>Endurance Fond.</td><td>65-75%</td><td>{z2}</td><td>Aisance respiratoire totale, conversation parfaitement fluide.</td></tr>
                <tr class="z3"><td><strong>Z3</strong></td><td>Tempo / Marathon</td><td>75-85%</td><td>{z3}</td><td>Respiration plus rythmée, phrases courtes possibles.</td></tr>
                <tr class="z4"><td><strong>Z4</strong></td><td>Seuil Anaérobie</td><td>85-90%</td><td>{z4}</td><td>Conversation impossible, effort difficile mais constant.</td></tr>
                <tr class="z5"><td><strong>Z5</strong></td><td>VMA Longue</td><td>90-100%</td><td>{z5}</td><td>Effort très dur, hyperventilation.</td></tr>
                <tr class="z6"><td><strong>Z6</strong></td><td>VMA Courte</td><td>100-110%</td><td>{z6}</td><td>Allure maximale sur des fractions courtes.</td></tr>
                <tr class="z7"><td><strong>Z7</strong></td><td>Sprint</td><td>> 110%</td><td>{z7}</td><td>Sprint pur, vitesse maximale sur quelques secondes.</td></tr>
                </table>
            """)
            pdf_zones_text = f"Z1: {z1}km/h | Z2: {z2}km/h | Z3: {z3}km/h | Z4: {z4}km/h | Z5: {z5}km/h (VMA)"
            prompt_style_instruction = "UTILISE LES % VMA ET ALLURES CIBLES. EXEMPLE : '3 séries de (3 min à 90% VMA puis 1 min30 de trot lent)'."
            html_lexique = "<div class='lexique'><strong>📚 GLOSSAIRE:</strong> VMA: Vitesse Max Aérobie (effort de 6 min) | EF: Endurance Fondamentale (Z2) | Trot: Allure très lente.</div>"

        else:
            html_zones = textwrap.dedent("""
                <table class="zone-table">
                <tr><th>Niveau</th><th>Intensité</th><th>RPE (1-10)</th><th>Durée Tenable</th><th>Sensations</th></tr>
                <tr class="z1"><td><strong>i1</strong></td><td>Récupération</td><td>1-2</td><td>sans limite</td><td>Trot très lent, aucune fatigue.</td></tr>
                <tr class="z2"><td><strong>i2</strong></td><td>Endurance Fond.</td><td>3-4</td><td>plusieurs heures</td><td>Aisance respiratoire totale, conversation fluide.</td></tr>
                <tr class="z3"><td><strong>i3</strong></td><td>Tempo</td><td>5-6</td><td>1h à 3h</td><td>Respiration rythmée, phrases courtes.</td></tr>
                <tr class="z4"><td><strong>i4</strong></td><td>Seuil Anaérobie</td><td>7-8</td><td>30min à 1h</td><td>Effort confortablement difficile, mots isolés.</td></tr>
                <tr class="z5"><td><strong>i5</strong></td><td>Fractionné Long</td><td>9</td><td>3min à 6min</td><td>Très difficile. Souffle court, hyperventilation.</td></tr>
                <tr class="z6"><td><strong>i6</strong></td><td>Fractionné Court</td><td>9.5</td><td>30sec à 2min</td><td>Effort quasi-maximal.</td></tr>
                <tr class="z7"><td><strong>i7</strong></td><td>Sprint</td><td>10</td><td>< 20 sec</td><td>Vitesse maximale absolue.</td></tr>
                </table>
            """)
            pdf_zones_text = "i1: Trot lent | i2: Endurance (RPE 3-4) | i3: Tempo (RPE 5-6) | i4: Seuil (RPE 7-8) | i5: Fractionné (RPE 9) | i6: Frac. court | i7: Sprint"
            prompt_style_instruction = "INTERDICTION D'UTILISER 'Z'. UTILISE UNIQUEMENT LES NIVEAUX 'i' (i1 à i7) OU L'ÉCHELLE RPE. EXEMPLE : '3 séries de (3 min à i4 puis 1 min30 de trot en i1)'."
            html_lexique = "<div class='lexique'><strong>📚 GLOSSAIRE:</strong> RPE: Ressenti de l'effort (1=Facile, 10=Sprint max) | EF: Endurance Fondamentale (i2).</div>"

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
            nb_semaines_bloc = end_w - start_w + 1
            
            status.write(f"Rédaction du bloc semaines {start_w} à {end_w}...")
            
            prompt = f"""
            Tu es un coach expert en {sport_principal} ({sport}).
            Athlète : {sexe}, Niveau : {niveau}.
            Disponibilités EXACTES de l'athlète : {dispos_str}.
            Objectif : {objectif}.
            
            MISSION : Génère un plan pour les semaines {start_w} à {end_w}.
            
            RÈGLES DE REDACTION :
            1. DÉTERMINISME ABSOLU : Temps, intensité et répétitions précis.
            2. FORMAT : La liste 'details' contient des phrases (Echauffement, séries, Retour au calme).
            3. NOMENCLATURE : {prompt_style_instruction}
            4. REPOS : Génère une séance pour chaque jour dispo. Si repos nécessaire, titre "Repos" avec nutrition "Hydratation".
            
            JSON ATTENDU :
            {{
              "weeks": [
                {{
                  "numero": {start_w},
                  "seances": [
                     {{
                       "jour": "Mardi", 
                       "titre": "Endurance", 
                       "duree_totale": "1h30",
                       "nutrition": "60g glucides/h",
                       "details": ["Echauffement...", "Corps de séance...", "Retour au calme..."]
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
        
        # --- AFFICHAGE WEB ---
        st.divider()
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

        # ==========================================
        # 5. GÉNÉRATION DU PDF PRO
        # ==========================================
        class PDF(FPDF):
            def header(self):
                # Bandeau rouge haut
                self.set_fill_color(255, 75, 75)
                self.rect(0, 0, 210, 18, 'F')
                self.set_y(6)
                self.set_font('Arial', 'B', 14)
                self.set_text_color(255, 255, 255)
                self.cell(0, 6, "ENDURIA - PLAN D'ENTRAINEMENT SUR-MESURE", 0, 1, 'C')
                self.ln(10)

            def footer(self):
                # Numéro de page en bas
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

            def clean(self, txt):
                if not txt: return ""
                # Supprime les emojis qui font planter le PDF
                txt = str(txt).replace("⏱️", "").replace("🍎", "").replace("⚡", "").replace("🎯", "")
                return txt.encode('latin-1', 'replace').decode('latin-1')

        pdf = PDF()
        pdf.add_page()
        
        # --- En-tête Titre ---
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 10, pdf.clean(f"OBJECTIF : {objectif.upper()}"), 0, 1, 'C')
        
        # Sous-titre
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(100, 100, 100)
        if sport_principal == "Cyclisme":
            infos = f"FTP : {ftp}W" if avec_capteur else "Sensations (RPE)"
        else:
            infos = f"VMA : {vma} km/h" if avec_vma else "Sensations (RPE)"
        pdf.cell(0, 6, pdf.clean(f"{sport_principal} | {sport} | {infos}"), 0, 1, 'C')
        pdf.ln(8)
        
        # --- Bloc Zones ---
        pdf.set_fill_color(240, 240, 240)
        pdf.set_draw_color(200, 200, 200)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, "  VOS ZONES DE TRAVAIL", border=1, ln=1, fill=True)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 6, pdf.clean(pdf_zones_text), border=1)
        pdf.ln(8)
        
        # --- Boucle des Semaines ---
        for week in full_plan['weeks']:
            if pdf.get_y() > 250: pdf.add_page()
            
            num_pdf = week.get('numero', '?')
            
            # Titre Semaine (Gris foncé)
            pdf.set_fill_color(50, 50, 50)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, pdf.clean(f"  SEMAINE {num_pdf}"), 0, 1, 'L', fill=True)
            pdf.ln(3)
            
            for seance in week.get('seances', []):
                if pdf.get_y() > 240: pdf.add_page()
                
                # En-tête de la séance (Gris clair)
                pdf.set_fill_color(245, 245, 245)
                pdf.set_font("Arial", "B", 10)
                
                jour_txt = pdf.clean(seance.get('jour', '').upper())
                duree_txt = pdf.clean(seance.get('duree_totale', ''))
                titre_txt = pdf.clean(seance.get('titre', ''))
                
                # Jour
                pdf.set_text_color(255, 75, 75) # Rouge
                pdf.cell(30, 8, f" {jour_txt} ", 0, 0, 'L', fill=True)
                
                # Titre + Durée
                pdf.set_text_color(40, 40, 40)
                pdf.cell(0, 8, f"{titre_txt}  |  Durée : {duree_txt}", 0, 1, 'L', fill=True)
                
                # Nutrition
                pdf.set_text_color(230, 120, 0) # Orange
                pdf.set_font("Arial", "B", 9)
                pdf.cell(30, 6, "", 0, 0) # Espace pour aligner
                pdf.cell(0, 6, pdf.clean(f"Nutrition : {seance.get('nutrition', '')}"), 0, 1)
                
                # Détails
                pdf.set_text_color(60, 60, 60)
                pdf.set_font("Arial", "", 9)
                details_pdf = seance.get('details', ["Non spécifié"])
                
                if isinstance(details_pdf, list):
                    for step in details_pdf:
                        pdf.set_x(40) # Aligner avec le texte
                        pdf.multi_cell(0, 5, pdf.clean(f"- {step}"))
                else:
                    pdf.set_x(40)
                    pdf.multi_cell(0, 5, pdf.clean(details_pdf))
                    
                pdf.ln(4)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        st.warning("⚠️ ATTENTION : Téléchargez votre PDF maintenant. Si vous fermez ou rafraîchissez cette page, votre plan sera perdu.")
        st.download_button(
            label="📥 TÉLÉCHARGER LE PDF DU PLAN",
            data=pdf_bytes,
            file_name=f"EndurIA_Plan_{sport_principal}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")