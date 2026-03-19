from sentence_transformers import SentenceTransformer

print("⏳ กำลังโหลด Embedding Model (โหลดครั้งเดียวในระบบ)...")
embed_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print("✅ โหลด Embedding Model พร้อมใช้งานแล้ว!")