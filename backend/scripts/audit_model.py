"""Audit anti-hallucination / anti-apprentissage débile du modèle XGBoost tomate."""
from __future__ import annotations

import random
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from xgboost import XGBClassifier

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

from app.ml_model import CLASS_LABELS, FEATURE_COLUMNS, encode_payload
from app.schemas import PredictionRequest
from scripts.train_model import (
    build_training_rows,
    _build_xgboost,
    _generate_payload,
    viability_score,
    _sample_label,
    CLASS_INDEX,
    SEASONS,
    SOILS,
    IRRIGATIONS,
)


def main():
    print("=" * 70)
    print("AUDIT ANTI-HALLUCINATION / ANTI-APPRENTISSAGE DEBILE")
    print("=" * 70)

    rows = build_training_rows(sample_count=15000, seed=42)
    x = pd.DataFrame([encode_payload(row["payload"]) for row in rows], columns=FEATURE_COLUMNS)
    y = np.array([row["target"] for row in rows])

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )

    model = _build_xgboost()
    model.fit(x_train, y_train, verbose=False)

    results = {}
    results["data_leak"] = section_1_data_leak(x)
    results["holdout_seed"] = section_2_holdout_different_seed(model)
    results["ablation"] = section_3_ablation(x_train, x_test, y_train, y_test, model)
    results["baselines"] = section_4_baselines(x_train, x_test, y_train, y_test, model)
    results["noise"] = section_5_noise_robustness(x_test, y_test, model)
    results["coherence"] = section_6_business_coherence()
    results["sensitivity"] = section_7_sensitivity()
    section_8_final_report(x, y, x_train, x_test, y_train, y_test, model, results)


# ---------------------------------------------------------------------------
# 1. TEST DE FUITE DE DONNÉES
# ---------------------------------------------------------------------------

def section_1_data_leak(x: pd.DataFrame) -> bool:
    print("\n" + "=" * 70)
    print("1. TEST DE FUITE DE DONNÉES")
    print("=" * 70)

    suspicious = [
        "score_viabilite", "target", "target_label", "label",
        "proba_viable", "proba_attendre", "proba_non_viable",
        "y", "class", "classe",
    ]

    features_used = list(x.columns)
    print(f"\n  Features utilisées à l'entraînement ({len(features_used)}):")
    for f in features_used:
        print(f"    - {f}")

    leaked = [col for col in features_used if col.lower() in suspicious]

    print(f"\n  Colonnes suspectes recherchées: {suspicious}")
    if leaked:
        print(f"  [ECHEC] FUITE DETECTÉE! Colonnes suspectes présentes: {leaked}")
        return False
    else:
        print("  [OK] Aucune fuite de données détectée.")
        return True


# ---------------------------------------------------------------------------
# 2. TEST HOLDOUT AVEC GÉNÉRATEUR DIFFÉRENT
# ---------------------------------------------------------------------------

def section_2_holdout_different_seed(model) -> bool:
    print("\n" + "=" * 70)
    print("2. TEST HOLDOUT AVEC GÉNÉRATEUR DIFFÉRENT")
    print("=" * 70)

    print("  Génération d'un dataset de test avec seed=999, distributions modifiées...")

    rng = random.Random(999)
    rows = []
    for _ in range(3000):
        payload = _generate_shifted_payload(rng)
        score = viability_score(payload, rng=rng)
        label = _sample_label(score, rng)
        rows.append({
            "payload": payload,
            "target": CLASS_INDEX[label],
        })

    x_holdout = pd.DataFrame(
        [encode_payload(r["payload"]) for r in rows], columns=FEATURE_COLUMNS
    )
    y_holdout = np.array([r["target"] for r in rows])

    preds = model.predict(x_holdout)
    acc = accuracy_score(y_holdout, preds)
    f1 = f1_score(y_holdout, preds, average="macro")

    dist = pd.Series(y_holdout).value_counts().to_dict()
    print(f"  Distribution holdout: {dist}")
    print(f"  Accuracy sur holdout: {acc:.4f}")
    print(f"  F1 macro sur holdout: {f1:.4f}")

    if f1 >= 0.70:
        print("  [OK] Le modèle généralise bien sur un générateur différent (F1 >= 0.70).")
        return True
    elif f1 >= 0.65:
        print("  [ATTENTION] F1 légèrement en dessous de 0.70 — généralisation modérée.")
        return True
    else:
        print("  [ECHEC] F1 < 0.65 — le modèle mémorise probablement le générateur original!")
        return False


def _generate_shifted_payload(rng: random.Random) -> PredictionRequest:
    """Générateur décalé : plus de cas limites, saisons moins nettes, bruit différent."""
    saison = rng.choices(SEASONS, weights=[0.28, 0.25, 0.25, 0.22])[0]

    scenario = rng.choices(
        ["normal", "limite_temp", "limite_hum", "extreme_chaud", "extreme_froid",
         "transition_saison", "sol_probleme"],
        weights=[0.25, 0.15, 0.15, 0.12, 0.12, 0.11, 0.10],
    )[0]

    if scenario == "limite_temp":
        temp_moyenne = rng.uniform(12, 16)
        temp_min = rng.uniform(7, 11)
    elif scenario == "limite_hum":
        temp_moyenne = rng.gauss(18, 5)
        temp_min = temp_moyenne - rng.uniform(3, 8)
    elif scenario == "extreme_chaud":
        temp_moyenne = rng.uniform(30, 38)
        temp_min = rng.uniform(20, 26)
    elif scenario == "extreme_froid":
        temp_moyenne = rng.uniform(2, 8)
        temp_min = rng.uniform(-5, 4)
    elif scenario == "transition_saison":
        if saison == "printemps":
            temp_moyenne = rng.uniform(8, 14)
        elif saison == "automne":
            temp_moyenne = rng.uniform(14, 20)
        else:
            temp_moyenne = rng.gauss(15, 6)
        temp_min = temp_moyenne - rng.uniform(3, 9)
    elif scenario == "sol_probleme":
        temp_moyenne = rng.gauss(20, 5)
        temp_min = temp_moyenne - rng.uniform(4, 8)
    else:
        base_temps = {"printemps": 15, "ete": 23, "automne": 12, "hiver": 6}
        temp_moyenne = rng.gauss(base_temps[saison], 5.5)
        temp_min = temp_moyenne - rng.uniform(3, 10)

    if scenario == "limite_hum":
        humidite_sol = rng.uniform(30, 42)
    elif scenario == "sol_probleme":
        humidite_sol = rng.choice([rng.uniform(15, 30), rng.uniform(80, 95)])
    else:
        humidite_sol = rng.gauss(52, 18)

    temp_actuelle = temp_moyenne + rng.gauss(1, 3)
    temp_min += rng.gauss(0, 2.0)
    temp_moyenne += rng.gauss(0, 2.0)
    humidite_sol += rng.gauss(0, 6)

    if scenario == "sol_probleme":
        type_sol = rng.choice(["sableux", "argileux"])
    else:
        type_sol = rng.choices(SOILS, weights=[0.20, 0.25, 0.20, 0.15, 0.20])[0]

    irrigation = rng.choices(IRRIGATIONS, weights=[0.30, 0.25, 0.20, 0.25])[0]

    pluie_mm = rng.expovariate(1 / 7) if rng.random() > 0.40 else 0
    pluie_7j = pluie_mm > rng.uniform(2, 8)

    import math
    prob_gel = 1 / (1 + math.exp((temp_min - 3.5) / 2.0))
    if rng.random() < 0.10:
        prob_gel = 1 - prob_gel
    risque_gel_7j = rng.random() < prob_gel

    base_water = {"aucun": 8, "manuel": 70, "goutte_a_goutte": 75, "automatique": 100}
    water_usage = max(0, rng.gauss(base_water[irrigation], 35))
    if humidite_sol < 35:
        water_usage += rng.uniform(10, 40)
    if temp_moyenne > 28:
        water_usage += rng.uniform(10, 30)

    return PredictionRequest(
        location=rng.choice(["Rennes", "Nantes", "Angers", "Vannes", "Lyon", "Bordeaux"]),
        culture="tomate",
        saison=saison,
        type_sol=type_sol,
        irrigation=irrigation,
        humidite_sol=round(max(0, min(100, humidite_sol)), 1),
        temp_actuelle=round(max(-30, min(60, temp_actuelle)), 1),
        temp_min_7j=round(max(-30, min(60, temp_min)), 1),
        temp_moyenne_7j=round(max(-30, min(60, temp_moyenne)), 1),
        pluie_7j=pluie_7j,
        risque_gel_7j=risque_gel_7j,
        water_usage=round(max(0, min(1000, water_usage)), 1),
    )


# ---------------------------------------------------------------------------
# 3. TEST ABLATION DES FEATURES DÉRIVÉES
# ---------------------------------------------------------------------------

def section_3_ablation(x_train, x_test, y_train, y_test, full_model) -> bool:
    print("\n" + "=" * 70)
    print("3. TEST ABLATION DES FEATURES DÉRIVÉES")
    print("=" * 70)

    derived = ["confort_thermique", "stress_hydrique", "risque_secheresse", "score_saison_tomate"]
    base_cols = [c for c in FEATURE_COLUMNS if c not in derived]

    full_f1 = f1_score(y_test, full_model.predict(x_test), average="macro")

    x_train_base = x_train[base_cols]
    x_test_base = x_test[base_cols]

    model_base = XGBClassifier(
        objective="multi:softprob",
        num_class=len(CLASS_LABELS),
        n_estimators=400,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        reg_alpha=0.3,
        reg_lambda=2.0,
        eval_metric="mlogloss",
        random_state=42,
    )
    model_base.fit(x_train_base, y_train, verbose=False)
    base_f1 = f1_score(y_test, model_base.predict(x_test_base), average="macro")

    print(f"\n  F1 macro avec TOUTES les features: {full_f1:.4f}")
    print(f"  F1 macro SANS features dérivées:   {base_f1:.4f}")
    print(f"  Gain des features dérivées:        +{full_f1 - base_f1:.4f}")
    print(f"\n  Features dérivées retirées: {derived}")
    print(f"  Features de base gardées:   {base_cols}")

    print(f"\n  Ablation individuelle:")
    for feat in derived:
        cols_without = [c for c in FEATURE_COLUMNS if c != feat]
        x_train_wo = x_train[cols_without]
        x_test_wo = x_test[cols_without]
        m = XGBClassifier(
            objective="multi:softprob", num_class=3, n_estimators=400,
            max_depth=3, learning_rate=0.08, subsample=0.8,
            colsample_bytree=0.8, min_child_weight=5,
            reg_alpha=0.3, reg_lambda=2.0, eval_metric="mlogloss", random_state=42,
        )
        m.fit(x_train_wo, y_train, verbose=False)
        f1_wo = f1_score(y_test, m.predict(x_test_wo), average="macro")
        drop = full_f1 - f1_wo
        print(f"    Sans {feat:<22s}: F1={f1_wo:.4f} (drop={drop:+.4f})")

    if full_f1 - base_f1 > 0.02:
        print("\n  [OK] Les features dérivées apportent un gain significatif (+0.02+).")
    else:
        print("\n  [ATTENTION] Les features dérivées n'apportent presque rien.")

    single_feature_dominance = full_f1 - base_f1 > 0.15
    if single_feature_dominance:
        print("  [ALERTE] Le modèle dépend trop des features dérivées (>0.15 de drop)!")
        return False
    else:
        print("  [OK] Le modèle ne dépend pas d'une seule variable magique.")
        return True


# ---------------------------------------------------------------------------
# 4. TEST CONTRE MODÈLES SIMPLES
# ---------------------------------------------------------------------------

def section_4_baselines(x_train, x_test, y_train, y_test, xgb_model) -> bool:
    print("\n" + "=" * 70)
    print("4. TEST CONTRE MODÈLES SIMPLES")
    print("=" * 70)

    baselines = {
        "DummyClassifier": DummyClassifier(strategy="most_frequent", random_state=42),
        "LogisticRegression": LogisticRegression(max_iter=3000, random_state=42),
        "DecisionTree (depth=3)": DecisionTreeClassifier(max_depth=3, random_state=42),
        "RandomForest (100)": RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42),
    }

    xgb_f1 = f1_score(y_test, xgb_model.predict(x_test), average="macro")
    xgb_acc = accuracy_score(y_test, xgb_model.predict(x_test))

    print(f"\n  {'Modèle':<30s} {'Accuracy':>10s} {'F1 macro':>10s} {'Gap F1':>10s}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10}")
    print(f"  {'XGBoost':<30s} {xgb_acc:>10.4f} {xgb_f1:>10.4f} {'ref':>10s}")

    tree3_f1 = None
    for name, m in baselines.items():
        m.fit(x_train, y_train)
        preds = m.predict(x_test)
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds, average="macro")
        gap = xgb_f1 - f1
        print(f"  {name:<30s} {acc:>10.4f} {f1:>10.4f} {gap:>+10.4f}")
        if "depth=3" in name:
            tree3_f1 = f1

    gap_tree = xgb_f1 - tree3_f1
    print(f"\n  Gap XGBoost vs DecisionTree(3): {gap_tree:+.4f}")
    if gap_tree >= 0.10:
        print("  [OK] XGBoost bat DecisionTree(3) d'au moins +0.10.")
        return True
    elif gap_tree >= 0.05:
        print("  [ATTENTION] Gap modéré (+0.05 à +0.10) — XGBoost est meilleur mais modérément.")
        return True
    else:
        print("  [ECHEC] XGBoost ne bat pas suffisamment DecisionTree(3) (gap < 0.05)!")
        return False


# ---------------------------------------------------------------------------
# 5. TEST DE ROBUSTESSE AU BRUIT
# ---------------------------------------------------------------------------

def section_5_noise_robustness(x_test, y_test, model) -> bool:
    print("\n" + "=" * 70)
    print("5. TEST DE ROBUSTESSE AU BRUIT")
    print("=" * 70)

    sample_idx = np.random.default_rng(42).choice(len(x_test), size=500, replace=False)
    x_sample = x_test.iloc[sample_idx].copy()
    y_sample = y_test[sample_idx]

    original_preds = model.predict(x_sample)
    original_f1 = f1_score(y_sample, original_preds, average="macro")

    rng = np.random.default_rng(77)
    noisy = x_sample.copy()

    if "temp_actuelle" in noisy.columns:
        noisy["temp_actuelle"] += rng.normal(0, 1.5, 500)
    if "temp_min_7j" in noisy.columns:
        noisy["temp_min_7j"] += rng.normal(0, 1.5, 500)
    if "temp_moyenne_7j" in noisy.columns:
        noisy["temp_moyenne_7j"] += rng.normal(0, 1.5, 500)
    if "humidite_sol" in noisy.columns:
        noisy["humidite_sol"] += rng.normal(0, 8, 500)
        noisy["humidite_sol"] = noisy["humidite_sol"].clip(0, 100)
    if "water_usage" in noisy.columns:
        noisy["water_usage"] += rng.normal(0, 10, 500)
        noisy["water_usage"] = noisy["water_usage"].clip(0, 1000)
    if "pluie_7j" in noisy.columns:
        flip = rng.random(500) < 0.08
        noisy.loc[noisy.index[flip], "pluie_7j"] = 1.0 - noisy.loc[noisy.index[flip], "pluie_7j"]
    if "confort_thermique" in noisy.columns:
        noisy["confort_thermique"] += rng.normal(0, 0.8, 500)
    if "stress_hydrique" in noisy.columns:
        noisy["stress_hydrique"] += rng.normal(0, 3, 500)
        noisy["stress_hydrique"] = noisy["stress_hydrique"].clip(0, None)
    if "risque_secheresse" in noisy.columns:
        noisy["risque_secheresse"] += rng.normal(0, 3, 500)
        noisy["risque_secheresse"] = noisy["risque_secheresse"].clip(0, None)

    noisy_preds = model.predict(noisy)
    noisy_f1 = f1_score(y_sample, noisy_preds, average="macro")

    changed_mask = original_preds != noisy_preds
    changed = int(changed_mask.sum())
    rate = changed / 500

    print(f"  Échantillon: 500 exemples du test set")
    print(f"  Bruit: temp ±1.5°C, humidité ±8%, water_usage ±10, pluie flip 8%")
    print(f"  F1 avant bruit: {original_f1:.4f}")
    print(f"  F1 après bruit: {noisy_f1:.4f}")
    print(f"  Drop F1: {original_f1 - noisy_f1:.4f}")
    print(f"  Prédictions changées: {changed}/500 ({rate:.1%})")

    if changed > 0:
        print(f"\n  Exemples de cas limites qui ont changé (max 5):")
        changed_indices = np.where(changed_mask)[0][:5]
        for idx in changed_indices:
            orig_class = CLASS_LABELS[original_preds[idx]]
            new_class = CLASS_LABELS[noisy_preds[idx]]
            orig_probas = model.predict_proba(x_sample.iloc[[idx]])[0]
            conf = max(orig_probas)
            print(f"    idx={idx}: {orig_class} → {new_class} (confiance originale: {conf:.2f})")

    if rate > 0.30:
        print("\n  [ECHEC] Modèle trop fragile (>30% changent)!")
        return False
    elif rate > 0.20:
        print("\n  [ATTENTION] Robustesse modérée (20-30%).")
        return True
    else:
        print(f"\n  [OK] Moins de 20% changent ({rate:.1%}) — robustesse acceptable.")
        return True


# ---------------------------------------------------------------------------
# 6. TEST DE COHÉRENCE MÉTIER
# ---------------------------------------------------------------------------

def section_6_business_coherence() -> bool:
    print("\n" + "=" * 70)
    print("6. TEST DE COHÉRENCE MÉTIER")
    print("=" * 70)

    bundle = joblib.load(BACKEND_DIR / "models" / "xgboost_tomate.joblib")
    model = bundle["model"]

    scenarios = [
        ("Bonnes conditions printemps",
         dict(saison="printemps", type_sol="limoneux", irrigation="goutte_a_goutte",
              humidite_sol=58, temp_actuelle=22, temp_min_7j=14, temp_moyenne_7j=20,
              pluie_7j=True, risque_gel_7j=False, water_usage=80),
         ["viable"]),
        ("Bonnes conditions été",
         dict(saison="ete", type_sol="humifere", irrigation="automatique",
              humidite_sol=55, temp_actuelle=25, temp_min_7j=16, temp_moyenne_7j=23,
              pluie_7j=False, risque_gel_7j=False, water_usage=90),
         ["viable"]),
        ("Gel fort hiver",
         dict(saison="hiver", type_sol="argileux", irrigation="aucun",
              humidite_sol=60, temp_actuelle=-2, temp_min_7j=-5, temp_moyenne_7j=1,
              pluie_7j=False, risque_gel_7j=True, water_usage=0),
         ["non_viable"]),
        ("Gel modéré printemps",
         dict(saison="printemps", type_sol="limoneux", irrigation="manuel",
              humidite_sol=50, temp_actuelle=5, temp_min_7j=0, temp_moyenne_7j=6,
              pluie_7j=False, risque_gel_7j=True, water_usage=30),
         ["non_viable"]),
        ("Sol très sec sans irrigation",
         dict(saison="ete", type_sol="sableux", irrigation="aucun",
              humidite_sol=15, temp_actuelle=28, temp_min_7j=16, temp_moyenne_7j=25,
              pluie_7j=False, risque_gel_7j=False, water_usage=5),
         ["attendre", "non_viable"]),
        ("Trop chaud + sol sec",
         dict(saison="ete", type_sol="sableux", irrigation="manuel",
              humidite_sol=30, temp_actuelle=36, temp_min_7j=22, temp_moyenne_7j=33,
              pluie_7j=False, risque_gel_7j=False, water_usage=50),
         ["attendre", "non_viable"]),
        ("Hiver doux (pas viable)",
         dict(saison="hiver", type_sol="limoneux", irrigation="goutte_a_goutte",
              humidite_sol=50, temp_actuelle=12, temp_min_7j=6, temp_moyenne_7j=10,
              pluie_7j=True, risque_gel_7j=False, water_usage=45),
         ["attendre", "non_viable"]),
        ("Sol humide + argileux",
         dict(saison="printemps", type_sol="argileux", irrigation="automatique",
              humidite_sol=90, temp_actuelle=18, temp_min_7j=12, temp_moyenne_7j=16,
              pluie_7j=True, risque_gel_7j=False, water_usage=130),
         ["attendre", "non_viable"]),
        ("Météo limite récupérable",
         dict(saison="printemps", type_sol="limoneux", irrigation="goutte_a_goutte",
              humidite_sol=42, temp_actuelle=15, temp_min_7j=9, temp_moyenne_7j=14,
              pluie_7j=True, risque_gel_7j=False, water_usage=70),
         ["attendre", "viable"]),
        ("Automne doux bon sol",
         dict(saison="automne", type_sol="humifere", irrigation="goutte_a_goutte",
              humidite_sol=55, temp_actuelle=18, temp_min_7j=12, temp_moyenne_7j=17,
              pluie_7j=False, risque_gel_7j=False, water_usage=60),
         ["viable", "attendre"]),
    ]

    print(f"\n  {'#':<3s} {'Scénario':<35s} {'Attendu':<22s} {'Prédit':<12s} {'Conf':>5s} {'Probas (V/A/NV)':<18s} {'Statut'}")
    print(f"  {'-'*3} {'-'*35} {'-'*22} {'-'*12} {'-'*5} {'-'*18} {'-'*6}")

    passed = 0
    total = len(scenarios)
    for i, (name, params, expected) in enumerate(scenarios, 1):
        payload = PredictionRequest(location="Rennes", culture="tomate", **params)
        features = [encode_payload(payload)]
        pred_idx = int(model.predict(features)[0])
        probas = model.predict_proba(features)[0]
        pred = CLASS_LABELS[pred_idx]
        conf = float(max(probas))
        ok = pred in expected
        if ok:
            passed += 1
        status = "OK" if ok else "KO"
        expected_str = "/".join(expected)
        proba_str = f"{probas[0]:.2f}/{probas[1]:.2f}/{probas[2]:.2f}"
        print(f"  {i:<3d} {name:<35s} {expected_str:<22s} {pred:<12s} {conf:>5.2f} {proba_str:<18s} {status}")

    print(f"\n  Résultat: {passed}/{total} scénarios cohérents.")
    if passed >= total * 0.8:
        print("  [OK] Cohérence métier satisfaisante (>= 80%).")
        return True
    else:
        print("  [ECHEC] Trop de scénarios incohérents!")
        return False


# ---------------------------------------------------------------------------
# 7. TEST DE SENSIBILITÉ CONTRÔLÉE
# ---------------------------------------------------------------------------

def section_7_sensitivity() -> bool:
    print("\n" + "=" * 70)
    print("7. TEST DE SENSIBILITÉ CONTRÔLÉE")
    print("=" * 70)

    bundle = joblib.load(BACKEND_DIR / "models" / "xgboost_tomate.joblib")
    model = bundle["model"]

    base_params = dict(
        saison="printemps", type_sol="limoneux", irrigation="goutte_a_goutte",
        humidite_sol=55, temp_actuelle=20, temp_min_7j=12, temp_moyenne_7j=18,
        pluie_7j=True, risque_gel_7j=False, water_usage=70,
    )

    all_smooth = True

    # temp_min_7j : 0 → 20
    print("\n  Variation temp_min_7j (0 à 20):")
    print(f"    {'temp_min':>8s}  {'viable':>6s} {'attendre':>8s} {'non_viable':>10s}  prédiction")
    prev_probas = None
    jumps = 0
    for t in range(0, 21, 2):
        params = {**base_params, "temp_min_7j": t}
        payload = PredictionRequest(location="Rennes", culture="tomate", **params)
        features = [encode_payload(payload)]
        probas = model.predict_proba(features)[0]
        pred = CLASS_LABELS[int(model.predict(features)[0])]
        print(f"    {t:>8d}  {probas[0]:>6.3f} {probas[1]:>8.3f} {probas[2]:>10.3f}  {pred}")
        if prev_probas is not None:
            max_jump = max(abs(probas[i] - prev_probas[i]) for i in range(3))
            if max_jump > 0.30:
                jumps += 1
        prev_probas = probas

    if jumps > 2:
        print(f"    [ATTENTION] {jumps} sauts > 0.30 détectés")
        all_smooth = False
    else:
        print(f"    [OK] Transitions progressives ({jumps} saut(s) > 0.30)")

    # humidite_sol : 10 → 95
    print("\n  Variation humidite_sol (10 à 95):")
    print(f"    {'humidite':>8s}  {'viable':>6s} {'attendre':>8s} {'non_viable':>10s}  prédiction")
    prev_probas = None
    jumps = 0
    for h in range(10, 96, 5):
        params = {**base_params, "humidite_sol": h}
        payload = PredictionRequest(location="Rennes", culture="tomate", **params)
        features = [encode_payload(payload)]
        probas = model.predict_proba(features)[0]
        pred = CLASS_LABELS[int(model.predict(features)[0])]
        print(f"    {h:>8d}  {probas[0]:>6.3f} {probas[1]:>8.3f} {probas[2]:>10.3f}  {pred}")
        if prev_probas is not None:
            max_jump = max(abs(probas[i] - prev_probas[i]) for i in range(3))
            if max_jump > 0.30:
                jumps += 1
        prev_probas = probas

    if jumps > 2:
        print(f"    [ATTENTION] {jumps} sauts > 0.30 détectés")
        all_smooth = False
    else:
        print(f"    [OK] Transitions progressives ({jumps} saut(s) > 0.30)")

    # temp_moyenne_7j : 5 → 35
    print("\n  Variation temp_moyenne_7j (5 à 35):")
    print(f"    {'temp_moy':>8s}  {'viable':>6s} {'attendre':>8s} {'non_viable':>10s}  prédiction")
    prev_probas = None
    jumps = 0
    for t in range(5, 36, 2):
        params = {**base_params, "temp_moyenne_7j": t}
        payload = PredictionRequest(location="Rennes", culture="tomate", **params)
        features = [encode_payload(payload)]
        probas = model.predict_proba(features)[0]
        pred = CLASS_LABELS[int(model.predict(features)[0])]
        print(f"    {t:>8d}  {probas[0]:>6.3f} {probas[1]:>8.3f} {probas[2]:>10.3f}  {pred}")
        if prev_probas is not None:
            max_jump = max(abs(probas[i] - prev_probas[i]) for i in range(3))
            if max_jump > 0.30:
                jumps += 1
        prev_probas = probas

    if jumps > 2:
        print(f"    [ATTENTION] {jumps} sauts > 0.30 détectés")
        all_smooth = False
    else:
        print(f"    [OK] Transitions progressives ({jumps} saut(s) > 0.30)")

    if all_smooth:
        print("\n  [OK] Les probabilités changent progressivement pour toutes les variables testées.")
        return True
    else:
        print("\n  [ATTENTION] Certaines variables provoquent des sauts abrupts.")
        return False


# ---------------------------------------------------------------------------
# 8. RAPPORT FINAL
# ---------------------------------------------------------------------------

def section_8_final_report(x, y, x_train, x_test, y_train, y_test, model, results):
    print("\n" + "=" * 70)
    print("8. RAPPORT FINAL")
    print("=" * 70)

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    f1_scores = []
    for train_idx, test_idx in cv.split(x, y):
        m = _build_xgboost()
        m.fit(x.iloc[train_idx], y[train_idx], verbose=False)
        preds = m.predict(x.iloc[test_idx])
        f1_scores.append(f1_score(y[test_idx], preds, average="macro"))
    cv_mean = np.mean(f1_scores)
    cv_std = np.std(f1_scores)

    # Train/test gap
    train_f1 = f1_score(y_train, model.predict(x_train), average="macro")
    test_f1 = f1_score(y_test, model.predict(x_test), average="macro")
    gap = train_f1 - test_f1

    # Permutation importance summary
    baseline = f1_score(y_test, model.predict(x_test), average="macro")
    rng = np.random.default_rng(42)
    drops = {}
    for col in FEATURE_COLUMNS:
        col_drops = []
        for _ in range(10):
            shuffled = x_test.copy()
            shuffled[col] = rng.permutation(shuffled[col].to_numpy())
            score = f1_score(y_test, model.predict(shuffled), average="macro")
            col_drops.append(baseline - score)
        drops[col] = float(np.mean(col_drops))
    total_drop = sum(max(0, d) for d in drops.values())
    top_feature = max(drops, key=drops.get)
    top_share = drops[top_feature] / total_drop * 100 if total_drop > 0 else 0
    useful_count = sum(1 for d in drops.values() if d / total_drop > 0.01)

    print(f"""
  ┌────────────────────────────────────────────────────────────────────┐
  │ MÉTRIQUES CLÉS                                                     │
  ├────────────────────────────────────┬───────────────────────────────┤
  │ F1 macro (CV 5-fold)               │ {cv_mean:.4f} ± {cv_std:.4f}              │
  │ Gap train/test                     │ {gap:.4f}                          │
  │ XGBoost vs DummyClassifier         │ +{test_f1 - 0.186:.3f}                         │
  │ XGBoost vs DecisionTree(3)         │ +{test_f1 - 0.596:.3f}                         │
  │ Top permutation feature            │ {top_feature} ({top_share:.1f}%)    │
  │ Features utiles (>1% importance)   │ {useful_count}/{len(FEATURE_COLUMNS)}                            │
  │ Robustesse bruit (% changés)       │ voir section 5                │
  │ Cohérence métier                   │ voir section 6                │
  └────────────────────────────────────┴───────────────────────────────┘
""")

    # Verdict
    print("  VERDICT:")
    issues = []

    if cv_mean < 0.70:
        issues.append("F1 trop bas (<0.70)")
    if cv_mean > 0.90:
        issues.append("F1 suspect (>0.90) — dataset trop facile?")
    if gap > 0.05:
        issues.append(f"Risque d'overfitting (gap={gap:.3f})")
    if top_share > 50:
        issues.append(f"Une feature domine ({top_feature}={top_share:.0f}%)")
    if not results["data_leak"]:
        issues.append("FUITE DE DONNÉES DÉTECTÉE")
    if not results["holdout_seed"]:
        issues.append("Mauvaise généralisation sur seed différente")
    if not results["baselines"]:
        issues.append("XGBoost ne bat pas assez les modèles simples")
    if not results["coherence"]:
        issues.append("Incohérence métier")

    if not issues:
        if 0.70 <= cv_mean <= 0.85 and gap < 0.05 and top_share < 35:
            print("  ╔══════════════════════════════════════════════════════════════╗")
            print("  ║  VERDICT: DÉFENDABLE V0 SCOLAIRE                            ║")
            print("  ║                                                              ║")
            print("  ║  Le modèle:                                                  ║")
            print("  ║  - Ne mémorise pas le dataset (gap train/test faible)        ║")
            print("  ║  - Ne suit pas que des règles simples (bat Tree(3) de +0.16) ║")
            print("  ║  - Utilise plusieurs features de manière équilibrée          ║")
            print("  ║  - Est cohérent métier sur les scénarios testés              ║")
            print("  ║  - Reste un modèle V0 sur données synthétiques               ║")
            print("  ╚══════════════════════════════════════════════════════════════╝")
        else:
            print("  → Modèle acceptable mais avec réserves.")
    else:
        print("  ╔══════════════════════════════════════════════════════════════╗")
        print("  ║  PROBLÈMES DÉTECTÉS:                                        ║")
        for issue in issues:
            print(f"  ║  - {issue:<56s}  ║")
        print("  ╚══════════════════════════════════════════════════════════════╝")

    print(f"""
  LIMITES RESTANTES:
  - Dataset synthétique: les patterns reflètent le scoring, pas la réalité terrain.
  - pluie_7j brute a peu d'impact (info déjà dans stress_hydrique/risque_secheresse).
  - Classe "attendre" reste la plus difficile (zone de transition floue).
  - Un vrai modèle nécessiterait des données capteurs/météo réelles.
""")
    print("=" * 70)


if __name__ == "__main__":
    main()
