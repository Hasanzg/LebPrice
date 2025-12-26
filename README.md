<img width="929" height="621" alt="image" src="https://github.com/user-attachments/assets/b1ef7115-de21-478a-9b5d-874b2c691ed1" /># LebPrice

A price comparison platform for Lebanese e-commerce stores. Scrapes product data, tracks price histories, and provides a unified API for comparing prices across multiple retailers.

## Requirements

- Python 3.8+
- Docker & Docker Compose (recommended)
- Kubernetes cluster (optional, for production deployment)
- Do "pip install -r requirements.txt" in any directory

## Getting Started

### With Docker Compose

```bash
docker-compose up -d
```

Access the services:
- Backend API: http://localhost:8000

### Running the Scraper

```bash
cd backend
python crawler.py
```
currently scrapes each of *PC and Parts* and *Expert Zone*

Can be expanded to scrape all types of stores, so long they have an online store.

## Features
### Login And Signing up
- User account creation with secure authentication
- Email/password login support
- Google Sign-In integration using Google OAuth
- User profile customization and management

### Price Tracking
- Automatic scraping from multiple Lebanese online stores
- Price history tracking for trend analysis
- Tax calculation (11% Lebanese VAT)
- Real-time stock availability monitoring
- Exports to CSV for data analysis

### Web Scraping
- Auto-discovers WooCommerce JSON APIs
- Falls back to HTML parsing when APIs unavailable
- Multi-threaded concurrent scraping
- Configurable store-specific settings
- Organized by product categories

### Search and Filtering
- Full-text search across products
- Filter by store, category, price range, stock status
- Sort by price, date, name
- RESTful API with advanced query parameters

### Microservices Architecture
- Backend: Core API and product management
- Auth: User authentication and authorization
- Frontend: User interface
- Cart: Shopping cart functionality

## Deployment

### Docker
The application is fully containerized. Each service has its own Dockerfile and can be deployed independently or together using Docker Compose. All services communicate over a shared network.

### Kubernetes
Complete Kubernetes configurations included in the `k8s/` directory:
- Individual deployments for each service
- Nginx Ingress controller for routing
- Service definitions for inter-pod communication
- Scalable architecture ready for production

Deploy to Kubernetes:
```bash
kubectl apply -f k8s/
```

## Technology Stack

- Django 4.x with Django REST Framework
- BeautifulSoup4 for web scraping
- SQLite (development) / PostgreSQL-ready
- Docker for containerization
- Kubernetes with Nginx Ingress

## API Endpoints

### Products
```
GET  /api/products/                     # List all products
GET  /api/products/{id}/                # Product details
GET  /api/products/{id}/price_history/  # Price history
GET  /api/products/search/?q=keyword    # Search
```

Filter examples:
```
/api/products/?store_name=PC and Parts
/api/products/?category__name=CPU
/api/products/?price__gte=100&price__lte=500
/api/products/?stock_status=in_stock
```

### Categories
```
GET  /api/categories/        # List categories
GET  /api/categories/{id}/   # Category details
```

## Supported Stores

**PC and Parts** (pcandparts.com)
- 27+ categories including CPUs, GPUs, RAM, Storage, Monitors
- Prices exclude tax (11% added automatically)

**Expert Zone** (ezonelb.com)
- 18+ categories including Desktop/Laptop, Screens, Accessories
- Prices include tax

## Adding New Stores

Create a configuration class in `backend/store_config.py`:

```python
class NewStoreConfig(StoreConfig):
    def __init__(self, auto_discover=True):
        super().__init__()
        self.store_name = "New Store"
        self.base_url = "https://newstore.com"
        self.categories = ["category1", "category2"]
        self.tax_included = False
        self.tax_rate = Decimal('0.11')
```

The scraper handles API discovery and data extraction automatically.

## Tax Handling

Automatic Lebanese VAT (11%) calculation:
- Detects if prices include tax
- Calculates pre-tax and post-tax prices
- Supports tax-exempt products
- Stores all price variants

## Data Storage

- Products saved to Django database
- Automatic CSV export to `backend/CSVs/`
- Price history tracked for every update
- Timestamps for all changes

## Project Structure

```
backend/     # Core API, scraper, product management
auth/        # User authentication
frontend/    # User interface
cart/        # Shopping cart
k8s/         # Kubernetes deployment configs
```

Demo:

For main page before signing up or logging in:

<img width="1218" height="805" alt="image" src="https://github.com/user-attachments/assets/10dc584f-25d3-4704-be85-b74d0e5a3486" />


Signing in with google:

<img width="929" height="621" alt="image" src="https://github.com/user-attachments/assets/7dccbce4-95ae-49dd-9ed8-b2d4e6fdf580" />

<img width="1463" height="329" alt="image" src="https://github.com/user-attachments/assets/f7254466-e7bf-4934-999c-d56d6026ea79" />


After logging in / Signing up, Main page:

<img width="1895" height="922" alt="image" src="https://github.com/user-attachments/assets/64888c07-0472-4f74-b605-01ce73d7abe6" />


Can search and sort as needed:

<img width="1895" height="898" alt="image" src="https://github.com/user-attachments/assets/5cb7aa1a-efea-41ee-8c25-6e60bebf4417" />

Can simulate cart and shows final price with VAT if not pre-included in the price.

May also customize profile, add favorite shops, add profile picture, and more!
