#--*- coding: utf-8 -*-

# =================================================================================================================
# 1- Importation des librairies
# 2- Configuration des barres de chargements pour visualiser les étpates 

# --------- FREQ ->
# 3- Clase fille Preprocessing_Freq : pour le préprocessing (héritage: BasEstimator, TransformerMixin)
# 4- Clase fille Feature_Engineer_Freq pour la feature engineering:  (héritage: BasEstimator, TransformerMixin)
# 5- Clase fille Model_Prediction_Freq pour le prédiction:  (héritage: BasEstimator)
# 6- Clase mère ModelPipeline_Freq pour orchestrer la construction, l’entraînement, l’amélioration du modèle

# --------- AMOUNT ->
# 7- Clase fille Preprocessing_Amount : pour le préprocessing (héritage: BasEstimator, TransformerMixin)
# 8- Clase fille Feature_Engineer_Amount pour la feature engineering:  (héritage: BasEstimator, TransformerMixin)
# 9- Clase fille Model_Prediction_Amount pour le prédiction:  (héritage: BasEstimator)
# 10- Clase mère ModelPipeline_Amount pour orchestrer la construction, l’entraînement, l’amélioration du modèle

# --------- AFFICHAGE ->
# 11- Clase pour les affichages les rendus

# --------- TEST UNITAIRE ->
# 12- Clase pour faire les testes unitaires
# =================================================================================================================



# =============================================
# 1- ---- IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
# --- Standard library ---
import os
import pickle
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

# --- Teste stack ---
import unittest

# --- Scientific stack ---
from matplotlib.path import Path
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

def run_internal_step(desc, fn, *args, **kwargs):
    bar = tqdm(total=1, desc=desc, **PROGRESS_STYLE_INTERNAL)
    try:
        result = fn(*args, **kwargs)
        bar.update(1)
    finally:
        bar.close()
    return result



# --------- FREQ ->
# ===================================================================================================
# 3- Clase fille Preprocessing_Freq : pour le préprocessing (héritage: BasEstimator, TransformerMixin)
# =====================================================================================================
class Preprocessing_Freq(BaseEstimator, TransformerMixin):
    def __init__(self, nan_remover=True):
        # flag to enable nan remover; method `nan_remover` remains callable
        self.nan_remover_enabled = nan_remover

    def nan_remover(self, df: pd.DataFrame, threshold: Optional[float]=0.5) -> List[str]:
            """Identifie les colonnes à supprimer en fonction du pourcentage de valeurs manquantes."""
            try:
                columns_to_remove = [
                    col for col in df.columns if df[col].isna().mean() > threshold
                ]
                return columns_to_remove
            except Exception as e:
                print(f"[ERROR][Preprocessing][nan_remover] {str(e)}")
                raise
    def fit(self, X, y=None):
            try:
                # ... fit custom logic ...
                # n'appliquer le nan_remover que si le flag est activé
                if getattr(self, 'nan_remover_enabled', False):
                    run_internal_step("NaN Remover Fit", self.nan_remover, X, 0.9)
                # appel de la méthode fit_scaler si elle existe (implémentation éventuelle)
                if hasattr(self, 'fit_scaler'):
                    run_internal_step("Scaler Fit", self.fit_scaler, X)
                return self
            except Exception as e:
                print(f"[ERROR][Preprocessing][fit] {str(e)}")
                raise
    def transform(self, X):
            try:
                # apply nan remover then scaler
                df = X.copy()
                if getattr(self, 'nan_remover_enabled', False):
                    cols_to_remove = run_internal_step("NaN Remover Transform", self.nan_remover, df, 0.9)
                else:
                    cols_to_remove = []
                if cols_to_remove:
                    df = df.drop(columns=cols_to_remove)
                return df
            except Exception as e:
                print(f"[ERROR][Preprocessing][transform] {str(e)}")
                raise

# ==============================================================================================================
# 4- Clase fille Feature_Engineer_Freq pour la feature engineering:  (héritage: BasEstimator, TransformerMixin)
# =============================================================================================================
class Feature_Engineer_Freq(BaseEstimator, TransformerMixin):
    def __init__(self, custom_features=True):
        self.custom_features = custom_features
    def fit(self, X, y=None):
            try:
                # ... fit logic ...
                return self
            except Exception as e:
                print(f"[ERROR][FeatureEngineer][fit] {str(e)}")
                raise
    def transform(self, X):
            try:
                # ... feature engineering ...
                return X
            except Exception as e:
                print(f"[ERROR][FeatureEngineer][transform] {str(e)}")
                raise


# ==================================================================================
# 5- Clase fille Model_Prediction_Freq pour le prédiction:  (héritage: BasEstimator)
# ==================================================================================
class Model_Prediction_Freq(BaseEstimator):
    def __init__(self, estimator):
        self.estimator = estimator
    def fit(self, X, y):
            try:
                self.estimator.fit(X, y)
                return self
            except Exception as e:
                print(f"[ERROR][ModelPrediction][fit] {str(e)}")
                raise
    def predict(self, X):
            try:
                return self.estimator.predict(X)
            except Exception as e:
                print(f"[ERROR][ModelPrediction][predict] {str(e)}")
                raise


# ==========================================================================================================
# 6- Clase mère ModelPipeline_Freq pour orchestrer la construction, l’entraînement, l’amélioration du modèle
# ==========================================================================================================
class ModelPipeline_Freq:
    def __init__(self, preprocessing, feature_engineer, model_prediction):
        # garantir que pipeline a toujours des étapes nommées; utiliser 'passthrough' si absent
        steps = [
            ('preprocessing', preprocessing if preprocessing is not None else 'passthrough'),
            ('feature_engineer', feature_engineer if feature_engineer is not None else 'passthrough'),
            ('model', model_prediction if model_prediction is not None else 'passthrough')
        ]
        self.pipeline = Pipeline(steps)
    def fit(self, X, y):
            try:
                self.pipeline.fit(X, y)
            except Exception as e:
                print(f"[ERROR][ModelPipeline][fit] {str(e)}")
                raise
    def predict(self, X):
            try:
                return self.pipeline.predict(X)
            except Exception as e:
                print(f"[ERROR][ModelPipeline][predict] {str(e)}")
                raise
    def save(self, path):
            try:
                # ... sauvegarde du pipeline ...
                pass
            except Exception as e:
                print(f"[ERROR][ModelPipeline][save] {str(e)}")
                raise
    def load(self, path):
            try:
                # ... chargement du pipeline ...
                pass
            except Exception as e:
                print(f"[ERROR][ModelPipeline][load] {str(e)}")
                raise


# --------- AMOUNT ->
# ======================================================================================================
# 7- Clase fille Preprocessing_Amount : pour le préprocessing (héritage: BasEstimator, TransformerMixin)
# ======================================================================================================
class Preprocessing_Amount(BaseEstimator, TransformerMixin):
    def __init__(self, nan_remover=True, 
                 scaler: Optional[Any]=None, 
                 imputer_strategy: str='median', 
                 categorical_cols: Optional[List[str]]=None, 
                 target_col: str='montant_sinistre', 
                 drop_id_cols: Optional[List[str]] = None, 
                 high_cardinality_threshold: int = 500, 
                 exclude_from_encoding: Optional[List[str]] = None):
        self.nan_remover_enabled = nan_remover
        self.scaler = scaler
        self.imputer_strategy = imputer_strategy
        self.categorical_cols = categorical_cols
        self.target_col = target_col
        # colonnes identifiants à retirer systématiquement
        if drop_id_cols is None:
            drop_id_cols = ['index', 'id_client', 'id_vehicule', 'id_contrat']
        self.drop_id_cols = drop_id_cols
        # colonnes à exclure de l'encodage (par défaut aucune; traiter marque/modele en FeatureEngineer si souhaité)
        if exclude_from_encoding is None:
            exclude_from_encoding = ['modele_vehicule']
        self.exclude_from_encoding = exclude_from_encoding
        # seuil au-dessus duquel on considère une variable comme haute cardinalité
        self.high_cardinality_threshold = high_cardinality_threshold
        # attributes set on fit
        self.removed_columns_ = []
        self.imputer_ = {}
        self.scaler_ = None
        self.encoders_ = {}
        self.outlier_bounds_ = {}
        self.selected_features_ = None


    def nan_remover(self, df: pd.DataFrame, threshold: Optional[float]=0.9) -> List[str]:
            """Identifie les colonnes à supprimer en fonction du pourcentage de valeurs manquantes."""
            try:
                columns_to_remove = [
                    col for col in df.columns if df[col].isna().mean() > threshold
                ]
                return columns_to_remove
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][nan_remover] {str(e)}")
                raise


    
    def validate_input(self, X: pd.DataFrame):
            try:
                if not isinstance(X, pd.DataFrame):
                    raise ValueError("Input X must be a pandas DataFrame")
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][validate_input] {str(e)}")
                raise

    def fit_imputer(self, X: pd.DataFrame):
            try:
                imputer = {}
                for col in X.columns:
                    if X[col].dtype.kind in 'biufc':
                        if self.imputer_strategy == 'median':
                            imputer[col] = X[col].median()
                        else:
                            imputer[col] = X[col].mean()
                    else:
                        mode = X[col].mode()
                        imputer[col] = mode.iloc[0] if len(mode) > 0 else ''
                self.imputer_ = imputer
                return imputer
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][fit_imputer] {str(e)}")
                raise

    def transform_imputer(self, X: pd.DataFrame) -> pd.DataFrame:
            try:
                df = X.copy()
                for col, val in self.imputer_.items():
                    if col in df.columns:
                        df[col] = df[col].fillna(val)
                return df
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][transform_imputer] {str(e)}")
                raise

    def fit_scaler(self, X: pd.DataFrame):
            try:
                if not self.scaler:
                    return None
                # determine numeric columns and store them for transform time
                num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
                self.num_cols_ = num_cols
                if len(self.num_cols_) == 0:
                    return None
                if isinstance(self.scaler, str) and self.scaler.lower() in ("standard", "standardscaler"):
                    scaler = StandardScaler()
                    scaler.fit(X[self.num_cols_])
                    self.scaler_ = scaler
                    return scaler
                if hasattr(self.scaler, "fit"):
                    self.scaler.fit(X[self.num_cols_])
                    self.scaler_ = self.scaler
                    return self.scaler
                return None
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][fit_scaler] {str(e)}")
                raise

    def transform_scaler(self, X: pd.DataFrame) -> pd.DataFrame:
            try:
                df = X.copy()
                if hasattr(self, "scaler_") and self.scaler_ is not None:
                    # Prefer numeric columns captured during fit to ensure consistent names/order
                    if hasattr(self, 'num_cols_') and len(self.num_cols_) > 0:
                        # add any missing expected columns with zeros so transform won't fail
                        missing = [c for c in self.num_cols_ if c not in df.columns]
                        for c in missing:
                            df[c] = 0
                        df[self.num_cols_] = self.scaler_.transform(df[self.num_cols_])
                    else:
                        num_cols = df.select_dtypes(include=[np.number]).columns
                        if len(num_cols) > 0:
                            df[num_cols] = self.scaler_.transform(df[num_cols])
                return df
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][transform_scaler] {str(e)}")
                raise

    def fit_encoders(self, X: pd.DataFrame):
            try:
                cols = self.categorical_cols if self.categorical_cols is not None else X.select_dtypes(include=['object', 'category']).columns.tolist()
                # exclure les colonnes id car inutiles à encoder
                cols = [c for c in cols if c not in self.drop_id_cols]
                # si code_postal a un mapping, il a été remplacé par region_code (valeurs réduites)
                encoders = {}
                for col in cols:
                    # sauter les colonnes à cardinalité très haute
                    try:
                        nunique = X[col].nunique()
                    except Exception:
                        nunique = None
                    if nunique is not None and self.high_cardinality_threshold and nunique > self.high_cardinality_threshold:
                        # on n'encode pas cette colonne
                        continue
                    le = LabelEncoder()
                    values = X[col].astype(str).fillna('')
                    le.fit(values)
                    encoders[col] = le
                self.encoders_ = encoders
                return encoders
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][fit_encoders] {str(e)}")
                raise

    def transform_encoders(self, X: pd.DataFrame) -> pd.DataFrame:
            try:
                df = X.copy()
                for col, le in self.encoders_.items():
                    if col in df.columns:
                        vals = df[col].astype(str).fillna('')
                        try:
                            df[col] = le.transform(vals)
                        except ValueError:
                            # unseen labels in transform; map known classes and set unknowns to -1
                            mapping = {v: i for i, v in enumerate(le.classes_)}
                            df[col] = vals.map(mapping).fillna(-1).astype(int)
                return df
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][transform_encoders] {str(e)}")
                raise

    def handle_outliers_fit(self, X: pd.DataFrame, method: str='iqr'):
            try:
                bounds = {}
                num_cols = X.select_dtypes(include=[np.number]).columns
                for col in num_cols:
                    q1 = X[col].quantile(0.25)
                    q3 = X[col].quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    bounds[col] = (lower, upper)
                self.outlier_bounds_ = bounds
                return bounds
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][handle_outliers_fit] {str(e)}")
                raise

    def handle_outliers_transform(self, X: pd.DataFrame) -> pd.DataFrame:
            try:
                df = X.copy()
                for col, (low, high) in self.outlier_bounds_.items():
                    if col in df.columns:
                        df[col] = df[col].clip(lower=low, upper=high)
                return df
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][handle_outliers_transform] {str(e)}")
                raise

    def select_features_fit(self, X: pd.DataFrame, y: Optional[pd.Series]=None):
            try:
                variances = X.var(numeric_only=True)
                selected = variances[variances > 0].index.tolist()
                self.selected_features_ = selected
                return selected
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][select_features_fit] {str(e)}")
                raise

    def select_features_transform(self, X: pd.DataFrame) -> pd.DataFrame:
            try:
                if self.selected_features_ is None:
                    return X
                cols = [c for c in self.selected_features_ if c in X.columns]
                return X[cols]
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][select_features_transform] {str(e)}")
                raise

    def create_custom_features(self, X: pd.DataFrame) -> pd.DataFrame:
            try:
                # emplacement réservé : opération nulle, l'utilisateur peut surcharger ou étendre
                return X
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][create_custom_features] {str(e)}")
                raise

    def save_state(self, path: str):
            try:
                state = {
                    'removed_columns_': self.removed_columns_,
                    'imputer_': self.imputer_,
                    'scaler_': self.scaler_,
                    'encoders_': self.encoders_,
                    'outlier_bounds_': self.outlier_bounds_,
                    'selected_features_': self.selected_features_
                }
                # ajouter mapping postal si présent
                if getattr(self, 'postal_mapping_', None) is not None:
                    state['postal_mapping_'] = self.postal_mapping_
                with open(path, 'wb') as f:
                    pickle.dump(state, f)
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][save_state] {str(e)}")
                raise

    def load_state(self, path: str):
            try:
                with open(path, 'rb') as f:
                    state = pickle.load(f)
                self.removed_columns_ = state.get('removed_columns_', [])
                self.imputer_ = state.get('imputer_', {})
                self.scaler_ = state.get('scaler_', None)
                self.encoders_ = state.get('encoders_', {})
                self.outlier_bounds_ = state.get('outlier_bounds_', {})
                self.selected_features_ = state.get('selected_features_', None)
                self.postal_mapping_ = state.get('postal_mapping_', None)
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][load_state] {str(e)}")
                raise

    def fit(self, X, y=None):
            try:
                self.validate_input(X)
                df = X.copy()
                y_series = None
                if y is not None:
                    y_series = pd.Series(y).reset_index(drop=True)
                    # drop rows where target is null
                    mask_notnull = y_series.notna()
                    # store mask and dropped count on self for traceability
                    self.mask_notnull_ = mask_notnull
                    self.n_dropped_ = int((~mask_notnull).sum())
                    if not mask_notnull.all():
                        df = df.loc[mask_notnull.values].reset_index(drop=True)
                        y_series = y_series.loc[mask_notnull].reset_index(drop=True)
                    # keep filtered target
                    self.y_filtered_ = y_series
                # NaN remover (only if enabled)
                if getattr(self, 'nan_remover_enabled', False):
                    cols_to_remove = run_internal_step("NaN Remover Fit", self.nan_remover, df, 0.5)
                else:
                    cols_to_remove = []
                # ajouter systématiquement les colonnes identifiants à retirer
                id_cols_present = [c for c in self.drop_id_cols if c in df.columns]
                cols_to_remove = list(dict.fromkeys((cols_to_remove or []) + id_cols_present))
                self.removed_columns_ = cols_to_remove or []
                if self.removed_columns_:
                    df = df.drop(columns=self.removed_columns_, errors='ignore')
                # appliquer le mapping postal si disponible (avant fit des encodeurs)
                df = run_internal_step("Postal Mapping Fit", self._apply_postal_mapping, df)
                # imputer
                run_internal_step("Imputer Fit", self.fit_imputer, df)
                # encoders
                run_internal_step("Encoders Fit", self.fit_encoders, df)
                # outliers
                run_internal_step("Outliers Fit", self.handle_outliers_fit, df)
                # scaler
                run_internal_step("Scaler Fit", self.fit_scaler, df)
                # feature selection
                run_internal_step("Select Features Fit", self.select_features_fit, df, y_series)
                return self
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][fit] {str(e)}")
                raise


    def transform(self, X, y: Optional[pd.Series]=None):
            try:
                self.validate_input(X)
                df = X.copy()
                # if y provided, drop rows where target is null (keep X and y aligned)
                if y is not None:
                    y_ser = pd.Series(y).reset_index(drop=True)
                    mask_notnull = y_ser.notna()
                    # store mask and dropped count on self for visibility
                    self.mask_notnull_ = mask_notnull
                    self.n_dropped_ = int((~mask_notnull).sum())
                    if not mask_notnull.all():
                        df = df.loc[mask_notnull.values].reset_index(drop=True)
                        y_ser = y_ser.loc[mask_notnull].reset_index(drop=True)
                    self.y_filtered_ = y_ser
                # drop removed cols
                if getattr(self, 'removed_columns_', None):
                    df = df.drop(columns=self.removed_columns_, errors='ignore')
                # appliquer le mapping postal si disponible (avant encodage)
                df = run_internal_step("Postal Mapping Transform", self._apply_postal_mapping, df)
                # impute
                if getattr(self, 'imputer_', None):
                    df = run_internal_step("Imputer Transform", self.transform_imputer, df)
                # create custom features
                df = run_internal_step("Create Custom Features", self.create_custom_features, df)
                # encode
                if getattr(self, 'encoders_', None):
                    df = run_internal_step("Encoders Transform", self.transform_encoders, df)
                # outliers
                if getattr(self, 'outlier_bounds_', None):
                    df = run_internal_step("Outliers Transform", self.handle_outliers_transform, df)
                # scaler
                df = run_internal_step("Scaler Transform", self.transform_scaler, df)
                # feature selection
                if getattr(self, 'selected_features_', None):
                    df = run_internal_step("Select Features Transform", self.select_features_transform, df)
                if y is not None:
                    return df, y_ser
                return df
            except Exception as e:
                print(f"[ERROR][Preprocessing_Amount][transform] {str(e)}")
                raise


# ==================================================================================================================
# 8- Clase fille Feature_Engineer_Amount pour la feature engineering:  (héritage: BasEstimator, TransformerMixin)
# ==================================================================================================================
class FeatureEngineer_Amount(BaseEstimator, TransformerMixin):
    """Feature engineering pour la cible `montant_sinistre`.

    Cette classe consomme les DataFrame retournés par `Preprocessing_Amount`.
    Elle peut recevoir l'objet de preprocessing lors du `fit` pour récupérer
    la métadonnée utile (colonnes supprimées, colonnes numériques, features
    sélectionnées, encodeurs, ...).
    """
    def __init__(self, custom_features: bool = True, top_n_brands: int = 20, brand_col: str = 'marque_vehicule', model_col: str = 'modele_vehicule'):
        self.custom_features = custom_features
        # paramétrage pour top-N marques
        self.top_n_brands = top_n_brands
        self.brand_col = brand_col
        self.model_col = model_col
        # attributs remplis au fit
        self.generated_features_: List[str] = []
        self.feature_names_in_: Optional[List[str]] = None
        self.preproc_metadata_: Dict[str, Any] = {}
        # top brands et mapping générés au fit
        self.top_brands_: List[str] = []
        self.brand_map_: Dict[str, int] = {}

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None, preprocessing_obj: Optional["Preprocessing_Amount"] = None):
            try:
                # validation et mise en place
                self.validate_input(X)
                # enregister l'ordre / les noms de colonnes d'entrée
                self.feature_names_in_ = X.columns.tolist()
                # si on reçoit l'objet de preprocessing, capturer les métadonnées utiles
                if preprocessing_obj is not None:
                    self.preproc_metadata_ = {
                        'removed_columns_': getattr(preprocessing_obj, 'removed_columns_', []),
                        'selected_features_': getattr(preprocessing_obj, 'selected_features_', None),
                        'encoders_': getattr(preprocessing_obj, 'encoders_', {}),
                        'num_cols_': getattr(preprocessing_obj, 'num_cols_', []),
                        'outlier_bounds_': getattr(preprocessing_obj, 'outlier_bounds_', {}),
                        'mask_notnull_': getattr(preprocessing_obj, 'mask_notnull_', None),
                        'n_dropped_': getattr(preprocessing_obj, 'n_dropped_', 0),
                    }
                # calculer top-N marques en fonction du nombre de sinistres si disponible
                try:
                    if self.brand_col in X.columns:
                        df = X.copy()
                        # si colonne nombre_sinistres présente, utiliser sa somme par marque
                        if 'nombre_sinistres' in df.columns:
                            stats = df.groupby(self.brand_col)['nombre_sinistres'].sum()
                        elif y is not None:
                            # utiliser y (présence de sinistre) si y fourni
                            ser = pd.Series(y).reset_index(drop=True)
                            df2 = df.copy().reset_index(drop=True)
                            df2['_y_flag'] = (ser > 0).astype(int)
                            stats = df2.groupby(self.brand_col)['_y_flag'].sum()
                        else:
                            stats = df[self.brand_col].value_counts()
                        top = list(stats.sort_values(ascending=False).head(self.top_n_brands).index.astype(str))
                        self.top_brands_ = top
                        # mapping numérique pour les top brands + OTHER
                        self.brand_map_ = {b: i for i, b in enumerate(self.top_brands_)}
                        self.brand_map_['OTHER'] = len(self.top_brands_)
                except Exception:
                    # ne pas faire échouer le fit si calcul top brands échoue
                    self.top_brands_ = []
                    self.brand_map_ = {}
                # opportunité : calculer les statistiques nécessaires aux transformations (à compléter)
                return self
            except Exception as e:
                print(f"[ERROR][FeatureEngineer_Amount][fit] {str(e)}")
                raise

    def create_custom_features(self, X: pd.DataFrame) -> pd.DataFrame:
            try:
                df = X.copy()
                created: List[str] = []
                # exemple d'une feature dérivée simple (remplacer/étendre selon besoin)
                if 'age_conducteur1' in df.columns and 'age_conducteur2' in df.columns:
                    df['age_diff'] = df['age_conducteur1'] - df['age_conducteur2']
                    created.append('age_diff')
                # brand top-N encoding (création d'une colonne encodée légère)
                try:
                    if self.brand_col in df.columns and getattr(self, 'brand_map_', None):
                        col_top = df[self.brand_col].astype(str).where(df[self.brand_col].astype(str).isin(self.top_brands_), 'OTHER')
                        df[f'{self.brand_col}_encoded'] = col_top.map(self.brand_map_).fillna(self.brand_map_.get('OTHER', 0)).astype(int)
                        created.append(f'{self.brand_col}_encoded')
                except Exception:
                    pass
                # enregistrez la liste des features générées
                self.generated_features_ = created
                return df
            except Exception as e:
                print(f"[ERROR][FeatureEngineer_Amount][create_custom_features] {str(e)}")
                raise

    def validate_input(self, X: pd.DataFrame):
            try:
                if not isinstance(X, pd.DataFrame):
                    raise ValueError("Input must be a pandas DataFrame")
            except Exception as e:
                print(f"[ERROR][FeatureEngineer_Amount][validate_input] {str(e)}")
                raise

    def encode_or_bin_features(self, X: pd.DataFrame) -> pd.DataFrame:
            try:
                # emplacement réservé : si binning ou encodage supplémentaire requis
                # actuellement opération nulle, conservé pour être appelé depuis transform si nécessaire
                return X
            except Exception as e:
                print(f"[ERROR][FeatureEngineer_Amount][encode_or_bin_features] {str(e)}")
                raise

    def aggregate_by_key(self, X: pd.DataFrame, key_cols: List[str], agg_specs: Dict[str, Any]) -> pd.DataFrame:
            try:
                # emplacement réservé : implémenter des agrégations spécifiques au domaine si nécessaire
                # renvoie un DataFrame de features agrégées à fusionner
                if not key_cols or not agg_specs:
                    return pd.DataFrame()
                agg = X.groupby(key_cols).agg(agg_specs).reset_index()
                return agg
            except Exception as e:
                print(f"[ERROR][FeatureEngineer_Amount][aggregate_by_key] {str(e)}")
                raise

    def save_state(self, path: str):
            try:
                state = {
                    'generated_features_': self.generated_features_,
                    'feature_names_in_': self.feature_names_in_,
                    'preproc_metadata_': self.preproc_metadata_,
                    'top_brands_': getattr(self, 'top_brands_', []),
                    'brand_map_': getattr(self, 'brand_map_', {}),
                }
                with open(path, 'wb') as f:
                    pickle.dump(state, f)
            except Exception as e:
                print(f"[ERROR][FeatureEngineer_Amount][save_state] {str(e)}")
                raise

    def load_state(self, path: str):
            try:
                with open(path, 'rb') as f:
                    state = pickle.load(f)
                self.generated_features_ = state.get('generated_features_', [])
                self.feature_names_in_ = state.get('feature_names_in_', None)
                self.preproc_metadata_ = state.get('preproc_metadata_', {})
                self.top_brands_ = state.get('top_brands_', [])
                self.brand_map_ = state.get('brand_map_', {})
            except Exception as e:
                print(f"[ERROR][FeatureEngineer_Amount][load_state] {str(e)}")
                raise

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
            try:
                df = X.copy()
                if self.custom_features:
                    df = self.create_custom_features(df)
                # si la sélection de features a été déterminée par le preprocessing,
                # on renvoie l'intersection (features sélectionnées + features générées)
                sel = self.preproc_metadata_.get('selected_features_')
                if sel is not None:
                    cols = [c for c in sel if c in df.columns]
                    # ajouter les features générées si elles existent
                    cols += [c for c in self.generated_features_ if c in df.columns]
                    # préserver l'ordre et enlever les doublons
                    cols = list(dict.fromkeys(cols))
                    return df[cols]
                return df
            except Exception as e:
                print(f"[ERROR][FeatureEngineer_Amount][transform] {str(e)}")
                raise


# ====================================================================================
# 9- Clase fille Model_Prediction_Amount pour le prédiction:  (héritage: BasEstimator)
# =====================================================================================
# Modèle de prédiction
class ModelPrediction_Amount(BaseEstimator):
    """Gère une famille d'estimateurs et la construction dynamique d'un Pipeline.

    - `self.models_` : dictionnaire name -> estimator instance (sklearn)
    - `self.model_name_` : nom de l'estimateur courant
    - `self.pipeline_` : Pipeline sklearn construit avec preprocessing + feature_engineer + estimator
    """
    def __init__(self, models: Optional[Dict[str, Any]] = None, model_name: str = 'LinearRegression'):
        # construire un dictionnaire par défaut si non fourni
        default_models = {
            'LinearRegression': LinearRegression(),
            'Ridge': Ridge(),
            'Lasso': Lasso(),
            'ElasticNet': ElasticNet(),
            'RandomForest': RandomForestRegressor(),
            'GradientBoosting': GradientBoostingRegressor(),
            'KNN': KNeighborsRegressor(),
            'SVR': SVR()
        }
        self.models_ = models if models is not None else default_models
        if model_name not in self.models_:
            # repli si le nom est inconnu
            model_name = list(self.models_.keys())[0]
        self.model_name_ = model_name
        self.pipeline_: Optional[Pipeline] = None
        # conserve les étapes utilisées pour reconstruire le pipeline
        self._preprocessing = None
        self._feature_engineer = None
        self.is_fitted_ = False

    def build_pipeline(self, preprocessing: Optional[BaseEstimator] = None, feature_engineer: Optional[BaseEstimator] = None, model_name: Optional[str] = None):
            try:
                if model_name is not None:
                    if model_name not in self.models_:
                        raise ValueError(f"Unknown model_name: {model_name}")
                    self.model_name_ = model_name
                model = self.models_[self.model_name_]
                # définir toujours trois étapes explicites pour faciliter l'introspection
                steps = [
                    ('preprocessing', preprocessing if preprocessing is not None else 'passthrough'),
                    ('feature_engineer', feature_engineer if feature_engineer is not None else 'passthrough'),
                    ('model', model)
                ]
                self.pipeline_ = Pipeline(steps)
                # stocker références pour permettre rebuild ultérieur
                self._preprocessing = preprocessing
                self._feature_engineer = feature_engineer
                self.is_fitted_ = False
                return self.pipeline_
            except Exception as e:
                print(f"[ERROR][ModelPrediction_Amount][build_pipeline] {str(e)}")
                raise

    def set_model(self, model_name: str):
            try:
                if model_name not in self.models_:
                    raise ValueError(f"Model '{model_name}' not found in available models")
                self.model_name_ = model_name
                # si pipeline existant, reconstruire en conservant les étapes précédentes
                if self._preprocessing is not None or self._feature_engineer is not None:
                    self.build_pipeline(self._preprocessing, self._feature_engineer, model_name)
            except Exception as e:
                print(f"[ERROR][ModelPrediction_Amount][set_model] {str(e)}")
                raise

    def fit(self, X, y, preprocessing: Optional[BaseEstimator] = None, feature_engineer: Optional[BaseEstimator] = None, model_name: Optional[str] = None):
            try:
                # build pipeline if not present or if a new model_name is requested
                if self.pipeline_ is None or model_name is not None:
                    self.build_pipeline(preprocessing or self._preprocessing, feature_engineer or self._feature_engineer, model_name)
                # fit the pipeline
                self.pipeline_.fit(X, y)
                self.is_fitted_ = True
                return self
            except Exception as e:
                print(f"[ERROR][ModelPrediction_Amount][fit] {str(e)}")
                raise

    def predict(self, X):
            try:
                if self.pipeline_ is None or not self.is_fitted_:
                    raise RuntimeError("Pipeline not built or not fitted. Call fit(...) first.")
                return self.pipeline_.predict(X)
            except Exception as e:
                print(f"[ERROR][ModelPrediction_Amount][predict] {str(e)}")
                raise

    def score(self, X, y):
            try:
                if self.pipeline_ is None or not self.is_fitted_:
                    raise RuntimeError("Pipeline not built or not fitted. Call fit(...) first.")
                return self.pipeline_.score(X, y)
            except Exception as e:
                print(f"[ERROR][ModelPrediction_Amount][score] {str(e)}")
                raise

    def set_params(self, **params):
            try:
                if self.pipeline_ is None:
                    raise RuntimeError("Pipeline not built. Build or fit before setting params.")
                self.pipeline_.set_params(**params)
            except Exception as e:
                print(f"[ERROR][ModelPrediction_Amount][set_params] {str(e)}")
                raise

    def save(self, path: str):
            try:
                with open(path, 'wb') as f:
                    pickle.dump(self.pipeline_, f)
            except Exception as e:
                print(f"[ERROR][ModelPrediction_Amount][save] {str(e)}")
                raise

    def load(self, path: str):
            try:
                with open(path, 'rb') as f:
                    self.pipeline_ = pickle.load(f)
                self.is_fitted_ = True
            except Exception as e:
                print(f"[ERROR][ModelPrediction_Amount][load] {str(e)}")
                raise

    def get_available_models(self) -> List[str]:
            return list(self.models_.keys())


# ==============================================================================================================
# 10- Clase mère ModelPipeline_Amount pour orchestrer la construction, l’entraînement, l’amélioration du modèle
# ==============================================================================================================
class ModelPipeline_Amount:
    def __init__(self, preprocessing: Optional[BaseEstimator], feature_engineer: Optional[BaseEstimator], model_prediction: Any):
        try:
            # Si model_prediction est une instance de ModelPrediction_Amount, déléguer la construction du pipeline
            if isinstance(model_prediction, ModelPrediction_Amount):
                # construire le pipeline interne dans ModelPrediction_Amount pour contenir preprocessing+feature_engineer+model
                model_prediction.build_pipeline(preprocessing, feature_engineer)
                self.pipeline = model_prediction.pipeline_
                # garder la référence
                self.model_prediction_obj = model_prediction
            else:
                # model_prediction est attendu comme un estimateur sklearn ou un wrapper compatible avec Pipeline
                steps = [
                    ('preprocessing', preprocessing if preprocessing is not None else 'passthrough'),
                    ('feature_engineer', feature_engineer if feature_engineer is not None else 'passthrough'),
                    ('model', model_prediction if model_prediction is not None else 'passthrough')
                ]
                self.pipeline = Pipeline(steps)
                self.model_prediction_obj = None
        except Exception as e:
            print(f"[ERROR][ModelPipeline_Amount][__init__] {str(e)}")
            raise
    def fit(self, X, y):
            try:
                self.pipeline.fit(X, y)
            except Exception as e:
                print(f"[ERROR][ModelPipeline_Amount][fit] {str(e)}")
                raise
    def predict(self, X):
            try:
                return self.pipeline.predict(X)
            except Exception as e:
                print(f"[ERROR][ModelPipeline_Amount][predict] {str(e)}")
                raise
    def save(self, path):
            try:
                # sauvegarde du pipeline complet
                with open(path, 'wb') as f:
                    pickle.dump(self.pipeline, f)
            except Exception as e:
                print(f"[ERROR][ModelPipeline_Amount][save] {str(e)}")
                raise
    def load(self, path):
            try:
                with open(path, 'rb') as f:
                    self.pipeline = pickle.load(f)
                # mark fitted if possible
                try:
                    # sklearn pipelines have named_steps
                    self.pipeline.predict
                except Exception:
                    pass
                return self.pipeline
            except Exception as e:
                print(f"[ERROR][ModelPipeline_Amount][load] {str(e)}")
                raise


# --------- AFFICHAGE ->
# ===========================================================================
# 11- Clase pour les affichages les rendus
# ===========================================================================
class DisplayManager:
    """Outils d'affichage et d'inspection pour les objets du pipeline.

    Méthodes principales:
    - `show_data`: aperçu d'un DataFrame
    - `show_preprocessing`, `show_feature_engineer`, `show_model_prediction`, `show_pipeline`: affichage spécialisé
    - `show_all`: tentative de dispatch automatique
    Les méthodes acceptent soit l'objet en mémoire soit le chemin vers un fichier pickle.
    """
    def __init__(self):
        pass

    def _maybe_load(self, obj_or_path: Any):
        """Si `obj_or_path` est un chemin existant, tente de le charger par pickle, sinon renvoie l'objet."""
        try:
            if isinstance(obj_or_path, str) and os.path.exists(obj_or_path):
                with open(obj_or_path, 'rb') as f:
                    return pickle.load(f)
        except Exception:
            # Ne pas échouer pour un chargement; laisser la logique appelante gérer
            print(f"[WARN][DisplayManager][_maybe_load] impossible de charger pickle: {obj_or_path}")
        return obj_or_path

    def _print_common(self, name: str, info: str):
        print(f"--- {name} ---")
        print(info)

    def show_data(self, df: pd.DataFrame, title: str = 'DataFrame'):
        try:
            self._print_common(title, f"shape={getattr(df, 'shape', None)} columns={list(df.columns)[:20]}")
            print(df.head())
            try:
                df.info()
            except Exception:
                print("(info unavailable)")
            try:
                print(df.describe(include='all'))
            except Exception:
                pass
        except Exception as e:
            print(f"[ERROR][DisplayManager][show_data] {str(e)}")
            raise

    def show_preprocessing(self, preproc_or_path: Any):
        try:
            obj = self._maybe_load(preproc_or_path)
            self._print_common('Preprocessing_Amount', f'type={type(obj)}')
            # attributs attendus
            attrs = [
                'removed_columns_', 'n_dropped_', 'mask_notnull_', 'y_filtered_',
                'imputer_', 'encoders_', 'num_cols_', 'selected_features_', 'outlier_bounds_'
            ]
            for a in attrs:
                if hasattr(obj, a):
                    val = getattr(obj, a)
                    if isinstance(val, (list, dict)):
                        print(f"{a}: {type(val)} (len={len(val)})")
                        if isinstance(val, dict):
                            # affiche clefs et aperçu
                            keys = list(val.keys())[:10]
                            print(f"  keys: {keys}")
                    else:
                        print(f"{a}: {type(val)} -> {str(val)[:200]}")
            # aperçu des encodeurs (classe et nombre de classes)
            if hasattr(obj, 'encoders_') and isinstance(obj.encoders_, dict):
                for col, le in obj.encoders_.items():
                    try:
                        classes = list(le.classes_)
                        print(f"encoder {col}: classes_len={len(classes)} sample={classes[:5]}")
                    except Exception:
                        print(f"encoder {col}: (non introspectable)")
            return obj
        except Exception as e:
            print(f"[ERROR][DisplayManager][show_preprocessing] {str(e)}")
            raise

    def show_feature_engineer(self, fe_or_path: Any):
        try:
            obj = self._maybe_load(fe_or_path)
            self._print_common('FeatureEngineer_Amount', f'type={type(obj)}')
            for a in ['generated_features_', 'feature_names_in_', 'preproc_metadata_']:
                if hasattr(obj, a):
                    val = getattr(obj, a)
                    print(f"{a}: type={type(val)} len={(len(val) if hasattr(val, '__len__') else 'n/a')}")
                    if a == 'preproc_metadata_' and isinstance(val, dict):
                        print(f"  keys: {list(val.keys())}")
            return obj
        except Exception as e:
            print(f"[ERROR][DisplayManager][show_feature_engineer] {str(e)}")
            raise

    def show_model_prediction(self, mp_or_path: Any):
        try:
            obj = self._maybe_load(mp_or_path)
            self._print_common('ModelPrediction_Amount', f'type={type(obj)}')
            if hasattr(obj, 'models_'):
                print(f"available models: {list(obj.models_.keys())}")
            if hasattr(obj, 'model_name_'):
                print(f"current model_name_: {getattr(obj, 'model_name_', None)}")
            if hasattr(obj, 'is_fitted_'):
                print(f"is_fitted_: {getattr(obj, 'is_fitted_', False)}")
            # pipeline introspection
            pipeline = getattr(obj, 'pipeline_', None)
            if pipeline is not None:
                print("pipeline steps:")
                try:
                    for name, step in pipeline.steps:
                        print(f" - {name}: {type(step)}")
                except Exception:
                    print(f"  (pipeline present but non standard: {type(pipeline)})")
                # final estimator
                try:
                    final = pipeline.steps[-1][1]
                    # coefficients / feature importances
                    if hasattr(final, 'coef_'):
                        print(f"final coef_ length: {len(getattr(final, 'coef_'))}")
                    if hasattr(final, 'feature_importances_'):
                        print(f"final feature_importances_ length: {len(getattr(final, 'feature_importances_'))}")
                except Exception:
                    pass
            return obj
        except Exception as e:
            print(f"[ERROR][DisplayManager][show_model_prediction] {str(e)}")
            raise

    def show_pipeline(self, pipeline_or_path: Any):
        try:
            obj = self._maybe_load(pipeline_or_path)
            self._print_common('ModelPipeline_Amount', f'type={type(obj)}')
            # si c'est un ModelPipeline_Amount
            if hasattr(obj, 'model_prediction_obj') and obj.model_prediction_obj is not None:
                print("contains ModelPrediction_Amount -> delegating")
                self.show_model_prediction(obj.model_prediction_obj)
                return obj
            # sinon si c'est un sklearn Pipeline
            pipeline = getattr(obj, 'pipeline', None) or getattr(obj, 'pipeline_', None) or obj
            try:
                steps = pipeline.steps
                print("pipeline steps:")
                for name, step in steps:
                    print(f" - {name}: {type(step)}")
                    # dispatch to specialized viewers
                    if name == 'preprocessing':
                        self.show_preprocessing(step)
                    if name == 'feature_engineer':
                        self.show_feature_engineer(step)
                    if name == 'model':
                        # if model is ModelPrediction_Amount, delegate
                        if isinstance(step, ModelPrediction_Amount):
                            self.show_model_prediction(step)
                        else:
                            print(f"model step type: {type(step)}")
            except Exception:
                print("(not a standard pipeline, attempting generic inspection)")
                self.inspect_object(pipeline)
            return obj
        except Exception as e:
            print(f"[ERROR][DisplayManager][show_pipeline] {str(e)}")
            raise

    def inspect_object(self, obj: Any):
        try:
            print(f"Inspecting object of type {type(obj)}")
            # DataFrame
            if isinstance(obj, pd.DataFrame):
                self.show_data(obj, title='DataFrame (inspect)')
                return
            # numpy
            try:
                import numpy as _np
                if isinstance(obj, _np.ndarray):
                    print(f"ndarray shape={obj.shape} dtype={obj.dtype}")
                    return
            except Exception:
                pass
            # sklearn Pipeline
            if hasattr(obj, 'steps'):
                print("Pipeline-like object with steps:")
                try:
                    for name, step in obj.steps:
                        print(f" - {name}: {type(step)}")
                except Exception:
                    pass
            # lister quelques attributs utiles
            attrs = [a for a in dir(obj) if not a.startswith('__')][:50]
            print(f"attrs: {attrs}")
        except Exception as e:
            print(f"[ERROR][DisplayManager][inspect_object] {str(e)}")
            raise

    def show_all(self, obj_or_path: Any):
        """Tentative de display complet : détecte le type et appelle les afficheurs dédiés."""
        try:
            obj = self._maybe_load(obj_or_path)
            # détection par attributs
            if hasattr(obj, 'removed_columns_') or hasattr(obj, 'imputer_'):
                return self.show_preprocessing(obj)
            if hasattr(obj, 'generated_features_') or hasattr(obj, 'preproc_metadata_'):
                return self.show_feature_engineer(obj)
            if hasattr(obj, 'models_') or hasattr(obj, 'model_name_'):
                return self.show_model_prediction(obj)
            if hasattr(obj, 'pipeline') or hasattr(obj, 'pipeline_') or hasattr(obj, 'model_prediction_obj'):
                return self.show_pipeline(obj)
            # fallback
            return self.inspect_object(obj)
        except Exception as e:
            print(f"[ERROR][DisplayManager][show_all] {str(e)}")
            raise

    def plot_feature_importance(self, feature_importances: pd.Series, title: str = 'Feature Importances'):
        try:
            import matplotlib.pyplot as plt
            feature_importances.sort_values(ascending=False).plot(kind='bar')
            plt.title(title)
            plt.show()
        except Exception as e:
            print(f"[ERROR][DisplayManager][plot_feature_importance] {str(e)}")
            raise

    def plot_prediction(self, metrics_dict: Dict[str, Any]):
        try:
            import matplotlib.pyplot as plt
            metrics_series = pd.Series(metrics_dict)
            metrics_series.plot(kind='bar')
            plt.title('Model Metrics')
            plt.show()
        except Exception as e:
            print(f"[ERROR][DisplayManager][plot_prediction] {str(e)}")
            raise

    def export_csv(self, df: pd.DataFrame, path: str):
        try:
            df.to_csv(path, index=False)
        except Exception as e:
            print(f"[ERROR][DisplayManager][export_csv] {str(e)}")
            raise

    def export_plot(self, fig, path: str):
        try:
            fig.savefig(path)
        except Exception as e:
            print(f"[ERROR][DisplayManager][export_plot] {str(e)}")
            raise


# --------- TEST UNITAIRE ->
# ===========================================================================
# 12- Clase pour faire les testes unitaires
# ===========================================================================

class TestPreprocessingAmount(unittest.TestCase):
    def test_nan_remover_identifies_columns(self):
        pre = Preprocessing_Amount()
        df = pd.DataFrame({
            'a': [1, None, None],
            'b': [1, 2, 3]
        })
        cols = pre.nan_remover(df, threshold=0.5)
        self.assertIn('a', cols)

    def test_load_postal_mapping_and_apply(self):
        pre = Preprocessing_Amount()
        population_df = pd.DataFrame({
            'code_postal': ['20000', '75000', '02000'],
            'departement': ['2A', '75', '02']
        })
        pre.load_postal_mapping(population_df, postal_col='code_postal', region_col_candidates=['departement'])
        # mapping doit normaliser 2A -> '20'
        self.assertEqual(pre.postal_mapping_.get('20000'), '20')
        df = pd.DataFrame({'code_postal': ['20000', '75000', '99999']})
        out = pre._apply_postal_mapping(df)
        self.assertEqual(out.loc[0, 'code_postal'], '20')
        self.assertEqual(out.loc[1, 'code_postal'], '75')
        # valeur inconnue reste inchangée
        self.assertEqual(out.loc[2, 'code_postal'], '99999')

    def test_fit_drops_null_target(self):
        pre = Preprocessing_Amount()
        X = pd.DataFrame({'c': [10, 20, 30]})
        y = pd.Series([1.0, None, 2.0])
        pre.fit(X, y)
        self.assertEqual(pre.n_dropped_, 1)
        self.assertEqual(len(pre.y_filtered_), 2)
        # mask_notnull_ doit exister et être de la bonne taille
        self.assertEqual(len(pre.mask_notnull_), 3)

    def test_fit_imputer_and_transform_imputer(self):
        pre = Preprocessing_Amount()
        df = pd.DataFrame({'num': [1.0, None, 3.0], 'cat': ['a', None, 'b']})
        # fit imputer on df
        pre.fit_imputer(df)
        out = pre.transform_imputer(df)
        # aucun NaN sur les colonnes imputées
        self.assertFalse(out['num'].isna().any())
        self.assertFalse(out['cat'].isna().any())


