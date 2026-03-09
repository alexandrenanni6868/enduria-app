import streamlit as st
import json
import math
import textwrap
from openai import OpenAI
from fpdf import FPDF

# ==========================================
# 1. CONFIGURATION
# ==========================================
MA_CLE_SECRETE = st.secrets["OPENAI_API_KEY"] # La nouvelle méthode sécurisée

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
# C'est ce code qui doit être dans l'URL de redirection de Stripe : ?token=PROCOACH2026SECURE
TOKEN_SECRET = "PROCOACH2026SECURE" 

parametres_url = st.query_params
a_paye = parametres_url.get("token") == TOKEN_SECRET

if a_paye:
    st.success("✅ Accès débloqué ! Configurez votre objectif ci-dessous pour générer votre plan.")
    
    # Adaptation du texte d'objectif selon le sport
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
    
    # REMPLACE CETTE URL PAR TON VRAI LIEN DE PAIEMENT STRIPE
    LIEN_STRIPE = "https://buy.stripe.com/TON_LIEN_STRIPE_ICI" 
    
    st.link_button("💳 DÉBLOQUER MON PLAN (19€) - Paiement Sécurisé", LIEN_STRIPE, type="primary", use_container_width=True)
    st.caption("🔒 Paiement 100% sécurisé via Stripe. Vous serez redirigé automatiquement ici après le paiement.")
    
    # On empêche l'exécution de la suite
    generer = False


# ==========================================
# 4. LOGIQUE MÉTIER
# ==========================================

if generer:
    if "sk-" not in MA_CLE_SECRETE:
        st.error("⚠️ Erreur : Clé API manquante.")
    else:
        client = OpenAI(api_key=MA_CLE_SECRETE)
        
        # ---------------------------------------------------------
        # A. DÉFINITION DES ZONES SELON LE SPORT ET LE MODE
        # ---------------------------------------------------------
        if sport_principal == "Cyclisme":
            if avec_capteur:
                # --- CYCLISME : CAPTEUR (Z) ---
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
                    <tr class="z1"><td><strong>Z1</strong></td><td>Récup Active</td><td>< {z1[1]} W</td><td>sans limite</td><td>Très facile ; respiration uniquement par le nez sans souci, tu peux parler en phrase longue sans souci, jambes légères.</td></tr>
                    <tr class="z2"><td><strong>Z2</strong></td><td>Endurance</td><td>{z2[0]} - {z2[1]} W</td><td>3h à 10h selon le niveau</td><td>Aisance respiratoire, tu peux tenir une discussion facilement, effort facile mais concentré.</td></tr>
                    <tr class="z3"><td><strong>Z3</strong></td><td>Tempo</td><td>{z3[0]} - {z3[1]} W</td><td>45min à 3h selon le niveau</td><td>Respiration clairement marqué, les phrases doivent être courtes, tu sens les jambes travailler. Exemple : ascension d'un long col.</td></tr>
                    <tr class="z4"><td><strong>Z4</strong></td><td>Seuil</td><td>{z4[0]} - {z4[1]} W</td><td>20min à 60min</td><td>Conversation impossible, juste "oui" ou "non", brûlure musculaire mais pas à fond. Exemple : col court. </td></tr>
                    <tr class="z5"><td><strong>Z5</strong></td><td>PMA</td><td>{z5[0]} - {z5[1]} W</td><td>3min à 8min</td><td>Respiration haletante. Compte à rebours mental. Exemple : bosse à bloc en course </td></tr>
                    <tr class="z6"><td><strong>Z6</strong></td><td>Anaérobie</td><td>{z6[0]} - {z6[1]} W</td><td>30sec à 3min</td><td>Effort violent, attaque prolongée, clairement à fond sur plus ou moins 1 minute.</td></tr>
                    <tr class="z7"><td><strong>Z7</strong></td><td>Sprint</td><td>> {z7[0]} W</td><td>< 5 à 30sec</td><td>Explosivité pure. Sprint très court. Force maximum sur durée extrêmement courte.</td></tr>
                    </table>
                """)
                pdf_zones_text = f"Z1: <{z1[1]}W | Z2: {z2[0]}-{z2[1]}W | Z3: {z3[0]}-{z3[1]}W | Z4: {z4[0]}-{z4[1]}W | Z5: {z5[0]}-{z5[1]}W | Z6: {z6[0]}-{z6[1]}W"
                prompt_style_instruction = "UTILISE LA NOTATION 'Z' (Z1, Z2, Z3...). EXEMPLE : '3 séries de (10 min en Z3 puis 5 min de récup en Z1)'."
                
                html_lexique = textwrap.dedent("""
                    <div class="lexique">
                    <strong>📚 GLOSSAIRE CYCLISME :</strong><br>
                    <strong>FTP</strong> : Puissance maximale tenable sur 1 heure.<br>
                    <strong>PMA</strong> : Puissance Maximale Aérobie (effort max de 5 min).<br>
                    <strong>RPM</strong> : Tours de pédale par minute (Cadence).<br>
                    </div>
                """)

            else:
                # --- CYCLISME : SANS CAPTEUR (i) ---
                html_zones = textwrap.dedent("""
                    <table class="zone-table">
                    <tr><th>Zone</th><th>Intensité</th><th>RPE (1-10)</th><th>Durée Tenable</th><th>Sensations</th></tr>
                    <tr class="z1"><td><strong>i1</strong></td><td>Récupération</td><td>1-2</td><td>sans limite</td><td>Très facile ; respiration uniquement par le nez sans souci, tu peux parler en phrase longue sans souci, jambes légères.</td></tr>
                    <tr class="z2"><td><strong>i2</strong></td><td>Endurance</td><td>3-4</td><td>3h à 10h</td><td>Aisance respiratoire, tu peux tenir une discussion facilement, effort facile mais concentré.</td></tr>
                    <tr class="z3"><td><strong>i3</strong></td><td>Tempo</td><td>5-6</td><td>45min à 3h</td><td>Respiration clairement marqué, les phrases doivent être courtes, tu sens les jambes travailler. Exemple : ascension d'un long col.</td></tr>
                    <tr class="z4"><td><strong>i4</strong></td><td>Seuil</td><td>7-8</td><td>20min à 60min</td><td>Conversation impossible, juste "oui" ou "non", brûlure musculaire mais pas à fond. Exemple : col court.</td></tr>
                    <tr class="z5"><td><strong>i5</strong></td><td>PMA</td><td>9</td><td>3min à 8min</td><td>Respiration haletante. Compte à rebours mental. Exemple : bosse à bloc en course.</td></tr>
                    <tr class="z6"><td><strong>i6</strong></td><td>Anaérobie</td><td>9.5</td><td>30sec à 3min</td><td>Effort violent, attaque prolongée, clairement à fond sur plus ou moins 1 minute.</td></tr>
                    <tr class="z7"><td><strong>i7</strong></td><td>Sprint</td><td>10</td><td>< 30 sec</td><td>Explosivité pure. Sprint très court. Force maximum sur durée extrêmement courte.</td></tr>
                    </table>
                """)
                pdf_zones_text = "i1: RPE 1-2 | i2: RPE 3-4 | i3: RPE 5-6 | i4: RPE 7-8 | i5: RPE 9 | i6: RPE 9.5 | i7: RPE 10"
                prompt_style_instruction = "INTERDICTION D'UTILISER 'Z'. UTILISE UNIQUEMENT 'i' (i1 à i7). EXEMPLE : '3 séries de (10 min en i3 puis 5 min de récup en i1)'."
                
                html_lexique = textwrap.dedent("""
                    <div class="lexique">
                    <strong>📚 GLOSSAIRE CYCLISME :</strong><br>
                    <strong>RPE</strong> : Ressenti de l'effort (1 = Facile, 10 = Extrême).<br>
                    <strong>FC</strong> : Fréquence Cardiaque (BPM).<br>
                    <strong>RPM</strong> : Cadence de pédalage.<br>
                    </div>
                """)

        else:
            # ---------------------------------------------------------
            # B. COURSE À PIED
            # ---------------------------------------------------------
            if avec_vma:
                # --- COURSE : VMA ---
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
                    <tr class="z2"><td><strong>Z2</strong></td><td>Endurance Fondamentale</td><td>65-75%</td><td>{z2}</td><td>Aisance respiratoire totale, conversation parfaitement fluide.</td></tr>
                    <tr class="z3"><td><strong>Z3</strong></td><td>Tempo / Allure Marathon</td><td>75-85%</td><td>{z3}</td><td>Respiration plus rythmée, phrases courtes possibles, foulée dynamique.</td></tr>
                    <tr class="z4"><td><strong>Z4</strong></td><td>Seuil Anaérobie</td><td>85-90%</td><td>{z4}</td><td>Allure semi-marathon/10km. Conversation impossible (mots isolés), effort difficile mais constant.</td></tr>
                    <tr class="z5"><td><strong>Z5</strong></td><td>VMA Longue</td><td>90-100%</td><td>{z5}</td><td>Effort très dur, hyperventilation, tenable sur des fractions de 3 à 6 minutes.</td></tr>
                    <tr class="z6"><td><strong>Z6</strong></td><td>VMA Courte</td><td>100-110%</td><td>{z6}</td><td>Allure maximale sur des fractions courtes (30s à 1min30).</td></tr>
                    <tr class="z7"><td><strong>Z7</strong></td><td>Sprint</td><td>> 110%</td><td>{z7}</td><td>Sprint pur, vitesse maximale sur quelques secondes.</td></tr>
                    </table>
                """)
                pdf_zones_text = f"Z1: {z1}km/h | Z2: {z2}km/h | Z3: {z3}km/h | Z4: {z4}km/h | Z5: {z5}km/h (VMA)"
                prompt_style_instruction = "UTILISE LES % VMA ET ALLURES CIBLES. EXEMPLE : '3 séries de (3 min à 90% VMA puis 1 min30 de trot lent)'."
                
                html_lexique = textwrap.dedent("""
                    <div class="lexique">
                    <strong>📚 GLOSSAIRE COURSE À PIED :</strong><br>
                    <strong>VMA</strong> : Vitesse Maximale Aérobie. Allure tenable sur environ 6 minutes.<br>
                    <strong>EF</strong> : Endurance Fondamentale (Z2). L'allure de base de la plupart des footings.<br>
                    <strong>Trot / Récup</strong> : Allure très lente pour récupérer entre deux efforts intenses.<br>
                    </div>
                """)

            else:
                # --- COURSE : SANS VMA (i1 à i7) ---
                html_zones = textwrap.dedent("""
                    <table class="zone-table">
                    <tr><th>Niveau</th><th>Intensité</th><th>RPE (1-10)</th><th>Durée Tenable</th><th>Sensations (Test de la parole)</th></tr>
                    <tr class="z1"><td><strong>i1</strong></td><td>Récupération</td><td>1-2</td><td>sans limite</td><td>Trot très lent, aucune fatigue, on peut chanter ou parler sans problème.</td></tr>
                    <tr class="z2"><td><strong>i2</strong></td><td>Endurance Fondamentale</td><td>3-4</td><td>plusieurs heures</td><td>Aisance respiratoire totale, conversation fluide avec d'autres coureurs.</td></tr>
                    <tr class="z3"><td><strong>i3</strong></td><td>Tempo / Allure modérée</td><td>5-6</td><td>1h à 3h</td><td>Respiration rythmée, on ne peut dire que des phrases courtes.</td></tr>
                    <tr class="z4"><td><strong>i4</strong></td><td>Seuil Anaérobie</td><td>7-8</td><td>30min à 1h</td><td>Effort "confortablement difficile". On ne dit que des mots isolés ("Oui", "Non").</td></tr>
                    <tr class="z5"><td><strong>i5</strong></td><td>Fractionné Long</td><td>9</td><td>3min à 6min</td><td>Très difficile. Souffle court, hyperventilation.</td></tr>
                    <tr class="z6"><td><strong>i6</strong></td><td>Fractionné Court</td><td>9.5</td><td>30sec à 2min</td><td>Effort quasi-maximal.</td></tr>
                    <tr class="z7"><td><strong>i7</strong></td><td>Sprint</td><td>10</td><td>< 20 sec</td><td>Vitesse maximale absolue.</td></tr>
                    </table>
                """)
                pdf_zones_text = "i1: Trot lent | i2: Endurance (RPE 3-4) | i3: Tempo (RPE 5-6) | i4: Seuil (RPE 7-8) | i5: Fractionné (RPE 9) | i6: Fractionné court | i7: Sprint"
                prompt_style_instruction = "INTERDICTION D'UTILISER 'Z'. UTILISE UNIQUEMENT LES NIVEAUX 'i' (i1 à i7) OU L'ÉCHELLE RPE. EXEMPLE : '3 séries de (3 min à i4 puis 1 min30 de trot en i1)'."
                
                html_lexique = textwrap.dedent("""
                    <div class="lexique">
                    <strong>📚 GLOSSAIRE COURSE À PIED :</strong><br>
                    <strong>RPE</strong> : Ressenti de l'effort (1 = Facile, 10 = Sprint max).<br>
                    <strong>Fractionné</strong> : Entraînement alternant périodes d'efforts intenses et récupérations.<br>
                    <strong>EF</strong> : Endurance Fondamentale (i2). L'allure de base.<br>
                    </div>
                """)

        # ---------------------------------------------------------
        # C. GÉNÉRATION DU PLAN VIA OPENAI
        # ---------------------------------------------------------
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
                
                RÈGLES DE REDACTION (TRÈS IMPORTANT - SUIS ÇA À LA LETTRE) :
                1. DÉTERMINISME ABSOLU : 
                   - INTERDIT : "selon envie", "environ", "si possible", "quelques".
                   - OBLIGATOIRE : Temps précis, Intensité précise, nombre de répétitions précis.
                   
                2. FORMAT DES SÉANCES (Liste à puces claire) :
                   - La liste 'details' DOIT contenir plusieurs lignes (strings).
                   - Élément 1 : Toujours l'Échauffement précis (Ex: "Échauffement de 20 minutes en Z1/i1").
                   - Éléments centraux : Les exercices. Écris les séries en une phrase claire (Ex: "3 séries de (4 minutes en Z4 suivies de 2 minutes de récupération en Z1)"). S'il y a plusieurs exercices différents, fais plusieurs lignes.
                   - Dernier élément : Toujours le Retour au calme précis (Ex: "Retour au calme de 10 minutes en Z1/i1").
                
                3. NOMENCLATURE : 
                   {prompt_style_instruction}

                4. GESTION DES JOURS DISPONIBLES ET DU REPOS : 
                   - Tu DOIS IMPÉRATIVEMENT générer un objet séance pour CHAQUE JOUR listé dans les disponibilités ({dispos_str}).
                   - Ce n'est pas parce que l'athlète est disponible qu'il faut s'entraîner dur. Si tu estimes qu'il faut du repos un jour disponible, crée une séance avec pour titre "Repos", "Étirements" ou "Renforcement".
                   - Inclus la durée totale dans la clé `duree_totale`.
                   - Inclus un conseil nutritionnel (ex: "40g glucides/h", "60g glucides/h", ou "0g (Hydratation seule)" pour le repos) dans la clé `nutrition`.
                
                JSON ATTENDU :
                {{
                  "weeks": [
                    {{
                      "numero": {start_w},
                      "seances": [
                         {{
                           "jour": "Mardi", 
                           "titre": "Titre Séance", 
                           "duree_totale": "1h30",
                           "nutrition": "60g glucides/h",
                           "details": [
                             "Échauffement de 20 minutes...", 
                             "Exercice 1 : 3 séries de (10 min en Z3 + 5 min Z1)...", 
                             "Exercice 2 : 15 min en Z2...",
                             "Retour au calme 10 min en Z1..."
                           ]
                         }},
                         {{
                           "jour": "Jeudi", 
                           "titre": "Repos ou Étirements", 
                           "duree_totale": "20 min",
                           "nutrition": "Hydratation",
                           "details": [
                             "Séance de mobilité ou repos complet."
                           ]
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

            # --- PDF ---
            class PDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 9)
                    self.set_text_color(150)
                    self.cell(0, 10, f'PLAN : {str(objectif).upper()}', 0, 1, 'R')
                def clean(self, txt):
                    return txt.encode('latin-1', 'replace').decode('latin-1') if txt else ""

            pdf = PDF()
            pdf.add_page()
            
            pdf.set_font("Arial", "B", 20)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, f"PLAN D'ENTRAINEMENT - {sport_principal.upper()}", 0, 1, 'C')
            
            pdf.set_font("Arial", "", 10)
            
            # Gestion du texte sous-titre selon sport/capteur
            if sport_principal == "Cyclisme":
                infos = f"FTP : {ftp}W" if avec_capteur else "Sans Capteur (Mode i)"
            else:
                infos = f"VMA : {vma} km/h" if avec_vma else "Sans VMA (Mode i/RPE)"
                
            pdf.cell(0, 10, pdf.clean(f"{infos} | {sport} | {sexe}"), 0, 1, 'C')
            pdf.ln(5)
            
            pdf.set_fill_color(245, 245, 245)
            pdf.rect(10, pdf.get_y(), 190, 45, 'FD')
            pdf.set_xy(15, pdf.get_y() + 5)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 5, "ZONES & INDICATIONS :", 0, 1)
            pdf.set_font("Arial", "", 8)
            pdf.multi_cell(180, 4, pdf.clean(pdf_zones_text))
            pdf.ln(2)
            
            # Petit lexique rapide PDF
            if sport_principal == "Cyclisme":
                pdf.multi_cell(180, 4, pdf.clean("RPM: Cadence | FTP: Puissance 1h | PMA: Puissance Max | RPE: Ressenti (1-10)"))
            else:
                pdf.multi_cell(180, 4, pdf.clean("VMA: Vitesse Max Aérobie | EF: Endurance Fondamentale | RPE: Ressenti (1-10)"))
            pdf.ln(15)
            
            for week in full_plan['weeks']:
                if pdf.get_y() > 240: pdf.add_page()
                
                pdf.set_fill_color(50, 50, 50)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Arial", "B", 12)
                
                num_pdf = week.get('numero', '?')
                titre = f"SEMAINE {num_pdf}"
                pdf.cell(0, 8, pdf.clean(titre), 0, 1, 'L', fill=True)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(2)
                
                seances_pdf = week.get('seances', [])
                for seance in seances_pdf:
                    if pdf.get_y() > 250: pdf.add_page()
                    
                    pdf.set_font("Arial", "B", 10)
                    pdf.cell(25, 5, pdf.clean(seance.get('jour', '')), 0, 0)
                    
                    # Titre + Durée
                    titre_duree = f"{pdf.clean(seance.get('titre', ''))} (Durée : {pdf.clean(seance.get('duree_totale', ''))})"
                    pdf.cell(0, 5, titre_duree, 0, 1)
                    
                    # Nutrition
                    pdf.set_font("Arial", "I", 9)
                    pdf.set_text_color(200, 100, 0) # Orange
                    pdf.cell(25, 5, "", 0, 0) # align with title
                    pdf.cell(0, 5, f"Nutrition : {pdf.clean(seance.get('nutrition', ''))}", 0, 1)
                    
                    pdf.set_font("Arial", "", 9)
                    pdf.set_text_color(0, 0, 0) # Black
                    
                    details_pdf = seance.get('details', ["Non spécifié"])
                    if isinstance(details_pdf, list):
                        for step in details_pdf:
                            pdf.cell(5)
                            pdf.multi_cell(0, 4, pdf.clean(f"- {step}"))
                    else:
                        pdf.multi_cell(0, 4, pdf.clean(details_pdf))
                        
                    pdf.ln(2)
                    pdf.set_draw_color(220, 220, 220)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(2)
                pdf.ln(2)

            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            st.download_button(
                label="📥 TÉLÉCHARGER LE PDF",
                data=pdf_bytes,
                file_name=f"Plan_{sport_principal}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")