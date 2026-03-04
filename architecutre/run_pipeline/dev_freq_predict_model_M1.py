#--*- coding: utf-8 -*-

# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import os
import pandas as pd
from datetime import datetime
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.base import BaseEstimator, TransformerMixin


# =============================================
#------ IMPORTATIONS DES MODULES -------------#
# =============================================
import sys
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from utils_functions import (run_step,
                             Feature_Engineer_Freq,
                             Model_Prediction_Freq,
                             Freq_Preprocessing)


# Préprocessing custom
class Preprocessing(BaseEstimator, TransformerMixin):
    def __init__(self, nan_remover=True, scaler=None):
        self.nan_remover = nan_remover
        self.scaler = scaler
    def fit(self, X, y=None):
        # ... fit custom logic ...
        return self
    def transform(self, X):
        # ... apply nan remover, scaler ...
        return X

# Feature engineering custom
class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self, custom_features=True):
        self.custom_features = custom_features
    def fit(self, X, y=None):
        # ... fit logic ...
        return self
    def transform(self, X):
        # ... feature engineering ...
        return X

# Modèle de prédiction
class ModelPrediction(BaseEstimator):
    def __init__(self, estimator):
        self.estimator = estimator
    def fit(self, X, y):
        self.estimator.fit(X, y)
        return self
    def predict(self, X):
        return self.estimator.predict(X)

# Orchestrateur
class ModelPipeline:
    def __init__(self, preprocessing, feature_engineer, model_prediction):
        self.pipeline = Pipeline([
            ('preprocessing', preprocessing),
            ('feature_engineer', feature_engineer),
            ('model', model_prediction)
        ])
    def fit(self, X, y):
        self.pipeline.fit(X, y)
    def predict(self, X):
        return self.pipeline.predict(X)
    def save(self, path):
        # ... sauvegarde du pipeline ...
        pass
    def load(self, path):
        # ... chargement du pipeline ...
        pass