import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from .models import SearchResult, SearchResponse, ProcessedDocument
from .utils import SearchError, setup_logger

logger = setup_logger(__name__)

class SearchEngine:
    
    def __init__(self, max_features=5000):
        self.max_features = max_features
        self.vectorizer = None
        self.current_document = None
        logger.info("Search Engine başlatıldı")
    
    def index_document(self, document: ProcessedDocument):
        
        try:
            logger.info(f"Döküman indeksleniyor: {document.filename}")
            
            if not document.chunks:
                raise SearchError("Döküman chunk'ı yok")
            
            
            chunk_texts = [chunk.text for chunk in document.chunks]
            
            
            self.vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
                lowercase=True
            )
            
            
            tfidf_matrix = self.vectorizer.fit_transform(chunk_texts)
            
            
            document.vectorizer = self.vectorizer
            document.tfidf_matrix = tfidf_matrix
            self.current_document = document
            
            logger.info(f"Döküman başarıyla indekslendi: {len(chunk_texts)} chunk")
            return True
            
        except Exception as e:
            error_msg = f"İndeksleme hatası: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)
    
    def search(self, query: str, max_results: int = 5, min_similarity: float = 0.01) -> SearchResponse:

        start_time = time.time()
        
        try:
            if not self.current_document or not self.vectorizer:
                raise SearchError("Önce döküman indekslenmeli")
            
            logger.info(f"Arama yapılıyor: '{query}'")
            
            
            query_vector = self.vectorizer.transform([query])
            
            
            similarities = cosine_similarity(query_vector, self.current_document.tfidf_matrix).flatten()
            
            
            top_indices = similarities.argsort()[-max_results:][::-1]
            
            
            results = []
            for idx in top_indices:
                similarity_score = similarities[idx]
                
                if similarity_score >= min_similarity:
                    chunk = self.current_document.chunks[idx]
                    result = SearchResult(
                        chunk_id=chunk.id,
                        chunk_text=chunk.text,
                        similarity_score=similarity_score
                    )
                    results.append(result)
            
            
            search_time = time.time() - start_time
            response = SearchResponse(
                query=query,
                results=results,
                search_time=search_time
            )
            
            logger.info(f"Arama tamamlandı: {len(results)} sonuç bulundu, {search_time:.3f}s")
            return response
            
        except Exception as e:
            error_msg = f"Arama hatası: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)
    
    def get_similar_chunks(self, chunk_id: int, max_results: int = 3) -> list:
        try:
            if not self.current_document or chunk_id >= len(self.current_document.chunks):
                return []
            
            
            reference_vector = self.current_document.tfidf_matrix[chunk_id:chunk_id+1]
            
            
            similarities = cosine_similarity(reference_vector, self.current_document.tfidf_matrix).flatten()
            
           
            similarities[chunk_id] = -1  
            top_indices = similarities.argsort()[-max_results:][::-1]
            
            similar_chunks = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    chunk = self.current_document.chunks[idx]
                    similar_chunks.append({
                        'chunk_id': chunk.id,
                        'text': chunk.text,
                        'similarity': similarities[idx]
                    })
            
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Benzer chunk bulma hatası: {e}")
            return []
    
    def get_search_statistics(self) -> dict:
        """Arama istatistiklerini döndürür"""
        if not self.current_document:
            return {}
        
        return {
            'indexed_document': self.current_document.filename,
            'total_chunks': len(self.current_document.chunks),
            'total_words': self.current_document.get_total_words(),
            'vectorizer_features': len(self.vectorizer.get_feature_names_out()) if self.vectorizer else 0,
            'indexed_at': self.current_document.processed_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_top_terms(self, n: int = 10) -> list:
        try:
            if not self.vectorizer or not self.current_document:
                return []
            
            
            feature_names = self.vectorizer.get_feature_names_out()
            
            
            mean_scores = np.mean(self.current_document.tfidf_matrix.toarray(), axis=0)
            
            
            top_indices = mean_scores.argsort()[-n:][::-1]
            
            top_terms = []
            for idx in top_indices:
                top_terms.append({
                    'term': feature_names[idx],
                    'score': round(mean_scores[idx], 4)
                })
            
            return top_terms
            
        except Exception as e:
            logger.error(f"Top terimler alınamadı: {e}")
            return []
