import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import io
import logging
import time
import sys

# Configuration avancée du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
logger.info("Démarrage de l'application")

from utils import (
    load_excel, calculate_presence_stats, format_person_name,
    save_data, load_data, clear_data, verify_admin
)

# Configuration de la page
try:
    st.set_page_config(
        page_title="Suivi des Présences",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    logger.info("Configuration de la page réussie")
except Exception as e:
    logger.error(f"Erreur lors de la configuration de la page: {str(e)}")
    st.error("Une erreur est survenue lors du chargement de l'application")

# Gestion de la session
def init_session_state():
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = time.time()
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = time.time()
    if 'initialized' not in st.session_state:
        try:
            personnel_df, presence_data = load_data()
            st.session_state.personnel_df = personnel_df
            st.session_state.presence_data = presence_data
            st.session_state.initialized = True
            st.session_state.authenticated = False
            logger.info("Initialisation des variables de session réussie")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation: {str(e)}")
            st.error("Une erreur est survenue lors de l'initialisation")

# Mise à jour de l'activité
def update_activity():
    st.session_state.last_activity = time.time()

# Vérification de la session
def check_session():
    current_time = time.time()
    session_duration = current_time - st.session_state.session_start_time
    inactivity_duration = current_time - st.session_state.last_activity

    # Réinitialisation si inactif pendant plus de 2 heures ou session > 8 heures
    if inactivity_duration > 7200 or session_duration > 28800:
        logger.info("Session expirée - Réinitialisation")
        init_session_state()
        return False
    return True

# Initialisation de la session
init_session_state()

# Mise à jour de l'activité à chaque interaction
update_activity()

# Page de connexion
if not st.session_state.authenticated:
    st.title("📊 Connexion")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.write("Veuillez vous connecter pour accéder à l'application")
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")

        if st.button("Se connecter"):
            try:
                if verify_admin(username, password):
                    st.session_state.authenticated = True
                    update_activity()
                    logger.info("Connexion réussie")
                    st.rerun()
                else:
                    logger.warning("Tentative de connexion échouée")
                    st.error("Identifiants incorrects!")
            except Exception as e:
                logger.error(f"Erreur lors de la connexion: {str(e)}")
                st.error("Une erreur est survenue lors de la connexion")

else:
    # Vérification de la session avant d'afficher le contenu
    if not check_session():
        st.session_state.authenticated = False
        st.rerun()

    try:
        # Titre de l'application
        st.title("📊 Suivi des Présences")

        # Sidebar pour l'import des données
        with st.sidebar:
            st.header("Import des données")
            uploaded_file = st.file_uploader(
                "Importez le fichier Excel (colonnes: Nom, Prénom)",
                type=['xlsx', 'xls']
            )

            if uploaded_file:
                df, error = load_excel(uploaded_file)
                if error:
                    st.error(error)
                else:
                    st.session_state.personnel_df = df
                    save_data(st.session_state.personnel_df, st.session_state.presence_data)
                    st.success("Données importées avec succès!")
                    update_activity()

            # Section réinitialisation (admin)
            st.header("Administration")
            if st.button("Se déconnecter"):
                st.session_state.authenticated = False
                logger.info("Déconnexion utilisateur")
                st.rerun()

            with st.expander("Réinitialiser les données"):
                admin_username = st.text_input("Nom d'utilisateur admin", key="admin_username")
                admin_password = st.text_input("Mot de passe admin", type="password", key="admin_password")

                if st.button("Réinitialiser toutes les données"):
                    if verify_admin(admin_username, admin_password):
                        st.session_state.personnel_df, st.session_state.presence_data = clear_data()
                        logger.info("Réinitialisation des données")
                        st.success("Toutes les données ont été effacées!")
                        update_activity()
                        st.rerun()
                    else:
                        st.error("Identifiants admin incorrects!")

        # Interface principale
        if st.session_state.personnel_df is not None:
            # Saisie des présences
            st.header("Enregistrement des présences")

            selected_date = st.date_input(
                "Sélectionnez la date",
                value=date.today()
            )

            if selected_date.weekday() >= 5:
                st.warning("Attention: date sélectionnée en weekend!")

            personnel_list = st.session_state.personnel_df.apply(format_person_name, axis=1).tolist()
            selected_persons = st.multiselect(
                "Sélectionnez les personnes présentes",
                options=personnel_list
            )

            if st.button("Enregistrer les présences"):
                for person in selected_persons:
                    if person not in st.session_state.presence_data:
                        st.session_state.presence_data[person] = []
                    if selected_date not in st.session_state.presence_data[person]:
                        st.session_state.presence_data[person].append(selected_date)

                # Sauvegarde des données après modification
                save_data(st.session_state.personnel_df, st.session_state.presence_data)
                logger.info(f"Présences enregistrées pour {len(selected_persons)} personnes")
                st.success("Présences enregistrées!")
                update_activity()

            # Affichage des statistiques
            if st.session_state.presence_data:
                st.header("Statistiques de présence")

                stats_df = calculate_presence_stats(st.session_state.presence_data)

                # Affichage du tableau
                st.dataframe(stats_df)

                # Visualisation
                fig = px.bar(
                    stats_df,
                    x='Personne',
                    y='Nombre de présences',
                    title="Nombre de présences par personne"
                )
                st.plotly_chart(fig)

                # Export des données
                if st.button("Exporter les résultats"):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        stats_df.to_excel(writer, index=False, sheet_name='Statistiques')

                    output.seek(0)
                    st.download_button(
                        label="Télécharger le fichier Excel",
                        data=output,
                        file_name="statistiques_presence.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    update_activity()

        else:
            st.info("👈 Commencez par importer un fichier Excel contenant la liste du personnel")
    except Exception as e:
        logger.error(f"Erreur dans l'application principale: {str(e)}")
        st.error("Une erreur est survenue dans l'application")