# ADR-018: Kota kontrollü canlı veri ve öğrenme döngüsü

## Karar

RapidAPI `Free API Live Football Data` BASIC aboneliği, yalnız sekiz izinli ligin
fikstür keşfi ve sınırlı derin kanıtı için ikincil kaynak olarak kullanılır. Anahtar
yalnız ortam değişkeninde tutulur. Sağlayıcı cevabı boş olduğunda oran, kadro,
istatistik veya sakatlık verisi üretilmez.

22 Ağustos 2026 tarihinde abonelik ekranında BASIC limitinin ayda 100 istek olduğu
doğrulandı. Bu nedenle adaptör:

- en fazla iki yerel günü tek yenilemede çeker;
- cevaptan yalnız Premier League, LaLiga, Bundesliga, Serie A, Ligue 1,
  Eredivisie, Primeira Liga ve Süper Lig kayıtlarını geçirir;
- analiz başına varsayılan dört derin istek kullanır;
- eksik alanları `coverage=false` olarak kilitli kanıta yazar;
- bookmaker oranı boşsa otomatik kupon hazır kabul etmez.

## Seçim politikası

Günlük seçim kotası yoktur. Gemini kaba eleme 0-6, eleştirmen 0-3 maç
döndürebilir. Nihai pazar filtresi ayrıca gerçek fiyat, güncellik, bookmaker
derinliği ve model-piyasa farkını uygular. Her seçim ve üretilen kupon için model
olasılığı en az `%70`, kilit anı decimal oranı en az `1.80` olmalıdır. Üst oran
sınırı yoktur; yüksek fiyat tek başına seçim sebebi değildir. Hiçbir aday geçmezse
çalışma başarıyla `0 seçim` sonucu üretir; bu hata değildir.

Her seçimde tez, destekleyici kanıt, karşı kanıt, fiyat gerekçesi, geçersizleştirme
koşulları, model-piyasa uyuşmazlığı ve kanıt kesme zamanı saklanır.

## Maç sonrası ölçüm

Sonuçlanan seçimler pazar bazında isabet, ortalama oran, Brier skoru, eşit birim
simülasyon ROI'si ve süreç kohortlarına ayrılır. `sound_win`, `lucky_win`,
`sound_but_unlucky_loss` ve `bad_process_loss` etiketleri nedensellik iddiası
değil, kilit anındaki edge ve bookmaker kapsamına dayalı ön sınıflandırmadır.
İlk 30 seçim yalnız erken sinyal sayılır.

## GitHub Actions otomasyonu

`.github/workflows/daily-analysis.yml` sabah ön-maç ve gece maç-sonrası fazlarını
GitHub-hosted runner üzerinde çalıştırır. Runner, secret'lardan geçici `.env`
oluşturur, Docker Compose stack'ini ayağa kaldırır, localhost API'ye otomasyon
çağrısı yapar, PostgreSQL'i dump eder ve ham veriyi runner kapanmadan önce
şifreler.

Gerekli secret'lar:

- `GEMINI_API_KEY`
- `THE_ODDS_API_KEY`
- `API_FOOTBALL_API_KEY`
- `RAPIDAPI_KEY`
- `MIRON_BABA_AUTOMATION_TOKEN`
- `DATA_ENCRYPTION_KEY`

Kalıcı öğrenme verisi public `main` branch'e yazılmaz. Şifreli Postgres dump'ı
ve şifreli çalışma raporları ayrı `automation-state` branch'inde tutulur. Bu
tasarım ev bilgisayarının açık kalmasını gerektirmez; ancak decrypt edilecek ham
metrikler için `DATA_ENCRYPTION_KEY` kaybedilmemelidir.
