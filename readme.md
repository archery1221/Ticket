# TicketBot

Discord sunucunuz için SSS ve destek sistemi sunan otomatik bot.

---

## 📌 Özellikler

1. **SSS (Sıkça Sorulan Sorular)**
   - Kullanıcıların sıkça sorduğu sorulara otomatik cevap verir.
   - Bot cevabı bulamazsa mesaj veritabanına kaydedilir.

2. **Ticket Sistemi**
   - Kullanıcılar `!menü` komutuyla destek talepleri oluşturabilir.
   - Ticket kanalları otomatik oluşturulur ve kapatma butonu ile kapatılabilir.
   - Yetkililer, ticket kanallarını görebilir ve yönetebilir.

3. **Veritabanı**
   - `tickets.db` dosyası ile tüm ticketler saklanır.
   - `unanswered` tablosu botun cevaplayamadığı mesajları tutar.
   - Sqlite3 kullanılır; ekstra bir kurulum gerekmez.

4. **Kullanıcı Arayüzü**
   - Butonlar ve dropdown menüler ile kullanıcı dostu bir arayüz sunar.
   - Ticket başlatma ve kapatma işlemleri kolayca yapılabilir.

---

## ⚙️ Kurulum

1. Python 3.10+ kurulu olmalı.
2. Gerekli kütüphaneler:
   ```bash
   pip install discord.py python-dotenv
