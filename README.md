# 🏋️ Fitness Bro — AI-Powered Fitness Buddy

> **Hackathon-ready** web application powered by **IBM Watsonx.ai** with **IBM Granite** foundation models.

[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![IBM Watsonx](https://img.shields.io/badge/IBM-Watsonx.ai-1261FE)](https://www.ibm.com/watsonx)
[![IBM Granite](https://img.shields.io/badge/IBM-Granite%20AI-purple)](https://www.ibm.com/granite)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Fitness Coach** | Real-time chat powered by IBM Granite via Watsonx.ai |
| 💪 **Workout Planner** | Personalized plans (home/gym, all levels, any goal) |
| 🥗 **Meal Planner** | Goal-based nutrition plans with macros |
| 📊 **BMI Calculator** | BMI analysis + AI fitness recommendations |
| ✅ **Habit Tracker** | Daily streaks, achievements, progress scoring |
| 📈 **Progress Dashboard** | Activity heatmap, charts, habit logs |
| 👤 **User Profile** | Personal details, goals, equipment preferences |
| 🌙 **Dark Mode** | Full dark/light theme toggle |
| 📱 **Responsive** | Mobile + desktop optimized |

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd fitness_bro
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure IBM Watsonx.ai

```bash
cp .env.example .env
```

Edit `.env` with your IBM Cloud credentials:

```env
IBM_API_KEY=your_ibm_cloud_api_key_here
IBM_PROJECT_ID=your_watsonx_project_id_here
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
FLASK_SECRET_KEY=your-random-secret-key
```

### 3. Run the App

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

> ✅ The app works **without IBM credentials** using intelligent fallback responses.  
> 🤖 Add credentials for **full IBM Granite AI** responses.

---

## 🧠 IBM Watsonx.ai Setup

### Step 1 — Create IBM Cloud Account
1. Go to [cloud.ibm.com](https://cloud.ibm.com) → Sign up for **Lite (free)** account
2. Navigate to **IAM → API Keys** → Create API key → copy it

### Step 2 — Create Watsonx.ai Project
1. Go to [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
2. Click **New Project** → choose **Create an empty project**
3. Copy your **Project ID** from project settings

### Step 3 — Configure Granite Model
The default model is `ibm/granite-13b-instruct-v2`.  
Alternative models available:
- `ibm/granite-3-8b-instruct` — Faster, lighter
- `ibm/granite-20b-multilingual` — Multi-language support

---

## 🤖 Customizing the AI Coach

The `AGENT_SYSTEM_PROMPT` in [`app.py`](app.py) is fully customizable.  
Look for the `AGENT_INSTRUCTIONS` section at the top of the file:

```python
AGENT_SYSTEM_PROMPT = """You are Fitness Bro — ...
# Edit this block to change AI personality, coaching style,
# nutrition approach, safety rules, and response format.
"""
```

**Customizable parameters:**
- 🎭 **Personality** — tone, communication style
- 🏋️ **Workout specialization** — focus areas, methodologies
- 🥗 **Nutrition approach** — dietary philosophies, caloric guidelines
- ⚠️ **Safety rules** — hard limits and medical disclaimers
- 💡 **Motivation style** — encouragement techniques
- 📝 **Response format** — structure, length, use of lists/emojis

---

## 📁 Project Structure

```
fitness_bro/
├── app.py                    # Flask backend + IBM Watsonx.ai integration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── database/
│   └── fitness_bro.db        # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── styles.css        # Full stylesheet (dark mode, responsive)
│   └── js/
│       └── main.js           # Theme toggle, sidebar, utilities
└── templates/
    ├── base.html             # Base layout (sidebar, header, theme)
    ├── dashboard.html        # Home dashboard
    ├── chat.html             # AI fitness coach chat
    ├── workout.html          # Workout planner
    ├── meal.html             # Meal planner
    ├── bmi.html              # BMI calculator
    ├── habits.html           # Habit tracker
    ├── progress.html         # Progress dashboard
    └── profile.html          # User profile
```

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message to AI coach |
| `GET`  | `/api/chat/history` | Get chat history |
| `DELETE` | `/api/chat/clear` | Clear chat |
| `POST` | `/api/workout/generate` | Generate workout plan |
| `POST` | `/api/meal/generate` | Generate meal plan |
| `POST` | `/api/bmi/calculate` | Calculate BMI + AI recs |
| `GET`  | `/api/habits/today` | Get today's habits |
| `POST` | `/api/habits/update` | Update habits |
| `GET`  | `/api/progress` | Get progress data |
| `GET`  | `/api/profile` | Get user profile |
| `POST` | `/api/profile` | Update profile |
| `GET`  | `/api/health` | App health check |

### Example: Chat API

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Give me a beginner workout for today"}'
```

### Example: Workout Generation

```bash
curl -X POST http://localhost:5000/api/workout/generate \
  -H "Content-Type: application/json" \
  -d '{
    "age": 25,
    "gender": "male",
    "height": 175,
    "weight": 75,
    "goal": "muscle_building",
    "level": "intermediate",
    "time_available": 60,
    "equipment": "dumbbells"
  }'
```

---

## ☁️ IBM Cloud Deployment

### Deploy to IBM Cloud Foundry

```bash
# Install IBM Cloud CLI
# Login
ibmcloud login

# Create manifest.yml in fitness_bro/
cat > manifest.yml << EOF
applications:
  - name: fitness-bro
    memory: 512M
    instances: 1
    buildpacks:
      - python_buildpack
    command: gunicorn app:app --bind 0.0.0.0:$PORT
EOF

# Set environment variables
ibmcloud cf set-env fitness-bro IBM_API_KEY "your_key"
ibmcloud cf set-env fitness-bro IBM_PROJECT_ID "your_project_id"

# Push
ibmcloud cf push
```

### Deploy to IBM Code Engine

```bash
# Build and push container
docker build -t fitness-bro .
ibmcloud ce application create --name fitness-bro \
  --image your-registry/fitness-bro \
  --env IBM_API_KEY=your_key \
  --env IBM_PROJECT_ID=your_project_id
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3, JavaScript ES6+, Bootstrap 5 |
| **Backend** | Python 3.9+, Flask 3.0 |
| **AI Engine** | IBM Watsonx.ai, IBM Granite Foundation Models |
| **Database** | SQLite (local) / IBM Cloud Databases (production) |
| **Cloud** | IBM Cloud Lite (free tier) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the app and test all pages
5. Submit a pull request

---

## ⚠️ Safety Disclaimer

This application provides **general fitness information only**.  
Always consult a qualified healthcare professional before starting any new exercise or nutrition program.

---

## 📄 License

MIT License — Built for IBM Granite AI Hackathon 🏆

---

*Powered by IBM Granite AI via IBM Watsonx.ai* 🧠
