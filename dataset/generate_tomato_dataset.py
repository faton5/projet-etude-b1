import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
np.random.seed(42)
N_SAMPLES = 8000  # Dataset plus large pour meilleure précision du modèle

def generate_tomato_dataset(n_samples=8000):
    """
    Génère un dataset synthétique réaliste pour la culture de tomates.
    """
    data = []
    start_date = datetime(2025, 3, 1)

    for i in range(n_samples):
        # Progression temporelle cohérente
        jour_culture = np.random.randint(1, 150)
        date = start_date + timedelta(days=jour_culture)

        # Détermination du stade de croissance basé sur jour_culture
        if jour_culture < 15:
            stade = "semis"
        elif jour_culture < 30:
            stade = "jeune_plant"
        elif jour_culture < 60:
            stade = "croissance"
        elif jour_culture < 80:
            stade = "floraison"
        elif jour_culture < 120:
            stade = "fructification"
        else:
            stade = "recolte"

        # Paramètres météo et environnement
        # Température air : 10-35°C avec variations saisonnières
        temp_air = np.random.normal(22, 5)
        temp_air = np.clip(temp_air, 8, 38)

        # Température sol : généralement plus stable, suit la température air
        temp_sol = temp_air + np.random.normal(-2, 1.5)
        temp_sol = np.clip(temp_sol, 10, 32)

        # Humidité air : 40-90%
        humidite_air = np.random.normal(65, 15)
        humidite_air = np.clip(humidite_air, 30, 95)

        # Humidité sol : 30-85%
        humidite_sol = np.random.normal(60, 15)
        humidite_sol = np.clip(humidite_sol, 20, 90)

        # pH sol : optimal pour tomates 6.0-7.0
        ph_sol = np.random.normal(6.5, 0.5)
        ph_sol = np.clip(ph_sol, 5.0, 8.0)

        # Lumière : 6-14 heures par jour
        lumiere = np.random.normal(10, 2)
        lumiere = np.clip(lumiere, 4, 15)

        # Pluie : 0-30mm sur 24h (plus rare les fortes pluies)
        pluie = np.random.exponential(3) if np.random.rand() > 0.3 else 0
        pluie = np.clip(pluie, 0, 50)

        # Arrosage : dépend de la pluie et de l'humidité sol
        if pluie > 10:
            arrosage = 0
        elif humidite_sol < 40:
            arrosage = np.random.uniform(2, 5)
        else:
            arrosage = np.random.uniform(0.5, 3)

        # Caractéristiques physiques du plant
        # Hauteur : augmente avec le temps et le stade
        if stade == "semis":
            hauteur = np.random.uniform(2, 8)
        elif stade == "jeune_plant":
            hauteur = np.random.uniform(8, 25)
        elif stade == "croissance":
            hauteur = np.random.uniform(25, 80)
        elif stade == "floraison":
            hauteur = np.random.uniform(60, 120)
        elif stade == "fructification":
            hauteur = np.random.uniform(80, 150)
        else:  # recolte
            hauteur = np.random.uniform(100, 180)

        # Nombre de fleurs
        if stade in ["semis", "jeune_plant"]:
            nb_fleurs = 0
        elif stade == "croissance":
            nb_fleurs = np.random.randint(0, 5)
        elif stade == "floraison":
            nb_fleurs = np.random.randint(5, 30)
        elif stade == "fructification":
            nb_fleurs = np.random.randint(2, 15)
        else:  # recolte
            nb_fleurs = np.random.randint(0, 8)

        # Nombre de fruits
        if stade in ["semis", "jeune_plant", "croissance"]:
            nb_fruits = 0
        elif stade == "floraison":
            nb_fruits = np.random.randint(0, 3)
        elif stade == "fructification":
            nb_fruits = np.random.randint(3, 25)
        else:  # recolte
            nb_fruits = np.random.randint(10, 40)

        # Couleur des feuilles (indicateur de santé)
        couleur_proba = np.random.rand()
        if couleur_proba < 0.6:
            couleur = "vert"
        elif couleur_proba < 0.75:
            couleur = "jaune"
        elif couleur_proba < 0.9:
            couleur = "fonce"
        else:
            couleur = "tachete"

        # État général du plant
        stress_score = 0

        # Calcul du stress basé sur les conditions
        if temp_air < 15 or temp_air > 32:
            stress_score += 2
        if humidite_sol < 40 or humidite_sol > 80:
            stress_score += 1
        if ph_sol < 5.8 or ph_sol > 7.2:
            stress_score += 1
        if lumiere < 6:
            stress_score += 1
        if pluie > 20:
            stress_score += 1

        if stress_score == 0:
            etat_general = "bon"
        elif stress_score <= 2:
            etat_general = "stress_leger"
        elif stress_score <= 4:
            etat_general = "stress_moyen"
        else:
            etat_general = "mauvais"

        # Détermination de la recommandation (logique de décision)
        recommandation = "bon"

        # Priorité aux conditions critiques
        if temp_air < 12:
            recommandation = "risque_froid"
        elif temp_air > 35:
            recommandation = "risque_chaleur"
        elif ph_sol < 5.5 or ph_sol > 7.5:
            recommandation = "sol_pas_adapte"
        elif humidite_sol < 35 and pluie < 5:
            recommandation = "arroser"
        elif humidite_sol > 80 or pluie > 25:
            recommandation = "trop_eau"
        elif lumiere < 6:
            recommandation = "manque_lumiere"
        elif stade == "recolte" and nb_fruits > 15 and jour_culture > 110:
            recommandation = "recolte_bientot"
        else:
            # Pour équilibrer le dataset, ajouter des variations même en conditions normales
            if stress_score > 0:
                if humidite_sol < 45:
                    recommandation = "arroser"
                elif temp_air < 15:
                    recommandation = "risque_froid"
                elif temp_air > 30:
                    recommandation = "risque_chaleur"
                elif lumiere < 8:
                    recommandation = "manque_lumiere"

        # Ajustement de la couleur des feuilles selon la recommandation
        if recommandation in ["trop_eau", "sol_pas_adapte"]:
            couleur = np.random.choice(["jaune", "tachete"], p=[0.6, 0.4])
        elif recommandation in ["arroser", "manque_lumiere"]:
            couleur = np.random.choice(["jaune", "fonce"], p=[0.7, 0.3])
        elif recommandation in ["risque_froid", "risque_chaleur"]:
            couleur = np.random.choice(["fonce", "tachete"], p=[0.5, 0.5])
        elif recommandation == "bon":
            couleur = np.random.choice(["vert", "vert", "vert", "jaune"], p=[0.7, 0.15, 0.1, 0.05])

        # Ajout de la ligne de données
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'jour_culture': jour_culture,
            'temperature_air_c': round(temp_air, 1),
            'temperature_sol_c': round(temp_sol, 1),
            'humidite_air_pourcent': round(humidite_air, 1),
            'humidite_sol_pourcent': round(humidite_sol, 1),
            'ph_sol': round(ph_sol, 2),
            'lumiere_heures_jour': round(lumiere, 1),
            'pluie_mm_24h': round(pluie, 1),
            'arrosage_litres_jour': round(arrosage, 2),
            'stade_croissance': stade,
            'hauteur_plant_cm': round(hauteur, 1),
            'nb_fleurs': int(nb_fleurs),
            'nb_fruits': int(nb_fruits),
            'couleur_feuilles': couleur,
            'etat_general': etat_general,
            'recommandation': recommandation
        })

    return pd.DataFrame(data)

# Génération du dataset
print("🍅 Génération du dataset de culture de tomates...")
df = generate_tomato_dataset(N_SAMPLES)

# Affichage des statistiques
print(f"\n✅ Dataset généré avec {len(df)} lignes")
print(f"\n📊 Distribution des recommandations:")
print(df['recommandation'].value_counts())
print(f"\n📈 Distribution des stades de croissance:")
print(df['stade_croissance'].value_counts())
print(f"\n🌡️ Statistiques des températures:")
print(df[['temperature_air_c', 'temperature_sol_c']].describe())

# Sauvegarde en CSV
output_file = 'tomato_dataset.csv'
df.to_csv(output_file, index=False)
print(f"\n💾 Dataset sauvegardé dans '{output_file}'")

# Affichage d'un échantillon
print(f"\n👀 Aperçu des premières lignes:")
print(df.head(10))
