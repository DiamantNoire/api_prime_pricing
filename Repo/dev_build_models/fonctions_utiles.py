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
from typing import Any, Dict, List, Optional

# --- Scientific stack ---
import numpy as np
import pandas as pd

# --- Scikit-learn ---
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler



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
    """Execute a pipeline step with a progress bar and return its result."""
    bar = tqdm(total=1, desc=desc, **PROGRESS_STYLE)
    try:
        result = fn(*args, **kwargs)
        bar.update(1)
    finally:
        bar.close()
    return result

def run_internal_step(desc, fn, *args, **kwargs):
    """Execute an internal sub-step with a dedicated progress style."""
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

def _generer_csv_pred_freqence(df:pd.DataFrame,
                                y_pred: pd.Series, 
                                path:str) -> None:
    """Export frequency predictions to a two-column CSV (index, pred)."""
    # Export prédictions test
    submission_df = pd.DataFrame({
        'index': df['index'],
        'pred':  y_pred
    })
    submission_df.to_csv(path, index=False)

@dataclass
class Frequence_Preprocessing:
    """Prétraitements métier pour la prédiction de la fréquence."""

    def __init__(self, target_col: str = "nombre_sinistres"):
        """Initialize frequency preprocessing settings and dataset id mappings."""
        self.target_col = target_col
        self.second_target_col = "montant_sinistre"
        self.preprocessing_map = {}
        self.id_columns_by_dataset = {
            "frequence_train": ['index', 'id_client', 'id_vehicule', 'id_contrat'],
            "frequence_valid": ['index', 'id_client', 'id_vehicule', 'id_contrat'],
            "frequence_test": ['index'],
        }

    def _ensure_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a defensive DataFrame copy from a DataFrame-like input."""
        if isinstance(df, pd.DataFrame):
            return df.copy()
        return pd.DataFrame(df)

    def set_preprocessing_map(self, preprocessing_map: Optional[dict]):
        """Store a custom preprocessing map used by downstream transformers."""
        self.preprocessing_map = preprocessing_map or {}

    def _transform_remove_id_columns(self, name: str, df: pd.DataFrame) -> pd.DataFrame:
        """Remove dataset-specific identifier columns when configured."""
        df = self._ensure_dataframe(df)
        cols_to_remove = self.id_columns_by_dataset.get(name)
        if cols_to_remove is None:
            return df.copy()
        return df.drop(columns=cols_to_remove, errors='ignore').copy()
    
    def _transform_remove_null_second_target(self, df:pd.DataFrame, second_target_col: Optional[str]=None) -> pd.DataFrame:
        """Filter rows where the secondary target column is null."""
        df = self._ensure_dataframe(df)
        second_target_col = second_target_col or self.second_target_col
        if second_target_col in df.columns:
            return df[df[second_target_col].notnull()].copy()
        return df
    
    def _fit_preprocess_NanRemover(
        self,
        df: pd.DataFrame,
        columns_to_remove: Optional[List[str]] = None,
        threshold: Optional[float] = 0.9
    ) -> List[str]:
        """Find columns whose null ratio is above the provided threshold."""
        df = self._ensure_dataframe(df)
        return [col for col in df.columns if df[col].isna().mean() > threshold]

    def _transform_preprocess_NanRemover(
        self,
        df: pd.DataFrame,
        columns_to_remove: Optional[List[str]]
    ) -> pd.DataFrame:
        """Drop columns identified during NaN-removal fitting."""
        df = self._ensure_dataframe(df)
        return df.drop(columns=columns_to_remove or [], errors='ignore')


@dataclass
class Frequence_Feature_Engineer(BaseEstimator, TransformerMixin):
    """Feature engineering sklearn pour la fréquence."""

    def __init__(self, frequence_process: Frequence_Preprocessing):
        """Initialize feature-engineering state for frequency modeling."""
        self.frequence_process = frequence_process
        self.columns_to_remove = []
        self.booking_applied = {}
        self.preprocessing_map = {}
        self.fill_values_ = {}
        self.selected_numeric_features_ = []

    def build_feature_engineer(
        self,
        fit_process_nan_remover: Optional[bool] = True,
        transform_process_nan_remover: Optional[bool] = True,
        transform_remove_id_columns: Optional[bool] = False,
        dataset_name_for_id_removal: Optional[str] = "frequence_train",
        threshold: Optional[float] = 0.9,
        preprocessing_map: Optional[dict] = None,
        select_numeric_features_only: Optional[bool] = True,
        excluded_feature_columns: Optional[List[str]] = None,
    ):
        """Configure which preprocessing operations are enabled for this transformer."""
        self.booking_applied = {
            "fit_process_nan_remover_key": fit_process_nan_remover,
            "transform_process_nan_remover_key": transform_process_nan_remover,
            "transform_remove_id_columns_key": transform_remove_id_columns,
            "dataset_name_for_id_removal_key": dataset_name_for_id_removal,
            "threshold_key": threshold,
            "select_numeric_features_only_key": select_numeric_features_only,
        }
        self.preprocessing_map = preprocessing_map or {}
        self.excluded_feature_columns_ = excluded_feature_columns or []
        self.frequence_process.set_preprocessing_map(self.preprocessing_map)
        return self

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        """Fit internal schema, selected features, and fill values on training data."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X = X.copy()

        if self.booking_applied.get("transform_remove_id_columns_key", False):
            X = self.frequence_process._transform_remove_id_columns(
                name=self.booking_applied.get("dataset_name_for_id_removal_key", "frequence_train"),
                df=X
            )

        if self.booking_applied.get("fit_process_nan_remover_key", False):
            self.columns_to_remove = self.frequence_process._fit_preprocess_NanRemover(
                df=X,
                columns_to_remove=self.columns_to_remove,
                threshold=self.booking_applied.get("threshold_key", 0.9)
            )

        if self.booking_applied.get("transform_process_nan_remover_key", False):
            X = self.frequence_process._transform_preprocess_NanRemover(X, self.columns_to_remove)

        if self.booking_applied.get("select_numeric_features_only_key", True):
            self.selected_numeric_features_ = [
                col for col in X.columns
                if pd.api.types.is_numeric_dtype(X[col]) and col not in self.excluded_feature_columns_
            ]
            X = X[self.selected_numeric_features_].copy()
        else:
            self.selected_numeric_features_ = list(X.columns)

        num = X.select_dtypes(include=[np.number])
        self.fill_values_ = num.median(numeric_only=True).to_dict() if not num.empty else {}
        return self

    def transform(self, X: pd.DataFrame, y: pd.Series = None):
        """Apply fitted preprocessing and return aligned engineered features."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X = X.copy()

        if self.booking_applied.get("transform_remove_id_columns_key", False):
            X = self.frequence_process._transform_remove_id_columns(
                name=self.booking_applied.get("dataset_name_for_id_removal_key", "frequence_train"),
                df=X
            )

        if self.booking_applied.get("transform_process_nan_remover_key", False):
            X = self.frequence_process._transform_preprocess_NanRemover(X, self.columns_to_remove)

        if self.selected_numeric_features_:
            X = X.reindex(columns=self.selected_numeric_features_)

        if self.fill_values_:
            X = X.fillna(self.fill_values_)

        return X

    def predict(self, X: pd.DataFrame):
        """Alias of transform for sklearn compatibility in simple pipelines."""
        return self.transform(X)

    def save_feature_engineer(self, fe, filepath: str):
        """Serialize and save a fitted frequency feature-engineering artifact."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                pickle.dump(fe, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du feature engineer fréquence: {e}")

    def load_feature_engineer(self, filepath: str):
        """Load a previously serialized frequency feature-engineering artifact."""
        try:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement du feature engineer fréquence: {e}")
            return None


@dataclass
class Model_Prediction_Frequence(BaseEstimator):
    """Prédiction de la fréquence (binaire) avec GradientBoostingClassifier."""

    def __init__(self):
        """Initialize the frequency model pipeline and training metadata."""
        self.model_name_ = "GradientBoostingClassifier"
        self.pipeline_ = Pipeline([
            ("scaler", StandardScaler()),
            ("model", GradientBoostingClassifier(random_state=42)),
        ])
        self.best_estimator_ = None
        self.best_params_ = None
        self.best_score_ = None
        self.selected_features_ = []
        self.fill_values_ = {}
        self.history_ = []

    def _ensure_dataframe(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return a defensive DataFrame copy from input features."""
        if isinstance(X, pd.DataFrame):
            return X.copy()
        return pd.DataFrame(X)

    def _prepare_X(self, X: pd.DataFrame) -> pd.DataFrame:
        """Reindex and impute features according to the fitted training schema."""
        X = self._ensure_dataframe(X)
        if self.selected_features_:
            X = X.reindex(columns=self.selected_features_)
        if self.fill_values_:
            X = X.fillna(self.fill_values_)
        return X

    def tune_GBClassifier_hyperparameters(self, X, y, param_grid=None):
        """Tune GradientBoostingClassifier hyperparameters via stratified CV."""
        X = self._ensure_dataframe(X)
        self.selected_features_ = list(X.columns)
        num = X.select_dtypes(include=[np.number])
        self.fill_values_ = num.median(numeric_only=True).to_dict() if not num.empty else {}
        X = X.fillna(self.fill_values_)

        if param_grid is None:
            param_grid = {
                'model__n_estimators': [100, 200, 300],
                'model__learning_rate': [0.01, 0.1, 0.2],
                'model__max_depth': [3, 5, 7]
            }

        cv_strat = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        grid = GridSearchCV(
            estimator=self.pipeline_,
            param_grid=param_grid,
            cv=cv_strat,
            scoring='roc_auc',
            n_jobs=-1,
            refit=True
        )
        grid.fit(X, y)

        self.best_estimator_ = grid.best_estimator_
        self.best_params_ = grid.best_params_
        self.best_score_ = grid.best_score_
        self.pipeline_ = grid.best_estimator_

        return {
            "best_params_": self.best_params_,
            "best_score_": self.best_score_,
            "cv_results_": grid.cv_results_,
        }

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Fit the frequency classification pipeline."""
        X = self._prepare_X(X)
        self.pipeline_.fit(X, y)
        self.history_.append({
            "step": "fit",
            "n_rows": X.shape[0],
            "n_cols": X.shape[1],
        })
        return self

    def predict(self, X: pd.DataFrame):
        """Predict frequency classes for prepared feature rows."""
        X = self._prepare_X(X)
        return self.pipeline_.predict(X)

    def predict_proba(self, X: pd.DataFrame):
        """Predict class probabilities for frequency classification."""
        X = self._prepare_X(X)
        return self.pipeline_.predict_proba(X)

    def metrics(self, 
                y_train: pd.Series, 
                y_pred_train: np.ndarray, 
                y_proba_train: Optional[np.ndarray] = None,
                
                y_valid: Optional[pd.Series] = None, 
                y_pred_valid: Optional[pd.Series] = None,
                y_proba_valid: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Compute training and optional validation metrics for classification."""
        out = {
            "train":{
                "accuracy": accuracy_score(y_train, y_pred_train),
                "f1": f1_score(y_train, y_pred_train, zero_division=0),
                "precision": precision_score(y_train, y_pred_train, zero_division=0),
                "recall": recall_score(y_train, y_pred_train, zero_division=0),
                "roc_auc": roc_auc_score(y_train, y_proba_train)
            }
        }
        if y_valid is not None and y_pred_valid is not None:
            out["valid"] = {
                "accuracy": accuracy_score(y_valid, y_pred_valid),
                "f1": f1_score(y_valid, y_pred_valid, zero_division=0),
                "precision": precision_score(y_valid, y_pred_valid, zero_division=0),
                "recall": recall_score(y_valid, y_pred_valid, zero_division=0),
                "roc_auc": roc_auc_score(y_valid, y_proba_valid)
            }
        return out
    
    def test_prediction_stats(self, 
                              y_pred_test: np.ndarray, 
                              filepath: Optional[str] = None) -> pd.Series:
        """Compute summary stats for test predictions and optionally save them."""
        stats_test = pd.Series(
            y_pred_test,
            name='predicted_montant_sinistre'
        ).aggregate(['mean', 'std', 'min', 'median', 'max'])

        if filepath is not None:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            stats_test.to_csv(filepath, index=False)

        return stats_test

    def save_model(self, model_, filepath: str, metadata: Optional[Dict[str, Any]] = None):
        """Save model pipeline and metadata to a pickle | json artifact."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            artifact = {
                "model_name_": self.model_name_,
                "pipeline_": self.pipeline_,
                "best_estimator_": self.best_estimator_,
                "best_params_": self.best_params_,
                "best_score_": self.best_score_,
                "selected_features_": self.selected_features_,
                "fill_values_": self.fill_values_,
                "history_": self.history_,
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    **(metadata or {})
                }
            }
            with open(filepath, 'wb') as f:
                pickle.dump(artifact, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du modèle fréquence: {e}")

    def load_model(self, filepath: str):
        """Load model artifact and restore tracked model attributes."""
        try:
            with open(filepath, 'rb') as f:
                loaded = pickle.load(f)
            if isinstance(loaded, dict):
                self.pipeline_ = loaded.get("pipeline_", self.pipeline_)
                self.best_estimator_ = loaded.get("best_estimator_", self.best_estimator_)
                self.best_params_ = loaded.get("best_params_", self.best_params_)
                self.best_score_ = loaded.get("best_score_", self.best_score_)
                self.selected_features_ = loaded.get("selected_features_", self.selected_features_)
                self.fill_values_ = loaded.get("fill_values_", self.fill_values_)
            return loaded
        except Exception as e:
            print(f"Erreur lors du chargement du modèle fréquence: {e}")
            return None
    def save_complete_artifact(
        self,
        filepath: str,
        feature_engineer=None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Save a complete inference artifact with feature engineer and model."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            artifact = {
                "feature_engineer": feature_engineer,
                "model_artifact": {
                    "model_name_": self.model_name_,
                    "pipeline_": self.pipeline_,
                    "best_estimator_": self.best_estimator_,
                    "best_params_": self.best_params_,
                    "best_score_": self.best_score_,
                    "selected_features_": self.selected_features_,
                    "fill_values_": self.fill_values_,
                    "history_": self.history_,
                },
                "metadata": {
                    "saved_at": datetime.utcnow().isoformat(),
                    "artifact_type": "complete_inference_artifact",
                    **(metadata or {}),
                }
            }
            with open(filepath, "wb") as f:
                pickle.dump(artifact, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'artefact complet fréquence: {e}")

    def save_synthetic_artifact(
        self,
        filepath: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Save a lightweight artifact containing key model metadata only."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            artifact = {
                "model_name_": self.model_name_,
                "best_params_": self.best_params_,
                "best_score_": self.best_score_,
                "selected_features_": self.selected_features_,
                "history_": self.history_,
                "metadata": {
                    "saved_at": datetime.utcnow().isoformat(),
                    "artifact_type": "synthetic_model_artifact",
                    **(metadata or {}),
                }
            }
            with open(filepath, "wb") as f:
                pickle.dump(artifact, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'artefact synthétique fréquence: {e}")

    def read_artifact_metadata(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Read and return metadata from a stored model artifact file."""
        try:
            with open(filepath, 'rb') as f:
                loaded = pickle.load(f)
            if isinstance(loaded, dict):
                return loaded.get("metadata")
            return None
        except Exception as e:
            print(f"Erreur lors de la lecture des métadonnées fréquence: {e}")
            return None



# ===========================================================================
# 4--- CLASSE DE PREDICTION DE LA SEVERITE (GRAVITE) D'UN SINISTRE --------#
# ===========================================================================

def _generer_csv_pred_severite(df:pd.DataFrame,
                                y_pred: pd.Series, 
                                path:str) -> None:
    """Export severity predictions to a two-column CSV (index, pred)."""
    # Export prédictions test
    submission_df = pd.DataFrame({
        'index': df['index'],
        'pred':  y_pred
    }).to_csv(path, index=False)


@dataclass
class Severite_Preprocessing:
    """Prétraitements métier pour la prédiction de la sévérité."""

    def __init__(self, target_col: str = "montant_sinistre"):
        """Initialize severity preprocessing settings and dataset id mappings."""
        self.target_col = target_col
        self.preprocessing_map = {}
        self.categorical_features = []
        self.id_columns_by_dataset = {
            "severite_train": ['index', 'id_client', 'id_vehicule', 'id_contrat'],
            "severite_valid": ['index', 'id_client', 'id_vehicule', 'id_contrat'],
            "severite_test": ['index'],
        }

    def _ensure_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a defensive DataFrame copy from a DataFrame-like input."""
        if isinstance(df, pd.DataFrame):
            return df.copy()
        return pd.DataFrame(df)

    def _transform_remove_id_columns(self, name: str, df: pd.DataFrame) -> pd.DataFrame:
        """Remove dataset-specific identifier columns when configured."""
        df = self._ensure_dataframe(df)
        cols_to_remove = self.id_columns_by_dataset.get(name)
        if cols_to_remove is None:
            return df.copy()
        return df.drop(columns=cols_to_remove, errors='ignore')

    def _transform_remove_zero_target(self, df: pd.DataFrame, target_col: Optional[str] = None) -> pd.DataFrame:
        """Filter rows where the target is equal to zero."""
        df = self._ensure_dataframe(df)
        target_col = target_col or self.target_col
        if target_col in df.columns:
            return df[df[target_col] != 0].copy()
        return df

    # Compatibilité avec le code existant
    def _transform_remove_null_target(self, df: pd.DataFrame, target_col: Optional[str] = None) -> pd.DataFrame:
        """Compatibility alias to remove rows with a zero target."""
        return self._transform_remove_zero_target(df, target_col=target_col)

    def _transform_preprocess_null_target(self, df: pd.DataFrame, target_col: Optional[str] = None) -> pd.DataFrame:
        """Filter rows where the target column is null."""
        df = self._ensure_dataframe(df)
        target_col = target_col or self.target_col
        if target_col in df.columns:
            return df[df[target_col].notnull()].copy()
        return df

    def set_preprocessing_map(self, preprocessing_map: Optional[dict]):
        """Store a custom preprocessing map used by downstream transformers."""
        self.preprocessing_map = preprocessing_map or {}

    def _fit_preprocess_NanRemover(
        self,
        df: pd.DataFrame,
        columns_to_remove: Optional[List[str]] = None,
        threshold: Optional[float] = 0.9
    ) -> List[str]:
        """Find columns whose null ratio is above the provided threshold."""
        df = self._ensure_dataframe(df)
        return [col for col in df.columns if df[col].isna().mean() > threshold]

    def _transform_preprocess_NanRemover(
        self,
        df: pd.DataFrame,
        columns_to_remove: Optional[List[str]]
    ) -> pd.DataFrame:
        """Drop columns identified during NaN-removal fitting."""
        df = self._ensure_dataframe(df)
        return df.drop(columns=columns_to_remove or [], errors='ignore')


@dataclass
class Severite_Feature_Engineer(BaseEstimator, TransformerMixin):
    """Wrapper sklearn pour le feature engineering de la sévérité."""

    def __init__(self, severite_process: Severite_Preprocessing):
        """Initialize feature-engineering state for severity modeling."""
        self.severite_process = severite_process
        self.columns_to_remove = []
        self.booking_applied = {}
        self.preprocessing_map = {}
        self.fill_values_ = {}
        self.dataset_name_for_transform_ = None
        self.selected_numeric_features_ = []
        self.excluded_feature_columns_ = []

    def build_feature_engineer(
        self,
        fit_process_nan_remover: Optional[bool] = True,
        transform_process_nan_remover: Optional[bool] = True,
        transform_remove_id_columns: Optional[bool] = False,
        dataset_name_for_id_removal: Optional[str] = "severite_train",
        transform_remove_zero_target: Optional[bool] = False,
        transform_preprocessing_null_target: Optional[bool] = False,
        threshold: Optional[float] = 0.9,
        preprocessing_map: Optional[dict] = None,
        select_numeric_features_only: Optional[bool] = True,
        excluded_feature_columns: Optional[List[str]] = None,
    ):
        """Configure which preprocessing operations are enabled for this transformer."""
        self.booking_applied = {
            "fit_process_nan_remover_key": fit_process_nan_remover,
            "transform_process_nan_remover_key": transform_process_nan_remover,
            "transform_remove_id_columns_key": transform_remove_id_columns,
            "dataset_name_for_id_removal_key": dataset_name_for_id_removal,
            "transform_remove_zero_target_key": transform_remove_zero_target,
            "transform_preprocessing_null_target_key": transform_preprocessing_null_target,
            "threshold_key": threshold,
            "select_numeric_features_only_key": select_numeric_features_only,
        }

        self.preprocessing_map = preprocessing_map or {}
        self.excluded_feature_columns_ = excluded_feature_columns or ["nombre_sinistres"]
        self.severite_process.set_preprocessing_map(self.preprocessing_map)
        return self

    def set_dataset_name_for_transform(self, dataset_name: str):
        """Set dataset-name context used during transform-time id-column removal."""
        self.dataset_name_for_transform_ = dataset_name
        return self

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        """Fit internal schema, selected features, and fill values on training data."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        X = X.copy()

        if self.booking_applied.get("transform_remove_id_columns_key", False):
            dataset_name = (
                self.dataset_name_for_transform_
                or self.booking_applied.get("dataset_name_for_id_removal_key", "severite_train")
            )
            X = self.severite_process._transform_remove_id_columns(name=dataset_name, df=X)

        if self.booking_applied.get("transform_process_nan_remover_key", False):
            self.columns_to_remove = self.severite_process._fit_preprocess_NanRemover(
                df=X,
                columns_to_remove=self.columns_to_remove,
                threshold=self.booking_applied.get("threshold_key", 0.9)
            )
            X = self.severite_process._transform_preprocess_NanRemover(X, self.columns_to_remove)

        if self.booking_applied.get("select_numeric_features_only_key", True):
            selected_cols = [
                col for col in X.columns
                if pd.api.types.is_numeric_dtype(X[col]) and col not in self.excluded_feature_columns_
            ]
            self.selected_numeric_features_ = selected_cols
            X = X[self.selected_numeric_features_].copy()
        else:
            self.selected_numeric_features_ = list(X.columns)

        num = X.select_dtypes(include=[np.number])
        self.fill_values_ = num.median(numeric_only=True).to_dict() if not num.empty else {}

        self.n_features_in_ = X.shape[1]
        self.feature_names_in_ = list(X.columns)
        return self

    def transform(self, X: pd.DataFrame, y: pd.Series = None):
        """Apply fitted preprocessing and return aligned engineered features."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X = X.copy()

        if self.booking_applied.get("transform_remove_id_columns_key", False):
            dataset_name = (
                self.dataset_name_for_transform_
                or self.booking_applied.get("dataset_name_for_id_removal_key", "severite_train")
            )
            X = self.severite_process._transform_remove_id_columns(
                name=dataset_name,
                df=X
            )

        if self.booking_applied.get("transform_remove_zero_target_key", False):
            X = self.severite_process._transform_remove_zero_target(X)

        if self.booking_applied.get("transform_preprocessing_null_target_key", False):
            X = self.severite_process._transform_preprocess_null_target(X)

        if self.booking_applied.get("transform_process_nan_remover_key", False):
            X = self.severite_process._transform_preprocess_NanRemover(
                X,
                self.columns_to_remove
            )

        if self.selected_numeric_features_:
            X = X.reindex(columns=self.selected_numeric_features_)

        if self.fill_values_:
            X = X.fillna(self.fill_values_)

        return X

    def predict(self, X: pd.DataFrame):
        """Alias of transform for sklearn compatibility in simple pipelines."""
        return self.transform(X)

    def save_feature_engineer(self, fe, filepath: str):
        """Serialize and save a fitted severity feature-engineering artifact."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                pickle.dump(fe, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du feature engineer: {e}")

    def load_feature_engineer(self, filepath: str):
        """Load a previously serialized severity feature-engineering artifact."""
        try:
            with open(filepath, 'rb') as f:
                fe = pickle.load(f)
            return fe
        except Exception as e:
            print(f"Erreur lors du chargement du feature engineer: {e}")
            return None


@dataclass
class Model_Prediction_Severite(BaseEstimator):
    """Regression model wrapper used to predict claim severity."""

    def __init__(self):
        """Initialize the severity model pipeline and training metadata."""
        self.model_name_ = "GradientBoostingRegressor"
        self.pipeline_ = Pipeline([
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(random_state=42)),
        ])
        self.best_estimator_ = None
        self.best_params_ = None
        self.best_score_ = None
        self.selected_features_ = []
        self.fill_values_ = {}
        self.history_ = []

    def _ensure_dataframe(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return a defensive DataFrame copy from input features."""
        if isinstance(X, pd.DataFrame):
            return X.copy()
        return pd.DataFrame(X)

    def _prepare_X(self, X: pd.DataFrame) -> pd.DataFrame:
        """Reindex and impute features according to the fitted training schema."""
        X = self._ensure_dataframe(X)

        if self.selected_features_:
            X = X.reindex(columns=self.selected_features_)

        if self.fill_values_:
            X = X.fillna(self.fill_values_)

        return X

    def tune_GBRegressor_hyperparameters(self, X, y, param_grid=None, cv=5, scoring='neg_mean_squared_error'):
        """Tune GradientBoostingRegressor hyperparameters via cross-validation."""
        X = self._ensure_dataframe(X)
        y = y.copy()

        X_copie = X.copy()
        y_copie = y.copy()

        self.selected_features_ = list(X_copie.columns)
        num = X_copie.select_dtypes(include=[np.number])
        self.fill_values_ = num.median(numeric_only=True).to_dict() if not num.empty else {}
        X_copie = X_copie.fillna(self.fill_values_)

        if param_grid is None:
            param_grid = {
                'model__n_estimators': [100, 200, 300],
                'model__learning_rate': [0.01, 0.1, 0.2],
                'model__max_depth': [3, 5, 7]
            }

        grid_search = GridSearchCV(
            estimator=self.pipeline_,
            param_grid=param_grid,
            cv=cv,
            scoring=scoring,
            n_jobs=-1,
            refit=True
        )

        grid_search.fit(X_copie, y_copie)

        self.best_estimator_ = grid_search.best_estimator_
        self.best_params_ = grid_search.best_params_
        self.best_score_ = grid_search.best_score_
        self.pipeline_ = grid_search.best_estimator_

        self.history_.append({
            "step": "tune",
            "best_params_": self.best_params_,
            "best_score_": self.best_score_,
        })

        return {
            "best_params_": self.best_params_,
            "best_score_": self.best_score_,
            "cv_results_": grid_search.cv_results_,
        }

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Fit the severity regression pipeline."""
        X = self._ensure_dataframe(X)
        y = y.copy()

        X_copie = X.copy()
        y_copie = y.copy()

        self.selected_features_ = list(X_copie.columns)
        num = X_copie.select_dtypes(include=[np.number])
        self.fill_values_ = num.median(numeric_only=True).to_dict() if not num.empty else {}
        X_copie = X_copie.fillna(self.fill_values_)

        self.pipeline_.fit(X_copie, y_copie)

        self.history_.append({
            "step": "fit",
            "n_rows": X_copie.shape[0],
            "n_cols": X_copie.shape[1],
        })

        return self

    def predict(self, X: pd.DataFrame):
        """Predict claim severity values for prepared feature rows."""
        X_prepared = self._prepare_X(X)
        return self.pipeline_.predict(X_prepared)

    def metrics(self, y_train: pd.Series, 
                y_pred_train: pd.Series,
                y_valid: Optional[pd.Series] = None, 
                y_pred_valid: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Compute regression metrics for train and optional validation sets."""
        results = {
            "train": {
                "rmse": root_mean_squared_error(y_train, y_pred_train),
                "mae": mean_absolute_error(y_train, y_pred_train),
                "r2": r2_score(y_train, y_pred_train),
            }
        }

        if y_valid is not None and y_pred_valid is not None:
            results["valid"] = {
                "rmse": root_mean_squared_error(y_valid, y_pred_valid),
                "mae": mean_absolute_error(y_valid, y_pred_valid),
                "r2": r2_score(y_valid, y_pred_valid),
            }

        return results

    def test_prediction_stats(self, 
                              y_pred_test: np.ndarray, 
                              filepath: Optional[str] = None) -> pd.Series:
        """Compute summary stats for test predictions and optionally save them."""
        stats_test = pd.Series(
            y_pred_test,
            name='predicted_montant_sinistre'
        ).aggregate(['mean', 'std', 'min', 'median', 'max'])

        if filepath is not None:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            stats_test.to_csv(filepath, index=False)

        return stats_test

    def save_model(self, model_, filepath: str, metadata: Optional[Dict[str, Any]] = None):
        """Save model pipeline and metadata to a pickle artifact."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            artifact = {
                "model_name_": self.model_name_,
                "pipeline_": self.pipeline_,
                "best_estimator_": self.best_estimator_,
                "best_params_": self.best_params_,
                "best_score_": self.best_score_,
                "selected_features_": self.selected_features_,
                "fill_values_": self.fill_values_,
                "history_": self.history_,
                "metadata": {
                    "saved_at": datetime.utcnow().isoformat(),
                    **(metadata or {}),
                }
            }
            with open(filepath, 'wb') as f:
                pickle.dump(artifact, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du modèle: {e}")

    def load_model(self, filepath: str):
        """Load model artifact and restore tracked model attributes."""
        try:
            with open(filepath, 'rb') as f:
                loaded = pickle.load(f)

            if isinstance(loaded, dict):
                self.model_name_ = loaded.get("model_name_", self.model_name_)
                self.pipeline_ = loaded.get("pipeline_", self.pipeline_)
                self.best_estimator_ = loaded.get("best_estimator_", self.best_estimator_)
                self.best_params_ = loaded.get("best_params_", self.best_params_)
                self.best_score_ = loaded.get("best_score_", self.best_score_)
                self.selected_features_ = loaded.get("selected_features_", self.selected_features_)
                self.fill_values_ = loaded.get("fill_values_", self.fill_values_)
                self.history_ = loaded.get("history_", self.history_)
            return loaded
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            return None

    def save_complete_artifact(
        self,
        filepath: str,
        feature_engineer=None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Save a complete inference artifact with feature engineer and model."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            artifact = {
                "feature_engineer": feature_engineer,
                "model_artifact": {
                    "model_name_": self.model_name_,
                    "pipeline_": self.pipeline_,
                    "best_estimator_": self.best_estimator_,
                    "best_params_": self.best_params_,
                    "best_score_": self.best_score_,
                    "selected_features_": self.selected_features_,
                    "fill_values_": self.fill_values_,
                    "history_": self.history_,
                },
                "metadata": {
                    "saved_at": datetime.utcnow().isoformat(),
                    "artifact_type": "complete_inference_artifact",
                    **(metadata or {}),
                }
            }
            with open(filepath, "wb") as f:
                pickle.dump(artifact, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'artefact complet: {e}")

    def save_synthetic_artifact(
        self,
        filepath: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Save a lightweight artifact containing key model metadata only."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            artifact = {
                "model_name_": self.model_name_,
                "best_params_": self.best_params_,
                "best_score_": self.best_score_,
                "selected_features_": self.selected_features_,
                "history_": self.history_,
                "metadata": {
                    "saved_at": datetime.utcnow().isoformat(),
                    "artifact_type": "synthetic_model_artifact",
                    **(metadata or {}),
                }
            }
            with open(filepath, "wb") as f:
                pickle.dump(artifact, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'artefact synthétique: {e}")

    def read_artifact_metadata(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Read and return metadata from a stored model artifact file."""
        try:
            with open(filepath, 'rb') as f:
                loaded = pickle.load(f)

            if isinstance(loaded, dict):
                return loaded.get('metadata', None)
            return None
        except Exception as e:
            print(f"Erreur lors de la lecture des métadonnées de l'artefact: {e}")
            return None
