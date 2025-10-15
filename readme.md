# PDF Chat App (Minimal RAG)

Bu uygulama; tek bir PDF belgesindeki metni parçalara ayırır, arka planda vektör uzayına (TF-IDF) dönüştürür ve **doğal dilde** yazdığın sorguya göre **en alakalı paragraf(ları)** bulup döndürür. Özetleme veya dış kaynak yok; yalnızca PDF içeriği + senin sorgun.

> Not: Bu sürüm **OpenAI/LLM gerektirmez**. Embedding yerine **TF-IDF + cosine similarity** kullanır, tamamen yereldir.



## Nasıl Çalışıyor?
--------------------------

Uygulama şu adımları izler:

1. **PDF Loading**  
   Yüklenen PDF dosyası okunur, metin çıkarımı yapılır ve temel temizlik uygulanır (sayfa etiketleri gibi izler temizlenir).

2. **Text Chunking**  
   Metin cümle bazlı toplanır ve **sabit uzunluk + örtüşme** (ör. 500 karakter, 100 karakter overlap) stratejisiyle parçalara (chunk) bölünür.

3. **Vectorization (TF-IDF)**  
   Her paragraf 1–2 n-gram TF-IDF vektörlerine dönüştürülür.

4. **Similarity Matching**  
   Sorgu metni de aynı uzaya aktarılır; **cosine similarity** ile tüm paragraflar skorlanır.

5. **Response**  
   En yüksek skorlu paragraf(lar) sonuç olarak döndürülür (varsayılan Top-1, istersen Top-N).

---

## Bağımlılıklar ve Kurulum
----------------------------

> Python **3.10+** önerilir.

```bash
git clone https://github.com/alimkacar/pdfchatbotfinalversion.git
cd pdfchatbotfinalversion

#Sanal ortam
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Bağımlılıklar
pip install -r requirements.txt

---
```
## Proje Yapısı
--------------------------
```bash
pdfchatbotfinalversion/
├─ app.py              # Flask + tek sayfalık HTML arayüz
├─ config.py           # Uygulama ayarları
├─ models.py           # DocumentChunk, ProcessedDocument, SearchResult, ...
├─ pdf_processor.py    # PDF okuma, temizlik, chunk'lama, pickle I/O
├─ search_engine.py    # TF-IDF (1–2 n-gram) + cosine similarity
├─ utils.py            # Doğrulama, temizleme, logging, özel hatalar
└─ data/
   ├─ uploads/         # Yüklenen PDF'ler (geçici)
   └─ processed/       # İşlenmiş doküman çıktıları (.pkl)
```
---
