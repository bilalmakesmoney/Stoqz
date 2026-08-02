# RetailPilot AI – Setup Instructions

## Prerequisites

* Python 3.11+
* Node.js 18+
* npm

---

## Backend Setup

1. Navigate to the backend folder:

```bash
cd backend
```

2. Create and activate a virtual environment:

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install the required Python packages:

```bash
pip install fastapi
pip install uvicorn
pip install sqlalchemy
pip install pandas
pip install numpy
pip install scikit-learn
pip install xgboost
pip install joblib
pip install python-multipart
pip install pydantic
pip install openpyxl
pip install python-dotenv
```

Or install everything at once:

```bash
pip install fastapi uvicorn sqlalchemy pandas numpy scikit-learn xgboost joblib python-multipart pydantic openpyxl python-dotenv
```

4. Run the backend:

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```
http://localhost:8000
```

---

## Frontend Setup

Navigate to the frontend folder:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

If required, install these packages:

```bash
npm install axios
npm install recharts
npm install framer-motion
npm install lucide-react
npm install @tabler/icons-react
```

Run the frontend:

```bash
npm run dev
```

Frontend runs at:

```
http://localhost:3000
```

---

## AI & Development Tools Used

This project was built using the following tools:

* ChatGPT (OpenAI) — architecture planning, debugging, backend development assistance, frontend development assistance, and code generation.
* Antigravity — AI-powered coding assistant used throughout development for implementation and rapid iteration.

---

## Technologies Used

### Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Axios
* Framer Motion
* Recharts
* Lucide React
* Tabler Icons

### Backend

* FastAPI
* SQLAlchemy
* Pandas
* NumPy
* Scikit-learn
* XGBoost
* Joblib
* Pydantic

### Database

* SQLite

### Machine Learning

* XGBoost Regression
* Feature Engineering
* Inventory Recommendation Engine
* Demand Forecasting

---

Thank you for reviewing RetailPilot AI!
