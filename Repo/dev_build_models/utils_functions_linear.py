


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
from sklearn.ensemble import  GradientBoostingRegressor
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import GridSearchCV

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
    """Classe de prétraitement pour la fréquence d'apparition d'un sinistre.

    Cette version reprend les utilitaires présents dans `Amount_Preprocessing` mais
    adaptés à la cible `nombre_sinistres` et aux besoins d'analyse de fréquence.
    """
    def __init__(self):
        self.preprocessing_map = {}
        self.categorical_features = []

    def analyse_stats_modalities(self, stats_df, target_type='numeric'):
        def _safe_fmt(val, fmt='.2f'):
            try:
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return 'NA'
                return format(val, fmt)
            except Exception:
                return str(val)

        n_modalities = stats_df.shape[0]
        for _, row in stats_df.iterrows():
            mean = row.get('mean', None)
            median = row.get('median', row.get('50%', None))
            median_positive = row.get('median_positive', None)
            count_zero = row.get('count_zero', None)
            pct_zero = row.get('pct_zero', None)
            std = row.get('std', None)
            variance = row.get('variance', None)
            n = row.get('n', None)
            label = row.get('marque_vehicule') or row.get('modele_vehicule')
            if label is None:
                try:
                    label = row.iloc[0]
                except Exception:
                    label = 'NA'

            extra = ''
            if median_positive is not None:
                extra += f", median_pos={_safe_fmt(median_positive)}"
            if pct_zero is not None:
                extra += f", pct_zero={_safe_fmt(pct_zero)}"

            print(
                f"Modalité: {label}, n={_safe_fmt(n, 'd') if isinstance(n, (int, np.integer)) else _safe_fmt(n)}",
                f"mean={_safe_fmt(mean)}, median={_safe_fmt(median)}, std={_safe_fmt(std)}, variance={_safe_fmt(variance)}{extra}",
            )

            if std is not None and mean is not None:
                try:
                    if std > 2 * abs(mean):
                        print("  ⚠ Forte dispersion (std élevé par rapport à la moyenne)")
                except Exception:
                    pass
            if variance is not None and mean is not None:
                try:
                    if variance > 2 * abs(mean):
                        print("  ⚠ Variance élevée")
                except Exception:
                    pass
            if n is not None:
                try:
                    if int(n) < 10:
                        print("  ⚠ Effectif faible, test non robuste.")
                except Exception:
                    pass
            if pct_zero is not None:
                try:
                    if isinstance(pct_zero, (float, int)) and pct_zero > 0.5:
                        print("  ⚠ Forte proportion de zéros dans la cible pour cette modalité. Considérer l'analyse uniquement sur fréquences > 0.")
                except Exception:
                    pass
            if mean is not None and median is not None and std is not None:
                try:
                    if abs(mean - median) < 0.1 * std:
                        print("  → Distribution plutôt normale, ANOVA possible si n > 30.")
                    else:
                        print("  → Distribution asymétrique ou outliers, privilégier Kruskal-Wallis.")
                except Exception:
                    pass

        print("\n[SUGGESTION DE TEST STATISTIQUE]")
        if target_type == 'binary':
            print("  → Variable cible binaire : privilégier chi² ou Fisher exact.")
        elif n_modalities == 2:
            print("  → Deux modalités : privilégier Mann-Whitney.")
        else:
            print("  → Plusieurs modalités : ANOVA si toutes distributions normales et n > 30, sinon Kruskal-Wallis.")

    def plot_modalities_distribution(self, df: pd.DataFrame, target: str, feature: str, max_modalities: int = 15):
        import matplotlib.pyplot as plt
        import seaborn as sns
        if feature not in df.columns or target not in df.columns:
            print(f"Colonne {feature} ou {target} absente du DataFrame.")
            return
        counts = df[feature].value_counts()
        valid_modalities = counts[counts >= 5].index[:max_modalities]
        df_plot = df[df[feature].isin(valid_modalities)].copy()
        plt.figure(figsize=(min(0.7*len(valid_modalities)+6, 18), 6))
        sns.boxplot(x=feature, y=target, data=df_plot, showfliers=False)
        plt.title(f"Boxplot de {target} par {feature} (top {max_modalities})")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

        for modality in valid_modalities:
            subset = df_plot[df_plot[feature] == modality][target]
            plt.figure(figsize=(6, 3))
            sns.histplot(subset, bins=20, kde=True)
            plt.title(f"Histogramme de {target} pour {feature} = {modality} (n={len(subset)})")
            plt.xlabel(target)
            plt.ylabel("Fréquence")
            plt.tight_layout()
            plt.show()

        stats = df_plot.groupby(feature)[target].describe(percentiles=[.25, .5, .75]).reset_index()
        stats['variance'] = df_plot.groupby(feature)[target].var().values
        print(f"\n[STATISTIQUES DESCRIPTIVES de {target} par {feature}]")
        print(stats[[feature, 'count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'variance']].head(max_modalities).to_string(index=False))

    def get_code_postal_modalities_by_correlation(self, df: pd.DataFrame, target: str) -> pd.DataFrame:
        import numpy as np
        if 'code_postal' not in df.columns or target not in df.columns:
            return pd.DataFrame()
        counts = df['code_postal'].value_counts()
        valid_modalities = counts[counts >= 5].index
        group = df[df['code_postal'].isin(valid_modalities)].groupby('code_postal')[target].mean().reset_index()
        group['correlation'] = group['code_postal'].apply(lambda x: df[df['code_postal'] == x][target].corr(df[target]))
        group = group[~group['correlation'].isna()]
        group = group[np.isfinite(group['correlation'])]
        return group.sort_values('correlation', ascending=True).reset_index(drop=True)

    def get_modele_vehicule_modalities_by_correlation(self, df: pd.DataFrame, target: str) -> pd.DataFrame:
        import numpy as np
        if 'modele_vehicule' not in df.columns or target not in df.columns:
            return pd.DataFrame()
        counts = df['modele_vehicule'].value_counts()
        valid_modalities = counts[counts >= 5].index
        group = df[df['modele_vehicule'].isin(valid_modalities)].groupby('modele_vehicule')[target].mean().reset_index()
        group['correlation'] = group['modele_vehicule'].apply(lambda x: df[df['modele_vehicule'] == x][target].corr(df[target]))
        group = group[~group['correlation'].isna()]
        group = group[np.isfinite(group['correlation'])]
        return group.sort_values('correlation', ascending=True).reset_index(drop=True)

    def get_modele_vehicule_modalities_stats(self, df: pd.DataFrame, target: str) -> pd.DataFrame:
        if 'modele_vehicule' not in df.columns or target not in df.columns:
            return pd.DataFrame()
        counts = df['modele_vehicule'].value_counts()
        valid_modalities = counts[counts >= 5].index
        result = []
        for modele in valid_modalities:
            subset = df[df['modele_vehicule'] == modele][target]
            stats = {
                'modele_vehicule': modele,
                'mean': subset.mean(),
                'median': subset.median(),
                'median_positive': subset[subset > 0].median() if (subset > 0).any() else np.nan,
                'count_zero': int((subset == 0).sum()),
                'pct_zero': float((subset == 0).mean()),
                'std': subset.std(),
                'min': subset.min(),
                'max': subset.max(),
                'n': subset.shape[0],
                'variance': subset.var()
            }
            result.append(stats)
        group = pd.DataFrame(result)
        return group.sort_values('variance', ascending=False).reset_index(drop=True)

    def get_marque_vehicule_modalities_stats(self, df: pd.DataFrame, target: str) -> pd.DataFrame:
        if 'marque_vehicule' not in df.columns or target not in df.columns:
            return pd.DataFrame()
        counts = df['marque_vehicule'].value_counts()
        valid_modalities = counts[counts >= 5].index
        result = []
        for marque in valid_modalities:
            subset = df[df['marque_vehicule'] == marque][target]
            stats = {
                'marque_vehicule': marque,
                'mean': subset.mean(),
                'median': subset.median(),
                'median_positive': subset[subset > 0].median() if (subset > 0).any() else np.nan,
                'count_zero': int((subset == 0).sum()),
                'pct_zero': float((subset == 0).mean()),
                'std': subset.std(),
                'min': subset.min(),
                'max': subset.max(),
                'n': subset.shape[0],
                'variance': subset.var()
            }
            result.append(stats)
        group = pd.DataFrame(result)
        return group.sort_values('variance', ascending=False).reset_index(drop=True)

    def one_hot_encode_low_cardinality(self, df:pd.DataFrame, modalities_dict:dict) -> pd.DataFrame:
        cols_to_encode = list(modalities_dict.keys())
        return pd.get_dummies(df, columns=cols_to_encode, drop_first=False)

    def remove_id_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        explicit_cols = ['id_client', 'id_vehicule', 'id_contrat']
        cols_to_remove = [col for col in df.columns if col.startswith('id_') or col in explicit_cols]
        return df.drop(columns=cols_to_remove, errors='ignore')

    def get_categorical_features_modalities_count(self, modalities_dict: dict) -> tuple:
        dict_inf_10 = {}
        dict_sup_10 = {}
        for col, modalities in modalities_dict.items():
            n = len(modalities)
            if n <= 10:
                dict_inf_10[col] = n
            else:
                dict_sup_10[col] = n
        return dict_inf_10, dict_sup_10

    def get_categorical_features_modalities(self, df:pd.DataFrame) -> dict:
        cat_cols = self.get_categorical_features(df)
        return {col: list(df[col].dropna().unique()) for col in cat_cols}

    def get_numerical_features_types(self, df:pd.DataFrame) -> dict:
        num_cols = self.get_numerical_features(df)
        return {col: str(df[col].dtype) for col in num_cols}

    def get_categorical_features(self, df:pd.DataFrame) -> list:
        return [col for col in df.columns if df[col].dtype == 'object' or str(df[col].dtype).startswith('category')]

    def get_numerical_features(self, df:pd.DataFrame) -> list:
        return [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]

    def transform_remove_zero_target(self, df, target_col='nombre_sinistres'):
        if target_col in df.columns:
            return df[df[target_col] != 0].copy()
        return df

    def transform_remove_null_target(self, df, target_col='nombre_sinistres'):
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
        for col, method in self.preprocessing_map.items():
            if method == 'winsorize':
                df = self.winsorize_feature(df, col)
            elif method == 'log':
                df = self.log_transform_feature(df, col)
            elif method == 'bin':
                df = self.bin_feature(df, col)
        if self.categorical_features:
            df = self.encode_categorical_features(df)
        return df

    def _fit_preprocess_NanRemover(self, df:pd.DataFrame, 
                                   columns_to_remove:List[str], 
                                   threshold:Optional[float]=0.9) -> List[str]:
        columns_to_remove = [
            col for col in df.columns if df[col].isna().mean() > threshold
        ]
        return columns_to_remove
    
    def _transform_preprocess_NanRemover(self, df:pd.DataFrame, columns_to_remove:List[str]) :
        df = df.drop(columns=columns_to_remove, errors='ignore')
        return df

    def _transform_preprocessing_null_target(self, df:pd.DataFrame, target_col:str = 'nombre_sinistres') -> pd.DataFrame:
        if target_col in df.columns:
            return df[df[target_col].notnull()].copy()
        return df
    

@dataclass
class Feature_Engineer_Freq(BaseEstimator, TransformerMixin):
    """Classe de feature engineering pour la prédiction de la fréquence d'apparition d'un sinistre."""
    def __init__(self, freq_process: Freq_Preprocessing = None):
        self.freq_process = freq_process or Freq_Preprocessing()
        self.columns_to_remove = []
        self.booking_applied = {}
        self.preprocessing_map = {}
        self.categorical_features = []
        # état appris
        self.fill_values_ = {}
        self.categ_mapping_ = {}
        self.winsor_bounds_ = {}
        self.scaler_ = None
        # paramètres pour target-encoding
        self.alpha = 10.0
        self.min_count = 5
        # regularisation / robustesse
        self.noise_during_fit = False
        self.noise_std = 0.01
        # post-processing des encodages
        self.do_standardize = False
        self.clip_pct = (0.01, 0.99)
        # stats d'encodage stockées
        self.enc_stats_ = {}
        # per-column overrides
        self.per_col_min_count = {}
        self.per_col_top_k = {}

    def build_feature_engineer(self,
                               fit_process_nan_remover: Optional[bool] = True,
                               transform_process_nan_remover: Optional[bool] = True,
                               transform_remove_zero_target: Optional[bool] = False,
                               threshold: Optional[float] = 0.9,
                               preprocessing_map: Optional[dict] = None,
                               categorical_features: Optional[list] = None,
                               alpha: Optional[float] = 10.0,
                               min_count: Optional[int] = 5,
                               per_col_min_count: Optional[dict] = None,
                               per_col_top_k: Optional[dict] = None,
                               noise_during_fit: Optional[bool] = False,
                               noise_std: Optional[float] = 0.01,
                               do_standardize: Optional[bool] = False,
                               clip_pct: Optional[tuple] = (0.01, 0.99),
                               transform_remove_null_target: Optional[bool] = True,
                               transform_preprocessing_null_target: Optional[bool] = False):
        print("[build_feature_engineer] Initialisation du booking des preprocessing...")
        self.booking_applied = {
            "fit_process_nan_remover_key": fit_process_nan_remover,
            "transform_process_nan_remover_key": transform_process_nan_remover,
            "transform_remove_zero_target_key": transform_remove_zero_target,
            "transform_remove_null_target_key": transform_remove_null_target,
            "transform_preprocessing_null_target_key": transform_preprocessing_null_target,
            "threshold_key": threshold}
        print(f"[build_feature_engineer] Booking appliqué : {self.booking_applied}")
        if preprocessing_map is not None:
            print(f"[build_feature_engineer] Mise à jour preprocessing_map : {preprocessing_map}")
            self.preprocessing_map = preprocessing_map
            self.freq_process.set_preprocessing_map(preprocessing_map)
        if categorical_features is not None:
            print(f"[build_feature_engineer] Mise à jour categorical_features : {categorical_features}")
            self.categorical_features = categorical_features
            self.freq_process.set_categorical_features(categorical_features)
        self.alpha = float(alpha)
        self.min_count = int(min_count)
        self.noise_during_fit = bool(noise_during_fit)
        self.noise_std = float(noise_std)
        self.do_standardize = bool(do_standardize)
        try:
            self.clip_pct = (float(clip_pct[0]), float(clip_pct[1]))
        except Exception:
            self.clip_pct = (0.01, 0.99)
        self.per_col_min_count = per_col_min_count or {}
        self.per_col_top_k = per_col_top_k or {}
        print("[build_feature_engineer] Initialisation terminée.")

    def _compute_tschuprow_t(self, series_x: pd.Series, y: pd.Series, n_bins: int = 10, min_count: int = 5) -> float:
        """Calcule Tschuprow's T entre une variable explicative numérique (après binning) et la cible quantitative.

        On discretise la variable explicative et la cible en quantiles (ou bins) puis on calcule
        la statistique chi2 sur la table de contingence et on en déduit Tschuprow's T.
        Retourne NaN si calcul non possible.
        """
        try:
            import pandas as _pd
            import numpy as _np
            from scipy.stats import chi2_contingency
        except Exception:
            return float('nan')

        if series_x is None or y is None:
            return float('nan')
        try:
            sx = series_x.dropna()
            sy = y.loc[sx.index]
        except Exception:
            sx = series_x.copy()
            sy = y.copy()

        if sx.shape[0] < int(min_count):
            return float('nan')

        # bin both series using quantiles for robustness
        try:
            bx = _pd.qcut(sx.rank(method='first'), q=int(n_bins), labels=False, duplicates='drop')
        except Exception:
            try:
                bx = _pd.cut(sx, bins=int(n_bins), labels=False)
            except Exception:
                return float('nan')
        try:
            by = _pd.qcut(sy.rank(method='first'), q=int(n_bins), labels=False, duplicates='drop')
        except Exception:
            try:
                by = _pd.cut(sy, bins=int(n_bins), labels=False)
            except Exception:
                return float('nan')

        df = _pd.DataFrame({'bx': bx, 'by': by}).dropna()
        if df.shape[0] < int(min_count):
            return float('nan')
        ct = _pd.crosstab(df['bx'], df['by'])
        if ct.shape[0] < 2 or ct.shape[1] < 2:
            return float('nan')
        try:
            chi2, p, dof, expected = chi2_contingency(ct)
        except Exception:
            return float('nan')
        n = ct.values.sum()
        r, c = ct.shape
        denom = n * _np.sqrt(max(0.0, (r - 1) * (c - 1)))
        if denom <= 0:
            return float('nan')
        T = _np.sqrt(max(0.0, float(chi2) / float(denom)))
        return float(T)

    def _compute_kruskal_wallis(self, series_cat: pd.Series, y: pd.Series, min_count: int = 5) -> dict:
        """Calcule le test de Kruskal-Wallis entre une variable catégorielle et la cible quantitative.

        Retourne un dict {'statistic': float, 'pvalue': float} ou NaN si non calculable.
        """
        try:
            import pandas as _pd
            import numpy as _np
            from scipy.stats import kruskal
        except Exception:
            return {'statistic': float('nan'), 'pvalue': float('nan')}

        if series_cat is None or y is None:
            return {'statistic': float('nan'), 'pvalue': float('nan')}

        df = _pd.DataFrame({'cat': series_cat.fillna('___NaN___').astype(str), 'y': y})
        counts = df['cat'].value_counts()
        valid = counts[counts >= int(min_count)].index.tolist()
        if len(valid) < 2:
            return {'statistic': float('nan'), 'pvalue': float('nan')}
        groups = [df.loc[df['cat'] == k, 'y'].values for k in valid]
        try:
            stat, p = kruskal(*groups)
            return {'statistic': float(stat), 'pvalue': float(p)}
        except Exception:
            return {'statistic': float('nan'), 'pvalue': float('nan')}

    def preselect_features(self, X: pd.DataFrame, y: pd.Series,
                           top_k_numeric: int = 20,
                           top_k_categorical: int = 20,
                           pvalue_threshold: float = 0.05,
                           n_bins: int = 10,
                           min_count: int = 5) -> list:
        """Présélectionne des features en appliquant :
        - Tschuprow's T pour variables numériques (via binning de la variable et de la cible)
        - Kruskal-Wallis pour variables catégorielles

        Stocke les listes `preselected_numeric_`, `preselected_categorical_` et `preselected_features_`.
        Retourne la liste combinée des features présélectionnées.
        """
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        # ignore index column if present
        num_cols = [c for c in num_cols if c != 'index']
        cat_cols = [c for c in (self.categorical_features or []) if c in X.columns]

        numeric_scores = {}
        for col in num_cols:
            try:
                if X[col].dropna().shape[0] < int(min_count):
                    numeric_scores[col] = float('nan')
                    continue
                t = self._compute_tschuprow_t(X[col], y, n_bins=n_bins, min_count=min_count)
                numeric_scores[col] = t
            except Exception:
                numeric_scores[col] = float('nan')

        # sort numeric by T (descending), NaN last
        import numpy as _np
        sorted_num = sorted(numeric_scores.items(), key=lambda kv: (_np.nan_to_num(kv[1], nan=-1.0)), reverse=True)
        selected_numeric = [k for k, v in sorted_num if not _np.isnan(v)][:int(top_k_numeric)]

        categorical_scores = {}
        for col in cat_cols:
            try:
                res = self._compute_kruskal_wallis(X[col], y, min_count=min_count)
                categorical_scores[col] = res
            except Exception:
                categorical_scores[col] = {'statistic': float('nan'), 'pvalue': float('nan')}

        # filter by pvalue threshold then sort by statistic descending
        cat_filtered = {k: v for k, v in categorical_scores.items() if v.get('pvalue') is not None and not _np.isnan(v.get('pvalue')) and v.get('pvalue') <= float(pvalue_threshold)}
        sorted_cat = sorted(cat_filtered.items(), key=lambda kv: (kv[1]['pvalue'], -kv[1]['statistic']))
        selected_categorical = [k for k, v in sorted_cat][:int(top_k_categorical)]

        self.preselected_numeric_ = selected_numeric
        self.preselected_categorical_ = selected_categorical
        self.preselected_features_ = selected_numeric + selected_categorical
        return self.preselected_features_

    def fit(self, X:pd.DataFrame, y:pd.Series=None):
        print("[fit] Synchronisation preprocessing_map et categorical_features avec freq_process...")
        if hasattr(self.freq_process, 'set_preprocessing_map') and self.preprocessing_map:
            print(f"[fit] Mise à jour preprocessing_map dans freq_process : {self.preprocessing_map}")
            self.freq_process.set_preprocessing_map(self.preprocessing_map)
        if hasattr(self.freq_process, 'set_categorical_features') and self.categorical_features:
            print(f"[fit] Mise à jour categorical_features dans freq_process : {self.categorical_features}")
            self.freq_process.set_categorical_features(self.categorical_features)
        if self.booking_applied.get("fit_process_nan_remover_key", False):
            print("[fit] Application du fit_process_nan_remover...")
            self.columns_to_remove = self.freq_process._fit_preprocess_NanRemover(X, 
                                                                                  self.columns_to_remove, 
                                                                                  self.booking_applied.get("threshold_key", 0.9))
            print(f"[fit] Colonnes à retirer : {self.columns_to_remove}")
        if isinstance(X, pd.DataFrame):
            num = X.select_dtypes(include=[np.number])
            if num.shape[1] > 0:
                self.fill_values_ = num.median(numeric_only=True).to_dict()
                print(f"[fit] Valeurs d'imputation calculées : {self.fill_values_}")
        if y is not None and self.categorical_features:
            print("[fit] Apprentissage des encodages catégoriels (target-encoding)...")
            df = X.copy()
            df = df.reset_index(drop=True)
            y = y.reset_index(drop=True)
            global_mean = float(y.mean())
            cv = 5
            min_count = int(self.min_count)
            alpha = float(self.alpha)
            for col in self.categorical_features:
                if col not in df.columns:
                    print(f"[fit] Colonne {col} absente, encodage ignoré.")
                    continue
                series = df[col].fillna('___NaN___').astype(str)
                col_top_k = int(self.per_col_top_k.get(col, 0)) if isinstance(self.per_col_top_k, dict) else 0
                if col_top_k and col_top_k > 0:
                    top_vals = series.value_counts().index[:col_top_k].tolist()
                    series = series.apply(lambda v: v if v in top_vals else 'OTHER')
                oof_values = pd.Series(index=df.index, dtype=float)
                rnd = np.random.RandomState(42)
                kf = KFold(n_splits=cv, shuffle=True, random_state=42)
                for train_idx, val_idx in kf.split(df):
                    train_cats = series.iloc[train_idx]
                    train_y = y.iloc[train_idx]
                    grp = train_y.groupby(train_cats).mean()
                    oof_values.iloc[val_idx] = series.iloc[val_idx].map(grp)
                oof_values = oof_values.fillna(global_mean)
                counts = series.value_counts()
                mapping = {}
                rare_cats = []
                col_min_count = int(self.per_col_min_count.get(col, min_count)) if isinstance(self.per_col_min_count, dict) else int(min_count)
                for cat, cnt in counts.items():
                    if cnt < col_min_count:
                        rare_cats.append(str(cat))
                    else:
                        cat_mean = float(y[series == cat].mean()) if cnt > 0 else global_mean
                        smooth = (cnt * cat_mean + alpha * global_mean) / (cnt + alpha)
                        if self.noise_during_fit:
                            noise = rnd.normal(loc=0.0, scale=(self.noise_std * float(y.std() if float(y.std())>0 else 1.0)))
                            smooth = float(smooth) + float(noise)
                        mapping[str(cat)] = float(smooth)
                other_mean = None
                if len(rare_cats) > 0:
                    mask_rare = series.isin(rare_cats)
                    try:
                        other_mean = float(y[mask_rare].mean())
                    except Exception:
                        other_mean = None
                if other_mean is None or np.isnan(other_mean):
                    other_mean = global_mean
                other_smooth = float((len(rare_cats) * other_mean + alpha * global_mean) / (len(rare_cats) + alpha)) if len(rare_cats) > 0 else float(global_mean)
                if self.noise_during_fit:
                    noise = rnd.normal(loc=0.0, scale=(self.noise_std * float(y.std() if float(y.std())>0 else 1.0)))
                    other_smooth = other_smooth + float(noise)
                mapping['OTHER'] = float(other_smooth)
                map_vals = np.array(list(mapping.values()), dtype=float)
                try:
                    low, high = np.percentile(map_vals, [100.0 * self.clip_pct[0], 100.0 * self.clip_pct[1]])
                except Exception:
                    low, high = (np.min(map_vals), np.max(map_vals))
                for k in list(mapping.keys()):
                    mapping[k] = float(np.clip(mapping[k], low, high))
                default_val = float(np.clip(global_mean, low, high))
                enc_mean = float(np.mean(list(mapping.values()))) if len(mapping) > 0 else float(default_val)
                enc_std = float(np.std(list(mapping.values()))) if len(mapping) > 0 else 1.0
                if self.do_standardize and enc_std != 0:
                    for k in list(mapping.keys()):
                        mapping[k] = float((mapping[k] - enc_mean) / enc_std)
                    default_val = float((default_val - enc_mean) / enc_std)
                self.categ_mapping_[col] = {
                    'mapping': mapping,
                    'default': default_val,
                    'alpha': float(alpha),
                    'min_count': int(col_min_count),
                    'rare_categories': rare_cats,
                }
                self.enc_stats_[col] = {'mean': enc_mean, 'std': enc_std, 'clip_bounds': (float(low), float(high))}
                print(f"[fit] Encodage target-encoding appris pour {col}.")
        print("[fit] Fin du fit.")
        return self
        """Entraîne les différentes étapes de feature engineering sur les données d'entraînement."""
        if self.booking_applied.get("fit_process_nan_remover_key", False):
            self.columns_to_remove = self.freq_process._fit_preprocess_NanRemover(X, 
                                                                                  self.columns_to_remove, 
                                                                                  self.booking_applied.get("threshold_key", 0.9))
        # calcul des valeurs d'imputation numériques
        if isinstance(X, pd.DataFrame):
            num = X.select_dtypes(include=[np.number])
            if num.shape[1] > 0:
                self.fill_values_ = num.median(numeric_only=True).to_dict()

        # Apprentissage des encodages catégoriels de type target-encoding (OOF smoothing)
        if y is not None and self.categorical_features:
            df = X.copy()
            df = df.reset_index(drop=True)
            y = y.reset_index(drop=True)
            global_mean = float(y.mean())
            cv = 5
            min_count = int(self.min_count)
            alpha = float(self.alpha)
            for col in self.categorical_features:
                if col not in df.columns:
                    continue
                series = df[col].fillna('___NaN___').astype(str)
                # per-column top_k reduction (keep only top_k frequent values, others -> 'OTHER')
                col_top_k = int(self.per_col_top_k.get(col, 0)) if isinstance(self.per_col_top_k, dict) else 0
                if col_top_k and col_top_k > 0:
                    top_vals = series.value_counts().index[:col_top_k].tolist()
                    series = series.apply(lambda v: v if v in top_vals else 'OTHER')
                oof_values = pd.Series(index=df.index, dtype=float)
                rnd = np.random.RandomState(42)
                kf = KFold(n_splits=cv, shuffle=True, random_state=42)
                for train_idx, val_idx in kf.split(df):
                    train_cats = series.iloc[train_idx]
                    train_y = y.iloc[train_idx]
                    grp = train_y.groupby(train_cats).mean()
                    oof_values.iloc[val_idx] = series.iloc[val_idx].map(grp)
                oof_values = oof_values.fillna(global_mean)

                # compute counts on full data
                counts = series.value_counts()
                mapping = {}
                rare_cats = []
                col_min_count = int(self.per_col_min_count.get(col, min_count)) if isinstance(self.per_col_min_count, dict) else int(min_count)
                for cat, cnt in counts.items():
                    if cnt < col_min_count:
                        rare_cats.append(str(cat))
                    else:
                        cat_mean = float(y[series == cat].mean()) if cnt > 0 else global_mean
                        smooth = (cnt * cat_mean + alpha * global_mean) / (cnt + alpha)
                        if self.noise_during_fit:
                            noise = rnd.normal(loc=0.0, scale=(self.noise_std * float(y.std() if float(y.std())>0 else 1.0)))
                            smooth = float(smooth) + float(noise)
                        mapping[str(cat)] = float(smooth)

                other_mean = None
                if len(rare_cats) > 0:
                    mask_rare = series.isin(rare_cats)
                    try:
                        other_mean = float(y[mask_rare].mean())
                    except Exception:
                        other_mean = None
                if other_mean is None or np.isnan(other_mean):
                    other_mean = global_mean

                other_smooth = float((len(rare_cats) * other_mean + alpha * global_mean) / (len(rare_cats) + alpha)) if len(rare_cats) > 0 else float(global_mean)
                if self.noise_during_fit:
                    noise = rnd.normal(loc=0.0, scale=(self.noise_std * float(y.std() if float(y.std())>0 else 1.0)))
                    other_smooth = other_smooth + float(noise)
                mapping['OTHER'] = float(other_smooth)

                map_vals = np.array(list(mapping.values()), dtype=float)
                try:
                    low, high = np.percentile(map_vals, [100.0 * self.clip_pct[0], 100.0 * self.clip_pct[1]])
                except Exception:
                    low, high = (np.min(map_vals), np.max(map_vals))
                for k in list(mapping.keys()):
                    mapping[k] = float(np.clip(mapping[k], low, high))

                default_val = float(np.clip(global_mean, low, high))

                enc_mean = float(np.mean(list(mapping.values()))) if len(mapping) > 0 else float(default_val)
                enc_std = float(np.std(list(mapping.values()))) if len(mapping) > 0 else 1.0
                if self.do_standardize and enc_std != 0:
                    for k in list(mapping.keys()):
                        mapping[k] = float((mapping[k] - enc_mean) / enc_std)
                    default_val = float((default_val - enc_mean) / enc_std)

                self.categ_mapping_[col] = {
                    'mapping': mapping,
                    'default': default_val,
                    'alpha': float(alpha),
                    'min_count': int(col_min_count),
                    'rare_categories': rare_cats,
                }
                self.enc_stats_[col] = {'mean': enc_mean, 'std': enc_std, 'clip_bounds': (float(low), float(high))}

        return self

    def transform(self, X:pd.DataFrame, y:pd.Series=None):
        print("[transform] Vérification et application preprocessing_map et categorical_features...")
        if hasattr(self.freq_process, 'set_preprocessing_map') and self.preprocessing_map:
            print(f"[transform] Mise à jour preprocessing_map dans freq_process : {self.preprocessing_map}")
            self.freq_process.set_preprocessing_map(self.preprocessing_map)
        if hasattr(self.freq_process, 'set_categorical_features') and self.categorical_features:
            print(f"[transform] Mise à jour categorical_features dans freq_process : {self.categorical_features}")
            self.freq_process.set_categorical_features(self.categorical_features)
        if self.booking_applied.get("transform_remove_zero_target_key", False):
            print("[transform] Suppression des zéros sur la cible...")
            X = self.freq_process.transform_remove_zero_target(X)
        if self.booking_applied.get("transform_remove_null_target_key", False):
            print("[transform] Suppression des null sur la cible...")
            X = self.freq_process.transform_remove_null_target(X)
        if self.booking_applied.get("transform_preprocessing_null_target_key", False):
            print("[transform] Application preprocessing null target...")
            X = self.freq_process._transform_preprocessing_null_target(X)
        if self.booking_applied.get("transform_process_nan_remover_key", False):
            print("[transform] Suppression des NaN selon booking...")
            X = self.freq_process._transform_preprocess_NanRemover(X, self.columns_to_remove)
        if self.preprocessing_map:
            print("[transform] Application preprocessing_map...")
            X = self.freq_process.apply_preprocessing(X)
        X = X.copy()
        if hasattr(self, 'fill_values_') and isinstance(self.fill_values_, dict):
            print(f"[transform] Imputation des valeurs manquantes : {self.fill_values_}")
            X = X.fillna(self.fill_values_)
        for col in self.categorical_features:
            if col not in X.columns:
                print(f"[transform] Colonne {col} absente, encodage ignoré.")
                continue
            info = self.categ_mapping_.get(col)
            if not info:
                print(f"[transform] Pas de mapping pour {col}, fallback label encoding.")
                X[col] = X[col].astype('category').cat.codes
                continue
            mapping = info.get('mapping', {})
            default = info.get('default', 0.0)
            def _map_val(v):
                k = str(v) if v is not None else '___NaN___'
                if k in mapping:
                    return mapping[k]
                if 'OTHER' in mapping:
                    return mapping['OTHER']
                return default
            X[col] = X[col].fillna('___NaN___').apply(_map_val)
            print(f"[transform] Encodage appliqué sur {col}.")
        print("[transform] Fin du transform.")
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
    scoring: str = 'neg_mean_squared_error'
    max_features: int = None
    random_state: int = 42
    ratio_keep_min: float = 0.5
    ratio_keep_max: float = 1.5
    n_repeats_importance: int = 5
    max_iter: int = 1000

    def __init__(self,
                 cv=5,
                 scoring='neg_mean_squared_error',
                 max_features=None,
                 random_state=42,
                 ratio_keep_min=0.5,
                 ratio_keep_max=1.5,
                 n_repeats_importance=5,
                 max_iter=1000,
                 models: Optional[dict] = None):
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
        self.history_ = []

        # Utiliser le même estimateur que pour Amount (XGBoost classifier)
        try:
            self.model_ = XGBClassifier(random_state=self.random_state)
            self.model_name_ = 'XGBoost'
        except Exception:
            # fallback minimal
            self.model_ = LogisticRegression(max_iter=self.max_iter, random_state=self.random_state)
            self.model_name_ = 'LogisticRegression'

    def fit(self, X: pd.DataFrame, y: pd.Series, fe_freq=None):
        """
        Entraîne le modèle sur les features présélectionnées par le feature engineer.
        """
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X_num = X.select_dtypes(include=[np.number]).copy()
        self.numeric_features_ = list(X_num.columns)
        self.fill_values_ = X_num.median(numeric_only=True).to_dict()
        X_num = X_num.fillna(self.fill_values_)
        if X_num.shape[1] == 0:
            raise ValueError("Aucune colonne numérique disponible pour entraîner le modèle Freq.")
        # Utiliser la sélection du feature engineer
        if fe_freq is not None and hasattr(fe_freq, 'preselected_features_'):
            selected_features = [f for f in fe_freq.preselected_features_ if f in X_num.columns]
        else:
            selected_features = self.numeric_features_
        self.selected_features_ = selected_features.copy()
        self.selected_features_keep_ = selected_features.copy()
        self.selected_features_investigate_ = []
        self.contribution_drift_df_ = pd.DataFrame()
        # Ajout KFold cross-validation
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=self.cv, shuffle=True, random_state=self.random_state)
        scores = []
        for train_idx, val_idx in kf.split(X_num[selected_features]):
            X_train, X_val = X_num.iloc[train_idx], X_num.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            self.model_.fit(X_train[selected_features], y_train)
            y_pred = self.model_.predict(X_val[selected_features])
            from sklearn.metrics import mean_squared_error
            scores.append(mean_squared_error(y_val, y_pred))
        print(f"[fit] KFold CV scores (MSE): {scores}")
        # Fit final model sur tout le jeu
        self.model_.fit(X_num[selected_features], y)
        self.history_ = [(self.selected_features_.copy(), None)]
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
        if hasattr(self.model_, 'predict_proba'):
            return self.model_.predict_proba(X_sel)
        raise AttributeError('Le modèle utilisé n\'a pas de méthode predict_proba')

    def get_selected_features(self):
        return self.selected_features_

    def get_selected_features_keep(self):
        return self.selected_features_keep_

    def get_selected_features_investigate(self):
        return self.selected_features_investigate_

    def metrics(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        # Calcul AUC

        from sklearn.metrics import roc_auc_score, mean_squared_error
        y_pred_proba = self.predict_proba(X)[:, 1] if hasattr(self.model_, 'predict_proba') else self.predict(X)
        auc = roc_auc_score(y, y_pred_proba) if len(set(y)) > 1 else float('nan')
        mse = mean_squared_error(y, self.predict(X))
        result = {
            'auc': auc,
            'mse': mse,
        }
        return result

    def save_model(self, model, filepath: str, metadata: Optional[Dict[str, Any]] = None):
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            artifact = {
                'model_': model,
                'selected_features_': self.selected_features_,
                'selected_features_keep_': self.selected_features_keep_,
                'selected_features_investigate_': self.selected_features_investigate_,
                'numeric_features_': self.numeric_features_,
                'fill_values_': self.fill_values_,
                'history_': self.history_,
                'config': {
                    'cv': self.cv,
                    'scoring': self.scoring,
                    'max_features': self.max_features,
                    'random_state': self.random_state,
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
                self.history_ = loaded.get('history_', self.history_)
                config = loaded.get('config', {})
                self.cv = config.get('cv', self.cv)
                self.scoring = config.get('scoring', self.scoring)
                self.max_features = config.get('max_features', self.max_features)
                self.random_state = config.get('random_state', self.random_state)
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

    def analyse_stats_modalities(self, stats_df, target_type='numeric'):
        """
        Analyse automatique des statistiques de distribution pour chaque modalité.
        Affiche les valeurs clés et propose le test statistique adapté.
        target_type: 'numeric' ou 'binary'
        """
        def _safe_fmt(val, fmt='.2f'):
            try:
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return 'NA'
                return format(val, fmt)
            except Exception:
                return str(val)

        n_modalities = stats_df.shape[0]
        for _, row in stats_df.iterrows():
            mean = row.get('mean', None)
            median = row.get('median', row.get('50%', None))
            # mediane des montants strictement positifs (utile si beaucoup de zéros)
            median_positive = row.get('median_positive', None)
            count_zero = row.get('count_zero', None)
            pct_zero = row.get('pct_zero', None)
            std = row.get('std', None)
            variance = row.get('variance', None)
            n = row.get('n', None)
            # safer label retrieval
            label = row.get('marque_vehicule') or row.get('modele_vehicule')
            if label is None:
                try:
                    label = row.iloc[0]
                except Exception:
                    label = 'NA'

            extra = ''
            if median_positive is not None:
                extra += f", median_pos={_safe_fmt(median_positive)}"
            if pct_zero is not None:
                extra += f", pct_zero={_safe_fmt(pct_zero)}"

            print(
                f"Modalité: {label}, n={_safe_fmt(n, 'd') if isinstance(n, (int, np.integer)) else _safe_fmt(n)}",
                f"mean={_safe_fmt(mean)}, median={_safe_fmt(median)}, std={_safe_fmt(std)}, variance={_safe_fmt(variance)}{extra}",
            )

            # Diagnostics prudents
            if std is not None and mean is not None:
                try:
                    if std > 2 * abs(mean):
                        print("  ⚠ Forte dispersion (std élevé par rapport à la moyenne)")
                except Exception:
                    pass
            if variance is not None and mean is not None:
                try:
                    if variance > 2 * abs(mean):
                        print("  ⚠ Variance élevée")
                except Exception:
                    pass
            if n is not None:
                try:
                    if int(n) < 10:
                        print("  ⚠ Effectif faible, test non robuste.")
                except Exception:
                    pass
            if pct_zero is not None:
                try:
                    if isinstance(pct_zero, (float, int)) and pct_zero > 0.5:
                        print("  ⚠ Forte proportion de zéros dans la cible pour cette modalité. Considérer l'analyse uniquement sur montants > 0.")
                except Exception:
                    pass
            if mean is not None and median is not None and std is not None:
                try:
                    if abs(mean - median) < 0.1 * std:
                        print("  → Distribution plutôt normale, ANOVA possible si n > 30.")
                    else:
                        print("  → Distribution asymétrique ou outliers, privilégier Kruskal-Wallis.")
                except Exception:
                    pass

        print("\n[SUGGESTION DE TEST STATISTIQUE]")
        if target_type == 'binary':
            print("  → Variable cible binaire : privilégier chi² ou Fisher exact.")
        elif n_modalities == 2:
            print("  → Deux modalités : privilégier Mann-Whitney.")
        else:
            print("  → Plusieurs modalités : ANOVA si toutes distributions normales et n > 30, sinon Kruskal-Wallis.")


    def plot_modalities_distribution(self, df: pd.DataFrame, target: str, feature: str, max_modalities: int = 15):
        """
        Visualise la distribution de la cible (montant_sinistre ou nombre_sinistres) pour chaque modalité d'une variable catégorielle
        (marque_vehicule ou modele_vehicule) avec boxplots, histogrammes et statistiques descriptives.
        Affiche les stats (moyenne, médiane, quartiles, min, max, variance) pour chaque modalité.
        Args:
            df (pd.DataFrame): DataFrame source
            target (str): Nom de la colonne cible
            feature (str): Nom de la variable catégorielle
            max_modalities (int): Nombre max de modalités à afficher (par défaut 15)
        """
        import matplotlib.pyplot as plt
        import seaborn as sns
        if feature not in df.columns or target not in df.columns:
            print(f"Colonne {feature} ou {target} absente du DataFrame.")
            return
        counts = df[feature].value_counts()
        valid_modalities = counts[counts >= 5].index[:max_modalities]
        df_plot = df[df[feature].isin(valid_modalities)].copy()
        # Boxplot
        plt.figure(figsize=(min(0.7*len(valid_modalities)+6, 18), 6))
        sns.boxplot(x=feature, y=target, data=df_plot, showfliers=False)
        plt.title(f"Boxplot de {target} par {feature} (top {max_modalities})")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

        # Histogrammes par modalité
        for modality in valid_modalities:
            subset = df_plot[df_plot[feature] == modality][target]
            plt.figure(figsize=(6, 3))
            sns.histplot(subset, bins=20, kde=True)
            plt.title(f"Histogramme de {target} pour {feature} = {modality} (n={len(subset)})")
            plt.xlabel(target)
            plt.ylabel("Fréquence")
            plt.tight_layout()
            plt.show()

        # Statistiques descriptives
        stats = df_plot.groupby(feature)[target].describe(percentiles=[.25, .5, .75]).reset_index()
        stats['variance'] = df_plot.groupby(feature)[target].var().values
        print(f"\n[STATISTIQUES DESCRIPTIVES de {target} par {feature}]")
        print(stats[[feature, 'count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'variance']].head(max_modalities).to_string(index=False))

    def get_code_postal_modalities_by_correlation(self, df: pd.DataFrame, target: str) -> pd.DataFrame:
        """
        Retourne un DataFrame des modalités de code_postal classées par ordre croissant de corrélation avec la cible, filtrées pour robustesse.
        Filtre les modalités avec moins de 5 occurrences et corrélation non définie (NaN/inf).
        """
        import numpy as np
        if 'code_postal' not in df.columns or target not in df.columns:
            return pd.DataFrame()
        counts = df['code_postal'].value_counts()
        valid_modalities = counts[counts >= 5].index
        group = df[df['code_postal'].isin(valid_modalities)].groupby('code_postal')[target].mean().reset_index()
        group['correlation'] = group['code_postal'].apply(lambda x: df[df['code_postal'] == x][target].corr(df[target]))
        group = group[~group['correlation'].isna()]
        group = group[np.isfinite(group['correlation'])]
        return group.sort_values('correlation', ascending=True).reset_index(drop=True)


    def get_modele_vehicule_modalities_by_correlation(self, df: pd.DataFrame, target: str) -> pd.DataFrame:
        """
        Retourne un DataFrame des modalités de modele_vehicule classées par ordre croissant de corrélation avec la cible, filtrées pour robustesse.
        Filtre les modalités avec moins de 5 occurrences et corrélation non définie (NaN/inf).
        """
        import numpy as np
        if 'modele_vehicule' not in df.columns or target not in df.columns:
            return pd.DataFrame()
        counts = df['modele_vehicule'].value_counts()
        valid_modalities = counts[counts >= 5].index
        group = df[df['modele_vehicule'].isin(valid_modalities)].groupby('modele_vehicule')[target].mean().reset_index()
        group['correlation'] = group['modele_vehicule'].apply(lambda x: df[df['modele_vehicule'] == x][target].corr(df[target]))
        group = group[~group['correlation'].isna()]
        group = group[np.isfinite(group['correlation'])]
        return group.sort_values('correlation', ascending=True).reset_index(drop=True)

    def get_modele_vehicule_modalities_stats(self, df: pd.DataFrame, target: str) -> pd.DataFrame:
        """
        Retourne un DataFrame des modalités de modele_vehicule avec stats de distribution de la cible (moyenne, std, min, max, n, variance).
        Filtre les modalités avec moins de 5 occurrences.
        """
        if 'modele_vehicule' not in df.columns or target not in df.columns:
            return pd.DataFrame()
        counts = df['modele_vehicule'].value_counts()
        valid_modalities = counts[counts >= 5].index
        result = []
        for modele in valid_modalities:
            subset = df[df['modele_vehicule'] == modele][target]
            stats = {
                'modele_vehicule': modele,
                'mean': subset.mean(),
                'median': subset.median(),
                'median_positive': subset[subset > 0].median() if (subset > 0).any() else np.nan,
                'count_zero': int((subset == 0).sum()),
                'pct_zero': float((subset == 0).mean()),
                'std': subset.std(),
                'min': subset.min(),
                'max': subset.max(),
                'n': subset.shape[0],
                'variance': subset.var()
            }
            result.append(stats)
        group = pd.DataFrame(result)
        return group.sort_values('variance', ascending=False).reset_index(drop=True)

    def get_marque_vehicule_modalities_stats(self, df: pd.DataFrame, target: str) -> pd.DataFrame:
        """
        Retourne un DataFrame des modalités de marque_vehicule avec stats de distribution de la cible (moyenne, std, min, max, n, variance).
        Filtre les modalités avec moins de 5 occurrences.
        """
        if 'marque_vehicule' not in df.columns or target not in df.columns:
            return pd.DataFrame()
        counts = df['marque_vehicule'].value_counts()
        valid_modalities = counts[counts >= 5].index
        result = []
        for marque in valid_modalities:
            subset = df[df['marque_vehicule'] == marque][target]
            stats = {
                'marque_vehicule': marque,
                'mean': subset.mean(),
                'median': subset.median(),
                'median_positive': subset[subset > 0].median() if (subset > 0).any() else np.nan,
                'count_zero': int((subset == 0).sum()),
                'pct_zero': float((subset == 0).mean()),
                'std': subset.std(),
                'min': subset.min(),
                'max': subset.max(),
                'n': subset.shape[0],
                'variance': subset.var()
            }
            result.append(stats)
        group = pd.DataFrame(result)
        return group.sort_values('variance', ascending=False).reset_index(drop=True)


    def one_hot_encode_low_cardinality(self, df:pd.DataFrame, modalities_dict:dict) -> pd.DataFrame:
        """
        Applique un one-hot encoding uniquement aux variables catégorielles dont le nombre de modalités est ≤10.
        Args:
            df (pd.DataFrame): Le DataFrame à encoder.
            modalities_dict (dict): Dictionnaire {colonne: [modalités]} pour les variables à encoder.
        Returns:
            pd.DataFrame: DataFrame avec variables encodées en one-hot.
        """
        cols_to_encode = list(modalities_dict.keys())
        return pd.get_dummies(df, columns=cols_to_encode, drop_first=False)
    
    def remove_id_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime toutes les colonnes dont le nom commence par 'id_' ou qui sont explicitement 'id_client', 'id_vehicule', 'id_contrat'.
        Args:
            df (pd.DataFrame): Le DataFrame à traiter.
        Returns:
            pd.DataFrame: Le DataFrame sans les colonnes 'id_*', 'id_client', 'id_vehicule', 'id_contrat'.
        """
        explicit_cols = ['id_client', 'id_vehicule', 'id_contrat']
        cols_to_remove = [col for col in df.columns if col.startswith('id_') or col in explicit_cols]
        return df.drop(columns=cols_to_remove, errors='ignore')
    
    def get_categorical_features_modalities_count(self, modalities_dict: dict) -> tuple:
        """
        Retourne deux dictionnaires :
        - {colonne: nombre_modalités} pour les variables avec <=10 modalités
        - {colonne: nombre_modalités} pour les variables avec >10 modalités
        Args:
            modalities_dict (dict): Dictionnaire des modalités par variable catégorielle.
        Returns:
            tuple: (dict_inf_10, dict_sup_10)
        """
        dict_inf_10 = {}
        dict_sup_10 = {}
        for col, modalities in modalities_dict.items():
            n = len(modalities)
            if n <= 10:
                dict_inf_10[col] = n
            else:
                dict_sup_10[col] = n
        return dict_inf_10, dict_sup_10

    def get_categorical_features_modalities(self, df:pd.DataFrame) -> dict:
        """
        Retourne un dictionnaire {colonne: [modalités]} pour chaque variable catégorielle du DataFrame.
        Args:
            df (pd.DataFrame): Le DataFrame à analyser.
        Returns:
            dict: Dictionnaire des modalités pour chaque colonne catégorielle.
        """
        cat_cols = self.get_categorical_features(df)
        return {col: list(df[col].dropna().unique()) for col in cat_cols}
    
    def get_numerical_features_types(self, df:pd.DataFrame) -> dict:
        """
        Retourne un dictionnaire {colonne: type} pour chaque variable numérique du DataFrame.
        Args:
            df (pd.DataFrame): Le DataFrame à analyser.
        Returns:
            dict: Dictionnaire des types des colonnes numériques.
        """
        num_cols = self.get_numerical_features(df)
        return {col: str(df[col].dtype) for col in num_cols}
    
    def get_categorical_features(self, df:pd.DataFrame) -> list:
        """
        Retourne la liste des variables catégorielles (type 'object' ou 'category') du DataFrame.
        Args:
            df (pd.DataFrame): Le DataFrame à analyser.
        Returns:
            list: Liste des noms de colonnes catégorielles.
        """
        return [col for col in df.columns if df[col].dtype == 'object' or str(df[col].dtype).startswith('category')]

    def get_numerical_features(self, df:pd.DataFrame) -> list:
        """
        Retourne la liste des variables numériques du DataFrame.
        Args:
            df (pd.DataFrame): Le DataFrame à analyser.
        Returns:
            list: Liste des noms de colonnes numériques.
        """
        return [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]

    def transform_remove_zero_target(self, df, target_col='montant_sinistre'):
        """Retire les lignes où la cible (target_col) est nulle."""
        if target_col in df.columns:
            return df[df[target_col] != 0].copy()
        return df

    def transform_remove_null_target(self, df, target_col='montant_sinistre'):
        """Retire les lignes où la ou les colonnes cibles (target_col) sont nulles."""
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

    def _transform_preprocessing_null_target(self, df:pd.DataFrame, target_col:str = 'montant_sinistre') -> pd.DataFrame:
        """
        Retire les lignes où la colonne cible (par défaut 'montant_sinistre') est nulle (NaN).
        Args:
            df (pd.DataFrame): Le DataFrame à traiter.
            target_col (str): Le nom de la colonne cible.
        Returns:
            pd.DataFrame: Un DataFrame sans valeurs nulles dans la colonne cible.
        """
        if target_col in df.columns:
            return df[df[target_col].notnull()].copy()
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
        # état appris lors du fit
        self.fill_values_ = {}
        self.categ_mapping_ = {}   # {col: {'mapping': {cat: val}, 'default': val, 'alpha': float, 'min_count': int}}
        self.winsor_bounds_ = {}
        self.scaler_ = None
        # paramètres pour target-encoding
        self.alpha = 10.0
        self.min_count = 5
        # regularisation / robustesse
        self.noise_during_fit = False
        self.noise_std = 0.01
        # post-processing des encodages
        self.do_standardize = False
        self.clip_pct = (0.01, 0.99)
        # stats d'encodage stockées
        self.enc_stats_ = {}  # {col: {'mean':..., 'std':..., 'clip_bounds':(low,high)}}
        # per-column overrides
        self.per_col_min_count = {}
        self.per_col_top_k = {}

    def build_feature_engineer(self,
                               fit_process_nan_remover: Optional[bool] = True,
                               transform_process_nan_remover: Optional[bool] = True,
                               transform_remove_zero_target: Optional[bool] = True,
                               threshold: Optional[float] = 0.9,
                               preprocessing_map: Optional[dict] = None,
                               categorical_features: Optional[list] = None,
                               alpha: Optional[float] = 10.0,
                               min_count: Optional[int] = 5,
                               per_col_min_count: Optional[dict] = None,
                               per_col_top_k: Optional[dict] = None,
                               noise_during_fit: Optional[bool] = False,
                               noise_std: Optional[float] = 0.01,
                               do_standardize: Optional[bool] = False,
                               clip_pct: Optional[tuple] = (0.01, 0.99),
                               transform_remove_null_target: Optional[bool] = True,
                               transform_preprocessing_null_target: Optional[bool] = False):
        print("[build_feature_engineer] Initialisation du booking des preprocessing...")
        self.booking_applied = {
            "fit_process_nan_remover_key": fit_process_nan_remover,
            "transform_process_nan_remover_key": transform_process_nan_remover,
            "transform_remove_zero_target_key": transform_remove_zero_target,
            "transform_remove_null_target_key": transform_remove_null_target,
            "transform_preprocessing_null_target_key": transform_preprocessing_null_target,
            "threshold_key": threshold
        }
        print(f"[build_feature_engineer] Booking appliqué : {self.booking_applied}")
        if preprocessing_map is not None:
            print(f"[build_feature_engineer] Mise à jour preprocessing_map : {preprocessing_map}")
            self.preprocessing_map = preprocessing_map
            self.amount_process.set_preprocessing_map(preprocessing_map)
        if categorical_features is not None:
            print(f"[build_feature_engineer] Mise à jour categorical_features : {categorical_features}")
            self.categorical_features = categorical_features
            self.amount_process.set_categorical_features(categorical_features)
        self.alpha = float(alpha)
        self.min_count = int(min_count)
        self.noise_during_fit = bool(noise_during_fit)
        self.noise_std = float(noise_std)
        self.do_standardize = bool(do_standardize)
        try:
            self.clip_pct = (float(clip_pct[0]), float(clip_pct[1]))
        except Exception:
            self.clip_pct = (0.01, 0.99)
        self.per_col_min_count = per_col_min_count or {}
        self.per_col_top_k = per_col_top_k or {}
        print("[build_feature_engineer] Initialisation terminée.")

    def fit(self, X:pd.DataFrame, y:pd.Series=None):
        print("[fit] Synchronisation preprocessing_map et categorical_features avec amount_process...")
        if hasattr(self.amount_process, 'set_preprocessing_map') and self.preprocessing_map:
            print(f"[fit] Mise à jour preprocessing_map dans amount_process : {self.preprocessing_map}")
            self.amount_process.set_preprocessing_map(self.preprocessing_map)
        if hasattr(self.amount_process, 'set_categorical_features') and self.categorical_features:
            print(f"[fit] Mise à jour categorical_features dans amount_process : {self.categorical_features}")
            self.amount_process.set_categorical_features(self.categorical_features)
        if self.booking_applied.get("fit_process_nan_remover_key", False):
            print("[fit] Application du fit_process_nan_remover...")
            self.columns_to_remove = self.amount_process._fit_preprocess_NanRemover(X, 
                                                                                    self.columns_to_remove, 
                                                                                    self.booking_applied.get("threshold_key", 0.9))
            print(f"[fit] Colonnes à retirer : {self.columns_to_remove}")
        if isinstance(X, pd.DataFrame):
            num = X.select_dtypes(include=[np.number])
            if num.shape[1] > 0:
                self.fill_values_ = num.median(numeric_only=True).to_dict()
                print(f"[fit] Valeurs d'imputation calculées : {self.fill_values_}")
        if y is not None:
            print("[fit] Présélection statistique des features...")
            try:
                pre = self.preselect_features(X, y)
                self.categorical_features_preselected_ = getattr(self, 'preselected_categorical_', [])
                self.numeric_features_preselected_ = getattr(self, 'preselected_numeric_', [])
                print(f"[fit] Features catégorielles présélectionnées : {self.categorical_features_preselected_}")
                print(f"[fit] Features numériques présélectionnées : {self.numeric_features_preselected_}")
                if len(self.categorical_features_preselected_) > 0:
                    enc_categorical_features = [c for c in self.categorical_features if c in self.categorical_features_preselected_]
                    if len(enc_categorical_features) == 0:
                        enc_categorical_features = self.categorical_features
                else:
                    enc_categorical_features = self.categorical_features
                print(f"[fit] Features utilisées pour target-encoding : {enc_categorical_features}")
            except Exception as e:
                print(f"[fit] Erreur présélection features: {e}")
                enc_categorical_features = self.categorical_features
        print("[fit] Fin du fit.")

    def _compute_tschuprow_t(self, series_x: pd.Series, y: pd.Series, n_bins: int = 10, min_count: int = 5) -> float:
        try:
            import pandas as _pd
            import numpy as _np
            from scipy.stats import chi2_contingency
        except Exception:
            return float('nan')
        if series_x is None or y is None:
            return float('nan')
        try:
            sx = series_x.dropna()
            sy = y.loc[sx.index]
        except Exception:
            sx = series_x.copy()
            sy = y.copy()
        if sx.shape[0] < int(min_count):
            return float('nan')
        try:
            bx = _pd.qcut(sx.rank(method='first'), q=int(n_bins), labels=False, duplicates='drop')
        except Exception:
            try:
                bx = _pd.cut(sx, bins=int(n_bins), labels=False)
            except Exception:
                return float('nan')
        try:
            by = _pd.qcut(sy.rank(method='first'), q=int(n_bins), labels=False, duplicates='drop')
        except Exception:
            try:
                by = _pd.cut(sy, bins=int(n_bins), labels=False)
            except Exception:
                return float('nan')
        df = _pd.DataFrame({'bx': bx, 'by': by}).dropna()
        if df.shape[0] < int(min_count):
            return float('nan')
        ct = _pd.crosstab(df['bx'], df['by'])
        if ct.shape[0] < 2 or ct.shape[1] < 2:
            return float('nan')
        try:
            chi2, p, dof, expected = chi2_contingency(ct)
        except Exception:
            return float('nan')
        n = ct.values.sum()
        r, c = ct.shape
        denom = n * _np.sqrt(max(0.0, (r - 1) * (c - 1)))
        if denom <= 0:
            return float('nan')
        T = _np.sqrt(max(0.0, float(chi2) / float(denom)))
        return float(T)

    def _compute_kruskal_wallis(self, series_cat: pd.Series, y: pd.Series, min_count: int = 5) -> dict:
        try:
            import pandas as _pd
            import numpy as _np
            from scipy.stats import kruskal
        except Exception:
            return {'statistic': float('nan'), 'pvalue': float('nan')}
        if series_cat is None or y is None:
            return {'statistic': float('nan'), 'pvalue': float('nan')}
        df = _pd.DataFrame({'cat': series_cat.fillna('___NaN___').astype(str), 'y': y})
        counts = df['cat'].value_counts()
        valid = counts[counts >= int(min_count)].index.tolist()
        if len(valid) < 2:
            return {'statistic': float('nan'), 'pvalue': float('nan')}
        groups = [df.loc[df['cat'] == k, 'y'].values for k in valid]
        try:
            stat, p = kruskal(*groups)
            return {'statistic': float(stat), 'pvalue': float(p)}
        except Exception:
            return {'statistic': float('nan'), 'pvalue': float('nan')}

    def preselect_features(self, X: pd.DataFrame, y: pd.Series,
                           top_k_numeric: int = 20,
                           top_k_categorical: int = 20,
                           pvalue_threshold: float = 0.05,
                           n_bins: int = 10,
                           min_count: int = 5) -> list:
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        num_cols = [c for c in num_cols if c != 'index']
        cat_cols = [c for c in (self.categorical_features or []) if c in X.columns]
        numeric_scores = {}
        for col in num_cols:
            try:
                if X[col].dropna().shape[0] < int(min_count):
                    numeric_scores[col] = float('nan')
                    continue
                t = self._compute_tschuprow_t(X[col], y, n_bins=n_bins, min_count=min_count)
                numeric_scores[col] = t
            except Exception:
                numeric_scores[col] = float('nan')
        import numpy as _np
        sorted_num = sorted(numeric_scores.items(), key=lambda kv: (_np.nan_to_num(kv[1], nan=-1.0)), reverse=True)
        selected_numeric = [k for k, v in sorted_num if not _np.isnan(v)][:int(top_k_numeric)]
        categorical_scores = {}
        for col in cat_cols:
            try:
                res = self._compute_kruskal_wallis(X[col], y, min_count=min_count)
                categorical_scores[col] = res
            except Exception:
                categorical_scores[col] = {'statistic': float('nan'), 'pvalue': float('nan')}
        cat_filtered = {k: v for k, v in categorical_scores.items() if v.get('pvalue') is not None and not _np.isnan(v.get('pvalue')) and v.get('pvalue') <= float(pvalue_threshold)}
        sorted_cat = sorted(cat_filtered.items(), key=lambda kv: (kv[1]['pvalue'], -kv[1]['statistic']))
        selected_categorical = [k for k, v in sorted_cat][:int(top_k_categorical)]
        self.preselected_numeric_ = selected_numeric
        self.preselected_categorical_ = selected_categorical
        self.preselected_features_ = selected_numeric + selected_categorical
        return self.preselected_features_

        # Apprentissage des encodages catégoriels de type target-encoding (OOF smoothing)
        if y is not None and self.categorical_features:
            df = X.copy()
            df = df.reset_index(drop=True)
            y = y.reset_index(drop=True)
            global_mean = float(y.mean())
            cv = 5
            min_count = int(self.min_count)
            alpha = float(self.alpha)
            for col in enc_categorical_features:
                if col not in df.columns:
                    continue
                series = df[col].fillna('___NaN___').astype(str)
                # per-column top_k reduction (keep only top_k frequent values, others -> 'OTHER')
                col_top_k = int(self.per_col_top_k.get(col, 0)) if isinstance(self.per_col_top_k, dict) else 0
                if col_top_k and col_top_k > 0:
                    top_vals = series.value_counts().index[:col_top_k].tolist()
                    series = series.apply(lambda v: v if v in top_vals else 'OTHER')
                oof_values = pd.Series(index=df.index, dtype=float)
                # random generator for reproducible noise per column
                rnd = np.random.RandomState(42)
                kf = KFold(n_splits=cv, shuffle=True, random_state=42)
                for train_idx, val_idx in kf.split(df):
                    train_cats = series.iloc[train_idx]
                    train_y = y.iloc[train_idx]
                    grp = train_y.groupby(train_cats).mean()
                    oof_values.iloc[val_idx] = series.iloc[val_idx].map(grp)
                # fallback to global mean
                oof_values = oof_values.fillna(global_mean)

                # compute counts on full data
                counts = series.value_counts()
                mapping = {}
                rare_cats = []
                # per-column min_count override
                col_min_count = int(self.per_col_min_count.get(col, min_count)) if isinstance(self.per_col_min_count, dict) else int(min_count)
                for cat, cnt in counts.items():
                    if cnt < col_min_count:
                        rare_cats.append(str(cat))
                    else:
                        cat_mean = float(y[series == cat].mean()) if cnt > 0 else global_mean
                        smooth = (cnt * cat_mean + alpha * global_mean) / (cnt + alpha)
                        # injection de bruit éventuelle (regularisation pendant le fit)
                        if self.noise_during_fit:
                            noise = rnd.normal(loc=0.0, scale=(self.noise_std * float(y.std() if float(y.std())>0 else 1.0)))
                            smooth = float(smooth) + float(noise)
                        mapping[str(cat)] = float(smooth)

                # compute representative value for 'OTHER' (rare categories)
                other_mean = None
                if len(rare_cats) > 0:
                    mask_rare = series.isin(rare_cats)
                    try:
                        other_mean = float(y[mask_rare].mean())
                    except Exception:
                        other_mean = None
                if other_mean is None or np.isnan(other_mean):
                    other_mean = global_mean

                other_smooth = float((len(rare_cats) * other_mean + alpha * global_mean) / (len(rare_cats) + alpha)) if len(rare_cats) > 0 else float(global_mean)
                if self.noise_during_fit:
                    noise = rnd.normal(loc=0.0, scale=(self.noise_std * float(y.std() if float(y.std())>0 else 1.0)))
                    other_smooth = other_smooth + float(noise)
                mapping['OTHER'] = float(other_smooth)

                # post-processing mapping values : clipping et standardisation optionnelle
                map_vals = np.array(list(mapping.values()), dtype=float)
                # compute clip bounds from percentiles
                try:
                    low, high = np.percentile(map_vals, [100.0 * self.clip_pct[0], 100.0 * self.clip_pct[1]])
                except Exception:
                    low, high = (np.min(map_vals), np.max(map_vals))
                # clip mapping
                for k in list(mapping.keys()):
                    mapping[k] = float(np.clip(mapping[k], low, high))

                default_val = float(np.clip(global_mean, low, high))

                # standardize if requested (z-score on mapping values after clipping)
                enc_mean = float(np.mean(list(mapping.values()))) if len(mapping) > 0 else float(default_val)
                enc_std = float(np.std(list(mapping.values()))) if len(mapping) > 0 else 1.0
                if self.do_standardize and enc_std != 0:
                    for k in list(mapping.keys()):
                        mapping[k] = float((mapping[k] - enc_mean) / enc_std)
                    default_val = float((default_val - enc_mean) / enc_std)

                # store mapping and stats
                self.categ_mapping_[col] = {
                    'mapping': mapping,
                    'default': default_val,
                    'alpha': float(alpha),
                    'min_count': int(col_min_count),
                    'rare_categories': rare_cats,
                }
                self.enc_stats_[col] = {'mean': enc_mean, 'std': enc_std, 'clip_bounds': (float(low), float(high))}

        return self

    def transform(self, X:pd.DataFrame, y:pd.Series=None):
        print("[transform] Vérification et application preprocessing_map et categorical_features...")
        if hasattr(self.amount_process, 'set_preprocessing_map') and self.preprocessing_map:
            print(f"[transform] Mise à jour preprocessing_map dans amount_process : {self.preprocessing_map}")
            self.amount_process.set_preprocessing_map(self.preprocessing_map)
        if hasattr(self.amount_process, 'set_categorical_features') and self.categorical_features:
            print(f"[transform] Mise à jour categorical_features dans amount_process : {self.categorical_features}")
            self.amount_process.set_categorical_features(self.categorical_features)
        if self.booking_applied.get("transform_remove_zero_target_key", False):
            print("[transform] Suppression des zéros sur la cible...")
            X = self.amount_process.transform_remove_zero_target(X)
        if self.booking_applied.get("transform_remove_null_target_key", False):
            print("[transform] Suppression des null sur la cible...")
            X = self.amount_process.transform_remove_null_target(X)
        if self.booking_applied.get("transform_preprocessing_null_target_key", False):
            print("[transform] Application preprocessing null target...")
            X = self.amount_process._transform_preprocessing_null_target(X)
        if self.booking_applied.get("transform_process_nan_remover_key", False):
            print("[transform] Suppression des NaN selon booking...")
            X = self.amount_process._transform_preprocess_NanRemover(X, self.columns_to_remove)
        if self.preprocessing_map:
            print("[transform] Application preprocessing_map...")
            X = self.amount_process.apply_preprocessing(X)
        X = X.copy()
        if hasattr(self, 'fill_values_') and isinstance(self.fill_values_, dict):
            print(f"[transform] Imputation des valeurs manquantes : {self.fill_values_}")
            X = X.fillna(self.fill_values_)
        for col in self.categorical_features:
            if col not in X.columns:
                print(f"[transform] Colonne {col} absente, encodage ignoré.")
                continue
            info = self.categ_mapping_.get(col)
            if not info:
                print(f"[transform] Pas de mapping pour {col}, fallback label encoding.")
                X[col] = X[col].astype('category').cat.codes
                continue
            mapping = info.get('mapping', {})
            default = info.get('default', 0.0)
            min_count = info.get('min_count', 5)
            def _map_val(v):
                k = str(v) if v is not None else '___NaN___'
                if k in mapping:
                    return mapping[k]
                if 'OTHER' in mapping:
                    return mapping['OTHER']
                return default
            X[col] = X[col].fillna('___NaN___').apply(_map_val)
            print(f"[transform] Encodage appliqué sur {col}.")
        print("[transform] Fin du transform.")
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
    # Paramètres généraux pour la validation croisée, l'importance, etc.
    cv: int = 5
    val_kfold: Optional[KFold] = KFold(n_splits=5, shuffle=True, random_state=42)
    scoring: str = 'neg_mean_squared_error'
    max_features: int = None
    random_state: int = 42
    tol_improvement: float = 1e-6
    # Hyperparamètres pour l'estimateur XGBoost


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
            self.models_ = {
                "LinearRegression": LinearRegression()
            }
        elif isinstance(models, dict):
            self.models_ = models
        else:
            raise ValueError("models doit être un dictionnaire {nom: modèle}")
        # Par défaut, le premier modèle du dict est utilisé
        self.model_name_ = list(self.models_.keys())[0]
        self.model_ = self.models_[self.model_name_]


    def tune_xgboost_hyperparameters(self, X, y, param_grid=None, cv=None, scoring=None):
        """
        Calibre les hyperparamètres de XGBoost avec GridSearchCV.
        Args:
            X (pd.DataFrame): Features d'entraînement.
            y (pd.Series): Target d'entraînement.
            param_grid (dict, optional): Grille des hyperparamètres à tester.
            cv (int ou KFold, optional): Validation croisée.
            scoring (str, optional): Fonction de scoring.
        Returns:
            best_estimator, best_params
        """

        if param_grid is None:
            param_grid = {
                'n_estimators': [100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            }
        if cv is None:
            cv = self.cv
        if scoring is None:
            scoring = self.scoring
        grid_search = GridSearchCV(self.models_["XGBoost"], param_grid, cv=cv, scoring=scoring, n_jobs=-1)
        grid_search.fit(X, y)
        self.model_ = grid_search.best_estimator_
        self.best_params_ = grid_search.best_params_
        return self.model_, self.best_params_
    
    def fit(self, X: pd.DataFrame, y: pd.Series, fe_amount=None, model_name: str = None):
        """
        Entraîne le modèle sur les features présélectionnées par le feature engineer.
        """
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        X_num = X.select_dtypes(include=[np.number]).copy()
        X_num = X_num.drop(columns=['index'], errors='ignore')
        self.numeric_features_ = list(X_num.columns)
        self.fill_values_ = X_num.median(numeric_only=True).to_dict()
        X_num = X_num.fillna(self.fill_values_)
        if X_num.shape[1] == 0:
            raise ValueError("Aucune colonne numérique disponible pour entraîner le modèle Amount.")
        # Détermination du modèle à utiliser
        if model_name is not None:
            if model_name not in self.models_:
                raise ValueError(f"Le modèle '{model_name}' n'est pas dans models_ : {list(self.models_.keys())}")
            model = self.models_[model_name]
        else:
            model = self.model_
        # Utiliser la sélection du feature engineer
        if fe_amount is not None and hasattr(fe_amount, 'preselected_features_'):
            selected_features = [f for f in fe_amount.preselected_features_ if f in X_num.columns]
        else:
            selected_features = self.numeric_features_
        self.selected_features_ = selected_features.copy()
        self.selected_features_keep_ = selected_features.copy()
        self.selected_features_investigate_ = []
        self.contribution_drift_df_ = pd.DataFrame()
        self.history_ = [(self.selected_features_.copy(), None)]
        # Ajout KFold cross-validation
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=self.cv, shuffle=True, random_state=self.random_state)
        scores = []
        for train_idx, val_idx in kf.split(X_num[selected_features]):
            X_train, X_val = X_num.iloc[train_idx], X_num.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            model.fit(X_train[selected_features], y_train)
            y_pred = model.predict(X_val[selected_features])
            from sklearn.metrics import mean_squared_error
            scores.append(mean_squared_error(y_val, y_pred))
        print(f"[fit] KFold CV scores (MSE): {scores}")
        # Fit final model sur tout le jeu
        model.fit(X_num[selected_features], y)
        self.model_name_ = model_name if model_name is not None else self.model_name_
        self.model_ = model
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
        y_pred = self.predict(X, model_name=model_name, kfold=kfold)
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        # Lecture des scores KFold
        kfold_scores = getattr(self, 'kfold_scores_', None)
        result = {
            'MSE': mse,
            'RMSE': rmse
        }
        if kfold_scores is not None:
            result['KFold_MSE'] = kfold_scores
            result['KFold_MSE_mean'] = float(np.mean(kfold_scores))
            result['KFold_MSE_std'] = float(np.std(kfold_scores))
        return result
    
    def save_model(self, model_, filepath: str, metadata: Optional[Dict[str, Any]] = None):
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            artifact = {
                'model_': model_,
                'selected_features_': self.selected_features_,
                'selected_features_keep_': self.selected_features_keep_,
                'selected_features_investigate_': self.selected_features_investigate_,
                'numeric_features_': self.numeric_features_,
                'fill_values_': self.fill_values_,
                'history_': self.history_,
                'config': {
                    'cv': self.cv,
                    'scoring': self.scoring,
                    'max_features': self.max_features,
                    'random_state': self.random_state,
                    'max_iter': getattr(self, 'max_iter', None),
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
                self.history_ = loaded.get('history_', self.history_)
                config = loaded.get('config', {})
                self.cv = config.get('cv', self.cv)
                self.scoring = config.get('scoring', self.scoring)
                self.max_features = config.get('max_features', self.max_features)
                self.random_state = config.get('random_state', self.random_state)
                self.max_iter = config.get('max_iter', getattr(self, 'max_iter', None))
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
    
