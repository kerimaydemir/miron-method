# ADR-019: NVIDIA NIM ile kayıtlı çoklu ajan analizi

Tarih: 7 Eylül 2026

## Karar

Model çağrıları NVIDIA NIM'in OpenAI uyumlu
`https://integrate.api.nvidia.com/v1/chat/completions` uç noktasına yönlendirilir.
`NVIDIA_API_KEY` yalnız sunucu ortamında veya GitHub Actions secret olarak tutulur.
İstemciye, kupon metnine, prompt arşivine veya açık Git geçmişine yazılmaz.
`AI_PROVIDER=nvidia_nim` ve `NVIDIA_ENABLED=true` birlikte seçilir; Gemini kapalı
kalır. Birden fazla sağlayıcıyı aynı anda açan çelişkili yapılandırma reddedilir.

Varsayılan rollerin tam model kimlikleri `config/models.yaml` dosyasındadır:

| Görev | Yapılandırılan model |
| --- | --- |
| Kaynak denetimi, araştırma, dört kör uzman | `nvidia/nemotron-3.5-lightning-30b-a3b` |
| Eleştirmen, senaryo kurulu, ana sentez ve revizyon | `nvidia/nemotron-3-super-120b-a12b` |
| Nihai eleştirmen | `nvidia/nemotron-3-ultra-550b-a55b` |

Kaynak denetimi ve araştırmadan sonra dört uzman ayrı çağrılarla çalışır.
Uzmanlar birbirlerinin yorumlarını görmez; aynı zaman damgalı kanıt paketini
kendi görevleri için inceler. Sonraki eleştirmen ve sentez çağrıları bu çıktıları
birleştirir. Bu görev ayrımı, farklı modellerin istatistiksel olarak bağımsız
olduğu veya sonucun daha yüksek başarı sağlayacağı anlamına gelmez.

## Kanıt ve çalışma kaydı

NVIDIA araştırma çağrısı yalnız kendisine verilen kanıtları kullanır. Otomatik
Google araması veya NVIDIA'nın maç haberlerini kendiliğinden canlı çektiği
varsayılmaz. Kadro, haber, sakatlık, oran ve istatistik kapsamı veri adaptörlerinden
gelir; eksik alanlar bilinmeyen olarak tutulur.

Her model aşaması kullanılan sağlayıcıyı, model kimliğini, sağlayıcı istek
kimliğini, token sayılarını, ücretlendirme biçimini ve aynı çağrıyı paylaşan
aşamaları kaydeder. Aşama sayısı model çağrısı veya benzersiz model sayısı değildir.
Arayüz, çalışmanın gerçek `analysis_provider` ve `model_ids` alanlarını gösterir.
Eksik model kaydı için isim uydurulmaz; mock sonuç açıkça deneme olarak etiketlenir.

Yapılandırma hazır olması, sağlayıcının o anda çalıştığının kanıtı değildir.
Canlı doğrulama; sağlayıcı yanıtını, şema doğrulamasını, kaydedilmiş model
aşamalarını ve tamamlanan çalışmayı birlikte kontrol eder. Telegram teslimi ve
şifreli raporun kalıcı kaydı ayrıca doğrulanır.

## Kota ve hata davranışı

Model yolları `trial_rate_limited` olarak işaretlenir. Sıfır dolar maliyet kaydı,
deneme uç noktası için yapılandırılmış tarife hesabıdır; fatura mutabakatı,
sınırsız kullanım, kalıcı ücretsiz erişim veya üretim SLA'sı değildir.
Eşzamanlılık, çağrı sayısı, çıktı boyutu, bekleme ve yeniden deneme sınırları
sağlayıcının kotasını korur. Süresi dolan model doğrulaması, geçersiz model çıktısı
ve sağlayıcı hatası başarılı model tahmini olarak kabul edilmez. Ücretli Gemini'ye
sessiz geçiş yapılmaz.

## Olasılık ve öğrenme sınırı

Model yüzdeleri `calibration_status=provisional` taşır. `%70` bir seçim eşiğidir;
ölçülmüş `%70` başarı veya kupon garantisi değildir. Gerçek bookmaker fiyatı,
kayıt zamanı ve olasılığın kaynağı ayrı saklanır. Birleşik kuponun olasılığı tek
bacağın olasılığı gibi sunulmaz; fiyatı olmayan maç kupon sayılmaz.

Maç sonrası değerlendirme kilitlenmiş ön-maç kaydını değiştirmez. İsabet, kayıp,
Brier skoru ve eşit birim simülasyon getirisi sonuçlanan örnekler üzerinde
izlenir. “Şanslı galibiyet” ve “şanssız kayıp” sınıfları mevcut veriye dayalı
süreç değerlendirmeleridir; tek maçtan kesin nedensellik veya kendiliğinden
iyileşen tahmin kalitesi iddia edilmez.

## Kaynaklar

- [NVIDIA hosted LLM API referansı](https://docs.api.nvidia.com/nim/reference/llm-apis)
- [NVIDIA NIM yapılandırılmış çıktı dokümantasyonu](https://docs.nvidia.com/nim/large-language-models/latest/structured-generation.html)
- [Nemotron 3.5 Lightning API sayfası ve deneme koşulları](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b/build)

Bu karar, ADR-014'ün yalnız Gemini yönlendirmesi kararını ve ADR-018'deki
Gemini'ye özgü model adlandırmalarını mevcut NVIDIA yapılandırması için günceller.
