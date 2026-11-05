# Ücretsiz 7S Hibrit Analiz Botu

## Kurulum (Windows)
1. Python 3.10 veya 3.11 yükle.
2. Klasörde Komut İstemi aç.
3. `python -m venv .venv`
4. `.venv\\Scripts\\activate`
5. `pip install -r requirements.txt`
6. `streamlit run app.py`
7. Tarayıcıda açılan sayfaya fiyat CSV dosyanı yükle.

## CSV formatı
Zorunlu sütunlar: `timestamp` (tarih/saat) ve `price` (sayısal fiyat). İsteğe bağlı `market` sütununa `OTC` veya `REAL` yaz. Aynı dosyadaki piyasaları arayüzde ayrı ayrı test et.

Örnek:
```csv
timestamp,price,market
2026-01-01 10:00:00.000,1.10000,REAL
2026-01-01 10:00:00.250,1.10002,REAL
```

## Bilmen gerekenler
- Bot 7 saniye sonrasına eşit veya daha geç ilk fiyatı hedef olarak kullanır. Veri aralığı seyrekse bu tam 7 saniye olmayabilir.
- İşlem geçmişi Excel'i (bahis/kâr listesi) fiyat tahmini için yeterli değildir; tick/saniyelik fiyat serisi gerekir.
- Son dönem test verisi kronolojik olarak ayrılır; rastgele karıştırma yapılmaz.
- 1.000+ etiketli örnek hedefle. Farklı günlerde yeni veriyle tekrar test et.
- OTC ve gerçek piyasayı karıştırma. Sabit bahis kullan, Martingale kullanma.
- Bot Pocket Option'a bağlanmaz, canlı veri çekmez ve otomatik işlem açmaz.
- Win rate, ödeme oranı ve belirsizlik aralığı birlikte değerlendirilir. Kazanç garantisi yoktur.
