"""
Système de conseil d'arrosage basé sur les features ML du modèle XGBoost.
Réutilise les calculs de stress_hydrique, risque_secheresse, etc.
"""

from app.schemas import WateringAdviceRequest, WateringAdviceResponse


def calculate_watering_advice(request: WateringAdviceRequest) -> WateringAdviceResponse:
    """
    Génère un conseil d'arrosage intelligent basé sur les features ML.

    Réutilise la logique de ml_model.py pour calculer:
    - stress_hydrique: tension sur la plante due au manque d'eau
    - risque_secheresse: risque de sécheresse combiné (sol + température + pluie)
    - confort_thermique: adaptation de la plante aux températures
    """

    # Valeurs par défaut si données manquantes
    humidite_sol = request.humidite_sol if request.humidite_sol is not None else 50.0
    temp_moyenne = request.temp_moyenne_7j if request.temp_moyenne_7j is not None else 18.0
    temp_min = request.temp_min_7j if request.temp_min_7j is not None else 12.0
    pluie_prevue = request.pluie_7j if request.pluie_7j is not None else False
    precipitation = request.precipitation_7j if request.precipitation_7j is not None else 0.0

    # ===== CALCUL DES FEATURES ML (identique à ml_model.py) =====

    # Stress hydrique: mesure la tension de la plante
    # Plus le sol est sec, plus le stress augmente
    # La pluie réduit le stress anticipé
    stress_hydrique = max(0.0, 50.0 - humidite_sol) * (1.0 if not pluie_prevue else 0.3)
    if request.irrigation == "aucun":
        stress_hydrique *= 1.5

    # Risque de sécheresse: indicateur combiné
    # Prend en compte: sol sec + température élevée + absence de pluie
    risque_secheresse = (
        max(0.0, 40.0 - humidite_sol)
        + max(0.0, temp_moyenne - 25.0) * 2.5
        + (5.0 if not pluie_prevue and humidite_sol < 40 else 0.0)
    )

    # Confort thermique: adaptation de la plante aux températures
    temp_ideal_center = 20.0
    confort_thermique = max(0.0, 10.0 - abs(temp_moyenne - temp_ideal_center) * 0.5)
    if temp_min < 8:
        confort_thermique *= max(0.2, temp_min / 8.0)

    # ===== ANALYSE CONTEXTUELLE =====

    facteurs = []

    # Analyse humidité du sol
    if humidite_sol < 30:
        facteurs.append("humidite_sol_critique")
    elif humidite_sol < 40:
        facteurs.append("humidite_sol_basse")
    elif humidite_sol > 75:
        facteurs.append("humidite_sol_elevee")

    # Analyse pluie
    if pluie_prevue:
        if precipitation > 10:
            facteurs.append("pluie_importante_prevue")
        else:
            facteurs.append("pluie_legere_prevue")
    else:
        facteurs.append("aucune_pluie_prevue")

    # Analyse température
    if temp_moyenne > 28:
        facteurs.append("temperature_elevee")
    elif temp_moyenne < 12:
        facteurs.append("temperature_basse")

    # Analyse irrigation
    if request.irrigation == "aucun":
        facteurs.append("aucune_irrigation")
    elif request.irrigation == "automatique":
        facteurs.append("irrigation_automatique")

    # Analyse type de sol
    if request.type_sol == "sableux" and humidite_sol < 50:
        facteurs.append("sol_sableux_retention_faible")
    elif request.type_sol == "argileux" and humidite_sol > 70:
        facteurs.append("sol_argileux_drainage_lent")

    # ===== GÉNÉRATION DU CONSEIL =====

    conseil, priorite, explication, action, verification = _generate_advice(
        stress_hydrique=stress_hydrique,
        risque_secheresse=risque_secheresse,
        confort_thermique=confort_thermique,
        humidite_sol=humidite_sol,
        pluie_prevue=pluie_prevue,
        precipitation=precipitation,
        temp_moyenne=temp_moyenne,
        irrigation=request.irrigation,
        type_sol=request.type_sol,
        facteurs=facteurs
    )

    return WateringAdviceResponse(
        conseil=conseil,
        priorite=priorite,
        explication=explication,
        facteurs_cles=facteurs[:4],  # Limiter à 4 facteurs principaux
        score_stress_hydrique=round(min(stress_hydrique, 100.0), 1),
        score_risque_secheresse=round(min(risque_secheresse, 100.0), 1),
        recommandation_action=action,
        prochaine_verification=verification
    )


def _generate_advice(
    stress_hydrique: float,
    risque_secheresse: float,
    confort_thermique: float,
    humidite_sol: float,
    pluie_prevue: bool,
    precipitation: float,
    temp_moyenne: float,
    irrigation: str,
    type_sol: str,
    facteurs: list[str]
) -> tuple[str, str, str, str, str]:
    """Génère le conseil final basé sur les scores ML."""

    # PRIORITÉ CRITIQUE: Stress hydrique très élevé
    if stress_hydrique > 40:
        return (
            "Arrosage urgent necessaire",
            "urgent",
            f"Le stress hydrique est tres eleve ({stress_hydrique:.1f}/100). "
            f"Les plantes souffrent d'un manque d'eau important avec une humidite du sol a {humidite_sol:.0f}%. "
            f"{'Aucune pluie prevue pour compenser.' if not pluie_prevue else f'Malgre {precipitation:.1f}mm de pluie prevue, le deficit est trop important.'}",
            f"Arroser immediatement avec {_calculate_water_amount(humidite_sol, type_sol)} litres par m2.",
            "Verifier dans 12-24 heures"
        )

    # PRIORITÉ ÉLEVÉE: Risque de sécheresse
    if risque_secheresse > 30 and not pluie_prevue:
        return (
            "Arrosage recommande dans les 24-48h",
            "eleve",
            f"Le risque de secheresse est eleve ({risque_secheresse:.1f}/100). "
            f"Sol a {humidite_sol:.0f}%, temperature moyenne de {temp_moyenne:.1f}°C et aucune pluie prevue. "
            f"Les conditions vont se degrader rapidement.",
            f"Prevoir un arrosage de {_calculate_water_amount(humidite_sol, type_sol)} litres par m2 dans les prochaines 48h.",
            "Verifier quotidiennement"
        )

    # SOL TRÈS HUMIDE: Pas d'arrosage
    if humidite_sol > 75:
        if pluie_prevue and precipitation > 5:
            return (
                "Aucun arrosage necessaire - Sol sature",
                "aucun",
                f"Le sol est tres humide ({humidite_sol:.0f}%) et {precipitation:.1f}mm de pluie sont prevus. "
                f"{'Attention au drainage avec un sol argileux.' if type_sol == 'argileux' else 'Surveiller le drainage.'}",
                "Ne pas arroser. Verifier le drainage du sol.",
                "Verifier dans 3-4 jours"
            )
        else:
            return (
                "Aucun arrosage necessaire - Sol bien hydrate",
                "aucun",
                f"Le sol est bien hydrate ({humidite_sol:.0f}%). Les plantes disposent de reserves suffisantes. "
                f"Le stress hydrique est faible ({stress_hydrique:.1f}/100).",
                "Pas d'arrosage necessaire pour le moment.",
                "Verifier dans 2-3 jours"
            )

    # SOL CORRECT + PLUIE IMPORTANTE
    if humidite_sol >= 50 and pluie_prevue and precipitation > 10:
        return (
            "Reporter l'arrosage - Pluie prevue",
            "faible",
            f"Le sol est a un niveau correct ({humidite_sol:.0f}%) et {precipitation:.1f}mm de pluie sont prevus. "
            f"L'arrosage n'est pas necessaire. Le stress hydrique est faible ({stress_hydrique:.1f}/100).",
            "Reporter l'arrosage. Laisser la pluie hydrater naturellement.",
            "Reverifier apres la pluie (2-3 jours)"
        )

    # SOL CORRECT + PLUIE LÉGÈRE
    if humidite_sol >= 40 and humidite_sol < 60 and pluie_prevue:
        return (
            "Surveiller apres la pluie",
            "moyen",
            f"Le sol est a {humidite_sol:.0f}% avec {precipitation:.1f}mm de pluie prevus. "
            f"{'Un sol sableux retient peu l\'eau.' if type_sol == 'sableux' else 'La pluie devrait maintenir un niveau correct.'} "
            f"Stress hydrique actuel: {stress_hydrique:.1f}/100.",
            "Attendre la pluie puis reevaluer. Completer si necessaire.",
            "Verifier dans 24-48h apres la pluie"
        )

    # SOL CORRECT SANS PLUIE
    if humidite_sol >= 40 and humidite_sol < 60 and not pluie_prevue:
        temps_chaud = temp_moyenne > 25
        return (
            "Surveiller l'evolution du sol" if not temps_chaud else "Prevoir un arrosage bientot",
            "moyen" if not temps_chaud else "eleve",
            f"Le sol est a {humidite_sol:.0f}% sans pluie prevue. "
            f"{'Temperatures elevees ({temp_moyenne:.1f}°C) vont accelerer l\'evaporation.' if temps_chaud else f'Stress hydrique modere ({stress_hydrique:.1f}/100).'} "
            f"Risque de secheresse: {risque_secheresse:.1f}/100.",
            f"{'Prevoir un arrosage de ' + str(_calculate_water_amount(humidite_sol, type_sol)) + ' litres par m2 dans 24-48h.' if temps_chaud else 'Surveiller quotidiennement. Arroser si le sol descend sous 40%.'}",
            "Verifier quotidiennement" if temps_chaud else "Verifier dans 2 jours"
        )

    # SOL BAS SANS PLUIE
    if humidite_sol >= 30 and humidite_sol < 40:
        return (
            "Arrosage necessaire rapidement",
            "eleve",
            f"Le sol est bas ({humidite_sol:.0f}%) et aucune pluie n'est prevue. "
            f"Le stress hydrique commence a monter ({stress_hydrique:.1f}/100). "
            f"{'Le sol sableux necessite des arrosages plus frequents.' if type_sol == 'sableux' else 'Risque de secheresse: ' + f'{risque_secheresse:.1f}/100.'}",
            f"Arroser sous 24h avec {_calculate_water_amount(humidite_sol, type_sol)} litres par m2.",
            "Verifier dans 24 heures"
        )

    # CAS PAR DÉFAUT: SOL OPTIMAL
    return (
        "Sol en bon etat - Surveillance reguliere",
        "faible",
        f"Le sol est a un niveau optimal ({humidite_sol:.0f}%). "
        f"Stress hydrique faible ({stress_hydrique:.1f}/100). "
        f"{'Pluie prevue (' + f'{precipitation:.1f}mm' + ') va maintenir l\'hydratation.' if pluie_prevue else 'Surveiller l\'evolution sans pluie prevue.'}",
        "Pas d'action immediate. Continuer la surveillance.",
        "Verifier dans 2-3 jours"
    )


def _calculate_water_amount(humidite_sol: float, type_sol: str) -> int:
    """Calcule la quantité d'eau recommandée en L/m2."""

    # Quantité de base selon le déficit
    deficit = max(0, 60 - humidite_sol)  # Cible: 60% d'humidité
    base_amount = deficit * 0.5  # ~0.5L par % de déficit

    # Ajustement selon le type de sol
    if type_sol == "sableux":
        # Sol sableux: arrosages plus fréquents mais moins abondants
        base_amount *= 0.8
    elif type_sol == "argileux":
        # Sol argileux: arrosages moins fréquents mais plus abondants
        base_amount *= 1.2

    return max(5, min(int(base_amount), 25))  # Entre 5 et 25 L/m2
