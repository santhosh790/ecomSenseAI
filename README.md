# ecomSenseAI

Automated vegetable item and quantity extraction engine with dual operational interfaces: an interactive **Streamlit dashboard** for human-in-the-loop validation and a high-performance **FastAPI REST API** built for edge devices, mobile applications, and external integrations.

---

## Architectural Evolution

ecomSenseAI has evolved from a single-node parsing script into an enterprise-ready, multi-interface data pipeline following **Domain-Driven Design (DDD)** principles:

```mermaid
flowchart TD
    subgraph Clients["Clients & Edge Devices"]
        Mobile["Mobile App / Handheld Scanners"]
        WebAdmin["Streamlit Web Dashboard"]
        External["External Services / POS"]
    end

    subgraph Interfaces["Interface Adapters"]
        API["FastAPI Backend (api/main.py)"]
        StreamlitUI["Streamlit App (ecomSenseAI.py)"]
    end

    subgraph Core["Application & Domain Core"]
        Detection["Vegetable Detection & Fuzzy Matcher"]
        Parser["Parser Strategies (Generic / VIT / FVIT / MHS)"]
        OCR["OCR Pipeline (PaddleOCR + OpenCV + Tesseract)"]
        Reporting["Challan & Report Engine (XLSX / PDF)"]
    end

    subgraph Persistence["Storage & Persistence Evolution"]
        Postgres[("PostgreSQL / Supabase (Primary Relational Store)")]
        GSheets[("Google Sheets (Collaborative Sync)")]
        CSVFile[("Local CSV Mirror (outputs/validated_YYYY-MM-DD.csv)")]
    end

    Mobile --> API
    External --> API
    WebAdmin --> StreamlitUI

    API --> Detection
    API --> Reporting
    StreamlitUI --> Detection
    StreamlitUI --> Reporting

    Detection --> OCR
    Detection --> Parser

    API --> Postgres
    API --> CSVFile
    StreamlitUI --> Postgres
    StreamlitUI --> GSheets
    StreamlitUI --> CSVFile
```

### Key Milestones

1. **Interface Evolution (Streamlit → FastAPI + Streamlit)**:
   - *Streamlit UI*: Provides a full-featured web console for uploading invoices, reviewing OCR detections with confidence scores, editing items, and downloading consolidated sheets.
   - *FastAPI Backend*: Exposes headless, low-latency REST endpoints optimized for edge devices (mobile apps, handheld warehouse scanners) and automated webhooks without UI overhead.

2. **Storage Evolution (Local Files → Google Sheets → PostgreSQL)**:
   - *Stage 1 (Local CSV)*: Saved confirmed orders to dated CSV files in the `outputs/` folder alongside static JSON configuration files.
   - *Stage 2 (Google Sheets)*: Added cloud-based multi-user synchronization via Google Sheets API for distributed warehouse teams.
   - *Stage 3 (PostgreSQL / Supabase)*: Introduced enterprise relational persistence via SQLAlchemy ORM with normalized `orders` and `order_items` tables, JSON payloads, and transactional integrity, retaining the local CSV mirror for zero-downtime backwards compatibility.

---

## Domain-Driven Architecture

The codebase enforces a clean separation of concerns:

- **Domain Layer** ([domain/models.py](domain/models.py)): Core business entities such as `VegetableDetection`, confidence thresholds, and parsing domain rules.
- **Application Layer**:
  - [application/extraction_service.py](application/extraction_service.py): Text parsing, regex patterns, PO number and order value extraction, fuzzy matching policies.
  - [application/vegetable_detection_service.py](application/vegetable_detection_service.py): High-level document detection and scoring coordinator.
  - [application/vegetable_catalog_service.py](application/vegetable_catalog_service.py): Catalog lookup, aliases, and Tamil translation mapping.
  - [application/reporting_service.py](application/reporting_service.py): Order consolidation, client-specific summaries, Excel exports, and PDF generation with WeasyPrint.
- **Infrastructure Layer**:
  - [infrastructure/ocr_engine.py](infrastructure/ocr_engine.py): PaddleOCR, OpenCV preprocessing (grayscale, adaptive thresholding), and Tesseract fallback.
  - [infrastructure/document_readers.py](infrastructure/document_readers.py): PDF, Excel, and image file parsers.
  - [infrastructure/database.py](infrastructure/database.py): SQLAlchemy engine configuration, session management, and Supabase connection resolution.
  - [infrastructure/order_repository.py](infrastructure/order_repository.py): PostgreSQL persistence, schema migrations (`Base.metadata.create_all`), and queries.
  - [infrastructure/google_sheets_service.py](infrastructure/google_sheets_service.py): Google Sheets API integration via gspread.
  - [infrastructure/persistence_service.py](infrastructure/persistence_service.py): Local CSV mirror and upload file management.
- **Interface Adapters**:
  - [api/main.py](api/main.py): FastAPI REST service for mobile/edge clients.
  - [ecomSenseAI.py](ecomSenseAI.py): Streamlit web application.

---

## FastAPI Backend (for Mobile & Edge Devices)

The FastAPI service delivers low-latency endpoints designed to power mobile applications, edge scanners, and automated backend systems.

### Run FastAPI Locally

Install the API dependencies from [requirements_api.txt](requirements_api.txt) and start the server:

```bash
pip install -r requirements_api.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Documentation (Swagger UI)**: `http://localhost:8000/docs`
- **OpenAPI Specification**: `http://localhost:8000/openapi.json`
- **Health Check**: `http://localhost:8000/api/v1/health`

### Key REST Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health status check. |
| `POST` | `/api/v1/extract` | Multipart upload (PDF, image, Excel). Runs OCR/parsing and returns detected vegetable items with confidence ratings, PO number, and order total. |
| `GET` | `/api/v1/orders` | Query saved orders for a given date (`?order_date=YYYY-MM-DD`). |
| `POST` | `/api/v1/orders/confirm` | Confirms and saves an order to PostgreSQL with dual-write to the local CSV mirror. |
| `GET` | `/api/v1/orders/individual/download` | Download individual order file as Excel (`.xlsx`) or PDF (`.pdf`). |
| `GET` | `/api/v1/orders/consolidated/download` | Download date-level consolidated orders as Excel or PDF. |
| `POST` | `/api/v1/delivery-challans/xlsx` | Generate a delivery challan in Excel format with custom billing and shipping headers. |
| `POST` | `/api/v1/delivery-challans/pdf` | Generate a delivery challan as a formatted PDF. |

### Edge Extraction Parameters

When invoking `POST /api/v1/extract`:
- `file`: Document upload (PDF, PNG, JPG, WEBP, XLSX up to 20 MB).
- `order_date`: Target date (`YYYY-MM-DD`).
- `parser_strategy`: Parser profile (`Generic`, `VIT`, `FVIT`, or `MHS`).
- `confidence_threshold`: Minimum name match confidence (default `75`).
- `auto_extract_threshold`: Auto-extract verification threshold (default `90`).

### Cloud Deployment (Render)

The repository includes [render.yaml](render.yaml) for one-click deployment on Render:

```yaml
services:
  - type: web
    name: ecomsenseai-api
    runtime: python
    buildCommand: pip install -r requirements_api.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/v1/health
    envVars:
      - key: DATABASE_URL
        sync: false
```

Detailed API guide is available in [docs/FASTAPI_API.md](docs/FASTAPI_API.md).

---

## PostgreSQL & Persistence Architecture

Orders and detected items are persisted into PostgreSQL using SQLAlchemy ORM.

### Database Schema

1. **`orders` table**:
   - `id`: Auto-incrementing primary key.
   - `order_date`: Target date (indexed).
   - `source_file`: Uploaded filename.
   - `client_name`: Client or vendor name.
   - `parser_strategy`: Strategy used (`Generic`, `VIT`, `FVIT`, `MHS`).
   - `purchase_order_number`: Extracted or overridden PO number.
   - `total_order_value`: Extracted or overridden order value.
   - `upload_type`: File type (`pdf`, `image`, `excel`).
   - `uploaded_image_path`: Path reference to stored upload.
   - `created_at` / `updated_at`: UTC timestamps.
   - Unique constraint: `(order_date, source_file)`.

2. **`order_items` table**:
   - `id`: Primary key.
   - `order_id`: Foreign key referencing `orders.id` with `ON DELETE CASCADE`.
   - `item_order`: Display sequence integer.
   - `item_data`: Complete item JSON payload (`Source Name`, `Tamil Name`, `Quantity`, `Status`, `Confidence`, etc.).

### Dual-Write Resilience

When an order is confirmed:
1. It is committed transactionally to **PostgreSQL**.
2. A compatibility mirror is written to a local dated CSV file in the outputs directory (e.g. validated_YYYY-MM-DD.csv).
3. If Google Sheets integration is enabled in Streamlit, rows are optionally synced to the connected sheet.

### Supabase Connection Pooling (IPv4 / IPv6 Note)

Direct connections to Supabase (`db.<project-ref>.supabase.co`) resolve exclusively to IPv6 addresses. Edge platforms, Streamlit Community Cloud, and certain cloud environments only support IPv4 outbound routing.

To ensure seamless connectivity across both local and cloud platforms, use the **Supabase Supavisor Connection Pooler** (Session mode on port 5432):

- **Host**: `aws-0-[region].pooler.supabase.com`
- **Port**: `5432` (Session mode for SQLAlchemy transactions)
- **User**: `postgres.[project-ref]` (tenant identifier prefix is required by the pooler)
- **Database**: `postgres`
- **SSL Mode**: `require`

Example connection string:
```text
postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require
```

---

## Streamlit Operations Dashboard

The Streamlit interface ([ecomSenseAI.py](ecomSenseAI.py)) serves as the administrative workspace:

- **Primary Flow**: Upload document → Preview OCR text → Review auto-extracted vs flagged items (`Needs Review`) → Edit quantities / mappings → Confirm order.
- **Confidence Tuning**: Interactive sliders for vegetable match confidence and auto-extract thresholds.
- **Saved Orders**: Reopen previously confirmed files by date, adjust rows, and re-save.
- **Consolidation**: Live aggregated quantities summed across all files for any selected date with multi-format downloads (Excel, PDF).

Run Streamlit locally:
```bash
streamlit run ecomSenseAI.py
```

---

## OCR & Processing Pipeline

- **PaddleOCR**: Line-level text and bounding box detection for invoices and handwritten receipts.
- **OpenCV Preprocessing**: Grayscale conversion, Otsu's adaptive thresholding, and contrast normalization.
- **Tesseract Fallback**: Secondary engine when PaddleOCR is unavailable or fails.
- **RapidFuzz Matching**: Fuzzy comparison against canonical vegetable records in [data/vegetables.json](data/vegetables.json) and client-specific aliases in [data/aliases.json](data/aliases.json).

### System Dependencies

Image OCR requires the `tesseract` system binary on the host machine:

#### macOS
```bash
brew install tesseract
```

#### Linux / Cloud Hosts ([packages.txt](packages.txt))
```txt
tesseract-ocr
tesseract-ocr-eng
fonts-noto-core
fonts-lohit-taml
```

---

## Tamil Typography & PDF Generation

PDF exports and delivery challans render bilingual English/Tamil typography using **WeasyPrint**.

To prevent broken or missing Tamil glyphs on Linux cloud containers (such as Streamlit Cloud or Render), install the Lohit Tamil and Noto fonts declared in [packages.txt](packages.txt):
- `fonts-noto-core`
- `fonts-lohit-taml`

---

## Configuration & Secrets

### Environment Variables

For FastAPI, edge deployments, and container runtimes:

```bash
# PostgreSQL connection string
export DATABASE_URL="postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require"

# Optional CORS configuration
export ECOMSENSE_CORS_ORIGINS="https://myapp.com,http://localhost:3000"

# Optional Google Sheets integration
export GOOGLE_SHEET_ID="YOUR_SPREADSHEET_ID"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### Streamlit Secrets ([.streamlit/secrets.toml](.streamlit/secrets.toml))

```toml
[database]
host = "aws-0-<region>.pooler.supabase.com"
port = "5432"
database = "postgres"
user = "postgres.<project-ref>"
password = "YOUR_PASSWORD"
sslmode = "require"

[google_sheet]
spreadsheet_id = "YOUR_SPREADSHEET_ID"
worksheet = "Sheet1"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@...iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

---

## Testing

Run unit and integration tests across services:

```bash
# Extraction service tests
python -m unittest tests/test_extraction_service.py

# API endpoint tests
python -m unittest tests/test_api.py

# Batch and database operations
python -m unittest tests/test_batch_operations.py
```
