from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class DocumentChunk:
    
    id: int
    text: str
    page_number: Optional[int] = None
    word_count: int = 0
    
    def __post_init__(self):
        if not self.word_count:
            self.word_count = len(self.text.split())

@dataclass
class ProcessedDocument:
    
    filename: str
    chunks: List[DocumentChunk] = field(default_factory=list)
    total_pages: int = 0
    processed_at: datetime = field(default_factory=datetime.now)
    
    
    vectorizer: Any = None
    tfidf_matrix: Any = None
    
    def get_chunk_count(self):
        return len(self.chunks)
    
    def get_total_words(self):
        return sum(chunk.word_count for chunk in self.chunks)
    
    def to_dict(self):
        return {
            'filename': self.filename,
            'chunk_count': self.get_chunk_count(),
            'total_words': self.get_total_words(),
            'total_pages': self.total_pages,
            'processed_at': self.processed_at.strftime('%Y-%m-%d %H:%M:%S')
        }

@dataclass
class SearchResult:
    chunk_id: int
    chunk_text: str
    similarity_score: float
    rank: int = 0
    
    def get_preview(self, max_length=150):
        if len(self.chunk_text) <= max_length:
            return self.chunk_text
        return self.chunk_text[:max_length].rsplit(' ', 1)[0] + "..."
    
    def get_confidence_level(self):
        """Güven seviyesi"""
        if self.similarity_score >= 0.7:
            return "Yüksek"
        elif self.similarity_score >= 0.4:
            return "Orta"
        else:
            return "Düşük"
    
    def to_dict(self):
        return {
            'rank': self.rank,
            'chunk_id': self.chunk_id,
            'similarity_score': round(self.similarity_score, 3),
            'text': self.chunk_text,
            'preview': self.get_preview(),
            'confidence': self.get_confidence_level()
        }

@dataclass
class SearchResponse:
    query: str
    results: List[SearchResult] = field(default_factory=list)
    total_found: int = 0
    search_time: float = 0.0
    
    def __post_init__(self):
        self.total_found = len(self.results)
        
        for i, result in enumerate(self.results, 1):
            result.rank = i
    
    def has_results(self):
        return len(self.results) > 0
    
    def get_top_results(self, n=3):
        return self.results[:n]
    
    def to_dict(self):
        return {
            'query': self.query,
            'total_found': self.total_found,
            'search_time': round(self.search_time, 3),
            'results': [result.to_dict() for result in self.results]
        }
