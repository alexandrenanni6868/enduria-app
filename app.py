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
    
    /* Ajustements Mobile */
    .stNumberInput {margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("⚡ ENDURIA")
st.markdown("Générez votre plan d'entraînement sur-mesure optimisé par l'IA.")
st.divider()

# ==========================================
# 2. CONFIGURATION SUR LA PAGE PRINCIPALE (MOBILE FIRST)
# ==========================================

st.header("👤 1. Votre Profil")

sport_principal = st.radio("Quel est votre sport ?", ["Cyclisme", "Course à pied"], horizontal=True)

if sport_principal == "Cyclisme":
    sport = st.selectbox("Discipline", ["Cyclisme sur route", "Gravel", "VTT XC", "Cyclocross"])
    sexe = st.radio("Sexe", ["Homme", "Femme"], horizontal=True)
    
    st.markdown("**⚡ Profil de Puissance**")
    avec_capteur = st.toggle("J'ai un Capteur de Puissance", value=True)
    
    if avec_capteur:
        cols_p = st.columns(2)
        with cols_p[0]:
            ftp = st.number_input("FTP (Watts)", value=250, step=5)
        with cols_p[1]:
            poids = st.number_input("Poids (kg)", value=70, step=1)
        wkg = round(ftp/poids, 2)
        st.info(f"📊 Rapport Poids/Puissance à FTP : **{wkg} W/kg**")
    else:
        ftp = None
        st.info("💡 Le plan sera basé sur vos sensations (Échelle RPE 1-10).")
        
else:  
    sport = st.selectbox("Discipline", ["Course sur route", "Trail", "Ultra trail"])
    sexe = st.radio("Sexe", ["Homme", "Femme"], horizontal=True)
    
    st.markdown("**🏃 Profil VMA**")
    avec_vma = st.toggle("Je connais ma VMA", value=True)
    
    if avec_vma:
        vma = st.number_input("VMA (Vitesse Maximale Aérobie en km/h)", value=15.0, step=0.5)
    else:
        vma = None
        st.info("💡 Le plan sera basé sur les niveaux d'intensité (i1 à i7) et vos sensations (RPE 1-10).")

niveau = st.selectbox("Niveau d'entraînement actuel", [
    "Moins de 2h par semaine", 
    "Entre 3h et 5h par semaine", 
    "Entre 5h et 10h par semaine", 
    "Entre 10h et 15h par semaine", 
    "Entre 15h et 20h par semaine"
])

st.divider()

st.header("📅 2. Vos Disponibilités")
st.caption("Indiquez le nombre d'heures où vous êtes disponible chaque jour.")

jours_dispos = {}
cols_d1, cols_d2 = st.columns(2)
with cols_d1:
    jours_dispos["Lundi"] = st.number_input("Lundi (h)", 0.0, 10.0, 0.0, 0.5)
    jours_dispos["Mardi"] = st.number_input("Mardi (h)", 0.0, 10.0, 1.0, 0.5)
    jours_dispos["Mercredi"] = st.number_input("Mercredi (h)", 0.0, 10.0, 0.0, 0.5)
    jours_dispos["Jeudi"] = st.number_input("Jeudi (h)", 0.0, 10.0, 1.0, 0.5)
with cols_d2:
    jours_dispos["Vendredi"] = st.number_input("Vendredi (h)", 0.0, 10.0, 0.0, 0.5)
    jours_dispos["Samedi"] = st.number_input("Samedi (h)", 0.0, 10.0, 2.0, 0.5)
    jours_dispos["Dimanche"] = st.number_input("Dimanche (h)", 0.0, 10.0, 2.0, 0.5)

volume_dispo_total = sum(jours_dispos.values())
st.success(f"**Total : {volume_dispo_total}h / semaine**")

st.divider()

# ==========================================
# 3. OBJECTIF & PAIEMENT STRIPE
# ==========================================

st.header("🎯 3. Votre Objectif")
duree_plan = st.slider("Durée du plan souhaitée (semaines)", 4, 52, 6)

if sport_principal == "Cyclisme":
    default_objectif = "Faire la meilleure performance possible à ma prochaine cyclosportive"
else:
    default_objectif = "Faire un semi-marathon en moins d'1h30"

objectif = st.text_input("Détaillez votre objectif :", default_objectif)

st.divider()

TOKEN_SECRET = "PROCOACH2026SECURE" 
parametres_url = st.query_params
a_paye = parametres_url.get("token") == TOKEN_SECRET

if a_paye:
    st.success("✅ Accès débloqué ! Vous pouvez lancer la génération.")
    generer = st.button("⚡ GÉNÉRER MON PLAN SUR-MESURE", type="primary", use_container_width=True)

else:
    st.info("💡 Votre profil est configuré. Débloquez l'accès pour générer votre plan d'entraînement.")
    st.markdown("""
    **Ce que vous obtenez (4,99 €) :**
    * 🎯 Un plan ultra-personnalisé généré par IA.
    * ⏱️ Une adaptation parfaite à vos disponibilités.
    * 🍎 Des conseils nutritionnels par séance.
    * 📥 Votre programme complet en PDF haute qualité.
    """)
    
    # RAPPEL : REMPLACE PAR TON VRAI LIEN STRIPE ICI 👇
    LIEN_STRIPE = "https://buy.stripe.com/TON_LIEN_STRIPE_ICI" 
    
    st.link_button("💳 DÉBLOQUER MON PLAN (4,99 €) - Paiement Sécurisé", LIEN_STRIPE, type="primary", use_container_width=True)
    st.caption("🔒 Paiement 100% sécurisé via Stripe.")
    generer = False

# ==========================================
# 4. LOGIQUE MÉTIER & DONNÉES ZONES/LEXIQUE
# ==========================================

if generer:
    client = OpenAI(api_key=MA_CLE_SECRETE)
    
    # --- PRÉPARATION DES DONNÉES (POUR PDF) ---
    if sport_principal == "Cyclisme":
        if avec_capteur:
            z1 = [0, int(ftp * 0.55)]; z2 = [int(ftp * 0.56), int(ftp * 0.75)]
            z3 = [int(ftp * 0.76), int(ftp * 0.90)]; z4 = [int(ftp * 0.91), int(ftp * 1.05)]
            z5 = [int(ftp * 1.06), int(ftp * 1.20)]; z6 = [int(ftp * 1.21), int(ftp * 1.50)]
            z7 = [int(ftp * 1.51), 9999]

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
            z1 = f"<{round(vma*0.65, 1)} km/h"; z2 = f"{round(vma*0.65, 1)} - {round(vma*0.75, 1)} km/h"
            z3 = f"{round(vma*0.75, 1)} - {round(vma*0.85, 1)} km/h"; z4 = f"{round(vma*0.85, 1)} - {round(vma*0.90, 1)} km/h"
            z5 = f"{round(vma*0.90, 1)} - {round(vma*1.0, 1)} km/h"; z6 = f"{round(vma*1.0, 1)} - {round(vma*1.10, 1)} km/h"
            z7 = f">{round(vma*1.10, 1)} km/h"

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

    # --- APPEL OPENAI ---
    dispos_str = ", ".join([f"{j}: {h}h" for j, h in jours_dispos.items() if h > 0])
    full_plan = {"titre": f"Prépa {objectif}", "weeks": []}
    taille_bloc = 4 
    nombre_blocs = math.ceil(duree_plan / taille_bloc)
    
    st.divider()
    progress_bar = st.progress(0)
    status = st.status("🧠 Analyse en cours et rédaction de votre plan...", expanded=True)
    
    try:
        for i in range(nombre_blocs):
            start_w = i * taille_bloc + 1
            end_w = min((i + 1) * taille_bloc, duree_plan)
            
            status.write(f"Rédaction des semaines {start_w} à {end_w}...")
            
            # 🚨 CHANGEMENT ICI : Le prompt force la nomenclature du repos
            prompt = f"""
            Tu es un coach expert en {sport_principal} ({sport}).
            Athlète : {sexe}, Niveau : {niveau}.
            Disponibilités EXACTES : {dispos_str}. Objectif : {objectif}.
            
            MISSION : Génère un plan pour les semaines {start_w} à {end_w}.
            1. DÉTERMINISME ABSOLU : Temps, intensité et répétitions précis.
            2. FORMAT : La liste 'details' contient des phrases.
            3. NOMENCLATURE : {prompt_style_instruction}
            4. REPOS : Si un jour est un jour de repos, mets "titre": "Repos", "duree_totale": "-", "nutrition": "Hydratation optimale", et "details": ["Profitez de cette journée pour récupérer."].
            
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
        # 5. GÉNÉRATION DU PDF PRO
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
        
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 10, pdf.clean(f"OBJECTIF : {objectif.upper()}"), 0, 1, 'C')
        
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(100, 100, 100)
        infos = f"FTP : {ftp}W" if (sport_principal=="Cyclisme" and avec_capteur) else (f"VMA : {vma} km/h" if (sport_principal=="Course à pied" and avec_vma) else "Sensations (RPE)")
        pdf.cell(0, 6, pdf.clean(f"{sport_principal} | {sport} | {infos}"), 0, 1, 'C')
        pdf.ln(8)
        
        pdf.set_fill_color(240, 240, 240)
        pdf.set_draw_color(200, 200, 200)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, "  VOS ZONES DE TRAVAIL", border=1, ln=1, fill=True)
        pdf.ln(2)

        for row in data_zones:
            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(250, 250, 250)
            pdf.set_text_color(255, 75, 75)
            pdf.cell(15, 6, pdf.clean(row[0]), border="LTB", align='C', fill=True)
            
            pdf.set_text_color(40, 40, 40)
            info_str = f" {row[1]}   |   {row[2]}   |   {row[3]}"
            pdf.cell(0, 6, pdf.clean(info_str), border="RTB", ln=1, fill=True)
            
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 5, pdf.clean(f"Sensations : {row[4]}"), border="LBR")
            pdf.ln(2)

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
                
                # 🚨 CHANGEMENT ICI : Logique d'affichage pour les jours de repos
                pdf.set_text_color(40, 40, 40)
                if "repos" in titre_txt.lower() or duree_txt == "-":
                    pdf.cell(0, 8, f"{titre_txt}", 0, 1, 'L', fill=True)
                else:
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
        # 6. AFFICHAGE DU RÉSULTAT
        # ==========================================
        st.success("🎉 Votre plan d'entraînement est prêt !")
        st.warning("⚠️ ATTENTION : Téléchargez votre PDF maintenant. Si vous fermez cette page ou actualisez, votre plan sera perdu.")
        
        st.download_button(
            label="📥 TÉLÉCHARGER MON PLAN (PDF)",
            data=pdf_bytes,
            file_name=f"EndurIA_Plan_{sport_principal}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        st.balloons()

    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")