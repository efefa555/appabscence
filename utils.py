import pandas as pd
from datetime import datetime, date
import json
import os

def load_excel(file):
    """Charge et valide le fichier Excel"""
    try:
        df = pd.read_excel(file)
        required_columns = ['Nom', 'Prénom']

        if not all(col in df.columns for col in required_columns):
            return None, "Le fichier doit contenir les colonnes 'Nom' et 'Prénom'"

        df = df[required_columns].copy()
        df['Nom'] = df['Nom'].str.strip().str.upper()
        df['Prénom'] = df['Prénom'].str.strip().str.title()

        return df, None
    except Exception as e:
        return None, f"Erreur lors de la lecture du fichier: {str(e)}"

def calculate_presence_stats(presence_data):
    """Calcule les statistiques de présence pour chaque personne"""
    results = []
    for person, dates in presence_data.items():
        present_days = len(set(dates))
        dates_str = ", ".join([d.strftime("%d/%m/%Y") for d in sorted(set(dates))])

        results.append({
            'Personne': person,
            'Nombre de présences': present_days,
            'Dates de présence': dates_str
        })

    return pd.DataFrame(results)

def format_person_name(row):
    """Formate le nom complet d'une personne"""
    return f"{row['Nom']} {row['Prénom']}"

def save_data(personnel_df, presence_data, filename="data.json"):
    """Sauvegarde les données dans un fichier JSON"""
    data = {
        'personnel': personnel_df.to_dict('records') if personnel_df is not None else None,
        'presence': {person: [d.strftime("%Y-%m-%d") for d in dates] 
                    for person, dates in presence_data.items()}
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data(filename="data.json"):
    """Charge les données depuis le fichier JSON"""
    if not os.path.exists(filename):
        return None, {}

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        personnel_df = pd.DataFrame(data['personnel']) if data['personnel'] else None
        presence_data = {person: [datetime.strptime(d, "%Y-%m-%d").date() 
                                for d in dates]
                        for person, dates in data['presence'].items()}

        return personnel_df, presence_data
    except Exception as e:
        return None, {}

def clear_data(filename="data.json"):
    """Efface toutes les données sauvegardées"""
    if os.path.exists(filename):
        os.remove(filename)
    return None, {}

def verify_admin(username, password):
    """Vérifie les identifiants admin"""
    return username.lower() == "admin" and password == "1234"