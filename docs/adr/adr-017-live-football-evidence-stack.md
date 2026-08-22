# ADR-017: Canlı futbol kanıt omurgası

## Durum

Kabul edildi — 2026-08-22.

## Sorun

Fikstür kaynağı tek başına derin analiz değildir. Takım adı ve maç saatiyle üretilen model
olasılıkları gerçek bookmaker oranı gibi gösterilemez. Kadro, sakatlık, form, istatistik,
teknik direktör, H2H, çevre ve piyasa kanıtları kaynak ve zaman damgasıyla taşınmalıdır.

## Karar

- API-Football ana yapılandırılmış futbol kanıtıdır. Maç kimliği bir kez eşlenir; finalistler
  için fikstür istatistikleri, kadrolar, oyuncular, sakatlıklar, tahminler, oranlar, puan
  durumu, son form, H2H ve teknik direktör verisi paralel alınır.
- The Odds API bağımsız ve çok-bookmaker piyasa gerçeğidir. Yayınlanan her oran bu kaynaktan,
  zaman damgası ve bookmaker sayısıyla gelmek zorundadır.
- Mevcut Gemini anahtarı Google Search Grounding ile güncel resmî kulüp/lig açıklamalarını
  ve güvenilir haberleri çapraz kontrol eder. Modelin yazdığı URL değil, grounding metadata
  içindeki gerçek URL saklanır.
- Open-Meteo anahtarsız çevre kanıtıdır. API-Football maç kaydındaki şehir geocode edilir ve
  maç günü saatlik tahmin kanıt paketine eklenir.
- StatsBomb Open Data yalnızca tarihsel RAG, benzerlik ve backtest tohumu olarak kullanılır;
  güncel fikstür veya canlı oran gerçeği sayılmaz.
- football-data.org ve OpenLigaDB fikstür fallback'idir. Bunların varlığı derin analiz
  readiness'i sağlamaz.

## Analiz düzeni

Üç Gemini modeli sekiz çağrıda 29 pre-match aşamasını ayrı görevlerle yürütür:

1. Güncel grounded araştırma ile kaynak doğrulama/normalizasyon paralel çalışır.
2. Uzman kurul S05-S16 için yapılandırılmış kanıtı inceler.
3. Bağımsız critic kurul S17-S21 arasında uzman sonuçlarını red-team eder.
4. Senaryo kurulu S22-S26 için üç sonucu steelman eder ve maç akışlarını kurar.
5. Chief ilk olasılık vektörünü üretir; Final Critic denetler; Chief en fazla bir revizyon yapar.
6. S30 uygulama tarafından değiştirilemez tahmin kilidi olarak oluşturulur.

Bir model çağrısının eksik veya yinelenen stage ID döndürmesi tüm analizi başarısız yapar.

## Fail-closed koşulları

Otomatik kupon şu dört koşul birlikte sağlanmadan çalışmaz:

- canlı The Odds API bağlantısı,
- Gemini rotası,
- API-Football derin veri bağlantısı,
- S01-S29 aşamalarının kodda uygulanmış olması.

Eksik veri model tarafından doldurulmaz. İki bookmaker'dan az, 15 dakikadan eski, en az yüzde
1 edge taşımayan veya model olasılığı yüzde 50 altında kalan seçim yayımlanmaz.

## Anahtar ve maliyet sınırı

Kullanıcıdan her veri kalemi için ayrı anahtar istenmez. Mevcut Gemini anahtarına ek olarak
üretim kalitesi için iki yeni read-only anahtar yeterlidir: API-Football ve The Odds API.
Open-Meteo ve StatsBomb anahtarsızdır. Hiçbir sağlayıcı üzerinden bahis yerleştirilmez.

API-Football free planın 10 istek/dakika sınırı sağlayıcı genelindeki ortak hız sınırlayıcıyla
uygulanır. Üç finalist için yaklaşık 39 derin istek free planda en az dört dakikaya yayılır;
ücretli planda `API_FOOTBALL_REQUESTS_PER_MINUTE` plan sınırına göre yükseltilebilir.
