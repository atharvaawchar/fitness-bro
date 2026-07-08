"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    FITNESS BRO - AI Fitness Buddy                          ║
║                    Backend: Flask + IBM Watsonx.ai                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

AGENT_INSTRUCTIONS
══════════════════════════════════════════════════════════════════════════════
Customize the AI Fitness Coach behavior below. These instructions are injected
into every IBM Granite model request as the system prompt.

PERSONALITY & TONE:
  - Act as "Fitness Bro" — a professional yet friendly personal trainer.
  - Be motivating, encouraging, and scientifically accurate.
  - Keep responses concise, structured, and actionable.
  - Use emojis sparingly to add energy (💪 🏋️ 🥗 🔥).

COACHING STYLE:
  - Progressive overload principle for strength training.
  - HIIT + steady-state cardio for weight loss.
  - Compound movements first, isolation last.
  - Rest and recovery are as important as training.

WORKOUT SPECIALIZATION:
  - Home workouts: bodyweight, resistance bands, dumbbells.
  - Gym routines: full machine + free-weight programs.
  - Strength training: powerlifting, hypertrophy, endurance.
  - Weight loss: caloric deficit strategies, fat-burning cardio.
  - Muscle building: progressive overload, protein timing.
  - Flexibility: yoga flows, dynamic + static stretching.

NUTRITION APPROACH:
  - Balanced macronutrients: protein 30%, carbs 40%, fats 30%.
  - Whole foods first; supplements as support, not replacement.
  - Caloric goals: deficit for loss (-300 to -500 kcal), surplus for gain (+200 to +400 kcal).
  - Hydration: minimum 8 glasses/day; more on training days.
  - Avoid recommending extreme diets (< 1200 kcal for women, < 1500 kcal for men).

SAFETY GUIDELINES:
  - Always recommend warm-up (5–10 min) before workouts.
  - Always recommend cool-down and stretching after workouts.
  - Advise consulting a doctor before starting if user has medical conditions.
  - Never recommend unsafe supplements or performance-enhancing drugs.
  - Provide beginner-friendly alternatives for every advanced exercise.
  - Flag any extreme calorie restrictions as unsafe.

MOTIVATION TECHNIQUES:
  - Celebrate small wins and milestones.
  - Use positive reinforcement, not shame or guilt.
  - Suggest habit-stacking strategies (pair workouts with existing habits).
  - Remind users: "Consistency beats perfection every time."
  - Provide weekly challenges to keep engagement high.

RESPONSE FORMAT:
  - Use markdown-style formatting in chat (bold, bullet points, numbered lists).
  - For workout plans: always include sets, reps, rest time, and form tips.
  - For meal plans: include calories estimate and prep time when possible.
  - Keep motivational messages brief and punchy.
══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import sqlite3
import datetime
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv

# IBM Watsonx.ai SDK
try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    IBM_WATSONX_AVAILABLE = True
except ImportError:
    IBM_WATSONX_AVAILABLE = False
    print("WARNING: ibm-watsonx-ai not installed. Install with: pip install ibm-watsonx-ai")

load_dotenv()

# ─────────────────────────────────────────────
#  Flask App Initialization
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fitness-bro-secret-key-2024")

# ─────────────────────────────────────────────
#  IBM Watsonx.ai Configuration
# ─────────────────────────────────────────────
IBM_API_KEY    = os.getenv("IBM_API_KEY", "")
IBM_PROJECT_ID = os.getenv("IBM_PROJECT_ID", "")
IBM_URL        = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_MODEL  = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-1-8b-base")

# ─────────────────────────────────────────────
#  AGENT SYSTEM PROMPT  (edit here to customize AI behavior)
# ─────────────────────────────────────────────
AGENT_SYSTEM_PROMPT = """You are Fitness Bro — a professional AI fitness coach and health mentor powered by IBM Granite.

Your personality:
- Energetic, motivating, and friendly personal trainer 💪
- Scientifically accurate and evidence-based advisor
- Beginner-friendly yet knowledgeable enough for advanced athletes
- Empathetic health mentor who celebrates every small victory

Your expertise:
- Personalized workout programming (home, gym, strength, cardio, flexibility)
- Nutrition guidance (meal planning, macros, hydration, healthy recipes)
- BMI analysis and body composition improvement
- Habit formation, consistency strategies, and mindset coaching
- Progressive overload, periodization, and recovery optimization

Safety rules you ALWAYS follow:
1. Recommend warm-up before and cool-down after every workout
2. Suggest doctor consultation for users with medical conditions
3. Never recommend extreme caloric restriction (< 1200 kcal women, < 1500 kcal men)
4. Provide beginner alternatives for every advanced exercise
5. Remind users: rest and recovery are part of training

Formatting rules:
- Use clear headings, bullet points, and numbered lists
- For workouts: always specify sets × reps, rest periods, and form tips
- For meals: include estimated calories and prep time
- Keep motivational messages short, punchy, and genuine
- Respond in the same language the user writes in

Remember: You are their personal Fitness Bro — professional, supportive, and always in their corner! 🔥"""

# ─────────────────────────────────────────────
#  Watsonx.ai Model Initialization
# ─────────────────────────────────────────────
watsonx_model = None
watsonx_error  = None   # stores the last init/query error for diagnostics

def init_watsonx():
    global watsonx_model, watsonx_error
    if not IBM_WATSONX_AVAILABLE:
        watsonx_error = "ibm-watsonx-ai SDK not installed"
        return False
    if not IBM_API_KEY or not IBM_PROJECT_ID:
        watsonx_error = "IBM_API_KEY or IBM_PROJECT_ID missing in .env"
        print(f"WARNING: {watsonx_error}")
        return False
    try:
        credentials = Credentials(url=IBM_URL, api_key=IBM_API_KEY)
        params = {
            GenParams.MAX_NEW_TOKENS: 1024,
            GenParams.MIN_NEW_TOKENS: 10,
            GenParams.TEMPERATURE: 0.7,
            GenParams.TOP_P: 0.9,
            GenParams.REPETITION_PENALTY: 1.1,
        }
        model = ModelInference(
            model_id=GRANITE_MODEL,
            params=params,
            credentials=credentials,
            project_id=IBM_PROJECT_ID,
        )
        # Fire a minimal test call to confirm auth + model access work
        test = model.generate_text(prompt="Hi")
        watsonx_model = model
        watsonx_error = None
        print(f"IBM Watsonx.ai connected -- Model: {GRANITE_MODEL}")
        return True
    except Exception as e:
        watsonx_error = str(e)
        print(f"ERROR: Watsonx.ai init failed: {e}")
        return False

def query_granite(prompt: str, system_context: str = "") -> str:
    """Send prompt to IBM Granite model and return response."""
    system = system_context if system_context else AGENT_SYSTEM_PROMPT
    # Plain prompt format compatible with granite-3-1-8b-base and llama models
    full_prompt = f"{system}\n\nUser: {prompt}\n\nAssistant:"

    if watsonx_model:
        try:
            response = watsonx_model.generate_text(prompt=full_prompt)
            return response.strip()
        except Exception as e:
            global watsonx_error
            watsonx_error = str(e)
            print(f"ERROR: Granite query failed: {e}")
            return f"Sorry, I hit an error talking to IBM Granite: {str(e)}"
    else:
        # Fallback demo response when Watsonx is not available
        return generate_fallback_response(prompt)

def generate_fallback_response(prompt: str) -> str:
    """Intelligent fallback when IBM Watsonx.ai is not available."""
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["workout", "exercise", "training", "gym"]):
        return """💪 **Your Personalized Workout Plan**

**Warm-up (5–10 min):**
- Jumping jacks × 30
- Arm circles × 20 each direction
- Hip rotations × 15

**Main Workout:**
1. **Push-ups** — 3 × 12 reps | Rest: 60s | *Keep core tight, full range of motion*
2. **Squats** — 3 × 15 reps | Rest: 60s | *Knees track over toes*
3. **Plank** — 3 × 30s hold | Rest: 45s | *Straight line head to heels*
4. **Lunges** — 3 × 10 each leg | Rest: 60s | *Step forward, knee at 90°*
5. **Mountain Climbers** — 3 × 20 reps | Rest: 45s | *Drive knees to chest*

**Cool-down (5 min):** Static stretching for all major muscle groups.

🔥 *Consistency beats perfection. Show up every day!*

> ⚠️ *Connect IBM Watsonx.ai in your .env file for fully personalized AI responses.*"""

    elif any(w in prompt_lower for w in ["meal", "food", "diet", "nutrition", "eat"]):
        return """🥗 **Balanced Daily Meal Plan**

**🌅 Breakfast (~400 kcal | 10 min prep)**
- Oatmeal with banana and almonds
- 2 boiled eggs
- Green tea or black coffee

**☀️ Lunch (~550 kcal | 15 min prep)**
- Grilled chicken breast (150g)
- Brown rice (1 cup cooked)
- Mixed salad with olive oil dressing

**🌙 Dinner (~500 kcal | 20 min prep)**
- Baked salmon or tofu (150g)
- Steamed broccoli and sweet potato
- Lemon water

**🍎 Snacks (~200 kcal)**
- Greek yogurt with berries
- Handful of mixed nuts

**💧 Hydration:** 8–10 glasses of water daily

> ⚠️ *Connect IBM Watsonx.ai for goal-specific nutrition plans.*"""

    elif any(w in prompt_lower for w in ["bmi", "weight", "height", "body"]):
        return """📊 **BMI Analysis**

Your BMI has been calculated. Here are general fitness recommendations:

**If Underweight (BMI < 18.5):**
- Focus on strength training to build muscle mass
- Increase caloric intake with nutrient-dense foods
- Eat 5–6 smaller meals throughout the day

**If Normal Weight (BMI 18.5–24.9):**
- Maintain current activity levels
- Focus on body composition (muscle vs fat ratio)
- Balanced cardio and strength training

**If Overweight (BMI 25–29.9):**
- Create a moderate caloric deficit (300–500 kcal/day)
- Combine cardio (3–4×/week) with strength training (2–3×/week)
- Prioritize sleep and stress management

> ⚠️ *Configure IBM Watsonx.ai for personalized BMI-based recommendations.*"""

    else:
        return """👋 **Hey there, I'm Fitness Bro!**

I'm your AI-powered personal fitness coach. Here's what I can help you with:

💪 **Workouts** — Personalized plans for home or gym
🥗 **Nutrition** — Meal plans aligned with your goals
📊 **BMI Analysis** — Body composition insights
🎯 **Habit Tracking** — Build consistency that lasts
📈 **Progress** — Track your fitness journey

**Quick tips for today:**
1. Stay hydrated — drink water before, during, and after workouts
2. Prioritize sleep — 7–9 hours for optimal recovery
3. Remember: every rep counts, every healthy meal matters!

🔥 *What fitness goal can I help you crush today?*

> ⚠️ *Add your IBM API credentials to .env for full AI-powered responses.*"""

# ─────────────────────────────────────────────
#  Database Setup (SQLite)
# ─────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "fitness_bro.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER,
            gender TEXT,
            height_cm REAL,
            weight_kg REAL,
            fitness_level TEXT DEFAULT 'beginner',
            fitness_goal TEXT DEFAULT 'general_fitness',
            equipment TEXT DEFAULT 'none',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            date TEXT NOT NULL,
            workout_done INTEGER DEFAULT 0,
            water_glasses INTEGER DEFAULT 0,
            sleep_hours REAL DEFAULT 0,
            healthy_meals INTEGER DEFAULT 0,
            steps INTEGER DEFAULT 0,
            notes TEXT,
            UNIQUE(user_id, date)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS bmi_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            date TEXT NOT NULL,
            height_cm REAL,
            weight_kg REAL,
            bmi REAL,
            category TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            date TEXT NOT NULL,
            plan_json TEXT,
            completed INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed default user if none exists
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO users (name, email, age, gender, height_cm, weight_kg, fitness_level, fitness_goal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Fitness Bro User", "user@fitnessbro.ai", 25, "prefer_not_to_say", 170.0, 70.0, "beginner", "general_fitness"))

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
#  Utility Helpers
# ─────────────────────────────────────────────
def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    if height_cm <= 0 or weight_kg <= 0:
        return {"bmi": 0, "category": "Invalid", "color": "gray"}
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)
    if bmi < 18.5:
        category, color = "Underweight", "#3b82f6"
    elif bmi < 25:
        category, color = "Normal Weight", "#22c55e"
    elif bmi < 30:
        category, color = "Overweight", "#f59e0b"
    else:
        category, color = "Obese", "#ef4444"
    return {"bmi": bmi, "category": category, "color": color}

def get_streak(user_id: int) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT date FROM habits WHERE user_id=? AND workout_done=1
        ORDER BY date DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        return 0
    streak = 0
    today = datetime.date.today()
    for i, row in enumerate(rows):
        expected = today - datetime.timedelta(days=i)
        if row["date"] == str(expected):
            streak += 1
        else:
            break
    return streak

# ─────────────────────────────────────────────
#  Frontend Routes
# ─────────────────────────────────────────────
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/chat")
def chat_page():
    return render_template("chat.html")

@app.route("/workout")
def workout_page():
    return render_template("workout.html")

@app.route("/meal")
def meal_page():
    return render_template("meal.html")

@app.route("/bmi")
def bmi_page():
    return render_template("bmi.html")

@app.route("/habits")
def habits_page():
    return render_template("habits.html")

@app.route("/progress")
def progress_page():
    return render_template("progress.html")

@app.route("/profile")
def profile_page():
    return render_template("profile.html")

# ─────────────────────────────────────────────
#  REST API Endpoints
# ─────────────────────────────────────────────

# — AI Chat —
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Fetch recent chat history for context
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT role, content FROM chat_history
        WHERE user_id=1 ORDER BY id DESC LIMIT 10
    """)
    history = list(reversed(c.fetchall()))

    # Build context-aware prompt
    context_lines = [f"{h['role'].upper()}: {h['content']}" for h in history]
    context_block = "\n".join(context_lines)
    prompt = f"Conversation history:\n{context_block}\n\nUSER: {user_message}\n\nRespond as Fitness Bro:"

    ai_response = query_granite(prompt)

    # Save to DB
    c.execute("INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)", (1, "user", user_message))
    c.execute("INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)", (1, "assistant", ai_response))
    conn.commit()
    conn.close()

    return jsonify({"response": ai_response, "timestamp": datetime.datetime.now().isoformat()})

# — Workout Generation —
@app.route("/api/workout/generate", methods=["POST"])
def api_generate_workout():
    data = request.get_json()
    age       = data.get("age", 25)
    gender    = data.get("gender", "prefer_not_to_say")
    height    = data.get("height", 170)
    weight    = data.get("weight", 70)
    goal      = data.get("goal", "general_fitness")
    level     = data.get("level", "beginner")
    time_min  = data.get("time_available", 45)
    equipment = data.get("equipment", "none")

    prompt = f"""Create a complete personalized workout plan for:
- Age: {age} | Gender: {gender}
- Height: {height}cm | Weight: {weight}kg
- Goal: {goal} | Fitness Level: {level}
- Time Available: {time_min} minutes
- Equipment: {equipment}

Generate a structured plan with:
1. Warm-up (5 min)
2. Main workout (with exercise name, sets × reps/duration, rest time, form tip)
3. Cool-down (5 min)
4. Safety notes and progression tips

Format each exercise clearly with sets, reps, rest, and coaching cues."""

    plan = query_granite(prompt)

    # Save to DB
    conn = get_db()
    c = conn.cursor()
    today = str(datetime.date.today())
    c.execute("""
        INSERT INTO workouts (user_id, date, plan_json)
        VALUES (?, ?, ?)
    """, (1, today, json.dumps({"plan": plan, "params": data})))
    conn.commit()
    conn.close()

    return jsonify({"plan": plan, "generated_at": datetime.datetime.now().isoformat()})

# — Meal Plan Generation —
@app.route("/api/meal/generate", methods=["POST"])
def api_generate_meal():
    data = request.get_json()
    goal         = data.get("goal", "general_fitness")
    calories     = data.get("calories", 2000)
    diet_type    = data.get("diet_type", "balanced")
    allergies    = data.get("allergies", "none")
    meals_per_day = data.get("meals_per_day", 3)

    prompt = f"""Create a detailed daily meal plan for:
- Fitness Goal: {goal}
- Daily Calorie Target: {calories} kcal
- Diet Type: {diet_type}
- Food Allergies/Restrictions: {allergies}
- Meals Per Day: {meals_per_day}

Include for each meal:
- Meal name and key ingredients
- Estimated calories
- Approximate prep time
- Macro breakdown (protein/carbs/fats)

Also include:
- 2 healthy snack options
- Daily hydration recommendation
- Meal prep tips for busy schedules"""

    meal_plan = query_granite(prompt)
    return jsonify({"meal_plan": meal_plan, "generated_at": datetime.datetime.now().isoformat()})

# — BMI Calculator —
@app.route("/api/bmi/calculate", methods=["POST"])
def api_calculate_bmi():
    data = request.get_json()
    weight_kg  = float(data.get("weight", 0))
    height_cm  = float(data.get("height", 0))
    age        = data.get("age", 25)
    gender     = data.get("gender", "prefer_not_to_say")
    goal       = data.get("goal", "general_fitness")

    result = calculate_bmi(weight_kg, height_cm)

    prompt = f"""A person with the following profile:
- Age: {age} | Gender: {gender}
- Height: {height_cm}cm | Weight: {weight_kg}kg
- BMI: {result['bmi']} ({result['category']})
- Fitness Goal: {goal}

Provide:
1. BMI interpretation and what it means for their health
2. 3 specific actionable fitness recommendations
3. A simple 4-week plan outline to improve their BMI/body composition
4. Motivational closing message"""

    ai_recommendations = query_granite(prompt)

    # Save BMI history
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO bmi_history (user_id, date, height_cm, weight_kg, bmi, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, str(datetime.date.today()), height_cm, weight_kg, result["bmi"], result["category"]))
    conn.commit()
    conn.close()

    return jsonify({
        "bmi": result["bmi"],
        "category": result["category"],
        "color": result["color"],
        "recommendations": ai_recommendations
    })

# — Habit Tracker —
@app.route("/api/habits/today", methods=["GET"])
def api_get_habits():
    today = str(datetime.date.today())
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM habits WHERE user_id=1 AND date=?", (today,))
    row = c.fetchone()

    if not row:
        c.execute("""
            INSERT INTO habits (user_id, date) VALUES (1, ?)
        """, (today,))
        conn.commit()
        c.execute("SELECT * FROM habits WHERE user_id=1 AND date=?", (today,))
        row = c.fetchone()

    streak = get_streak(1)
    conn.close()

    return jsonify({
        "date": today,
        "workout_done": bool(row["workout_done"]),
        "water_glasses": row["water_glasses"],
        "sleep_hours": row["sleep_hours"],
        "healthy_meals": row["healthy_meals"],
        "steps": row["steps"],
        "notes": row["notes"] or "",
        "streak": streak
    })

@app.route("/api/habits/update", methods=["POST"])
def api_update_habits():
    data = request.get_json()
    today = str(datetime.date.today())
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO habits (user_id, date, workout_done, water_glasses, sleep_hours, healthy_meals, steps, notes)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET
            workout_done  = excluded.workout_done,
            water_glasses = excluded.water_glasses,
            sleep_hours   = excluded.sleep_hours,
            healthy_meals = excluded.healthy_meals,
            steps         = excluded.steps,
            notes         = excluded.notes
    """, (
        today,
        int(data.get("workout_done", 0)),
        int(data.get("water_glasses", 0)),
        float(data.get("sleep_hours", 0)),
        int(data.get("healthy_meals", 0)),
        int(data.get("steps", 0)),
        data.get("notes", "")
    ))
    conn.commit()
    streak = get_streak(1)
    conn.close()
    return jsonify({"success": True, "streak": streak})

# — Progress Dashboard —
@app.route("/api/progress", methods=["GET"])
def api_get_progress():
    conn = get_db()
    c = conn.cursor()

    # Last 30 days habits
    c.execute("""
        SELECT date, workout_done, water_glasses, sleep_hours, healthy_meals, steps
        FROM habits WHERE user_id=1
        ORDER BY date DESC LIMIT 30
    """)
    habits = [dict(r) for r in c.fetchall()]

    # BMI history
    c.execute("""
        SELECT date, bmi, category FROM bmi_history
        WHERE user_id=1 ORDER BY date DESC LIMIT 10
    """)
    bmi_history = [dict(r) for r in c.fetchall()]

    # Workout count
    c.execute("SELECT COUNT(*) as count FROM workouts WHERE user_id=1")
    workout_count = c.fetchone()["count"]

    # Total workouts done
    c.execute("SELECT COUNT(*) as count FROM habits WHERE user_id=1 AND workout_done=1")
    workouts_done = c.fetchone()["count"]

    streak = get_streak(1)
    conn.close()

    return jsonify({
        "habits_history": habits,
        "bmi_history": bmi_history,
        "total_workouts_generated": workout_count,
        "total_workouts_completed": workouts_done,
        "current_streak": streak
    })

# — User Profile —
@app.route("/api/profile", methods=["GET"])
def api_get_profile():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=1")
    user = c.fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(dict(user))

@app.route("/api/profile", methods=["POST"])
def api_update_profile():
    data = request.get_json()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE users SET
            name=?, age=?, gender=?, height_cm=?, weight_kg=?,
            fitness_level=?, fitness_goal=?, equipment=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=1
    """, (
        data.get("name", ""),
        data.get("age", 25),
        data.get("gender", "prefer_not_to_say"),
        data.get("height_cm", 170),
        data.get("weight_kg", 70),
        data.get("fitness_level", "beginner"),
        data.get("fitness_goal", "general_fitness"),
        data.get("equipment", "none")
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Profile updated successfully!"})

# — Chat History —
@app.route("/api/chat/history", methods=["GET"])
def api_chat_history():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT role, content, timestamp FROM chat_history
        WHERE user_id=1 ORDER BY id DESC LIMIT 50
    """)
    history = list(reversed([dict(r) for r in c.fetchall()]))
    conn.close()
    return jsonify({"history": history})

@app.route("/api/chat/clear", methods=["DELETE"])
def api_clear_chat():
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE user_id=1")
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# — Health Check —
@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "healthy",
        "app": "Fitness Bro",
        "version": "1.0.0",
        "ibm_watsonx_configured": bool(IBM_API_KEY and IBM_PROJECT_ID),
        "ibm_watsonx_connected": watsonx_model is not None,   # TRUE only when model is live
        "ibm_watsonx_sdk": IBM_WATSONX_AVAILABLE,
        "ibm_watsonx_error": watsonx_error,                   # shows exact error if any
        "model": GRANITE_MODEL,
        "timestamp": datetime.datetime.now().isoformat()
    })

# ─────────────────────────────────────────────
#  App Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    init_watsonx()
    print("🏋️  Fitness Bro starting on http://localhost:5000")
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true", port=5000, host="0.0.0.0")
