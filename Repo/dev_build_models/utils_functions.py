#--*- coding: utf-8 -*-

# ===============================================================
# 1- IMPORTATIONS DES LIBRAIRIES 
# 2- CONFIGURATION DE LA BARRE DE CHARGEMENT
# 3- CLASSES UTILES FREQUENCE D'APPARITION D'UN SINISTRE 
# 4- CLASSE DE PREDICTION DE LA SEVERITE (GRAVITE) D'UN SINISTRE
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
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from xgboost import XGBRegressor
# from lightgbm import LGBMRegressor
# from catboost import CatBoostRegressor
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

def run_internal_step(desc, fn, *args, **kwargs):
    bar = tqdm(total=1, desc=desc, **PROGRESS_STYLE_INTERNAL)
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
class Freq_Preprocessing():
    """Classe de prétraitement pour la fréquence d'apparition d'un sinistre."""
    def __init__(self):
        pass


    def _fit_preprocess_NanRemover(self, df:pd.DataFrame, 
                                   columns_to_remove:List[str], 
                                   threshold:Optional[float]=0.5) -> List[str]:
        """Identifie les colonnes à supprimer en fonction du pourcentage de valeurs manquantes."""
        columns_to_remove = [
            col for col in df.columns if df[col].isna().mean() > threshold
        ]
        return columns_to_remove
    
    def _transform_preprocess_NanRemover(self, df:pd.DataFrame, columns_to_remove:List[str]) :
        """Supprime les colonnes identifiées comme ayant trop de valeurs manquantes."""
        df = df.drop(columns=columns_to_remove, errors='ignore')
        return df


@dataclass
class Feature_Engineer_Freq(BaseEstimator, TransformerMixin):
    """Classe de feature engineering pour la prédiction de la fréquence d'apparition d'un sinistre."""
    def __init__(self):
        self.freq_process = Freq_Preprocessing()
        self.columns_to_remove = []
        self.booking_applied = {}

    def build_feature_engineer(self,
                               fit_process_nan_remover: Optional[bool] = True,
                               transform_process_nan_remover: Optional[bool] = True,
                               threshold: Optional[float] = 0.9):
        """Booking des preprocessing pour fit et transform."""
        self.booking_applied = {
            "fit_process_nan_remover_key": fit_process_nan_remover,
            "transform_process_nan_remover_key": transform_process_nan_remover,
            "threshold_key": threshold}

    def fit(self, X:pd.DataFrame, y:pd.Series=None): 
        """Entraîne les différentes étapes de feature engineering sur les données d'entraînement."""
        if self.booking_applied.get("fit_process_nan_remover_key", False):
            self.columns_to_remove = self.freq_process._fit_preprocess_NanRemover(X, 
                                                                                  self.columns_to_remove, 
                                                                                  self.booking_applied.get("threshold_key", 0.9))
        return self

    def transform(self, X:pd.DataFrame, y:pd.Series=None):
        if self.booking_applied.get("transform_process_nan_remover_key", False):
            X = self.freq_process._transform_preprocess_NanRemover(X, self.columns_to_remove)
        return X

    def predict(self):
        """Fait une prédiction en utilisant le modèle entraîné."""
        pass

    def save_feature_engineer(self, fe, filepath: str):
        """Sauvegarde le feature engineer dans un fichier.

        Args:
            fe (Feature_Engineer_Freq): Le feature engineer à sauvegarder.
            filepath (str): Chemin vers le fichier où sauvegarder le feature engineer.
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                pickle.dump(fe, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du feature engineer: {e}")

    def load_feature_engineer(self, filepath: str):
        """Charge le feature engineer depuis un fichier.

        Args:
            filepath (str): Chemin vers le fichier contenant le feature engineer.

        Returns:
            Feature_Engineer_Freq: Le feature engineer chargé depuis le fichier.
        """
        try:
            with open(filepath, 'rb') as f:
                fe = pickle.load(f)
            return fe
        except Exception as e:
            print(f"Erreur lors du chargement du feature engineer: {e}")
            return None


@dataclass
class Model_Prediction_Freq(BaseEstimator):
    """Classe de prédiction de la fréquence d'apparition d'un sinistre."""
    cv: int = 5
    scoring: str = 'accuracy'
    max_features: int = None
    random_state: int = 42
    ratio_keep_min: float = 0.5
    ratio_keep_max: float = 1.5
    n_repeats_importance: int = 5
    max_iter: int = 1000

    def __init__(self,
                 cv=5,
                 scoring='accuracy',
                 max_features=None,
                 random_state=42,
                 ratio_keep_min=0.5,
                 ratio_keep_max=1.5,
                 n_repeats_importance=5,
                 max_iter=1000):
        self.cv = cv
        self.scoring = scoring
        self.max_features = max_features
        self.random_state = random_state
        self.ratio_keep_min = ratio_keep_min
        self.ratio_keep_max = ratio_keep_max
        self.n_repeats_importance = n_repeats_importance
        self.max_iter = max_iter

        self.selected_features_ = []
        self.selected_features_keep_ = []
        self.selected_features_investigate_ = []
        self.numeric_features_ = []
        self.fill_values_ = {}
        self.contribution_drift_df_ = pd.DataFrame()
        self.model_ = LogisticRegression(max_iter=self.max_iter, random_state=self.random_state)
        self.history_ = []

    def fit(self, X: pd.DataFrame, y: pd.Series):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        X_num = X.select_dtypes(include=[np.number]).copy()
        self.numeric_features_ = list(X_num.columns)
        self.fill_values_ = X_num.median(numeric_only=True).to_dict()
        X_num = X_num.fillna(self.fill_values_)

        if X_num.shape[1] == 0:
            raise ValueError("Aucune colonne numérique disponible pour entraîner le modèle Freq.")

        stratify_y = y if isinstance(y, pd.Series) and y.nunique() > 1 else None
        X_train_i, X_valid_i, y_train_i, y_valid_i = train_test_split(
            X_num,
            y,
            test_size=0.2,
            random_state=self.random_state,
            shuffle=True,
            stratify=stratify_y,
        )

        model_for_importance = LogisticRegression(max_iter=self.max_iter, random_state=self.random_state)
        model_for_importance.fit(X_train_i, y_train_i)

        perm_train = permutation_importance(
            model_for_importance,
            X_train_i,
            y_train_i,
            n_repeats=self.n_repeats_importance,
            random_state=self.random_state,
            scoring=self.scoring,
        )
        perm_valid = permutation_importance(
            model_for_importance,
            X_valid_i,
            y_valid_i,
            n_repeats=self.n_repeats_importance,
            random_state=self.random_state,
            scoring=self.scoring,
        )

        contribution_drift_df = pd.DataFrame({
            'feature': self.numeric_features_,
            'contribution_train': perm_train.importances_mean,
            'contribution_valid': perm_valid.importances_mean,
        })
        contribution_drift_df['drift_abs'] = (
            contribution_drift_df['contribution_train'] - contribution_drift_df['contribution_valid']
        ).abs()
        contribution_drift_df['drift_ratio_train_over_valid'] = (
            contribution_drift_df['contribution_train'].abs() + 1e-9
        ) / (contribution_drift_df['contribution_valid'].abs() + 1e-9)

        keep_mask = (
            (contribution_drift_df['contribution_valid'] > 0)
            & (contribution_drift_df['drift_ratio_train_over_valid'] >= self.ratio_keep_min)
            & (contribution_drift_df['drift_ratio_train_over_valid'] <= self.ratio_keep_max)
        )

        self.selected_features_keep_ = contribution_drift_df.loc[keep_mask, 'feature'].tolist()
        self.selected_features_investigate_ = contribution_drift_df.loc[~keep_mask, 'feature'].tolist()

        if len(self.selected_features_keep_) == 0:
            fallback = contribution_drift_df.loc[
                contribution_drift_df['contribution_valid'] > 0,
                'feature'
            ].tolist()
            self.selected_features_keep_ = fallback if len(fallback) > 0 else self.numeric_features_

        self.selected_features_ = self.selected_features_keep_.copy()
        self.contribution_drift_df_ = contribution_drift_df.sort_values('drift_abs', ascending=False)
        self.history_ = [(self.selected_features_.copy(), None)]

        self.model_ = LogisticRegression(max_iter=self.max_iter, random_state=self.random_state)
        self.model_.fit(X_num[self.selected_features_], y)
        return self

    def predict(self, X: pd.DataFrame):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X_sel = X.reindex(columns=self.selected_features_)
        X_sel = X_sel.fillna(self.fill_values_)
        return self.model_.predict(X_sel)

    def predict_proba(self, X: pd.DataFrame):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X_sel = X.reindex(columns=self.selected_features_)
        X_sel = X_sel.fillna(self.fill_values_)
        return self.model_.predict_proba(X_sel)

    def get_selected_features(self):
        return self.selected_features_

    def get_selected_features_keep(self):
        return self.selected_features_keep_

    def get_selected_features_investigate(self):
        return self.selected_features_investigate_

    def metrics(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        y_pred = self.predict(X)
        accuracy = float((y_pred == y).mean())
        return {
            'accuracy': accuracy
        }

    def save_model(self, model, filepath: str, metadata: Optional[Dict[str, Any]] = None):
        """Sauvegarde le modèle dans un fichier.

        Args:
            model (Model_Prediction_Freq): Le modèle à sauvegarder.
            filepath (str): Chemin vers le fichier où sauvegarder le modèle.
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            artifact = {
                'model_': model,
                'selected_features_': self.selected_features_,
                'selected_features_keep_': self.selected_features_keep_,
                'selected_features_investigate_': self.selected_features_investigate_,
                'numeric_features_': self.numeric_features_,
                'fill_values_': self.fill_values_,
                'contribution_drift_df_': self.contribution_drift_df_.to_dict(orient='records'),
                'history_': self.history_,
                'config': {
                    'cv': self.cv,
                    'scoring': self.scoring,
                    'max_features': self.max_features,
                    'random_state': self.random_state,
                    'ratio_keep_min': self.ratio_keep_min,
                    'ratio_keep_max': self.ratio_keep_max,
                    'n_repeats_importance': self.n_repeats_importance,
                    'max_iter': self.max_iter,
                },
                'metadata': {
                    'saved_at': datetime.utcnow().isoformat(),
                    **(metadata or {}),
                }
            }
            with open(filepath, 'wb') as f:
                pickle.dump(artifact, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du modèle: {e}")

    def load_model(self, filepath: str):
        """Charge le modèle depuis un fichier.

        Args:
            filepath (str): Chemin vers le fichier contenant le modèle.

        Returns:
            Model_Prediction_Freq: Le modèle chargé depuis le fichier.
        """
        try:
            with open(filepath, 'rb') as f:
                loaded = pickle.load(f)

            if isinstance(loaded, dict) and 'model_' in loaded:
                self.model_ = loaded.get('model_', self.model_)
                self.selected_features_ = loaded.get('selected_features_', self.selected_features_)
                self.selected_features_keep_ = loaded.get('selected_features_keep_', self.selected_features_keep_)
                self.selected_features_investigate_ = loaded.get('selected_features_investigate_', self.selected_features_investigate_)
                self.numeric_features_ = loaded.get('numeric_features_', self.numeric_features_)
                self.fill_values_ = loaded.get('fill_values_', self.fill_values_)
                contribution_drift_records = loaded.get('contribution_drift_df_', [])
                self.contribution_drift_df_ = pd.DataFrame(contribution_drift_records)
                self.history_ = loaded.get('history_', self.history_)
                config = loaded.get('config', {})
                self.cv = config.get('cv', self.cv)
                self.scoring = config.get('scoring', self.scoring)
                self.max_features = config.get('max_features', self.max_features)
                self.random_state = config.get('random_state', self.random_state)
                self.ratio_keep_min = config.get('ratio_keep_min', self.ratio_keep_min)
                self.ratio_keep_max = config.get('ratio_keep_max', self.ratio_keep_max)
                self.n_repeats_importance = config.get('n_repeats_importance', self.n_repeats_importance)
                self.max_iter = config.get('max_iter', self.max_iter)
                return loaded

            self.model_ = loaded
            return loaded
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            return None

    def read_artifact_metadata(self, filepath: str) -> Optional[Dict[str, Any]]:
        try:
            with open(filepath, 'rb') as f:
                loaded = pickle.load(f)

            if isinstance(loaded, dict):
                return loaded.get('metadata', None)
            return None
        except Exception as e:
            print(f"Erreur lors de la lecture des métadonnées de l'artefact: {e}")
            return None



# ===========================================================================
# 4--- CLASSE DE PREDICTION DE LA SEVERITE (GRAVITE) D'UN SINISTRE --------#
# ===========================================================================
@dataclass
class Amount_Preprocessing:

    """Classe de prétraitement pour la prédiction du montant d'un sinistre."""
    def __init__(self):
        self.preprocessing_map = {}
        self.categorical_features = []

    def transform_remove_zero_target(self, df, target_col='montant_sinistre'):
        """Retire les lignes où la cible (target_col) est nulle."""
        if target_col in df.columns:
            return df[df[target_col] != 0].copy()
        return df
    def transform_remove_null_target(self, df, target_col='montant_sinistre'):
        """Retire les lignes où la ou les colonnes cibles (target_col) sont nulles (NaN)."""
        if isinstance(target_col, list):
            for col in target_col:
                if col in df.columns:
                    df = df[df[col].notnull()]
            return df.copy()
        elif isinstance(target_col, str):
            if target_col in df.columns:
                return df[df[target_col].notnull()].copy()
        return df
    def set_categorical_features(self, categorical_features):
        self.categorical_features = categorical_features

    def encode_categorical_features(self, df):
        df = df.copy()
        for col in self.categorical_features:
            if col in df.columns:
                df[col] = df[col].astype('category').cat.codes
        return df

    def set_preprocessing_map(self, preprocessing_map):
        self.preprocessing_map = preprocessing_map

    def winsorize_feature(self, df, col, lower=0.01, upper=0.99):
        if col in df.columns:
            l = df[col].quantile(lower)
            u = df[col].quantile(upper)
            df[col] = np.clip(df[col], l, u)
        return df

    def log_transform_feature(self, df, col):
        if col in df.columns and (df[col] > 0).all():
            df[col] = np.log1p(df[col])
        return df

    def bin_feature(self, df, col, bins=5):
        if col in df.columns:
            df[col] = pd.cut(df[col], bins=bins, labels=False)
        return df

    def apply_preprocessing(self, df):
        df = df.copy()
        # Appliquer les traitements numériques
        for col, method in self.preprocessing_map.items():
            if method == 'winsorize':
                df = self.winsorize_feature(df, col)
            elif method == 'log':
                df = self.log_transform_feature(df, col)
            elif method == 'bin':
                df = self.bin_feature(df, col)
        # Appliquer l'encodage catégoriel
        if self.categorical_features:
            df = self.encode_categorical_features(df)
        return df

    def _fit_preprocess_NanRemover(self, df:pd.DataFrame, 
                                   columns_to_remove:List[str], 
                                   threshold:Optional[float]=0.9) -> List[str]:
        """Identifie les colonnes à supprimer en fonction du pourcentage de valeurs manquantes."""
        columns_to_remove = [
            col for col in df.columns if df[col].isna().mean() > threshold
        ]
        return columns_to_remove
    
    def _transform_preprocess_NanRemover(self, df:pd.DataFrame, columns_to_remove:List[str]) :
        """Supprime les colonnes identifiées comme ayant trop de valeurs manquantes."""
        df = df.drop(columns=columns_to_remove, errors='ignore')
        return df

@dataclass
class Feature_Engineer_Amount(BaseEstimator, TransformerMixin):
    """Classe de feature engineering pour la prédiction du montant d'un sinistre."""
    def __init__(self, amount_process: Amount_Preprocessing):
        self.amount_process = amount_process
        self.columns_to_remove = []
        self.booking_applied = {}
        self.preprocessing_map = {}
        self.categorical_features = []

    def build_feature_engineer(self,
                               fit_process_nan_remover: Optional[bool] = True,
                               transform_process_nan_remover: Optional[bool] = True,
                               transform_remove_zero_target: Optional[bool] = True,
                               threshold: Optional[float] = 0.9,
                               preprocessing_map: Optional[dict] = None,
                               categorical_features: Optional[list] = None,
                               transform_remove_null_target: Optional[bool] = True):
        """Booking des preprocessing pour fit, transform, suppression des zéros et features catégorielles."""
        self.booking_applied = {
            "fit_process_nan_remover_key": fit_process_nan_remover,
            "transform_process_nan_remover_key": transform_process_nan_remover,
            "transform_remove_zero_target_key": transform_remove_zero_target,
            "transform_remove_null_target_key": transform_remove_null_target,
            "threshold_key": threshold
        }
        if preprocessing_map:
            self.preprocessing_map = preprocessing_map
            self.amount_process.set_preprocessing_map(preprocessing_map)
        if categorical_features:
            self.categorical_features = categorical_features
            self.amount_process.set_categorical_features(categorical_features)

    def fit(self, X:pd.DataFrame, y:pd.Series=None):
        if self.booking_applied.get("fit_process_nan_remover_key", False):
            self.columns_to_remove = self.amount_process._fit_preprocess_NanRemover(X, 
                                                                                    self.columns_to_remove, 
                                                                                    self.booking_applied.get("threshold_key", 0.9))

        return self

    def transform(self, X:pd.DataFrame, y:pd.Series=None):
        if self.booking_applied.get("transform_remove_zero_target_key", False):
            X = self.amount_process.transform_remove_zero_target(X)
        if self.booking_applied.get("transform_remove_null_target_key", False):
            X = self.amount_process.transform_remove_null_target(X)
        if self.booking_applied.get("transform_process_nan_remover_key", False):
            X = self.amount_process.transform_remove_null_target(X, self.columns_to_remove)
        if self.preprocessing_map:
            X = self.amount_process.apply_preprocessing(X)
        return X

    def save_feature_engineer(self, fe, filepath: str):
        """Sauvegarde le feature engineer dans un fichier.

        Args:
            fe (Feature_Engineer_Amount): Le feature engineer à sauvegarder.
            filepath (str): Chemin vers le fichier où sauvegarder le feature engineer.
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                pickle.dump(fe, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du feature engineer: {e}")

    def load_feature_engineer(self, filepath: str):
        """Charge le feature engineer depuis un fichier.

        Args:
            filepath (str): Chemin vers le fichier contenant le feature engineer.

        Returns:
            Feature_Engineer_Amount: Le feature engineer chargé depuis le fichier.
        """
        try:
            with open(filepath, 'rb') as f:
                fe = pickle.load(f)
            return fe
        except Exception as e:
            print(f"Erreur lors du chargement du feature engineer: {e}")
            return None

@dataclass
class Model_Prediction_Amount(BaseEstimator):
    """Classe de prédiction du montant d'un sinistre, supporte plusieurs modèles nommés."""
    cv: int = 5
    val_kfold: Optional[KFold] = KFold(n_splits=5, shuffle=True, random_state=42)
    scoring: str = 'neg_mean_squared_error'
    max_features: int = None
    random_state: int = 42
    tol_improvement: float = 1e-6

    def __init__(self,
                 cv=5,
                 val_kfold=None,
                 scoring='neg_mean_squared_error',
                 max_features=None,
                 random_state=42,
                 tol_improvement=1e-6,
                 ratio_keep_min=0.5,
                 ratio_keep_max=1.5,
                 n_repeats_importance=5,
                 models=None):
        self.cv = cv
        self.val_kfold = val_kfold
        self.scoring = scoring
        self.max_features = max_features
        self.random_state = random_state
        self.tol_improvement = tol_improvement
        self.ratio_keep_min = ratio_keep_min
        self.ratio_keep_max = ratio_keep_max
        self.n_repeats_importance = n_repeats_importance
        self.selected_features_ = []
        self.selected_features_keep_ = []
        self.selected_features_investigate_ = []
        self.numeric_features_ = []
        self.fill_values_ = {}
        self.contribution_drift_df_ = pd.DataFrame()
        self.history_ = []  # pour tracer l'évolution de la sélection (features sélectionnées, score)

        # Ajout : support d'un dictionnaire {nom: modèle}
        if models is None:
            self.models_ = {#"LinearRegression": LinearRegression(),
                            #"Ridge": Ridge(),
                            #"Lasso": Lasso(),
                            #"ElasticNet": ElasticNet(),
                            #"RandomForest": RandomForestRegressor(),
                            #"GBR": GradientBoostingRegressor(),
                            #"SVR": SVR(),
                            #"KNN": KNeighborsRegressor(),
                            "XGBoost": XGBRegressor(),
                            # "LightGBM": LGBMRegressor(),
                            #"CatBoost": CatBoostRegressor(),
            }
        elif isinstance(models, dict):
            self.models_ = models
        else:
            raise ValueError("models doit être un dictionnaire {nom: modèle}")
        # Par défaut, le premier modèle du dict est utilisé
        self.model_name_ = list(self.models_.keys())[0]
        self.model_ = self.models_[self.model_name_]
    
    def fit(self, X: pd.DataFrame, y: pd.Series, model_name: str = None, kfold=None):
        """
        Correction :
        - Chaque modèle s'entraîne sur le split train/valid utilisé pour l'importance.
        - Importance calculée sur le modèle courant.
        - Features sélectionnées par permutation importance du modèle courant.
        - Traçabilité complète.
        """
        if kfold is None:
            kfold = self.val_kfold

        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        X_num = X.select_dtypes(include=[np.number]).copy()
        X_num = X_num.drop(columns=['index'], errors='ignore')
        self.numeric_features_ = list(X_num.columns)
        self.fill_values_ = X_num.median(numeric_only=True).to_dict()
        X_num = X_num.fillna(self.fill_values_)

        if X_num.shape[1] == 0:
            raise ValueError("Aucune colonne numérique disponible pour entraîner le modèle Amount.")

        # Split train/valid pour importance et entraînement
        if kfold is not None:
            splits = run_internal_step("KFold split", kfold.split, X_num, y)
            train_idx, valid_idx = splits[0]
            X_train_i, X_valid_i = X_num.iloc[train_idx], X_num.iloc[valid_idx]
            y_train_i, y_valid_i = y.iloc[train_idx], y.iloc[valid_idx]
        else:
            X_train_i, X_valid_i, y_train_i, y_valid_i = run_internal_step(
                "Train/Validation split",
                train_test_split,
                X_num,
                y,
                test_size=0.2,
                random_state=self.random_state,
                shuffle=True,
            )

        self.models_features_ = {}
        self.models_contribution_ = {}
        self.models_history_ = {}
        self.models_artifacts_ = {}  # Ajout : artefact structuré par modèle

        # Si model_name fourni, fit uniquement ce modèle
        if model_name is not None:
            if model_name not in self.models_:
                raise ValueError(f"Le modèle '{model_name}' n'est pas dans models_ : {list(self.models_.keys())}")
            model = self.models_[model_name]
            # Importance sur le modèle courant
            run_internal_step("Fit modèle: " + model_name, model.fit, X_train_i, y_train_i)
            perm_train = run_internal_step("Permutation importance train", permutation_importance,
                model,
                X_train_i,
                y_train_i,
                n_repeats=self.n_repeats_importance,
                random_state=self.random_state,
                scoring=self.scoring,
            )
            perm_valid = run_internal_step("Permutation importance valid", permutation_importance,
                                           model,
                                           X_valid_i,
                                           y_valid_i,
                                           n_repeats=self.n_repeats_importance,
                                           random_state=self.random_state,
                                           scoring=self.scoring,
            )
            contribution_drift_df = pd.DataFrame({
                'feature': self.numeric_features_,
                'contribution_train': perm_train.importances_mean,
                'contribution_valid': perm_valid.importances_mean,
            })
            contribution_drift_df['drift_abs'] = (
                contribution_drift_df['contribution_train'] - contribution_drift_df['contribution_valid']
            ).abs()
            contribution_drift_df['drift_ratio_train_over_valid'] = (
                contribution_drift_df['contribution_train'].abs() + 1e-9
            ) / (contribution_drift_df['contribution_valid'].abs() + 1e-9)

            keep_mask = (
                (contribution_drift_df['contribution_valid'] > 0)
                & (contribution_drift_df['drift_ratio_train_over_valid'] >= self.ratio_keep_min)
                & (contribution_drift_df['drift_ratio_train_over_valid'] <= self.ratio_keep_max)
            )
            selected_features = contribution_drift_df.loc[keep_mask, 'feature'].tolist()
            if len(selected_features) == 0:
                fallback = contribution_drift_df.loc[
                    contribution_drift_df['contribution_valid'] > 0,
                    'feature'
                ].tolist()
                selected_features = fallback if len(fallback) > 0 else self.numeric_features_
            self.selected_features_ = selected_features.copy()
            self.selected_features_keep_ = selected_features.copy()
            self.selected_features_investigate_ = contribution_drift_df.loc[~keep_mask, 'feature'].tolist()
            self.contribution_drift_df_ = contribution_drift_df.sort_values('drift_abs', ascending=False)
            self.history_ = [(self.selected_features_.copy(), None)]
            self.models_features_[model_name] = self.selected_features_.copy()
            self.models_contribution_[model_name] = contribution_drift_df.copy()
            self.models_history_[model_name] = [(self.selected_features_.copy(), None)]
            # Fit sur features sélectionnées
            run_internal_step("Fit " + model_name + " sur features sélectionnées", model.fit, X_num[self.selected_features_], y)
            self.model_name_ = model_name
            self.model_ = model
            # Ajout artefact structuré
            self.models_artifacts_[model_name] = {
                'model': model,
                'selected_features': self.selected_features_.copy(),
                'selected_features_keep': self.selected_features_keep_.copy(),
                'selected_features_investigate': self.selected_features_investigate_.copy(),
                'numeric_features': self.numeric_features_.copy(),
                'fill_values': self.fill_values_.copy(),
                'contribution_drift_df': contribution_drift_df.copy(),
                'history': self.history_.copy(),
                'config': {
                    'cv': self.cv,
                    'scoring': self.scoring,
                    'max_features': self.max_features,
                    'random_state': self.random_state,
                    'tol_improvement': self.tol_improvement,
                    'ratio_keep_min': self.ratio_keep_min,
                    'ratio_keep_max': self.ratio_keep_max,
                    'n_repeats_importance': self.n_repeats_importance,
                },
                'performance': self.metrics(X_num[self.selected_features_], y, model_name=model_name),
                'metadata': {
                    'fitted_at': datetime.utcnow().isoformat(),
                }
            }
        else:
            for name, model in self.models_.items():
                run_internal_step("Fit " + name + " sur features sélectionnées", model.fit, X_train_i, y_train_i)
                perm_train = run_internal_step("Permutation importance train", permutation_importance,
                    model,
                    X_train_i,
                    y_train_i,
                    n_repeats=self.n_repeats_importance,
                    random_state=self.random_state,
                    scoring=self.scoring,
                )
                perm_valid = run_internal_step("Permutation importance valid", permutation_importance,
                    model,
                    X_valid_i,
                    y_valid_i,
                    n_repeats=self.n_repeats_importance,
                    random_state=self.random_state,
                    scoring=self.scoring,
                )
                contribution_drift_df = pd.DataFrame({
                    'feature': self.numeric_features_,
                    'contribution_train': perm_train.importances_mean,
                    'contribution_valid': perm_valid.importances_mean,
                })
                contribution_drift_df['drift_abs'] = (
                    contribution_drift_df['contribution_train'] - contribution_drift_df['contribution_valid']
                ).abs()
                contribution_drift_df['drift_ratio_train_over_valid'] = (
                    contribution_drift_df['contribution_train'].abs() + 1e-9
                ) / (contribution_drift_df['contribution_valid'].abs() + 1e-9)

                keep_mask = (
                    (contribution_drift_df['contribution_valid'] > 0)
                    & (contribution_drift_df['drift_ratio_train_over_valid'] >= self.ratio_keep_min)
                    & (contribution_drift_df['drift_ratio_train_over_valid'] <= self.ratio_keep_max)
                )
                selected_features = contribution_drift_df.loc[keep_mask, 'feature'].tolist()
                if len(selected_features) == 0:
                    fallback = contribution_drift_df.loc[
                        contribution_drift_df['contribution_valid'] > 0,
                        'feature'
                    ].tolist()
                    selected_features = fallback if len(fallback) > 0 else self.numeric_features_
                self.models_features_[name] = selected_features.copy()
                self.models_contribution_[name] = contribution_drift_df.copy()
                self.models_history_[name] = [(selected_features.copy(), None)]
                # Fit sur features sélectionnées
                run_internal_step("Fit " + name + " sur features sélectionnées", model.fit, X_num[selected_features], y)
                # Ajout artefact structuré
                self.models_artifacts_[name] = {
                    'model': model,
                    'selected_features': selected_features.copy(),
                    'selected_features_keep': selected_features.copy(),
                    'selected_features_investigate': contribution_drift_df.loc[~keep_mask, 'feature'].tolist(),
                    'numeric_features': self.numeric_features_.copy(),
                    'fill_values': self.fill_values_.copy(),
                    'contribution_drift_df': contribution_drift_df.copy(),
                    'history': self.models_history_[name].copy(),
                    'config': {
                        'cv': self.cv,
                        'scoring': self.scoring,
                        'max_features': self.max_features,
                        'random_state': self.random_state,
                        'tol_improvement': self.tol_improvement,
                        'ratio_keep_min': self.ratio_keep_min,
                        'ratio_keep_max': self.ratio_keep_max,
                        'n_repeats_importance': self.n_repeats_importance,
                    },
                    'performance': self.metrics(X_num[selected_features], y, model_name=name),
                    'metadata': {
                        'fitted_at': datetime.utcnow().isoformat(),
                    }
                }
            
            # On garde le modèle principal comme le premier du dict
            first_model = list(self.models_.keys())[0]
            self.selected_features_ = self.models_features_[first_model].copy()
            self.selected_features_keep_ = self.selected_features_.copy()
            self.selected_features_investigate_ = self.models_contribution_[first_model].loc[~keep_mask, 'feature'].tolist()
            self.contribution_drift_df_ = self.models_contribution_[first_model].sort_values('drift_abs', ascending=False)
            self.history_ = self.models_history_[first_model].copy()
            self.model_name_ = first_model
            self.model_ = self.models_[first_model]
        return self

    def predict(self, X: pd.DataFrame, model_name: str = None, kfold=None):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X = X.drop(columns=['index'], errors='ignore')
        # Correction : utiliser les features sélectionnées par modèle
        if model_name is not None:
            if model_name not in self.models_:
                raise ValueError(f"Le modèle '{model_name}' n'est pas dans models_ : {list(self.models_.keys())}")
            model = self.models_[model_name]
            features = self.models_features_.get(model_name, self.selected_features_)
            fill_values = self.fill_values_  # Option : peut être affiné par modèle
        else:
            model = self.model_
            features = self.selected_features_
            fill_values = self.fill_values_
        X_sel = X.reindex(columns=features)
        X_sel = X_sel.fillna(fill_values)
        return model.predict(X_sel)

    def get_selected_features(self):
        return self.selected_features_

    def get_selected_features_keep(self):
        return self.selected_features_keep_

    def get_selected_features_investigate(self):
        return self.selected_features_investigate_

    def metrics(self, X:pd.DataFrame, y:pd.Series, model_name: str = None, kfold=None) -> Dict[str, float]:
        """Évalue les performances du modèle en utilisant différentes métriques.

        Args:
            X (pd.DataFrame): Les données d'entrée pour l'évaluation.
            y (pd.Series): Les étiquettes réelles correspondantes aux données d'entrée.
            model_name (str): Nom du modèle à utiliser (par défaut None = modèle principal)

        Returns:
            Dict[str, float]: Un dictionnaire contenant les valeurs des métriques d'évaluation.
        """
        y_pred = self.predict(X, model_name=model_name, kfold=kfold)
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        return {
            'MSE': mse,
            'RMSE': rmse
        }
    def save_model(self, model_, filepath: str, metadata: Optional[Dict[str, Any]] = None):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        artifact = {
            'model_': model_,
            'selected_features_': self.selected_features_,
            'selected_features_keep_': self.selected_features_keep_,
            'selected_features_investigate_': self.selected_features_investigate_,
            'numeric_features_': self.numeric_features_,
            'fill_values_': self.fill_values_,
            'contribution_drift_df_': self.contribution_drift_df_.to_dict(orient='records'),
            'history_': self.history_,
            'config': {
                'cv': self.cv,
                'scoring': self.scoring,
                'max_features': self.max_features,
                'random_state': self.random_state,
                'tol_improvement': self.tol_improvement,
                'ratio_keep_min': self.ratio_keep_min,
                'ratio_keep_max': self.ratio_keep_max,
                'n_repeats_importance': self.n_repeats_importance,
            },
            'metadata': {
                'saved_at': datetime.utcnow().isoformat(),
                **(metadata or {}),
            }
        }
        with open(filepath, 'wb') as f:
            pickle.dump(artifact, f)

    def load_model(self, filepath: str):
        """Charge le modèle depuis un fichier.

        Args:
            filepath (str): Chemin vers le fichier contenant le modèle.

        Returns:
            Model_Prediction_Amount: Le modèle chargé depuis le fichier.
        """
        try:
            with open(filepath, 'rb') as f:
                loaded = pickle.load(f)

            if isinstance(loaded, dict) and 'model_' in loaded:
                self.model_ = loaded.get('model_', self.model_)
                self.selected_features_ = loaded.get('selected_features_', self.selected_features_)
                self.selected_features_keep_ = loaded.get('selected_features_keep_', self.selected_features_keep_)
                self.selected_features_investigate_ = loaded.get('selected_features_investigate_', self.selected_features_investigate_)
                self.numeric_features_ = loaded.get('numeric_features_', self.numeric_features_)
                self.fill_values_ = loaded.get('fill_values_', self.fill_values_)
                contribution_drift_records = loaded.get('contribution_drift_df_', [])
                self.contribution_drift_df_ = pd.DataFrame(contribution_drift_records)
                self.history_ = loaded.get('history_', self.history_)
                config = loaded.get('config', {})
                self.cv = config.get('cv', self.cv)
                self.scoring = config.get('scoring', self.scoring)
                self.max_features = config.get('max_features', self.max_features)
                self.random_state = config.get('random_state', self.random_state)
                self.tol_improvement = config.get('tol_improvement', self.tol_improvement)
                self.ratio_keep_min = config.get('ratio_keep_min', self.ratio_keep_min)
                self.ratio_keep_max = config.get('ratio_keep_max', self.ratio_keep_max)
                self.n_repeats_importance = config.get('n_repeats_importance', self.n_repeats_importance)
                return loaded

            self.model_ = loaded
            return loaded
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            return None
        
    def read_artifact_metadata(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Lit uniquement les métadonnées d'un artefact modèle sauvegardé.

        Args:
            filepath (str): Chemin vers le fichier d'artefact.

        Returns:
            Optional[Dict[str, Any]]: Dictionnaire de métadonnées si présent, sinon None.
        """
        try:
            with open(filepath, 'rb') as f:
                loaded = pickle.load(f)

            if isinstance(loaded, dict):
                return loaded.get('metadata', None)
            return None
        except Exception as e:
            print(f"Erreur lors de la lecture des métadonnées de l'artefact: {e}")
            return None
    