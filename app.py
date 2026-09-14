from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
import random
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

# Local: SQLite. Railway: add PostgreSQL and Railway provides DATABASE_URL.
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
if not database_url:
    database_url = "sqlite:///qauipsiz.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(180), nullable=False)
    class_name = db.Column(db.String(40))
    age = db.Column(db.Integer)
    linked_student_id = db.Column(db.Integer)


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket = db.Column(db.String(40), unique=True, nullable=False)
    student_id = db.Column(db.Integer)
    student_name = db.Column(db.String(180), nullable=False)
    class_name = db.Column(db.String(40), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="review")
    created_at = db.Column(db.String(40), nullable=False)
    is_guest = db.Column(db.Boolean, nullable=False, default=False)


class MentorMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_user_id = db.Column(db.Integer)
    sender_role = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.String(40), nullable=False)


def create_ticket():
    while True:
        ticket = f"{datetime.now().year}-{random.randint(10000, 99999)}"
        if not Case.query.filter_by(ticket=ticket).first():
            return ticket


def seed_demo_data():
    if User.query.first():
        return

    student = User(
        username="student",
        password_hash=generate_password_hash("student123"),
        role="student",
        full_name="Оқушы",
        class_name="8А",
        age=14,
    )
    db.session.add(student)
    db.session.flush()

    db.session.add(User(
        username="parent",
        password_hash=generate_password_hash("parent123"),
        role="parent",
        full_name="Ата-ана",
        linked_student_id=student.id,
    ))
    db.session.add(User(
        username="teacher",
        password_hash=generate_password_hash("teacher123"),
        role="teacher",
        full_name="Мұғалім",
    ))

    db.session.add(Case(
        ticket=create_ticket(), student_id=student.id, student_name="Оқушы",
        class_name="8А", age=14, category="Кибербуллинг",
        description="Мессенджерде жағымсыз хабарламалар жіберіп жатыр.",
        status="review", created_at=datetime.now().strftime("%Y-%m-%d %H:%M"), is_guest=False,
    ))
    db.session.add(Case(
        ticket=create_ticket(), student_id=student.id, student_name="Оқушы",
        class_name="8А", age=14, category="Мазақтау",
        description="Сыныпта бірнеше рет мазақтады.",
        status="solved", created_at=datetime.now().strftime("%Y-%m-%d %H:%M"), is_guest=False,
    ))
    db.session.commit()


with app.app_context():
    db.create_all()
    if os.environ.get("SEED_DEMO", "1") == "1":
        seed_demo_data()


def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def user_public(user):
    if not user:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "class_name": user.class_name,
        "age": user.age,
        "linked_student_id": user.linked_student_id,
    }


def case_public(c):
    return {
        "id": c.id,
        "ticket": c.ticket,
        "student_id": c.student_id,
        "student_name": c.student_name,
        "class_name": c.class_name,
        "age": c.age,
        "category": c.category,
        "description": c.description,
        "status": c.status,
        "created_at": c.created_at,
        "is_guest": bool(c.is_guest),
    }


def require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify({"ok": False, "error": "Авторизация қажет"}), 401
        return fn(*args, **kwargs)
    return wrapper


@app.get("/")
def index():
    return render_template("index.html", user=current_user())


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "").strip()

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"ok": False, "error": "Логин немесе құпиясөз қате"}), 401
    if role and user.role != role:
        return jsonify({"ok": False, "error": "Таңдалған рөл бұл аккаунтқа сәйкес емес"}), 403

    session["user_id"] = user.id
    return jsonify({"ok": True, "user": user_public(user)})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/me")
def me():
    user = current_user()
    return jsonify({"logged_in": bool(user), "user": user_public(user)})


@app.post("/api/register/student")
def register_student():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    class_name = (data.get("class_name") or "").strip()
    age = data.get("age")

    if not all([username, password, full_name, class_name, age]):
        return jsonify({"ok": False, "error": "Барлық өрісті толтырыңыз"}), 400
    try:
        age = int(age)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Жас дұрыс көрсетілмеген"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"ok": False, "error": "Бұл логин бос емес"}), 409

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role="student",
        full_name=full_name,
        class_name=class_name,
        age=age,
    )
    db.session.add(user)
    db.session.commit()
    session["user_id"] = user.id
    return jsonify({"ok": True})


@app.get("/api/cases")
@require_login
def get_cases():
    user = current_user()
    status = request.args.get("status", "all")
    query = Case.query

    if user.role == "student":
        query = query.filter_by(student_id=user.id)
    elif user.role == "parent":
        if not user.linked_student_id:
            return jsonify([])
        query = query.filter_by(student_id=user.linked_student_id)

    if status in ("review", "solved"):
        query = query.filter_by(status=status)

    rows = query.order_by(Case.id.desc()).all()
    return jsonify([case_public(c) for c in rows])


@app.post("/api/cases")
def create_case():
    data = request.get_json(silent=True) or {}
    user = current_user()
    category = (data.get("category") or data.get("type") or "Басқа").strip()
    description = (data.get("description") or "").strip()

    if user and user.role == "student":
        student_id = user.id
        student_name = user.full_name
        class_name = user.class_name or (data.get("class_name") or "").strip()
        age = user.age or data.get("age")
        is_guest = False
    else:
        student_id = None
        student_name = (data.get("student_name") or "").strip()
        class_name = (data.get("class_name") or "").strip()
        age = data.get("age")
        is_guest = True

    if not all([student_name, class_name, age, category, description]):
        return jsonify({"ok": False, "error": "Барлық міндетті өрісті толтырыңыз"}), 400
    try:
        age = int(age)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Жас дұрыс көрсетілмеген"}), 400

    c = Case(
        ticket=create_ticket(), student_id=student_id, student_name=student_name,
        class_name=class_name, age=age, category=category, description=description,
        status="review", created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        is_guest=is_guest,
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"ok": True, "ticket": c.ticket}), 201


@app.get("/api/stats")
@require_login
def stats():
    user = current_user()
    if user.role == "student":
        return jsonify({"ok": False, "error": "Бұл статистика оқушыға қолжетімсіз"}), 403

    query = Case.query
    if user.role == "parent":
        if not user.linked_student_id:
            return jsonify({"ok": True, "total": 0, "review": 0, "solved": 0})
        query = query.filter_by(student_id=user.linked_student_id)

    return jsonify({
        "ok": True,
        "total": query.count(),
        "review": query.filter_by(status="review").count(),
        "solved": query.filter_by(status="solved").count(),
    })


@app.post("/api/mentor")
@require_login
def mentor_message():
    user = current_user()
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Хабарлама бос болмауы керек"}), 400

    db.session.add(MentorMessage(
        sender_user_id=user.id,
        sender_role=user.role,
        message=message,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    ))
    db.session.commit()
    return jsonify({"ok": True})


QUIZ_BANK = [
    ("Күн сайын әдейі мазақтау, қорлау немесе кемсіту қалай аталады?", ["Буллинг","Жай әзіл","Пікірталас","Сабақ"], 0, "Қайталанатын әдейі қорлау немесе кемсіту — буллинг."),
    ("Интернетте қорлайтын хабарламалар келсе, пайдалы әрекетті таңда.", ["Скриншот жасап, дәлелді сақтау","Парольді жіберу","Қорлаушыны қайта қорлау","Барлығын бірден өшіру"], 0, "Дәлелді сақтау әрі қарай көмек алуға көмектеседі."),
    ("Егер тікелей қауіп төніп тұрса, бірінші кезекте не істеу керек?", ["Қауіпсіз жерге бару","Дауды жалғастыру","Әлеуметтік желіге жазу","Ешкімге айтпау"], 0, "Бірінші орында — өз қауіпсіздігің."),
    ("Қай мәліметті бөтен адамға беруге болмайды?", ["Аккаунт паролі","Сүйікті түс","Сүйікті пән","Хобби"], 0, "Пароль — құпия жеке дерек."),
    ("Күдікті сілтеме келсе не істеген дұрыс?", ["Ашпау және тексеру","Бірден ашу","Пароль енгізу","Достарға тарату"], 0, "Күдікті сілтемені ашпау қауіпсіз."),
    ("Қиын жағдай туралы кімге айтуға болады?", ["Сенетін ересек адамға немесе маманға","Тек бейтаныс адамға","Ешкімге айтуға болмайды","Тек әлеуметтік желіге"], 0, "Сенетін ересек адамнан немесе маманнан көмек сұрауға болады."),
    ("Бейтаныс адам жеке сурет сұраса не істеген дұрыс?", ["Жібермеу және сенімді ересекке айту","Бірден жіберу","Парольмен бірге жіберу","Барлық достарға тарату"], 0, "Жеке материалдарды бейтаныс адамдарға жібермеу керек."),
    ("Жанжал күшейіп бара жатса не істеген дұрыс?", ["Қауіпсіз жерге кетіп, көмек сұрау","Қарсы шабуылдау","Арандатуды жалғастыру","Күліп қарау"], 0, "Қауіпсіз жерге кетіп, көмек сұрау дұрыс."),
    ("Біреу карта дерегін сұраса не істеген дұрыс?", ["Жібермеу және сенімді адаммен тексеру","CVV кодын беру","Парольді де жіберу","Бірден ақша аудару"], 0, "Карта мен құпия деректерді жібермеу керек."),
    ("Қорлаушы аккаунтпен не істеуге болады?", ["Бұғаттау және шағымдану","Парольді жіберу","Үй мекенжайын жазу","Кек алу"], 0, "Бұғаттау және шағымдану қауіпсіз әрекеттердің бірі."),
    ("Мектептегі буллингті байқасаң не істеген дұрыс?", ["Жауапты ересек адамға хабарлау","Қосылып мазақтау","Видеоға түсіріп тарату","Күліп қарау"], 0, "Жауапты ересек адамға хабарлау маңызды."),
    ("Интернетте мекенжайды ашық жариялау дұрыс па?", ["Жоқ, қажетсіз жарияламаған дұрыс","Иә, әрқашан","Тек бейтаныстарға","Парольмен бірге"], 0, "Мекенжай сияқты жеке деректерді қажетсіз жарияламаған дұрыс."),
    ("Екі оқушы төбелесіп жатса, қауіпсіз әрекет қайсы?", ["Ересек адамға хабарлау","Арасына жалғыз кіру","Қосылып кету","Күліп қарау"], 0, "Қауіпсіздік үшін жауапты ересек адамға хабарлаған дұрыс."),
    ("Күшті парольге қайсысы көбірек ұқсайды?", ["Ұзын әрі әртүрлі таңбалары бар пароль","123456","password","Туған жыл"], 0, "Ұзын және әртүрлі таңбалары бар пароль қауіпсізірек."),
    ("Қорқыту хабарламасы келсе не істеген дұрыс?", ["Сақтап, сенімді ересекке көрсету","Бірден өшіру және жасыру","Кек алу","Кездесуге жалғыз бару"], 0, "Хабарламаны дәлел ретінде сақтап, көмек сұраған дұрыс."),
]


def shuffled_question(item):
    stem, options, correct, explanation = item
    pairs = list(enumerate(options))
    random.shuffle(pairs)
    new_options = [p[1] for p in pairs]
    new_correct = next(i for i, p in enumerate(pairs) if p[0] == correct)
    return {"question": stem, "options": new_options, "correct": new_correct, "explanation": explanation}


@app.get("/api/quiz")
def quiz():
    try:
        count = int(request.args.get("count", 10))
    except (TypeError, ValueError):
        count = 10
    count = max(5, min(count, min(10, len(QUIZ_BANK))))
    chosen = random.sample(QUIZ_BANK, count)
    return jsonify({"ok": True, "questions": [shuffled_question(q) for q in chosen]})


AI_SYSTEM_PROMPT = """Сен «Қауіпсіз Қадам» платформасындағы жасөспірімдерге арналған қауіпсіздік көмекшісісің.
Тек сауатты, табиғи қазақ тілінде жауап бер. Қырғызша, орысша немесе ағылшынша сөздерді араластырма.
Жауап қысқа, түсінікті және әрекетке бағытталған болсын. Қауіпті жағдайда қауіпсіз жерге баруды және сенімді ересек адамға хабарлауды ұсын.
Заңгер, дәрігер немесе полиция қызметкері ретінде көрсетпе. Нақты қауіп болса, жедел көмек қызметіне немесе сенімді ересек адамға жүгінуді ұсын.
Ішкі ойлау процесін, reasoning немесе Thinking мәтінін ешқашан көрсетпе."""


def ai_config():
    return {
        "base_url": os.environ.get("AI_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
        "model": os.environ.get("AI_MODEL", "hf.co/mradermacher/Qwen3.5-4B-Kazakh-GGUF:Q4_K_M"),
        "timeout": int(os.environ.get("AI_TIMEOUT", "90")),
        "enabled": os.environ.get("AI_ENABLED", "1") == "1",
    }


def ask_ollama(message):
    cfg = ai_config()
    if not cfg["enabled"]:
        raise RuntimeError("AI disabled")

    payload = {
        "model": cfg["model"],
        "stream": False,
        "think": False,
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        "options": {"temperature": 0.3},
    }
    response = requests.post(f'{cfg["base_url"]}/api/chat', json=payload, timeout=cfg["timeout"])
    response.raise_for_status()
    data = response.json()
    text = ((data.get("message") or {}).get("content") or "").strip()
    if not text:
        raise RuntimeError("AI returned an empty response")
    return text


@app.post("/api/ai")
def ai():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Жағдайды жазыңыз"}), 400

    try:
        text = ask_ollama(message)
        return jsonify({
            "ok": True,
            "category": "AI қауіпсіздік навигаторы",
            "answer_text": text,
            "disclaimer": "AI жауабы ақпараттық көмек үшін берілген. Тікелей қауіп болса, сенімді ересек адамға немесе жедел көмек қызметіне хабарласыңыз.",
        })
    except requests.exceptions.ConnectionError:
        return jsonify({"ok": False, "error": "AI серверіне қосылу мүмкін болмады. Ollama немесе AI_BASE_URL параметрін тексеріңіз."}), 503
    except requests.exceptions.Timeout:
        return jsonify({"ok": False, "error": "AI жауабы тым ұзақ күттірді. Қайта көріңіз."}), 504
    except Exception as exc:
        app.logger.exception("AI request failed")
        return jsonify({"ok": False, "error": f"AI қатесі: {str(exc)[:160]}"}), 502


@app.get("/api/ai/status")
def ai_status():
    cfg = ai_config()
    if not cfg["enabled"]:
        return jsonify({"ok": True, "enabled": False, "reachable": False, "model": cfg["model"]})
    try:
        r = requests.get(f'{cfg["base_url"]}/api/tags', timeout=5)
        return jsonify({"ok": True, "enabled": True, "reachable": r.ok, "model": cfg["model"]})
    except requests.RequestException:
        return jsonify({"ok": True, "enabled": True, "reachable": False, "model": cfg["model"]})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "database": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
