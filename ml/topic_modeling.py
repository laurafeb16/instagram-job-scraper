# -*- coding: utf-8 -*-
"""
Módulo para modelado de temas en ofertas de trabajo.
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

class TopicModeler:
    """Clase para modelado de temas en ofertas de trabajo."""
    
    def __init__(self, n_topics=5):
        """Inicializa el modelador de temas.
        
        Args:
            n_topics (int): Número de temas a identificar
        """
        self.n_topics = n_topics
        self.vectorizer = CountVectorizer(max_df=0.95, min_df=2)
        self.lda = LatentDirichletAllocation(
            n_components=n_topics, 
            random_state=42,
            learning_method='online'
        )
        
    def preprocess_text(self, texts):
        """Preprocesa los textos para análisis.
        
        Args:
            texts (list): Lista de textos a preprocesar
            
        Returns:
            list: Textos preprocesados
        """
        # Implementación básica a completar
        return texts
        
    def fit(self, texts):
        """Entrena el modelo con los textos proporcionados.
        
        Args:
            texts (list): Lista de textos para entrenamiento
        """
        # Preprocesar textos
        processed_texts = self.preprocess_text(texts)
        
        # Vectorizar
        self.dtm = self.vectorizer.fit_transform(processed_texts)
        
        # Entrenar LDA
        self.lda.fit(self.dtm)
        
    def get_topics(self, n_terms=10):
        """Obtiene los términos más relevantes para cada tema.
        
        Args:
            n_terms (int): Número de términos a mostrar por tema
            
        Returns:
            list: Lista de temas con sus términos más relevantes
        """
        features = self.vectorizer.get_feature_names_out()
        topics = []
        
        for topic_idx, topic in enumerate(self.lda.components_):
            top_features_idx = topic.argsort()[:-n_terms - 1:-1]
            top_features = [features[i] for i in top_features_idx]
            topics.append(top_features)
            
        return topics
