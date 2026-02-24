#--*- coding: utf-8 -*-

# ===============================================================
# 1- IMPORTATIONS DES LIBRAIRIES 
# 2- CONFIGURATION DE LA BARRE DE CHARGEMENT
# 3- CLASSES UTILES FREQUENCE D'APPARITION D'UN SINISTRE 
# 4- CLASSE DE PREDICTION DE LA SEVERITE (GRAVITE) D'UN SINISTRE
# 5- CLASSE D'ANALYSES COMPARAISONS AFFICHAGES DES RESULTATS
# ===============================================================

# =============================================
# 1- ---- IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
# --- Standard library ---
import os
import pickle
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
# --- Scientific stack ---
import numpy as np
import pandas as pd
# --- Scikit-learn ---
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.datasets import make_regression
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, make_scorer
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline


# ===================================================
# 2----- CONFIGURATION DE LA BARRE DE CHARGEMENT ---#
# ===================================================
try:
    from tqdm.auto import tqdm
except ImportError:
    class _DummyTqdm:
        def __init__(self, total=1, desc=None, leave=True):
            pass
        def update(self, n):
            pass
        def close(self):
            pass
    def tqdm(*args, **kwargs):
        return _DummyTqdm()
    
PROGRESS_STYLE = {
    'ascii': True,
    'colour': 'cyan',
    'bar_format': '{l_bar}{bar} | {n_fmt}/{total_fmt} • {elapsed} < {remaining}',
    'dynamic_ncols': True,
    'leave': True,
}
PROGRESS_STYLE_INTERNAL = {
    'ascii': True,
    'colour': 'red',
    'bar_format': '{l_bar}{bar} | {n_fmt}/{total_fmt} • {elapsed} < {remaining}',
    'dynamic_ncols': True,
    'leave': True,
}
def run_step(desc, fn, *args, **kwargs):
    bar = tqdm(total=1, desc=desc, **PROGRESS_STYLE)
    try:
        result = fn(*args, **kwargs)
        bar.update(1)
    finally:
        bar.close()
    return result


# ===========================================================================
# 3--- CLASSES UTILES FREQUENCE D'APPARITION D'UN SINISTRE --------#
# ===========================================================================
@dataclass
class Freq_Preprocessing((BaseEstimator, TransformerMixin)):
    """Classe de prétraitement pour la fréquence d'apparition d'un sinistre."""
    def __init__(self):
        pass
    # Liste des pre-traitements
    def _fit_preprocess_name_1(self):
        pass
    
    def _transform_preprocess_name_1(slef):
        pass

@dataclass
class Feature_Engineer_Freq(BaseEstimator, TransformerMixin):
    """Classe de feature engineering pour la prédiction de la fréquence d'apparition d'un sinistre."""
    def __init__(self):
        self.freq_process = Freq_Preprocessing()
        self.columns_to_remove = []
        self.booking_applied = {} # Booking des preprocessing pour la Feature_Engineering

    def build_feature_engineer(self):
        """ Le constructeur de la Feature Engineering"""
        pass

    def fit(self, X:pd.DataFrame, y:pd.Series=None): 
        """Entraîne les différentes étapes de feature engineering sur les données d'entraînement."""
        pass

    def transform(self, X:pd.DataFrame, y:pd.Series=None):
        pass

    def predict(self):
        """Fait une prédiction en utilisant le modèle entraîné."""
        pass

    def save_feature_engineer(self, fe, filepath: str):
        """Sauvegarde le feature engineer dans un fichier"""
        pass

    def load_feature_engineer(self, filepath: str):
        """Charge le feature engineer depuis un fichier"""
        pass

@dataclass
class Model_Prediction_Freq(BaseEstimator):
    """Classe de prédiction de la fréquence d'apparition d'un sinistre."""
    # Liste des hyper-paramètres
    # cv: int = 5
    # scoring: Optional[str] = 'accuracy'
    # max_features: Optional[int] = None
    # random_state: Optional[int] = 42
    # ratio_keep_min: Optional[float] = 0.5
    # ratio_keep_max: Optional[float] = 1.5
    # n_repeats_importance: Optional[int] = 5
    # max_iter: Optional[int] = 1000

    def __init__(self,
            # Déclare les arguments du constructeur de la classe
            # cv=
            # scoring =
            # max_features = 
            # random_state = 
            # ratio_keep_min = 
            # ratio_keep_max = 
            # n_repeats_importance = 
            # max_iter = 
        ):
        # self.cv = cv
        # self.scoring = scoring
        # self.max_features = max_features
        # self.random_state = random_state
        # self.ratio_keep_min = ratio_keep_min
        # self.ratio_keep_max = ratio_keep_max
        # self.n_repeats_importance = n_repeats_importance
        # self.max_iter = max_iter

        # Penser à tout 
        # self.selected_features_ = []
        # self.selected_features_keep_ = []
        # self.selected_features_investigate_ = []
        # self.numeric_features_ = []
        # self.fill_values_ = {}
        # self.contribution_drift_df_ = pd.DataFrame()

        # Une liste de modèles danss l'idéal    
        # self.model_ = LogisticRegression(max_iter=self.max_iter, random_state=self.random_state)
        # Optionnel idée garder la trace des transformations
        # self.history_ = [] 
        pass

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """ Entrainement"""

        # Après entrainement garder une trace dans un artefact en pickle
        # Ajout artefact structuré : il y a pour cela un boucle sur les la liste des modèles passé dans le constructeur
        # self.models_artifacts_[model_name] = {
        #     'model': model,
        #     'selected_features': self.selected_features_.copy(),
        #     'selected_features_keep': self.selected_features_keep_.copy(),
        #     'selected_features_investigate': self.selected_features_investigate_.copy(),
        #     'numeric_features': self.numeric_features_.copy(),
        #     'fill_values': self.fill_values_.copy(),
        #     'contribution_drift_df': contribution_drift_df.copy(),
        #     'history': self.models_history_.copy(),
        #     'config': {
        #         'cv': self.cv,
        #         'scoring': self.scoring,
        #         'max_features': self.max_features,
        #         'random_state': self.random_state,
        #         'tol_improvement': self.tol_improvement,
        #         'ratio_keep_min': self.ratio_keep_min,
        #         'ratio_keep_max': self.ratio_keep_max,
        #         'n_repeats_importance': self.n_repeats_importance,
        #     },
        #     'performance': self.metrics(X_num[self.selected_features_], y, model_name=model_name),
        #     'metadata': {
        #         'fitted_at': datetime.utcnow().isoformat(),
        #     }
        # }
        pass

    def predict(self, X: pd.DataFrame):
        """ Prédiction"""
        pass

    def predict_proba(self, X: pd.DataFrame):
        """ Prédiction spécifique"""
        pass

    def get_selected_features(self):
        """ Obtenir les variables explicatives qui ont été sélectionnées"""
        pass

    def get_selected_features_keep(self):
        """ Obtenir les variables explicatives qui ont contribuées à la construction du/des modèle(s)"""
        pass

    def get_selected_features_investigate(self):
        """ Obtenir les varialbes explicatives qui nécessite une investigation poussée"""
        pass

    def metrics(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """ Les metriques de performances"""
        pass

    def save_model(self, model, filepath: str, metadata: Optional[Dict[str, Any]] = None):
        """Sauvegarde le modèle dans un fichier."""
        pass

    def load_model(self, filepath: str):
        """Charge le modèle depuis un fichier."""
        pass

    def read_artifact_metadata(self, filepath: str) -> Optional[Dict[str, Any]]:
        """ Lire l'artefact du modèle"""
        pass



# ===========================================================================
# 4--- CLASSE DE PREDICTION DE LA SEVERITE (GRAVITE) D'UN SINISTRE --------#
# ===========================================================================
@dataclass
class Amount_Preprocessing():
    """Classe de prétraitement pour la prédiction du montant d'un sinistre."""
    def __init__(self):
        pass
    # Liste des pre-traitements
    def _fit_preprocess_name_1(self):
        pass
    
    def _transform_preprocess_name_1(slef):
        pass


@dataclass
class Feature_Engineer_Amount(BaseEstimator, TransformerMixin):
    """Classe de feature engineering pour la prédiction du montant d'un sinistre."""
    
    def __init__(self):
        pass
    # Liste des pre-traitements
    def _fit_preprocess_name_1(self):
        pass
    
    def _transform_preprocess_name_1(slef):
        pass


@dataclass
class Model_Prediction_Amount(BaseEstimator):
    """Classe de prédiction du montant d'un sinistre, supporte plusieurs modèles nommés."""
    
    # Liste des hyper-paramètres

    def __init__(self,
            # Déclare les arguments du constructeur de la classe

        ):
        # Leurs instanciations
        # Et plus.. 
        pass

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """ Entrainement"""
        pass

    def predict(self, X: pd.DataFrame):
        """ Prédiction"""
        pass

    def predict_proba(self, X: pd.DataFrame):
        """ Prédiction spécifique"""
        pass

    def get_selected_features(self):
        """ Obtenir les variables explicatives qui ont été sélectionnées"""
        pass

    def get_selected_features_keep(self):
        """ Obtenir les variables explicatives qui ont contribuées à la construction du/des modèle(s)"""
        pass

    def get_selected_features_investigate(self):
        """ Obtenir les varialbes explicatives qui nécessite une investigation poussée"""
        pass

    def metrics(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """ Les metriques de performances"""
        pass

    def save_model(self, model, filepath: str, metadata: Optional[Dict[str, Any]] = None):
        """Sauvegarde le modèle dans un fichier."""
        pass

    def load_model(self, filepath: str):
        """Charge le modèle depuis un fichier."""
        pass

    def read_artifact_metadata(self, filepath: str) -> Optional[Dict[str, Any]]:
        """ Lire l'artefact du modèle"""
        pass


# ===========================================================================
# 5- ----- CLASSE D'ANALYSES COMPARAISONS AFFICHAGES DES RESULTATS --------#
# ===========================================================================@dataclass
class Analyses_Comparaisons_Affichages_Resultats:
    """Classe qui restitur le travail de moélisation"""
    def __init__(self):
        pass

    def affichage_artefact(self, path:str)-> None:
        """Affiche l'arteface d'un modèle"""
        pass

    def afficher_metadata(self, path:str) -> None:
        """Affiche les metadata du modèle complet"""
        pass

    def analyser_model_complet(self, path:str)-> None:
        """Analyse les performances d'un modèle complet"""
        pass
    def comparer_les_modeles_complet(slef, path:str) -> None:
        """ Comparaison des performances pour plusieurs modèles"""
        pass