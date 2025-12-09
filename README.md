[![CI/CD Pipeline](https://github.com/MulyaP/VibeDish-Project-3/actions/workflows/ci.yml/badge.svg)](https://github.com/MulyaP/VibeDish-Project-3/actions/workflows/ci.yml)
[![codecov](https://codecov.io/github/MulyaP/VibeDish-Project-3/graph/badge.svg?token=XCZ40C1SHT)](https://codecov.io/github/MulyaP/VibeDish-Project-3)
[![GitHub issues](https://img.shields.io/github/issues/MulyaP/VibeDish-Project-3)](https://github.com/MulyaP/VibeDish-Project-3/issues)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17870270.svg)](https://doi.org/10.5281/zenodo.17870270)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/MulyaP/VibeDish-Project-3/blob/main/LICENSE)


[![Pull Requests](https://img.shields.io/github/issues-pr/MulyaP/VibeDish-Project-3)](https://github.com/MulyaP/VibeDish-Project-3/pulls)
[![GitHub contributors](https://img.shields.io/github/contributors/MulyaP/VibeDish-Project-3)](https://github.com/MulyaP/VibeDish-Project-3/graphs/contributors)
[![GitHub last commit](https://img.shields.io/github/last-commit/MulyaP/VibeDish-Project-3)](https://github.com/MulyaP/VibeDish-Project-3/commits/main)
[![Repo Size](https://img.shields.io/github/repo-size/MulyaP/VibeDish-Project-3)](https://github.com/MulyaP/VibeDish-Project-3)

<!-- Frontend Code Quality Tool Badges -->
[![Code Style: Prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg)](https://github.com/prettier/prettier)
[![Type Checker: TypeScript](https://img.shields.io/badge/type_checker-typescript-blue)](https://www.typescriptlang.org/)
[![Testing: Jest](https://img.shields.io/badge/testing-jest-red)](https://jestjs.io/)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Node Version](https://img.shields.io/badge/node-20+-green)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/framework-fastapi-009688)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/framework-next.js-black)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-blue)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/database-postgresql-blue)](https://www.postgresql.org/)

<!-- Backend Code Quality Tool Badges -->
[![Linting: Flake8](https://img.shields.io/badge/linting-flake8-yellowgreen)](https://flake8.pycqa.org/)
[![Testing: Pytest](https://img.shields.io/badge/testing-pytest-blue)](https://pytest.org/)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/framework-fastapi-009688)](https://fastapi.tiangolo.com/)


# 🍽️ VibeDish - Mood-Based Food Delivery Platform

VibeDish is a comprehensive food delivery platform that combines mood-based recommendations with a complete order management system. The platform integrates Spotify listening history to analyze user mood and suggest personalized meal recommendations.

## 🌟 Key Features

### 🎵 Mood-Based Recommendations
- **Spotify Integration**: Analyzes recent listening history to determine user mood
- **AI-Powered Analysis**: Uses Groq AI to interpret music preferences and emotional states
- **Smart Food Matching**: Recommends meals based on detected mood patterns
- **Personalized Suggestions**: Considers user dietary preferences and restrictions

### 🛒 Complete Order Management
- **Shopping Cart**: Add, update, and remove items with real-time inventory validation
- **Multi-Step Checkout**: Address management, delivery fee calculation, and order placement
- **Order Tracking**: Real-time status updates from placement to delivery
- **Order History**: View past orders with detailed information

### 🚗 Delivery System
- **Driver Dashboard**: View available and active deliveries
- **Route Optimization**: Mapbox integration for distance and duration calculations
- **Delivery Code Verification**: Secure 6-digit code system for order completion
- **Driver Analytics**: Track earnings, deliveries, and performance metrics

### 🏪 Restaurant Owner Portal
- **Menu Management**: Create, update, and delete meals with image uploads
- **Order Management**: Accept, prepare, and mark orders ready for delivery
- **Restaurant Profile**: Manage restaurant information and settings
- **Order Analytics**: View order history and statistics

### 📊 Nutrition Information
- **FatSecret API Integration**: Real-time nutrition data for meals
- **Detailed Breakdown**: Calories, protein, carbs, and fat content
- **Fallback Estimates**: Smart estimates when API data unavailable
- **Serving Size Information**: Clear portion details

### ⭐ Feedback System
- **Restaurant Ratings**: Rate food quality and service
- **Driver Ratings**: Evaluate delivery experience
- **Review System**: Leave detailed feedback for orders
- **One-Time Submission**: Prevents duplicate feedback

## 🏗️ Architecture

### Backend (FastAPI)
```
app/
├── routers/           # API endpoints
│   ├── auth_routes.py      # Authentication & authorization
│   ├── cart.py             # Shopping cart operations
│   ├── orders.py           # Order management
│   ├── delivery_routes.py  # Delivery operations
│   ├── driver_analytics.py # Driver performance metrics
│   ├── feedback.py         # Rating & review system
│   ├── chat.py             # AI chatbot endpoints
│   ├── catalog.py          # Browse meals & restaurants
│   └── owner_orders.py     # Restaurant owner operations
├── services/          # Business logic
│   ├── chat_service.py     # Groq AI integration
│   ├── chat_persistence.py # Chat history management
│   └── nutrition_service.py # FatSecret API integration
├── owner_meals/       # Restaurant owner features
│   ├── restaurant.py       # Restaurant management
│   └── service.py          # Menu operations
└── Mood2FoodRecSys/   # Recommendation engine
    ├── Spotify_Auth.py     # Spotify OAuth
    ├── RecSys.py           # Recommendation API
    └── RecSysFunctions.py  # Mood analysis logic
```

### Frontend (Next.js 16)
```
client/app/
├── browse/            # Browse restaurants & meals
├── cart/              # Shopping cart page
├── orders/            # Order history & tracking
├── chat/              # AI chatbot interface
├── driver/            # Driver dashboard & analytics
├── owner/             # Restaurant owner portal
├── profile/           # User profile management
├── recommendations/   # Mood-based suggestions
└── support/           # Customer support
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (via Supabase)
- Spotify Developer Account
- Mapbox API Token
- Groq API Key
- FatSecret API Credentials (optional)

### Backend Setup

1. **Clone the repository**
```bash
cd Project
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
Create a `.env` file:
```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# JWT
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256

# Spotify
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/spotify/callback

# Groq AI
GROQ_API_KEY=your_groq_api_key

# Mapbox
MAPBOX_TOKEN=your_mapbox_token

# FatSecret (optional)
FATSECRET_CLIENT_ID=your_fatsecret_client_id
FATSECRET_CLIENT_SECRET=your_fatsecret_client_secret

# AWS S3 (for image uploads)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
S3_BUCKET_NAME=your_bucket_name
```

4. **Run database migrations**
```bash
alembic upgrade head
```

5. **Start the backend server**
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. **Navigate to client directory**
```bash
cd client
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment variables**
Create a `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
```

4. **Start the development server**
```bash
npm run dev
```

5. **Access the application**
Open [http://localhost:3000](http://localhost:3000)

## 🧪 Testing

### Backend Tests

**Comprehensive test coverage: 86%+ across all modules**

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test suites
pytest tests/test_routers.py -v                    # Core functionality (33 tests)
pytest tests/test_routers_edge_cases.py -v         # Edge cases (44 tests)
pytest tests/test_true_e2e_order_flow.py -v        # E2E order flow (12 tests)
pytest tests/test_recsys.py -v                     # Recommendation system
pytest tests/test_chat.py -v                       # Chatbot functionality
pytest tests/test_nutrition.py -v                  # Nutrition service

# View HTML coverage report
open htmlcov/index.html
```

### Frontend Tests

```bash
cd client

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Watch mode
npm run test:watch
```

### Test Reports
- **Router Tests**: 77/77 passing (100%)
- **E2E Tests**: 12/12 passing (100%)
- **Recommendation System**: 95/99 passing (96%)
- **Overall Coverage**: 86%+

See detailed reports:
- `tests/COMPREHENSIVE_TEST_REPORT.md`
- `tests/E2E_TEST_FINAL_REPORT.md`
- `coverage/COVERAGE_REPORT.md`

## 📡 API Documentation

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token

### Catalog & Browse
- `GET /catalog` - Browse restaurants
- `GET /meals` - List all meals
- `GET /meals/{meal_id}` - Get meal details

### Cart Operations
- `GET /cart` - Get current cart
- `POST /cart/items` - Add item to cart
- `PATCH /cart/items/{item_id}` - Update cart item
- `DELETE /cart/items/{item_id}` - Remove from cart
- `POST /cart/checkout` - Place order

### Order Management
- `GET /orders` - List user orders
- `GET /orders/{order_id}` - Get order details
- `PATCH /orders/{order_id}/cancel` - Cancel order
- `PATCH /orders/{order_id}/accept` - Accept order (staff)
- `PATCH /orders/{order_id}/preparing` - Mark preparing (staff)
- `PATCH /orders/{order_id}/ready` - Mark ready (staff)

### Delivery
- `GET /deliveries/ready` - List available deliveries
- `GET /deliveries/active` - Get active deliveries
- `PATCH /deliveries/{order_id}/accept` - Accept delivery
- `PATCH /deliveries/{order_id}/picked-up` - Mark picked up
- `PATCH /deliveries/{order_id}/deliver` - Complete delivery

### Driver Analytics
- `GET /driver/analytics` - Get driver performance metrics

### Feedback
- `POST /orders/{order_id}/feedback` - Submit feedback
- `GET /orders/{order_id}/feedback` - Get order feedback

### Chat
- `POST /chat/messages` - Send message to AI
- `GET /chat/history` - Get chat history
- `GET /chat/sessions` - List chat sessions
- `POST /chat/sessions` - Create new session
- `DELETE /chat/sessions/{session_id}` - Delete session

### Recommendations
- `POST /recsys/get_recommendations` - Get mood-based recommendations
- `GET /spotify/auth` - Initiate Spotify OAuth
- `GET /spotify/callback` - Spotify OAuth callback

### Restaurant Owner
- `POST /owner/meals` - Create meal
- `PATCH /owner/meals/{meal_id}` - Update meal
- `DELETE /owner/meals/{meal_id}` - Delete meal
- `GET /owner/orders` - List restaurant orders
- `GET /owner/restaurant` - Get restaurant info

## 🔑 Key Technologies

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database & authentication
- **SQLAlchemy** - ORM for database operations
- **Groq AI** - LLM for chatbot and mood analysis
- **Spotipy** - Spotify API integration
- **Boto3** - AWS S3 for image storage
- **HTTPX** - Async HTTP client
- **Pytest** - Testing framework

### Frontend
- **Next.js 16** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Radix UI** - Accessible component primitives
- **Mapbox GL** - Interactive maps
- **React Hook Form** - Form management
- **Zod** - Schema validation
- **Jest** - Testing framework

### External APIs
- **Spotify Web API** - Music listening history
- **Mapbox API** - Routing and geocoding
- **FatSecret API** - Nutrition information
- **Groq API** - AI language model

## 👥 User Roles

### Customer
- Browse restaurants and meals
- Get mood-based recommendations
- Add items to cart and checkout
- Track order status
- Chat with AI assistant
- Submit feedback and ratings

### Restaurant Staff
- Manage menu items
- Accept and process orders
- Update order status
- View order history
- Upload meal images

### Delivery Driver
- View available deliveries
- Accept delivery assignments
- Update delivery status
- Track earnings and analytics
- View delivery history

## 🔒 Security Features

- **JWT Authentication** - Secure token-based auth
- **Role-Based Access Control** - Endpoint protection by user role
- **Password Hashing** - Bcrypt for secure password storage
- **Delivery Code Verification** - 6-digit codes for order completion
- **Session Management** - Secure chat session ownership
- **Input Validation** - Pydantic models for request validation

## 📈 Performance & Scalability

- **Async Operations** - Non-blocking I/O for better performance
- **Database Indexing** - Optimized queries with proper indexes
- **Caching Strategy** - Reduced API calls with smart caching
- **Batch Processing** - Efficient Mapbox matrix API usage
- **Connection Pooling** - Optimized database connections


## 📝 Documentation

- **API Docs**: Visit `/docs` when running the backend
- **Test Reports**: See `tests/` directory for detailed test documentation
- **Migration Guide**: `MIGRATION_GUIDE.md` for database changes
- **ORM Setup**: `ORM_SETUP.md` for database configuration

## 🤝 Contributing

This is a student project developed as part of a Software Engineering course. The team has implemented:

- **Order Management System** - Complete order lifecycle
- **Delivery System** - Driver operations and route optimization
- **Recommendation Engine** - Spotify-based mood analysis
- **AI Chatbot** - Customer support automation
- **Nutrition Integration** - Health-conscious meal information
- **Comprehensive Testing** - 86%+ code coverage

## 📄 License

This project is developed for educational purposes as part of a university course.

---

**Built with ❤️ by the VibeDish Team**
