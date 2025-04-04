#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèles AIOps pour la maintenance prédictive et l'optimisation continue
de l'écosystème cloud automatisé.
"""

import os
import json
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.cluster import DBSCAN
from statsmodels.tsa.arima.model import ARIMA
import joblib

# Constantes de configuration
MODEL_PATH = os.environ.get('MODEL_PATH', '/app/models')
DATA_PATH = os.environ.get('DATA_PATH', '/app/data')
CONFIG_PATH = os.environ.get('CONFIG_PATH', '/app/config')

class BaseAIOpsModel:
    """Classe de base pour tous les modèles AIOps."""
    
    def __init__(self, name, version='1.0.0'):
        """Initialise le modèle avec un nom et une version."""
        self.name = name
        self.version = version
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        # Créer les répertoires nécessaires
        os.makedirs(MODEL_PATH, exist_ok=True)
        os.makedirs(DATA_PATH, exist_ok=True)
        
        # Chemin du modèle sauvegardé
        self.model_path = f"{MODEL_PATH}/{self.name}_{self.version}.joblib"
        self.scaler_path = f"{MODEL_PATH}/{self.name}_{self.version}_scaler.joblib"
        
        # Chargement du modèle s'il existe
        self._load_if_exists()
    
    def _load_if_exists(self):
        """Charge le modèle s'il existe déjà."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                if os.path.exists(self.scaler_path):
                    self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                print(f"Modèle {self.name} chargé depuis {self.model_path}")
            except Exception as e:
                print(f"Erreur lors du chargement du modèle {self.name}: {str(e)}")
    
    def save_model(self):
        """Sauvegarde le modèle et le scaler."""
        if self.model is not None:
            joblib.dump(self.model, self.model_path)
            if self.scaler is not None:
                joblib.dump(self.scaler, self.scaler_path)
            print(f"Modèle {self.name} sauvegardé dans {self.model_path}")
    
    def preprocess_data(self, data):
        """Prétraitement des données avant entraînement ou prédiction."""
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes dérivées")
    
    def train(self, data):
        """Entraîne le modèle avec les données fournies."""
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes dérivées")
    
    def predict(self, data):
        """Effectue des prédictions avec le modèle."""
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes dérivées")
    
    def evaluate(self, data, labels=None):
        """Évalue les performances du modèle."""
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes dérivées")
    
    def get_metadata(self):
        """Retourne les métadonnées du modèle."""
        metadata = {
            "name": self.name,
            "version": self.version,
            "is_trained": self.is_trained,
            "model_type": self.__class__.__name__,
            "model_path": self.model_path,
            "features": getattr(self, 'features', []),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        return metadata
    
    def log_prediction(self, input_data, prediction, feedback=None):
        """Enregistre les prédictions pour traçabilité et amélioration continue."""
        log_entry = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "model_name": self.name,
            "model_version": self.version,
            "input_data": input_data if isinstance(input_data, dict) else {"data": str(input_data)},
            "prediction": prediction if isinstance(prediction, (dict, list, int, float, str)) else str(prediction),
            "feedback": feedback
        }
        
        log_path = f"{DATA_PATH}/{self.name}_predictions.jsonl"
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


class AnomalyDetectionModel(BaseAIOpsModel):
    """Modèle de détection d'anomalies pour la surveillance des métriques du système."""
    
    def __init__(self, features=None, contamination=0.01, version='1.0.0'):
        """
        Initialise le modèle de détection d'anomalies.
        
        Args:
            features: Liste des caractéristiques à utiliser
            contamination: Pourcentage attendu d'anomalies dans les données
            version: Version du modèle
        """
        super().__init__(name="anomaly_detection", version=version)
        self.contamination = contamination
        self.features = features or [
            'cpu_usage', 'memory_usage', 'network_in', 'network_out',
            'disk_io_read', 'disk_io_write', 'request_latency', 'error_rate'
        ]
        
        if not self.is_trained:
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
                max_samples='auto'
            )
            self.scaler = StandardScaler()
    
    def preprocess_data(self, data):
        """
        Prétraite les données pour la détection d'anomalies.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            DataFrame prétraité avec les caractéristiques normalisées
        """
        # S'assurer que toutes les caractéristiques sont présentes
        for feature in self.features:
            if feature not in data.columns:
                raise ValueError(f"La caractéristique '{feature}' est manquante dans les données")
        
        # Sélectionner uniquement les caractéristiques pertinentes
        X = data[self.features].copy()
        
        # Remplacer les valeurs manquantes
        X.fillna(X.mean(), inplace=True)
        
        # Normaliser les données
        if not self.is_trained:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def train(self, data):
        """
        Entraîne le modèle de détection d'anomalies.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            self: Le modèle entraîné
        """
        X_scaled = self.preprocess_data(data)
        
        # Entraîner le modèle
        self.model.fit(X_scaled)
        self.is_trained = True
        
        # Sauvegarder le modèle
        self.save_model()
        
        return self
    
    def predict(self, data):
        """
        Prédit si les points de données sont des anomalies.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            dict: Résultats avec les points de données et leur statut (anomalie ou normal)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez d'abord train().")
        
        X_scaled = self.preprocess_data(data)
        
        # Prédire les anomalies (-1 pour anomalie, 1 pour normal)
        predictions = self.model.predict(X_scaled)
        scores = self.model.decision_function(X_scaled)
        
        # Convertir les prédictions en état d'anomalie
        anomaly_status = [{"status": "anomaly" if p == -1 else "normal", "score": s} 
                         for p, s in zip(predictions, scores)]
        
        # Ajouter l'horodatage si disponible
        if 'timestamp' in data.columns:
            for i, ts in enumerate(data['timestamp']):
                anomaly_status[i]['timestamp'] = ts
        
        # Enregistrer les prédictions
        self.log_prediction(data.to_dict(orient='records'), anomaly_status)
        
        return {
            "anomalies_detected": (predictions == -1).sum(),
            "total_points": len(predictions),
            "anomaly_status": anomaly_status
        }
    
    def evaluate(self, data, labels=None):
        """
        Évalue les performances du modèle de détection d'anomalies.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            labels: Étiquettes réelles des anomalies (si disponibles)
            
        Returns:
            dict: Métriques de performance
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez d'abord train().")
        
        X_scaled = self.preprocess_data(data)
        predictions = self.model.predict(X_scaled)
        scores = self.model.decision_function(X_scaled)
        
        # Si des étiquettes sont fournies, calculer des métriques supervisées
        if labels is not None:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            # Convertir prédictions (-1, 1) en (1, 0) pour correspondre au format habituel des anomalies
            pred_binary = (predictions == -1).astype(int)
            
            metrics = {
                "accuracy": accuracy_score(labels, pred_binary),
                "precision": precision_score(labels, pred_binary, zero_division=0),
                "recall": recall_score(labels, pred_binary, zero_division=0),
                "f1_score": f1_score(labels, pred_binary, zero_division=0)
            }
        else:
            # Sans étiquettes, fournir des statistiques sur les prédictions
            metrics = {
                "anomalies_detected": (predictions == -1).sum(),
                "anomalies_percentage": (predictions == -1).mean() * 100,
                "normal_points": (predictions == 1).sum(),
                "avg_anomaly_score": scores[predictions == -1].mean() if (predictions == -1).any() else 0,
                "min_score": scores.min(),
                "max_score": scores.max()
            }
        
        return metrics


class ResourcePredictionModel(BaseAIOpsModel):
    """Modèle de prédiction des besoins en ressources pour l'auto-scaling."""
    
    def __init__(self, features=None, target='cpu_usage', horizon=12, version='1.0.0'):
        """
        Initialise le modèle de prédiction des ressources.
        
        Args:
            features: Liste des caractéristiques à utiliser
            target: Métrique cible à prédire
            horizon: Horizon de prédiction (en unités de temps)
            version: Version du modèle
        """
        super().__init__(name=f"resource_prediction_{target}", version=version)
        self.target = target
        self.horizon = horizon
        self.features = features or [
            'cpu_usage', 'memory_usage', 'request_rate', 'time_of_day', 
            'day_of_week', 'pods_running'
        ]
        
        if not self.is_trained:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.scaler = StandardScaler()
    
    def _add_time_features(self, data):
        """Ajoute des caractéristiques temporelles au DataFrame."""
        # Vérifier si timestamp existe et est au bon format
        if 'timestamp' in data.columns:
            if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
                data['timestamp'] = pd.to_datetime(data['timestamp'])
            
            # Ajouter des caractéristiques temporelles
            data['hour'] = data['timestamp'].dt.hour
            data['minute'] = data['timestamp'].dt.minute
            data['day_of_week'] = data['timestamp'].dt.dayofweek
            data['month'] = data['timestamp'].dt.month
            data['is_weekend'] = data['timestamp'].dt.dayofweek.isin([5, 6]).astype(int)
            
            # Caractéristique cyclique pour l'heure (pour capturer la nature cyclique du temps)
            data['time_of_day'] = data['hour'] + data['minute'] / 60.0
            data['time_sin'] = np.sin(2 * np.pi * data['time_of_day'] / 24.0)
            data['time_cos'] = np.cos(2 * np.pi * data['time_of_day'] / 24.0)
            
            # Caractéristique cyclique pour le jour de la semaine
            data['day_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7.0)
            data['day_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7.0)
        
        return data
    
    def _create_lagged_features(self, data, lags=[1, 3, 6, 12]):
        """Crée des caractéristiques décalées pour la série temporelle."""
        if self.target in data.columns:
            for lag in lags:
                data[f'{self.target}_lag_{lag}'] = data[self.target].shift(lag)
            
            # Ajouter des moyennes mobiles
            data[f'{self.target}_rolling_mean_3'] = data[self.target].rolling(window=3).mean()
            data[f'{self.target}_rolling_mean_6'] = data[self.target].rolling(window=6).mean()
            
            # Supprimer les lignes avec des valeurs NaN dues aux lags
            data = data.dropna()
        
        return data
    
    def preprocess_data(self, data):
        """
        Prétraite les données pour la prédiction des ressources.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            tuple: (X, y) - Features prétraitées et valeurs cibles
        """
        # Copier les données pour éviter de modifier l'original
        df = data.copy()
        
        # Ajouter des caractéristiques temporelles
        df = self._add_time_features(df)
        
        # Créer des caractéristiques décalées si on prédit une série temporelle
        df = self._create_lagged_features(df)
        
        # Sélectionner les caractéristiques pour l'entraînement
        available_features = [f for f in self.features if f in df.columns]
        
        # Ajouter les caractéristiques décalées générées
        lag_features = [col for col in df.columns if col.startswith(f'{self.target}_lag_') or 
                        col.startswith(f'{self.target}_rolling_')]
        available_features.extend(lag_features)
        
        # Ajouter les caractéristiques cycliques
        if 'time_sin' in df.columns:
            available_features.extend(['time_sin', 'time_cos', 'day_sin', 'day_cos'])
        
        # Vérifier qu'il y a des caractéristiques disponibles
        if not available_features:
            raise ValueError("Aucune caractéristique disponible après prétraitement")
        
        # Sélectionner X et y
        X = df[available_features]
        y = df[self.target] if self.target in df.columns else None
        
        # Normaliser les données
        if self.scaler is not None:
            if not self.is_trained:
                X_scaled = self.scaler.fit_transform(X)
            else:
                X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        return (X_scaled, y)
    
    def train(self, data):
        """
        Entraîne le modèle de prédiction des ressources.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            self: Le modèle entraîné
        """
        X_scaled, y = self.preprocess_data(data)
        
        if y is None:
            raise ValueError(f"La cible '{self.target}' n'est pas présente dans les données")
        
        # Entraîner le modèle
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Sauvegarder le modèle
        self.save_model()
        
        return self
    
    def predict(self, data):
        """
        Prédit les besoins futurs en ressources.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            dict: Prédictions des besoins en ressources
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez d'abord train().")
        
        X_scaled, _ = self.preprocess_data(data)
        
        # Prédire les valeurs
        predictions = self.model.predict(X_scaled)
        
        # Préparer le résultat
        result = {
            "target": self.target,
            "predictions": predictions.tolist(),
            "mean_prediction": np.mean(predictions),
            "min_prediction": np.min(predictions),
            "max_prediction": np.max(predictions),
        }
        
        # Ajouter l'horodatage si disponible
        if 'timestamp' in data.columns:
            result["timestamps"] = data['timestamp'].tolist()
        
        # Estimer les besoins en ressources
        if self.target == 'cpu_usage':
            # Exemple simple: ajouter 20% de marge aux prédictions maximales
            result["recommended_cpu_limit"] = np.max(predictions) * 1.2
        elif self.target == 'memory_usage':
            result["recommended_memory_limit"] = np.max(predictions) * 1.2
        
        # Enregistrer les prédictions
        self.log_prediction(data.to_dict(orient='records'), result)
        
        return result
    
    def evaluate(self, data, labels=None):
        """
        Évalue les performances du modèle de prédiction.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            labels: Non utilisé, inclus pour compatibilité avec l'interface
            
        Returns:
            dict: Métriques de performance
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez d'abord train().")
        
        X_scaled, y = self.preprocess_data(data)
        
        if y is None:
            raise ValueError(f"La cible '{self.target}' n'est pas présente dans les données")
        
        # Faire des prédictions
        y_pred = self.model.predict(X_scaled)
        
        # Calculer les métriques
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        metrics = {
            "mean_absolute_error": mean_absolute_error(y, y_pred),
            "mean_squared_error": mean_squared_error(y, y_pred),
            "root_mean_squared_error": np.sqrt(mean_squared_error(y, y_pred)),
            "r2_score": r2_score(y, y_pred),
            "mean_prediction": np.mean(y_pred),
            "true_mean": np.mean(y),
            "max_prediction": np.max(y_pred),
            "true_max": np.max(y)
        }
        
        return metrics


class ClusteringModel(BaseAIOpsModel):
    """Modèle de clustering pour regrouper des comportements similaires."""
    
    def __init__(self, features=None, eps=0.5, min_samples=5, version='1.0.0'):
        """
        Initialise le modèle de clustering.
        
        Args:
            features: Liste des caractéristiques à utiliser
            eps: Distance maximale entre deux points pour être considérés comme voisins
            min_samples: Nombre minimum de points pour former un cluster dense
            version: Version du modèle
        """
        super().__init__(name="workload_clustering", version=version)
        self.eps = eps
        self.min_samples = min_samples
        self.features = features or [
            'cpu_usage', 'memory_usage', 'request_rate', 'request_latency',
            'error_rate', 'time_of_day', 'day_of_week'
        ]
        
        if not self.is_trained:
            self.model = DBSCAN(
                eps=self.eps,
                min_samples=self.min_samples,
                metric='euclidean',
                n_jobs=-1
            )
            self.scaler = StandardScaler()
    
    def preprocess_data(self, data):
        """
        Prétraite les données pour le clustering.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            DataFrame prétraité avec les caractéristiques normalisées
        """
        # Ajouter des caractéristiques temporelles si timestamp est présent
        if 'timestamp' in data.columns:
            if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
                data['timestamp'] = pd.to_datetime(data['timestamp'])
            
            data['hour'] = data['timestamp'].dt.hour
            data['day_of_week'] = data['timestamp'].dt.dayofweek
            data['time_of_day'] = data['hour'] / 24.0
        
        # Sélectionner les caractéristiques disponibles
        available_features = [f for f in self.features if f in data.columns]
        
        if not available_features:
            raise ValueError("Aucune caractéristique disponible pour le clustering")
        
        X = data[available_features].copy()
        
        # Remplacer les valeurs manquantes
        X.fillna(X.mean(), inplace=True)
        
        # Normaliser les données
        if not self.is_trained:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def train(self, data):
        """
        Entraîne le modèle de clustering.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            self: Le modèle entraîné
        """
        X_scaled = self.preprocess_data(data)
        
        # Entraîner le modèle
        self.model.fit(X_scaled)
        self.is_trained = True
        
        # Analyser les résultats du clustering
        labels = self.model.labels_
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        print(f"Nombre de clusters trouvés: {n_clusters}")
        print(f"Nombre de points de bruit: {n_noise}")
        
        # Sauvegarder le modèle
        self.save_model()
        
        return self
    
    def predict(self, data):
        """
        Assigne des clusters aux nouvelles données.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            dict: Résultats du clustering
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez d'abord train().")
        
        X_scaled = self.preprocess_data(data)
        
        # Prédire les clusters
        cluster_labels = self.model.fit_predict(X_scaled)
        
        # Préparer le résultat
        clusters = {}
        for i, label in enumerate(cluster_labels):
            label_str = str(label)
            if label_str not in clusters:
                clusters[label_str] = []
            
            # Ajouter l'index ou l'horodatage si disponible
            if 'timestamp' in data.columns:
                timestamp = data['timestamp'].iloc[i]
                clusters[label_str].append({"index": i, "timestamp": timestamp})
            else:
                clusters[label_str].append({"index": i})
        
        result = {
            "n_clusters": len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0),
            "n_noise": list(cluster_labels).count(-1),
            "cluster_sizes": {label: len(items) for label, items in clusters.items()},
            "clusters": clusters
        }
        
        # Enregistrer les prédictions
        self.log_prediction(data.to_dict(orient='records'), result)
        
        return result
    
    def evaluate(self, data, labels=None):
        """
        Évalue la qualité du clustering.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            labels: Étiquettes réelles des clusters (si disponibles)
            
        Returns:
            dict: Métriques de qualité du clustering
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez d'abord train().")
        
        X_scaled = self.preprocess_data(data)
        
        # Prédire les clusters
        cluster_labels = self.model.fit_predict(X_scaled)
        
        # Calculer des métriques internes (sans besoin d'étiquettes réelles)
        from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
        
        metrics = {}
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        
        if n_clusters > 1:
            # Filtrer les points de bruit pour calculer les scores
            non_noise_mask = cluster_labels != -1
            if non_noise_mask.sum() > 1:
                metrics["silhouette_score"] = silhouette_score(
                    X_scaled[non_noise_mask], cluster_labels[non_noise_mask]
                )
                metrics["calinski_harabasz_score"] = calinski_harabasz_score(
                    X_scaled[non_noise_mask], cluster_labels[non_noise_mask]
                )
                metrics["davies_bouldin_score"] = davies_bouldin_score(
                    X_scaled[non_noise_mask], cluster_labels[non_noise_mask]
                )
        
        # Ajouter des statistiques sur les clusters
        cluster_counts = np.bincount(cluster_labels[cluster_labels != -1] 
                                     if -1 in cluster_labels else cluster_labels)
        
        metrics.update({
            "n_clusters": n_clusters,
            "n_noise_points": list(cluster_labels).count(-1),
            "noise_percentage": list(cluster_labels).count(-1) / len(cluster_labels) * 100,
            "avg_cluster_size": np.mean(cluster_counts) if len(cluster_counts) > 0 else 0,
            "min_cluster_size": np.min(cluster_counts) if len(cluster_counts) > 0 else 0,
            "max_cluster_size": np.max(cluster_counts) if len(cluster_counts) > 0 else 0
        })
        
        # Si des étiquettes sont fournies, calculer des métriques externes
        if labels is not None:
            from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score
            
            metrics.update({
                "adjusted_rand_score": adjusted_rand_score(labels, cluster_labels),
                "adjusted_mutual_info_score": adjusted_mutual_info_score(labels, cluster_labels)
            })
        
        return metrics


class DeepLearningAnomalyModel(BaseAIOpsModel):
    """Modèle d'anomalie basé sur les réseaux de neurones pour les séquences temporelles."""
    
    def __init__(self, features=None, sequence_length=10, hidden_size=64, version='1.0.0'):
        """
        Initialise le modèle d'anomalie basé sur l'autoencoder.
        
        Args:
            features: Liste des caractéristiques à utiliser
            sequence_length: Longueur de la séquence temporelle
            hidden_size: Taille de la couche cachée de l'autoencoder
            version: Version du modèle
        """
        super().__init__(name="deep_anomaly_detection", version=version)
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.features = features or [
            'cpu_usage', 'memory_usage', 'network_in', 'network_out',
            'disk_io_read', 'disk_io_write', 'request_latency', 'error_rate'
        ]
        self.threshold = None  # Seuil d'anomalie, déterminé après entraînement
        
        if not self.is_trained:
            self.scaler = StandardScaler()
            self._build_model()
    
    def _build_model(self):
        """Construit le modèle d'autoencoder."""
        # Nombre de caractéristiques
        n_features = len(self.features)
        
        # Définir le modèle
        inputs = keras.Input(shape=(self.sequence_length, n_features))
        
        # Encodeur LSTM
        encoded = keras.layers.LSTM(self.hidden_size, return_sequences=False)(inputs)
        encoded = keras.layers.Dropout(0.2)(encoded)
        
        # Décodeur LSTM
        decoded = keras.layers.RepeatVector(self.sequence_length)(encoded)
        decoded = keras.layers.LSTM(self.hidden_size, return_sequences=True)(decoded)
        decoded = keras.layers.TimeDistributed(keras.layers.Dense(n_features))(decoded)
        
        # Créer le modèle autoencoder
        autoencoder = keras.Model(inputs, decoded)
        autoencoder.compile(optimizer='adam', loss='mse')
        
        self.model = autoencoder
    
    def _create_sequences(self, data):
        """
        Crée des séquences temporelles à partir des données.
        
        Args:
            data: DataFrame pandas avec les métriques
            
        Returns:
            numpy.ndarray: Séquences pour l'entraînement
        """
        X = []
        
        for i in range(len(data) - self.sequence_length + 1):
            X.append(data[i:(i + self.sequence_length)])
        
        return np.array(X)
    
    def preprocess_data(self, data):
        """
        Prétraite les données pour la détection d'anomalies.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            numpy.ndarray: Données prétraitées sous forme de séquences
        """
        # S'assurer que toutes les caractéristiques sont présentes
        available_features = [f for f in self.features if f in data.columns]
        
        if not available_features:
            raise ValueError("Aucune caractéristique disponible pour le modèle")
        
        # Mettre à jour la liste des caractéristiques disponibles
        self.features = available_features
        
        # Sélectionner uniquement les caractéristiques pertinentes
        X = data[self.features].copy()
        
        # Remplacer les valeurs manquantes
        X.fillna(X.mean(), inplace=True)
        
        # Normaliser les données
        if not self.is_trained:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        # Créer des séquences
        X_sequences = self._create_sequences(X_scaled)
        
        return X_sequences
    
    def train(self, data, epochs=50, batch_size=32, validation_split=0.2):
        """
        Entraîne le modèle d'autoencoder pour la détection d'anomalies.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            epochs: Nombre d'époques d'entraînement
            batch_size: Taille du batch
            validation_split: Proportion des données à utiliser pour la validation
            
        Returns:
            self: Le modèle entraîné
        """
        X_sequences = self.preprocess_data(data)
        
        # Vérifier s'il y a suffisamment de données
        if len(X_sequences) < 10:
            raise ValueError("Pas assez de données pour l'entraînement (moins de 10 séquences)")
        
        # Entraîner le modèle
        history = self.model.fit(
            X_sequences, X_sequences,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            shuffle=True,
            verbose=1
        )
        
        # Calculer les erreurs de reconstruction pour toutes les séquences
        reconstructions = self.model.predict(X_sequences)
        
        # Pour chaque séquence, calculer l'erreur MSE
        mse = np.mean(np.square(X_sequences - reconstructions), axis=(1, 2))
        
        # Définir le seuil comme la moyenne + 3 écarts-types des erreurs MSE
        self.threshold = np.mean(mse) + 3 * np.std(mse)
        print(f"Seuil d'anomalie défini à: {self.threshold}")
        
        self.is_trained = True
        
        # Sauvegarder le modèle (keras ne fonctionne pas bien avec joblib)
        self.model.save(f"{MODEL_PATH}/{self.name}_{self.version}.h5")
        
        # Sauvegarder les autres composants avec joblib
        joblib_data = {
            "scaler": self.scaler,
            "threshold": self.threshold,
            "features": self.features,
            "sequence_length": self.sequence_length
        }
        joblib.dump(joblib_data, f"{MODEL_PATH}/{self.name}_{self.version}_components.joblib")
        
        return self
    
    def _load_if_exists(self):
        """Surcharge pour charger le modèle Keras."""
        model_h5_path = f"{MODEL_PATH}/{self.name}_{self.version}.h5"
        components_path = f"{MODEL_PATH}/{self.name}_{self.version}_components.joblib"
        
        if os.path.exists(model_h5_path) and os.path.exists(components_path):
            try:
                # Charger le modèle Keras
                self.model = keras.models.load_model(model_h5_path)
                
                # Charger les autres composants
                components = joblib.load(components_path)
                self.scaler = components["scaler"]
                self.threshold = components["threshold"]
                self.features = components["features"]
                self.sequence_length = components["sequence_length"]
                
                self.is_trained = True
                print(f"Modèle {self.name} chargé depuis {model_h5_path}")
            except Exception as e:
                print(f"Erreur lors du chargement du modèle {self.name}: {str(e)}")
    
    def predict(self, data):
        """
        Détecte les anomalies dans les données.
        
        Args:
            data: DataFrame pandas avec les métriques du système
            
        Returns:
            dict: Résultats avec les points de données et leur statut (anomalie ou normal)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez d'abord train().")
        
        if len(data) < self.sequence_length:
            raise ValueError(f"Le DataFrame doit contenir au moins {self.sequence_length} lignes")
        
        X_sequences = self.preprocess_data(data)
        
        # Prédire les reconstructions
        reconstructions = self.model.predict(X_sequences)
        
        # Calculer l'erreur MSE pour chaque séquence
        mse = np.mean(np.square(X_sequences - reconstructions), axis=(1, 2))
        
        # Déterminer les anomalies
        anomalies = mse > self.threshold
        
        # Convertir les résultats en données lisibles
        anomaly_results = []
        
        for i, (is_anomaly, error) in enumerate(zip(anomalies, mse)):
            result = {
                "sequence_idx": i,
                "start_idx": i,
                "end_idx": i + self.sequence_length - 1,
                "status": "anomaly" if is_anomaly else "normal",
                "reconstruction_error": float(error),
                "threshold": float(self.threshold)
            }
            
            # Ajouter l'horodatage si disponible
            if 'timestamp' in data.columns:
                result["start_time"] = data['timestamp'].iloc[i]
                result["end_time"] = data['timestamp'].iloc[i + self.sequence_length - 1]
            
            anomaly_results.append(result)
        
        # Résultat global
        result = {
            "anomalies_detected": int(np.sum(anomalies)),
            "total_sequences": len(anomalies),
            "anomaly_percentage": float(np.mean(anomalies) * 100),
            "avg_reconstruction_error": float(np.mean(mse)),
            "max_reconstruction_error": float(np.max(mse)),
            "threshold": float(self.threshold),
            "anomaly_status": anomaly_results
        }
        
        # Enregistrer les prédictions
        self.log_prediction(data.to_dict(orient='records'), result)
        
        return result


# D'autres classes AIOps peuvent être ajoutées ici
