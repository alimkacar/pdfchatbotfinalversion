import PyPDF2
from pathlib import Path
from datetime import datetime
import pickle

from .models import DocumentChunk, ProcessedDocument
from .utils import TextCleaner, PDFProcessingError, setup_logger

logger = setup_logger(__name__)

class PDFProcessor:
    
    
    def __init__(self, chunk_size=500, overlap=100):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.text_cleaner = TextCleaner()
        logger.info("PDF Processor başlatıldı")
    
    def process_pdf(self, pdf_path, filename):
        """
        Args:
            pdf_path: PDF dosya yolu
            filename: Dosya adı
            
        Returns:
            Tuple[ProcessedDocument, error_message]
        """
        try:
            logger.info(f"PDF işleniyor: {filename}")
            
            
            raw_text, page_count = self._extract_text_from_pdf(pdf_path)
            if not raw_text:
                return None, "PDF'den metin çıkarılamadı"
            
            
            clean_text = self.text_cleaner.clean_pdf_text(raw_text)
            
            
            text_chunks = self.text_cleaner.create_chunks(clean_text, self.chunk_size, self.overlap)
            if not text_chunks:
                return None, "Metin chunk'lara bölünemedi"
            
            
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunk = DocumentChunk(
                    id=i,
                    text=chunk_text,
                    page_number=self._extract_page_number(chunk_text)
                )
                chunks.append(chunk)
            
            
            processed_doc = ProcessedDocument(
                filename=filename,
                chunks=chunks,
                total_pages=page_count,
                processed_at=datetime.now()
            )
            
            logger.info(f"PDF başarıyla işlendi: {filename}, {len(chunks)} chunk oluşturuldu")
            return processed_doc, None
            
        except Exception as e:
            error_msg = f"PDF işleme hatası: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def _extract_text_from_pdf(self, pdf_path):
        text = ""
        page_count = 0
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text += f"\n--- Sayfa {page_num} ---\n"
                            text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Sayfa {page_num} okunamadı: {e}")
                        continue
                        
        except Exception as e:
            raise PDFProcessingError(f"PDF okuma hatası: {str(e)}")
        
        return text, page_count
    
    def _extract_page_number(self, text):
        import re
        match = re.search(r'--- Sayfa (\d+) ---', text)
        return int(match.group(1)) if match else None
    
    def save_processed_document(self, doc, filepath):
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(doc, f)
            return True
        except Exception as e:
            logger.error(f"Döküman kaydedilemedi: {e}")
            return False
    
    def load_processed_document(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Döküman yüklenemedi: {e}")
            return None
    
    def validate_pdf(self, pdf_path):
        
        try:
            if not Path(pdf_path).exists():
                return False, "Dosya bulunamadı"
            
            if Path(pdf_path).stat().st_size == 0:
                return False, "Dosya boş"
            
            
            with open(pdf_path, 'rb') as file:
                header = file.read(8)
                if not header.startswith(b'%PDF-'):
                    return False, "Geçersiz PDF formatı"
            
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if len(pdf_reader.pages) == 0:
                    return False, "PDF sayfa içermiyor"
            
            return True, None
            
        except Exception as e:
            return False, f"PDF validasyon hatası: {str(e)}"
    
    def get_pdf_info(self, pdf_path):
        """PDF hakkında bilgi döndürür"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                return {
                    'page_count': len(pdf_reader.pages),
                    'file_size': Path(pdf_path).stat().st_size,
                    'file_name': Path(pdf_path).name
                }
        except Exception as e:
            logger.error(f"PDF bilgisi alınamadı: {e}")
            return None
