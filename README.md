<div align="center">

# ColorIQ

**Intelligent Industrial Color Quality Control System**

Real-time camera-based fabric color grouping using CNN feature extraction, LAB color analysis, and machine learning clustering.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green.svg)](https://riverbankcomputing.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-red.svg)](https://opencv.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-orange.svg)](https://scikit-learn.org)

</div>

---

## Overview

ColorIQ is an industrial color quality control system designed for textile and fabric manufacturing environments. It captures fabric samples via camera, extracts deep features using CNN (MobileNetV3-Large), LAB color space, and texture descriptors, then automatically groups similar tones into lots using unsupervised machine learning.

**Key differentiator:** No reference sample required. Workers simply place fabric pieces in front of the camera, and the system automatically clusters them by color similarity.

## Features

| Feature | Description |
|---------|-------------|
| **Automatic Lot Grouping** | Camera capture -> CNN + LAB + Texture feature extraction -> K-Means / DBSCAN / Agglomerative clustering |
| **4 Delta E Methods** | CIE 1976, CIE 1994, CIEDE 2000, CMC (l:c) |
| **Reference-Free** | No master sample needed -- system clusters all measurements automatically |
| **CNN Feature Extraction** | MobileNetV3-Large (960D) + LAB (3D) + Texture/Gabor/LBP (138D) = 1101D feature vectors |
| **Real-Time Tolerance** | Adjustable tolerance slider (0.1 - 5.0) with instant reclustering |
| **Target Board** | Live a\*b\* color distribution scatter plot |
| **Spectral Curves** | Multi-sample spectral reflectance overlay graphs |
| **Metamerism Check** | Multi-illuminant color consistency evaluation (D65, A, TL84, F2, F7, F11) |
| **X-Rite Integration** | Import CSV, TXT, CXF, XML files from spectrophotometers |
| **File Watcher** | Auto-import new measurement files from watch directory |
| **Excel Reports** | Professional multi-sheet reports with charts and images |
| **Barcode Generation** | Lot-based barcode and quality label printing |
| **Dark Theme** | Professional dark UI optimized for factory floor use |

## Architecture

```
ColorIQ/
├── config/
│   └── settings.py              # Application configuration (camera, tolerances, CNN, UI)
├── core/
│   ├── models/
│   │   └── color_data.py        # Data models (LabColor, LCHColor, MeasurementRecord, etc.)
│   ├── camera/
│   │   └── manager.py           # Camera management (OpenCV singleton)
│   ├── color_engine/
│   │   ├── engine.py            # Color computation engine
│   │   ├── color_convert.py     # RGB <-> LAB <-> LCH conversions
│   │   ├── delta_e.py           # Delta E calculations (4 methods, pure Python)
│   │   ├── delta_e_lib.py       # Colormath-based Delta E wrappers
│   │   └── feature_extractor.py # CNN + LAB + Texture feature extraction (1101D)
│   ├── spectrophotometer/
│   │   ├── parser.py            # CSV/TXT file parser
│   │   ├── cxf3_parser.py       # CxF3 XML parser (X-Rite)
│   │   └── watcher.py           # Directory file watcher
│   ├── lotting/
│   │   └── engine.py            # Lot clustering engine (K-Means/DBSCAN/Agglomerative)
│   ├── analysis/
│   │   ├── spectral_graph.py    # Spectral reflectance curve plotting
│   │   ├── color_plot.py        # Target board (a*b*) scatter + DE bar chart
│   │   ├── metamerism.py        # Multi-illuminant metamerism checker
│   │   └── tolerance.py         # Auto-tolerance engine
│   ├── export/
│   │   ├── excel_report.py      # Excel report generator
│   │   └── barcode.py           # Barcode/label generator
│   └── job/
│       └── manager.py           # Job management (JSON CRUD)
├── ui/
│   ├── main_window.py           # Main application window
│   └── styles/
│       └── dark_theme.py        # Professional dark theme
├── tests/
│   ├── test_core.py             # Unit tests
│   └── test_imports.py          # Integration tests
├── main.py                      # Application entry point
├── requirements.txt
└── README.md
```

## Installation

```bash
# Clone the repository
git clone https://github.com/lgcnrb/ColorIQ.git
cd ColorIQ

# Create conda environment (recommended)
conda create -n coloriq python=3.12
conda activate coloriq

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `numpy` | Numerical computation |
| `opencv-python` | Camera capture and image processing |
| `scikit-image` | Color space conversions |
| `colormath` | Delta E reference calculations |
| `PyQt6` | Professional GUI framework |
| `matplotlib` | Graph and chart generation |
| `pandas` + `xlsxwriter` | Excel report generation |
| `scikit-learn` | K-Means, DBSCAN, Agglomerative clustering |
| `torch` + `torchvision` | CNN feature extraction (MobileNetV3-Large) |
| `watchdog` | File system monitoring |

## Usage

```bash
python main.py
```

### Workflow

1. **Open Camera** -- Click "OPEN CAMERA" to start the live feed
2. **Place Fabric** -- Put the fabric piece in front of the camera
3. **Capture** -- Click "SNAP" to capture and analyze (auto-lot assignment)
4. **Repeat** -- Add more fabric pieces with each SNAP
5. **Adjust Tolerance** -- Use the tolerance slider to fine-tune grouping sensitivity
6. **Select Method** -- Choose between K-Means (auto-k), DBSCAN (density), or Agglomerative (hierarchical)
7. **Review** -- Check the Target Board for color distribution and lot table for groupings
8. **Export** -- Save Excel report with one click

### Clustering Methods

| Method | Parameters | Best For |
|--------|-----------|----------|
| **K-Means** | Auto-k (silhouette score), fixed k | General purpose, fast, well-separated groups |
| **DBSCAN** | eps (tolerance), min_samples | Noisy data, variable-density clusters |
| **Agglomerative** | linkage (ward/complete/average) | Hierarchical relationships, dendrogram visualization |

### Lot Classification

| Lot | Delta E Range | Description |
|-----|--------------|-------------|
| LOT A | DE <= 0.5 | Perfect match |
| LOT B | DE <= 1.0 | Good match |
| LOT C | DE <= 2.0 | Acceptable |
| LOT D | DE <= 3.5 | Borderline |
| LOT F | DE > 3.5 | Rejected |

## Configuration

All settings are in `config/settings.py`:

```python
# Camera
CAMERA = CameraConfig(width=640, height=480, fps_target=30)

# Clustering
LOTTING = LottingConfig(
    default_eps=1.0,
    lot_a_threshold=0.5,
    lot_b_threshold=1.0,
    lot_c_threshold=2.0,
    lot_d_threshold=3.5,
)

# CNN Feature Extraction
CNN = CNNConfig(
    model_name="mobilenet_v3_large",
    feature_dim=960,
    use_gpu=True,
)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_core.py -v
```

## Technical Details

### Feature Vector (1101 dimensions)

| Component | Dimensions | Description |
|-----------|-----------|-------------|
| LAB Statistics | 3 | Mean L\*, a\*, b\* values |
| CNN (MobileNetV3-Large) | 960 | Deep visual features from fabric image |
| Texture Histogram | 32 | Color distribution histogram |
| Gabor Filters | 32 | Texture orientation and frequency |
| LBP (Local Binary Pattern) | 26 | Micro-texture patterns |
| Color Histogram | 38 | Additional color distribution features |

### Delta E Methods

- **CIE 1976 (dE\*ab):** Simple Euclidean distance in LAB space
- **CIE 1994 (dE\*94):** Textile-adapted with weighting factors
- **CIEDE 2000 (dE00):** State-of-the-art with lightness/chroma/hue compensation
- **CMC l:c:** Textile industry standard (l=2, c=1)

## License

MIT License

## Author

**lgcnrb** -- [GitHub](https://github.com/lgcnrb)
