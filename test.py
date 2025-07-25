import streamlit as st
from datetime import datetime, timedelta, date, time

# Paramètres horaires
heure_debut_travail = time(9, 0)
heure_fin_travail = time(17, 42)

# --- Interface utilisateur (inchangée) ---
col1, col2, col3 = st.columns(3)
with col2:
    try:
        st.image("sfr-logo.png", width=200)
    except FileNotFoundError:
        st.warning("Logo SFR non trouvé.")

st.markdown("<h1 style='text-align: center;'>Calcul des Heures de Récupération - Déplacement Pro</h1>", unsafe_allow_html=True)

temps_trajet = st.selectbox("Temps habituel Maison <> Travail :", ["30 min", "45 min", "60 min", "90 min", "120 min"])
pays = st.selectbox("Choisir le pays de destination :", ["Côte d'Ivoire", "Madagascar", "Maroc", "Portugal", "Sénégal"])

st.markdown("<h3 style='text-align: center;'>--- Trajet Aller ---</h3>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    aller_dep_date = st.date_input("Date départ aller :", date.today())
with col2:
    aller_dep_heure = st.time_input("Heure départ aller :", time(0, 0))
col3, col4 = st.columns(2)
with col3:
    aller_arr_date = st.date_input("Date arrivée aller :", date.today())
with col4:
    aller_arr_heure = st.time_input("Heure arrivée aller :", time(0, 0))

st.markdown("<h3 style='text-align: center;'>--- Trajet Retour ---</h3>", unsafe_allow_html=True)
col5, col6 = st.columns(2)
with col5:
    retour_dep_date = st.date_input("Date départ retour :", date.today() + timedelta(days=1))
with col6:
    retour_dep_heure = st.time_input("Heure départ retour :", time(0, 0))
col7, col8 = st.columns(2)
with col7:
    retour_arr_date = st.date_input("Date arrivée retour :", date.today() + timedelta(days=2))
with col8:
    retour_arr_heure = st.time_input("Heure arrivée retour :", time(0, 0))

# --- Fonctions de calcul ---
def calculer_recup_hors_travail(debut, fin):
    total = timedelta()
    current = debut
    while current < fin:
        jour_suivant = datetime.combine(current.date(), time(0, 0)) + timedelta(days=1)
        tranche_debut = datetime.combine(current.date(), heure_debut_travail)
        tranche_fin = datetime.combine(current.date(), heure_fin_travail)
        if current < tranche_debut:
            fin_periode = min(tranche_debut, fin)
            total += fin_periode - current
            current = fin_periode
        elif current >= tranche_fin:
            fin_periode = min(jour_suivant, fin)
            total += fin_periode - current
            current = fin_periode
        else:
            current = tranche_fin
    return total

def calculer_recup():
    try:
        # La déduction de base est toujours le trajet A/R complet
        trajet_habituel_minutes = int(temps_trajet.split()[0]) * 2
    
        # La liste des pays concernés
        pays_long_courrier = ["Côte d'Ivoire", "Madagascar", "Sénégal"]

        # --- Calcul Aller ---
        date_depart_aller = datetime.combine(aller_dep_date, aller_dep_heure)
        date_arrivee_aller = datetime.combine(aller_arr_date, aller_arr_heure)
        temps_hors_travail_aller = calculer_recup_hors_travail(date_depart_aller, date_arrivee_aller)
        
        # Le calcul pour l'aller : déduction du trajet A/R complet
        deduction_aller = timedelta(minutes=trajet_habituel_minutes)
        recup_aller = temps_hors_travail_aller - deduction_aller

        if date_depart_aller.weekday() >= 5 or date_arrivee_aller.weekday() >= 5:
            recup_aller = (date_arrivee_aller - date_depart_aller) - deduction_aller

        if recup_aller.total_seconds() < 0:
            recup_aller = timedelta(0)

        # --- Calcul Retour (avec la logique conditionnelle) ---
        date_depart_retour = datetime.combine(retour_dep_date, retour_dep_heure)
        date_arrivee_retour = datetime.combine(retour_arr_date, retour_arr_heure)
        
        # La déduction par défaut pour le retour est aussi le trajet A/R complet
        deduction_retour = timedelta(minutes=trajet_habituel_minutes)
        
        # On calcule le trajet simple juste pour la logique de la "fenêtre de trajet"
        trajet_simple = timedelta(minutes=int(temps_trajet.split()[0]))
        
        # Règle 1 : Départ tardif (s'applique à tous les pays)
        heure_limite_retour = datetime.combine(date_depart_retour.date(), heure_fin_travail) + trajet_simple
        if date_depart_retour > heure_limite_retour:
            deduction_retour = timedelta(0)
            
        # --- CORRECTION ---
        # Règle 2 : Arrivée en journée (s'applique UNIQUEMENT aux pays de la liste)
        # Pour ces pays, si l'arrivée est en journée, on compte TOUT le temps comme récupération
        if (pays in pays_long_courrier) and (heure_debut_travail <= date_arrivee_retour.time() < heure_fin_travail):
            # Pas de déduction du trajet habituel
            deduction_retour = timedelta(0)
            # On compte TOUT le temps de voyage comme récupération (même les heures de travail)
            recup_retour = date_arrivee_retour - date_depart_retour
        else:
            # Calcul normal pour les autres cas
            temps_hors_travail_retour = calculer_recup_hors_travail(date_depart_retour, date_arrivee_retour)
            recup_retour = temps_hors_travail_retour - deduction_retour

        # Gestion des weekends (s'applique à tous les pays si pas déjà traité)
        if (date_depart_retour.weekday() >= 5 or date_arrivee_retour.weekday() >= 5) and not ((pays in pays_long_courrier) and (heure_debut_travail <= date_arrivee_retour.time() < heure_fin_travail)):
            recup_retour = (date_arrivee_retour - date_depart_retour) - deduction_retour

        if recup_retour.total_seconds() < 0:
            recup_retour = timedelta(0)

        # --- Total ---
        total_recup = recup_aller + recup_retour
        heures_aller, reste_aller = divmod(recup_aller.total_seconds(), 3600)
        minutes_aller = reste_aller // 60
        heures_retour, reste_retour = divmod(recup_retour.total_seconds(), 3600)
        minutes_retour = reste_retour // 60
        heures_total, reste_total = divmod(total_recup.total_seconds(), 3600)
        minutes_total = reste_total // 60

        st.info(f"Récupération pour le trajet aller : {int(heures_aller)}h{int(minutes_aller):02d}min")
        st.info(f"Récupération pour le trajet retour : {int(heures_retour)}h{int(minutes_retour):02d}min")
        st.success(f"Temps total de récupération pour {pays} est estimé : {int(heures_total)}h{int(minutes_total):02d}min")

    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")

# --- Bouton de calcul (inchangé) ---
st.write("")
col1, col2, col3 = st.columns(3)
with col2:
    if st.button("Calculer les heures de récupération"):
        calculer_recup()