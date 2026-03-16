import os
import sys
import unittest

import pandas as pd


CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from fonctions_utiles import (
    Frequence_Feature_Engineer,
    Frequence_Preprocessing,
    Severite_Feature_Engineer,
    Severite_Preprocessing,
)


TRAIN_FIXTURE_PATH = os.path.join(CURRENT_DIR, "input", "train_unit.csv")
TEST_FIXTURE_PATH = os.path.join(CURRENT_DIR, "input", "test_unit.csv")


class TestDevBuildModelsFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train_df = pd.read_csv(TRAIN_FIXTURE_PATH)
        cls.test_df = pd.read_csv(TEST_FIXTURE_PATH)

    def test_frequency_preprocessing_filters_expected_rows(self):
        preprocessing = Frequence_Preprocessing(target_col="nombre_sinistres")

        prepared = preprocessing._transform_remove_id_columns("frequence_train", self.train_df)
        filtered = preprocessing._transform_remove_null_second_target(prepared)

        self.assertNotIn("index", prepared.columns)
        self.assertNotIn("id_client", prepared.columns)
        self.assertEqual(filtered["montant_sinistre"].isna().sum(), 0)
        self.assertEqual(len(filtered), 4)

    def test_frequency_feature_engineer_keeps_numeric_schema(self):
        preprocessing = Frequence_Preprocessing(target_col="nombre_sinistres")

        train_prepared = preprocessing._transform_remove_id_columns("frequence_train", self.train_df)
        train_prepared = preprocessing._transform_remove_null_second_target(train_prepared)
        test_prepared = preprocessing._transform_remove_id_columns("frequence_test", self.test_df)

        X_train = train_prepared.drop(columns=["nombre_sinistres"])
        y_train = train_prepared["nombre_sinistres"]

        feature_engineer = Frequence_Feature_Engineer(
            frequence_process=preprocessing
        ).build_feature_engineer(
            fit_process_nan_remover=True,
            transform_process_nan_remover=True,
            transform_remove_id_columns=False,
            threshold=0.9,
            preprocessing_map={},
            select_numeric_features_only=True,
            excluded_feature_columns=[],
        )

        transformed_train = feature_engineer.fit_transform(X_train, y_train)
        transformed_test = feature_engineer.transform(test_prepared)

        self.assertTrue(all(pd.api.types.is_numeric_dtype(dtype) for dtype in transformed_train.dtypes))
        self.assertListEqual(list(transformed_train.columns), list(transformed_test.columns))
        self.assertIn("montant_sinistre", transformed_train.columns)

    def test_severity_preprocessing_filters_zero_targets(self):
        preprocessing = Severite_Preprocessing(target_col="montant_sinistre")

        prepared = preprocessing._transform_remove_id_columns("severite_train", self.train_df)
        filtered = preprocessing._transform_remove_null_target(prepared)

        self.assertNotIn("id_contrat", prepared.columns)
        self.assertFalse((filtered["montant_sinistre"] == 0).any())
        self.assertEqual(len(filtered), 4)

    def test_severity_feature_engineer_excludes_frequency_target(self):
        preprocessing = Severite_Preprocessing(target_col="montant_sinistre")

        train_prepared = preprocessing._transform_remove_id_columns("severite_train", self.train_df)
        train_prepared = preprocessing._transform_remove_null_target(train_prepared)
        test_prepared = preprocessing._transform_remove_id_columns("severite_test", self.test_df)

        X_train = train_prepared.drop(columns=["montant_sinistre"])
        y_train = train_prepared["montant_sinistre"]

        feature_engineer = Severite_Feature_Engineer(
            severite_process=preprocessing
        ).build_feature_engineer(
            fit_process_nan_remover=True,
            transform_process_nan_remover=True,
            transform_remove_id_columns=False,
            transform_remove_zero_target=False,
            transform_preprocessing_null_target=False,
            threshold=0.9,
            preprocessing_map={},
            select_numeric_features_only=True,
            excluded_feature_columns=["nombre_sinistres"],
        )

        transformed_train = feature_engineer.fit_transform(X_train, y_train)
        transformed_test = feature_engineer.transform(test_prepared)

        self.assertNotIn("nombre_sinistres", transformed_train.columns)
        self.assertTrue(all(pd.api.types.is_numeric_dtype(dtype) for dtype in transformed_train.dtypes))
        self.assertListEqual(list(transformed_train.columns), list(transformed_test.columns))


if __name__ == "__main__":
    unittest.main()