# Hybrid Color Control System

Endustriyel spektrofotometre (X-Rite) ve kamera tabanli goruntu analizini birlestiren, **Multimodal Kalite Kontrol Sistemi**.

<p align="center">
  <img src="test_image/ColorDif.png" alt="Hybrid Color Control System" width="800" />
</p>

## Ozellikler

- **Cok Modlu Analiz:** Spektrofotometre + Kamera entegrasyonu
- **4 Delta E Yontemi:** CIE 1976, CIE 1994, CIEDE 2000, CMC
- **Hibrit Lot Karari:** Cihaz + Kamera verilerini birlestiren karar motoru
- **Yuzey Homojenlik Analizi:** Kumaş表面 renk dalgalanması tespiti
- **X-Rite Dosya Destegi:** CSV, TXT, CXF, XML formatlarinda veri yukleme
- **Profesyonel Arayuz:** Koyu tema, renk ornekleyicileri, canli onizleme
- **Excel Raporlama:** Detayli rapor export islemi

## Mimari

```
Color-Difference-Calculator/
├── config/
│   ├── __init__.py
│   └── settings.py              # Uygulama sabitleri ve konfigurasyon
├── core/
│   ├── models/
│   │   ├── __init__.py
│   │   └── color_data.py        # Veri modelleri (dataclass)
│   ├── camera/
│   │   ├── __init__.py
│   │   └── manager.py           # Kamera yonetimi (singleton)
│   ├── color_engine/
│   │   ├── __init__.py
│   │   └── engine.py            # Renk hesaplama motoru
│   ├── spectrophotometer/
│   │   ├── __init__.py
│   │   └── parser.py            # X-Rite dosya parser
│   └── lotting/
│       ├── __init__.py
│       └── engine.py            # Hibrit lotlama karar motoru
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # Ana pencere (MVC: View)
│   ├── styles/
│   │   └── dark_theme.py        # Profesyonel koyu tema
│   └── widgets/
├── data/
│   ├── samples/                 # Ornek veriler
│   ├── exports/                 # Disa aktarilan dosyalar
│   └── logs/                    # Log dosyalari
├── tests/
│   ├── __init__.py
│   └── test_core.py             # Birim testler
├── main.py                      # Uygulama giris noktasi
├── requirements.txt
└── README.md
```

## Kurulum

```bash
pip install -r requirements.txt
```

## Calistirma

```bash
python main.py
```

## Testler

```bash
pytest tests/ -v
```

## Bilimsel Temeller

### Hibrit Lot Karar Mekanizmasi

Sistem iki kanaldan gelen veriyi birlestirerek lot kararini verir:

1. **Spektrofotometre Kanali (%70 agirlik):** X-Rite cihazindan gelen $L^*a^*b^*$ degerleri
2. **Kamera Kanali (%30 agirlik):** Goruntu analizinden elde edilen ortalama renk + yuzey homojenligi

**Lot Sinirlari:**
| Lot | Delta E Esimigi | Aciklama |
|-----|-----------------|----------|
| LOT A | DE <= 0.8 | Kusursuz uyum |
| LOT B | DE <= 1.0 | Kabul edilebilir sapma |
| LOT C | DE <= 1.5 | Kendi icinde eslesme |
| RED | DE > 1.5 veya heterojen | Tolerans disi |

### Yuzey Homojenlik Testi

Kameradan alinan goruntudeki L* kanalinin standart sapması hesaplanir:
- Eger $\sigma_{L^*}$ > 2.0 ise yuzey **heterojen** olarak isaretlenir
- Heterojen lotlar otomatik olarak **RED** karari alir

## Kullanim Senaryolari

### 1. Sadece Kamera ile
1. Master rengi ayarla
2. Referansi olc
3. Kumaş样品 olc
4. Delta E ve lot kararini gor

### 2. X-Rite + Kamera Hibrit
1. X-Rite dosyasini yukle (otomatik master olarak ayarlanir)
2. Kamera ile referansi olc
3. Kamera ile sample olc
4. Hibrit karar motoru sonucu uretir

### 3. Sadece RGB
1. Renk uzayini RGB olarak sec
2. Referansi olc
3. Sample olc
4. RGB fark degerlerini gor

## Guncelleme Notlari

- **v2.0:** MVC mimarisi, hibrit lot motoru, X-Rite entegrasyonu
- **v1.0:** Tek dosya yapisi, temel Delta E hesaplama
