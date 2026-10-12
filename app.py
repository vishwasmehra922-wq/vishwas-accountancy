import json
import os
import re
import secrets
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from jinja2 import DictLoader
from werkzeug.security import check_password_hash, generate_password_hash

from chapters import CHAPTERS
from quizzes import QUIZZES
from templates_html import TEMPLATES

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.jinja_loader = DictLoader(TEMPLATES)

DB_PATH = os.environ.get("DB_PATH", "students.db")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.@+\-]{4,120}$")

SECTIONS = [
    ("introduction", "Chapter Introduction"),
    ("theory", "Theory"),
    ("definitions", "Important Definitions"),
    ("formulas", "Important Formulas"),
    ("numericals", "Solved Numerical Questions"),
    ("short", "Short Answer Questions"),
    ("long", "Long Answer Questions"),
    ("mcq", "MCQ"),
    ("exam", "Exam-oriented Important Questions"),
    ("revision", "Revision Notes"),
]


# ---------------- Database ----------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            class_level TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quiz_id TEXT NOT NULL,
            answers TEXT NOT NULL,
            total INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            wrong INTEGER NOT NULL,
            unanswered INTEGER NOT NULL,
            score REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()


init_db()


# ---------------- Security helpers ----------------

def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def verify_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        if not sent or sent != session.get("csrf"):
            abort(400)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("कृपया पहले Login करें / Please login first.", "error")
            return redirect(url_for("login_page"))
        return view(*args, **kwargs)
    return wrapper


def current_user():
    if "user_id" not in session:
        return None
    return get_db().execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()


app.jinja_env.globals["current_user"] = current_user


# ---------------- Public pages ----------------

@app.route("/")
def home_page():
    return render_template("index.html", chapters=CHAPTERS)


@app.route("/class/11")
def class11_page():
    return render_template("class11.html")


@app.route("/class/12")
def class12_page():
    return render_template("class12.html", chapters=CHAPTERS)


@app.route("/study-material")
def material_page():
    return render_template("material.html", chapters=CHAPTERS)


@app.route("/chapter/<int:number>")
def chapter_page(number):
    if number < 1 or number > len(CHAPTERS):
        abort(404)
    chapter = CHAPTERS[number - 1]
    quiz = QUIZZES.get(str(number))
    return render_template("chapter.html", chapter=chapter, number=number,
                           sections=SECTIONS, quiz=quiz)


@app.route("/about")
def about_page():
    return render_template("about.html")


@app.route("/contact")
def contact_page():
    return render_template("contact.html")


# ---------------- Student auth ----------------

@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html", form={})

    form = {k: request.form.get(k, "").strip() for k in
            ("full_name", "username", "class_level")}
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    errors = []

    if not (2 <= len(form["full_name"]) <= 100):
        errors.append("पूरा नाम 2 से 100 अक्षरों के बीच होना चाहिए।")
    username = form["username"].lower()
    if not USERNAME_RE.match(username):
        errors.append("Username/Email में केवल अक्षर, अंक और _ . @ + - (4 से 120 अक्षर) हो सकते हैं।")
    if form["class_level"] not in ("11", "12"):
        errors.append("कृपया Class 11 या 12 चुनें।")
    if len(password) < 8:
        errors.append("पासवर्ड कम से कम 8 अक्षरों का होना चाहिए।")
    if password != confirm:
        errors.append("Password और Confirm Password मेल नहीं खाते।")

    if not errors:
        db = get_db()
        if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            errors.append("यह Username/Email पहले से registered है।")
        else:
            try:
                db.execute(
                    "INSERT INTO users (full_name, username, class_level, password_hash, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (form["full_name"], username, form["class_level"],
                     generate_password_hash(password),
                     datetime.utcnow().isoformat(timespec="seconds")),
                )
                db.commit()
                flash("Registration सफल! अब Login करें। / Registration successful, please login.", "success")
                return redirect(url_for("login_page"))
            except sqlite3.IntegrityError:
                errors.append("यह Username/Email पहले से registered है।")

    for e in errors:
        flash(e, "error")
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    user = None
    if username and password:
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

    if user and check_password_hash(user["password_hash"], password):
        session.clear()
        session["user_id"] = user["id"]
        session["csrf"] = secrets.token_hex(16)
        return redirect(url_for("dashboard_page"))

    flash("Username या Password गलत है। / Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout_page():
    session.clear()
    flash("आप Logout हो गए हैं। / You have been logged out.", "success")
    return redirect(url_for("home_page"))


# ---------------- Dashboard & results ----------------

@app.route("/dashboard")
@login_required
def dashboard_page():
    user = current_user()
    db = get_db()
    recent = db.execute(
        "SELECT * FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 10",
        (user["id"],),
    ).fetchall()
    quiz_titles = {qid: q["title"] for qid, q in QUIZZES.items()}
    return render_template("dashboard.html", user=user, chapters=CHAPTERS,
                           quizzes=QUIZZES, results=recent,
                           quiz_titles=quiz_titles)


@app.route("/results")
@login_required
def results_page():
    user = current_user()
    rows = get_db().execute(
        "SELECT * FROM results WHERE user_id = ? ORDER BY id DESC",
        (user["id"],),
    ).fetchall()
    quiz_titles = {qid: q["title"] for qid, q in QUIZZES.items()}
    return render_template("results.html", results=rows, quiz_titles=quiz_titles)


# ---------------- Quiz ----------------

@app.route("/quizzes")
@login_required
def quizzes_page():
    return render_template("quizzes.html", quizzes=QUIZZES, chapters=CHAPTERS)


@app.route("/quiz/<quiz_id>", methods=["GET", "POST"])
@login_required
def quiz_page(quiz_id):
    quiz = QUIZZES.get(quiz_id)
    if quiz is None:
        abort(404)

    if request.method == "GET":
        return render_template("quiz.html", quiz_id=quiz_id, quiz=quiz)

    # Server-side grading: only the stored answer key is trusted.
    answers = []
    correct = wrong = unanswered = 0
    for i, q in enumerate(quiz["questions"]):
        raw = request.form.get(f"q{i}")
        if raw is None or not raw.isdigit() or int(raw) >= len(q["options"]):
            answers.append(None)
            unanswered += 1
            continue
        choice = int(raw)
        answers.append(choice)
        if choice == q["answer"]:
            correct += 1
        else:
            wrong += 1

    total = len(quiz["questions"])
    score = round(correct / total * 100, 2) if total else 0.0
    user = current_user()

    db = get_db()
    cur = db.execute(
        "INSERT INTO results (user_id, quiz_id, answers, total, correct, wrong, "
        "unanswered, score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user["id"], quiz_id, json.dumps(answers), total, correct, wrong,
         unanswered, score, datetime.utcnow().isoformat(timespec="seconds")),
    )
    db.commit()
    return redirect(url_for("result_detail_page", result_id=cur.lastrowid))


@app.route("/results/<int:result_id>")
@login_required
def result_detail_page(result_id):
    row = get_db().execute(
        "SELECT * FROM results WHERE id = ? AND user_id = ?",
        (result_id, session["user_id"]),
    ).fetchone()
    if row is None:
        abort(404)

    quiz = QUIZZES.get(row["quiz_id"])
    if quiz is None:
        abort(404)

    stored = json.loads(row["answers"])
    review = []
    for i, q in enumerate(quiz["questions"]):
        chosen = stored[i] if i < len(stored) else None
        review.append({
            "question": q["q"],
            "options": q["options"],
            "chosen": chosen,
            "answer": q["answer"],
            "explanation": q["explanation"],
            "is_correct": chosen == q["answer"],
        })

    return render_template("result_detail.html", result=row, quiz=quiz,
                           review=review)


# ---------------- Errors ----------------

@app.errorhandler(400)
def bad_request(_e):
    return render_template("error.html", code=400,
                           message="अमान्य अनुरोध / Invalid request. पेज रीफ्रेश करके दोबारा कोशिश करें।"), 400


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404,
                           message="पेज नहीं मिला / Page not found."), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("error.html", code=500,
                           message="कुछ गड़बड़ हो गई / Something went wrong."), 500


if __name__ == "__main__":
    app.run(debug=True)
    CHAPTERS = [
    {
        "title": "1. साझेदारी लेखांकन",
        "english": "Accounting for Partnership",
        "theory": [
            "साझेदारी दो या दो से अधिक व्यक्तियों के बीच किया गया समझौता है, जिसमें व्यवसाय के लाभ को आपस में बाँटने की सहमति होती है।",
            "साझेदारी विलेख में लाभ-विभाजन अनुपात, पूँजी, वेतन, कमीशन, ब्याज आदि की शर्तें लिखी जाती हैं।",
            "यदि Partnership Deed में कोई बात नहीं लिखी है तो Indian Partnership Act के प्रावधान लागू होते हैं।",
            "Capital Account Fixed या Fluctuating हो सकता है।",
            "Profit and Loss Appropriation Account के द्वारा साझेदारों में लाभ का वितरण किया जाता है।",
            "Goodwill फर्म की प्रतिष्ठा और भविष्य में अधिक लाभ कमाने की क्षमता का मूल्य है।",
        ],
        "formulas": [
            "Interest on Capital = Capital × Rate × Time / 100",
            "Interest on Drawings = Drawings × Rate × Time / 100",
            "Average Profit = Total Profits / Number of Years",
            "Super Profit = Average Profit − Normal Profit",
            "Goodwill = Super Profit × Number of Years Purchase",
        ],
        "questions": [
            "साझेदारी की कोई चार विशेषताएँ लिखिए।",
            "Partnership Deed क्या है?",
            "Fixed और Fluctuating Capital में अंतर बताइए।",
            "Goodwill क्या है?",
            "Average Profit Method से Goodwill ज्ञात कीजिए।",
        ],
    },
    {
        "title": "2. साझेदारी फर्म का पुनर्गठन",
        "english": "Reconstitution of Partnership Firm",
        "theory": [
            "जब साझेदारों के बीच संबंध या लाभ-विभाजन अनुपात में परिवर्तन होता है तो साझेदारी फर्म का पुनर्गठन कहलाता है।",
            "पुनर्गठन में सामान्यतः नया लाभ-विभाजन अनुपात और त्याग अनुपात निकाला जाता है।",
            "Goodwill और Assets तथा Liabilities के पुनर्मूल्यांकन का समायोजन किया जाता है।",
            "Revaluation Account का उपयोग assets और liabilities में हुए बदलाव का लाभ या हानि ज्ञात करने के लिए किया जाता है।",
        ],
        "formulas": [
            "Gaining Ratio = New Ratio − Old Ratio",
            "Sacrificing Ratio = Old Ratio − New Ratio",
        ],
        "questions": [
            "साझेदारी फर्म का पुनर्गठन क्या है?",
            "त्याग अनुपात क्या है?",
            "लाभ अनुपात और त्याग अनुपात में अंतर बताइए।",
            "Revaluation Account क्यों बनाया जाता है?",
            "नए लाभ-विभाजन अनुपात की गणना कीजिए।",
        ],
    },
    {
        "title": "3. नये साझेदार का प्रवेश",
        "english": "Admission of a New Partner",
        "theory": [
            "जब कोई नया व्यक्ति साझेदारी फर्म में साझेदार के रूप में शामिल होता है तो इसे नए साझेदार का प्रवेश कहते हैं।",
            "नया साझेदार फर्म में पूँजी और Goodwill ला सकता है।",
            "नए साझेदार के प्रवेश पर पुराने साझेदारों का लाभ-विभाजन अनुपात बदल जाता है।",
            "नए साझेदार द्वारा लाई गई Goodwill पुराने साझेदारों को उनके Sacrificing Ratio में दी जाती है।",
            "Revaluation Account और Partners Capital Accounts में आवश्यक adjustments किए जाते हैं।",
        ],
        "formulas": [
            "New Ratio = Old Ratio − Sacrifice",
            "New Partner's Share of Goodwill = Total Goodwill × New Partner's Share",
        ],
        "questions": [
            "नए साझेदार का प्रवेश क्या है?",
            "नया साझेदार Goodwill क्यों लाता है?",
            "Sacrificing Ratio क्या है?",
            "Admission के समय Revaluation Account क्यों बनाया जाता है?",
            "नए साझेदार के प्रवेश की Journal Entries लिखिए।",
        ],
    },
    {
        "title": "4. साझेदार की निवृत्ति या मृत्यु",
        "english": "Retirement or Death of a Partner",
        "theory": [
            "जब कोई साझेदार फर्म से अलग हो जाता है तो उसे साझेदार की निवृत्ति कहते हैं।",
            "निवृत्त होने वाले साझेदार को उसका Capital, Goodwill और अन्य देय राशि दी जाती है।",
            "निवृत्ति के बाद शेष साझेदारों का नया लाभ-विभाजन अनुपात निकाला जाता है।",
            "साझेदार की मृत्यु होने पर उसके खाते में Capital, Goodwill, Profit आदि का समायोजन किया जाता है।",
        ],
        "formulas": [
            "Gaining Ratio = New Ratio − Old Ratio",
            "Retiring Partner's Goodwill Share = Total Goodwill × Retiring Partner's Share",
        ],
        "questions": [
            "साझेदार की निवृत्ति क्या है?",
            "निवृत्त साझेदार को कौन-कौन सी राशियाँ दी जाती हैं?",
            "Gaining Ratio क्या है?",
            "साझेदार की मृत्यु पर उसके खाते का निपटारा कैसे किया जाता है?",
            "Retirement की Journal Entries कीजिए।",
        ],
    },
    {
        "title": "5. साझेदारी फर्म का समापन",
        "english": "Dissolution of Partnership Firm",
        "theory": [
            "जब साझेदारी फर्म का व्यवसाय पूरी तरह बंद कर दिया जाता है तो इसे फर्म का विघटन या Dissolution कहते हैं।",
            "विघटन के समय Assets को बेचा जाता है और Liabilities का भुगतान किया जाता है।",
            "Realisation Account बनाया जाता है।",
            "Realisation Account से होने वाला लाभ या हानि साझेदारों में उनके Profit Sharing Ratio में बाँटा जाता है।",
            "अंत में Partners Capital Accounts और Bank/Cash Account का निपटारा किया जाता है।",
        ],
        "formulas": [
            "Realisation Profit → Partners Capital Accounts",
            "Realisation Loss → Partners Capital Accounts",
        ],
        "questions": [
            "Dissolution of Firm क्या है?",
            "Realisation Account क्यों बनाया जाता है?",
            "Realisation Profit कैसे बाँटा जाता है?",
            "फर्म के विघटन की Journal Entries लिखिए।",
            "Realisation Account तैयार कीजिए।",
        ],
    },
    {
        "title": "6. कम्पनी लेखे — अंशों का निर्गमन",
        "english": "Issue of Shares",
        "theory": [
            "Company अपनी पूँजी को छोटे-छोटे भागों में बाँटती है जिन्हें Shares कहा जाता है।",
            "Shareholder कंपनी में अपने shares के अनुसार पूँजी लगाता है।",
            "Shares को Par, Premium या कुछ परिस्थितियों में Discount पर जारी करने से संबंधित accounting entries की जाती हैं।",
            "Share Capital को अलग-अलग stages जैसे Application, Allotment और Calls में प्राप्त किया जा सकता है।",
        ],
        "formulas": [
            "Amount Due = Number of Shares × Amount per Share",
            "Application Money = Shares × Application Rate",
            "Allotment Money = Shares × Allotment Rate",
        ],
        "questions": [
            "Share क्या है?",
            "Share Capital क्या है?",
            "Application और Allotment में अंतर बताइए।",
            "Shares को Premium पर जारी करने की entries कीजिए।",
            "Share Issue का numerical हल कीजिए।",
        ],
    },
    {
        "title": "7. अंशों का हरण एवं पुनर्निर्गमन",
        "english": "Forfeiture and Reissue of Shares",
        "theory": [
            "यदि shareholder shares पर देय राशि समय पर नहीं देता तो कंपनी उसके shares को Forfeit कर सकती है।",
            "Forfeited Shares को कंपनी बाद में Reissue कर सकती है।",
            "Forfeiture के समय Share Capital Account और संबंधित unpaid amount का adjustment किया जाता है।",
            "Reissue के बाद बचा हुआ forfeiture amount Capital Reserve में transfer किया जा सकता है।",
        ],
        "formulas": [
            "Capital Reserve = Forfeited Amount − Reissue Discount",
        ],
        "questions": [
            "Forfeiture of Shares क्या है?",
            "Shares को Forfeit क्यों किया जाता है?",
            "Reissue of Shares क्या है?",
            "Forfeiture की Journal Entry कीजिए।",
            "Reissue और Capital Reserve का numerical हल कीजिए।",
        ],
    },
    {
        "title": "8. ऋणपत्रों का निर्गमन",
        "english": "Issue of Debentures",
        "theory": [
            "Debenture कंपनी द्वारा लिया गया दीर्घकालीन ऋण दर्शाता है।",
            "Debenture holder कंपनी का creditor होता है।",
            "Debentures को Par, Premium या Discount पर issue किया जा सकता है।",
            "Debenture पर दिया जाने वाला Interest कंपनी के लिए expense होता है।",
        ],
        "formulas": [
            "Interest on Debentures = Face Value × Rate / 100",
            "Annual Interest = Debenture Value × Interest Rate",
        ],
        "questions": [
            "Debenture क्या है?",
            "Share और Debenture में अंतर बताइए।",
            "Debentures को Premium पर issue करने की entry लिखिए।",
            "Debenture Interest की गणना कीजिए।",
            "Debenture Issue का numerical हल कीजिए।",
        ],
    },
    {
        "title": "9. कम्पनी के वित्तीय विवरण",
        "english": "Financial Statements of a Company",
        "theory": [
            "Financial Statements कंपनी की financial position और performance को दिखाते हैं।",
            "Balance Sheet कंपनी की assets, liabilities और equity की स्थिति दिखाती है।",
            "Statement of Profit and Loss से कंपनी का profit या loss पता चलता है।",
            "Financial statements का उपयोग investors, management और अन्य users द्वारा किया जाता है।",
        ],
        "formulas": [
            "Profit = Revenue − Expenses",
            "Assets = Equity + Liabilities",
        ],
        "questions": [
            "Financial Statements क्या हैं?",
            "Balance Sheet क्या दिखाती है?",
            "Statement of Profit and Loss का उद्देश्य क्या है?",
            "Balance Sheet तैयार कीजिए।",
            "Financial Statements के कोई चार उपयोग लिखिए।",
        ],
    },
    {
        "title": "10. लेखांकन अनुपात",
        "english": "Accounting Ratios",
        "theory": [
            "Accounting Ratios का उपयोग financial statements का analysis करने के लिए किया जाता है।",
            "Ratios से कंपनी की liquidity, solvency और profitability के बारे में जानकारी मिलती है।",
            "Current Ratio और Quick Ratio liquidity को मापने में उपयोगी हैं।",
            "Debt Equity Ratio और Proprietary Ratio solvency से संबंधित हैं।",
            "Gross Profit Ratio और Net Profit Ratio profitability से संबंधित हैं।",
        ],
        "formulas": [
            "Current Ratio = Current Assets / Current Liabilities",
            "Quick Ratio = Quick Assets / Current Liabilities",
            "Gross Profit Ratio = Gross Profit / Revenue × 100",
            "Net Profit Ratio = Net Profit / Revenue × 100",
            "Debt Equity Ratio = Debt / Equity",
        ],
        "questions": [
            "Accounting Ratio क्या है?",
            "Current Ratio ज्ञात कीजिए।",
            "Quick Ratio ज्ञात कीजिए।",
            "Gross Profit Ratio ज्ञात कीजिए।",
            "Debt Equity Ratio का अर्थ बताइए।",
        ],
    },
    {
        "title": "11. रोकड़ प्रवाह विवरण",
        "english": "Cash Flow Statement",
        "theory": [
            "Cash Flow Statement किसी अवधि में cash और cash equivalents में हुए बदलाव को दिखाता है।",
            "Cash flows को Operating, Investing और Financing Activities में बाँटा जाता है।",
            "Operating Activities व्यवसाय की मुख्य गतिविधियों से संबंधित होती हैं।",
            "Investing Activities में assets और investments की खरीद-बिक्री शामिल होती है।",
            "Financing Activities में capital और borrowings से संबंधित cash flows आते हैं।",
        ],
        "formulas": [
            "Net Cash Flow = Operating Cash Flow + Investing Cash Flow + Financing Cash Flow",
            "Closing Cash = Opening Cash + Net Cash Flow",
        ],
        "questions": [
            "Cash Flow Statement क्या है?",
            "Operating Activity क्या है?",
            "Investing Activity क्या है?",
            "Financing Activity क्या है?",
            "Cash Flow Statement तैयार कीजिए।",
        ],
    },
]
    # answer = index (0 se shuru) of correct option.
# Yeh sample questions hain; aap apne chapter ke hisaab se aur questions jod sakte hain.

QUIZZES = {
    "1": {
        "title": "Ch 1: साझेदारी लेखांकन",
        "questions": [
            {"q": "Partnership Deed में कोई बात न लिखी हो तो कौन-सा Act लागू होता है?",
             "options": ["Companies Act, 2013", "Indian Partnership Act, 1932", "Negotiable Instruments Act", "Sale of Goods Act"],
             "answer": 1,
             "explanation": "Deed में लिखी न हो तो Indian Partnership Act, 1932 के प्रावधान लागू होते हैं।"},
            {"q": "Average Profit ₹60,000 और Normal Profit ₹40,000 हैं, 3 वर्ष का Purchase: Goodwill कितना?",
             "options": ["₹60,000", "₹1,20,000", "₹1,80,000", "₹40,000"],
             "answer": 0,
             "explanation": "Super Profit = 60,000 − 40,000 = 20,000; Goodwill = 20,000 × 3 = ₹60,000।"},
        ],
    },
    "2": {
        "title": "Ch 2: साझेदारी फर्म का पुनर्गठन",
        "questions": [
            {"q": "A का Old Ratio 1/2 और New Ratio 2/5 है। A का Sacrificing Ratio कितना?",
             "options": ["1/10", "1/5", "3/10", "1/2"],
             "answer": 0,
             "explanation": "Sacrificing Ratio = Old − New = 1/2 − 2/5 = 5/10 − 4/10 = 1/10।"},
            {"q": "Revaluation Account किसलिए बनाया जाता है?",
             "options": ["Assets और Liabilities में हुए बदलाव का लाभ/हानि ज्ञात करने", "Dividend देने", "Shares जारी करने", "Interest भुगतान"],
             "answer": 0,
             "explanation": "Revaluation Account से assets व liabilities के मूल्य-परिवर्तन का लाभ या हानि पता चलती है।"},
        ],
    },
    "3": {
        "title": "Ch 3: नये साझेदार का प्रवेश",
        "questions": [
            {"q": "कुल Goodwill ₹1,20,000 है और नए साझेदार का हिस्सा 1/4 है। उसका Goodwill हिस्सा?",
             "options": ["₹30,000", "₹40,000", "₹20,000", "₹60,000"],
             "answer": 0,
             "explanation": "1,20,000 × 1/4 = ₹30,000।"},
            {"q": "Admission के समय नए साझेदार द्वारा लाई गई Goodwill किसे दी जाती है?",
             "options": ["Sacrificing partners (पुराने साझेदारों) को", "Bank को", "Creditors को", "Debenture holders को"],
             "answer": 0,
             "explanation": "नया साझेदार Goodwill का हिस्सा पुराने साझेदारों को उनके Sacrificing Ratio में देता है।"},
        ],
    },
    "4": {
        "title": "Ch 4: साझेदार की निवृत्ति या मृत्यु",
        "questions": [
            {"q": "निवृत्त साझेदार को सामान्यतः क्या दिया जाता है?",
             "options": ["Capital, Goodwill में हिस्सा और देय लाभ", "केवल वेतन", "कंपनी के शेयर", "Debentures"],
             "answer": 0,
             "explanation": "निवृत्त साझेदार को उसका Capital, Goodwill में हिस्सा और अन्य देय राशि दी जाती है।"},
            {"q": "Gaining Ratio की सही परिभाषा क्या है?",
             "options": ["Old Ratio − New Ratio", "New Ratio − Old Ratio", "Old Ratio + New Ratio", "New Ratio ÷ Old Ratio"],
             "answer": 1,
             "explanation": "Gaining Ratio = New Ratio − Old Ratio।"},
        ],
    },
    "5": {
        "title": "Ch 5: साझेदारी फर्म का समापन",
        "questions": [
            {"q": "Realisation Loss किस अनुपात में साझेदारों में बाँटी जाती है?",
             "options": ["Profit Sharing Ratio में", "Capital के अनुपात में", "बराबर भागों में", "वेतन के अनुपात में"],
             "answer": 0,
             "explanation": "Realisation लाभ/हानि साझेदारों में उनके Profit Sharing Ratio में बाँटी जाती है।"},
            {"q": "Realisation Account किसलिए बनाया जाता है?",
             "options": ["Assets की बिक्री और Liabilities के निपटारे का हिसाब रखने", "Shares जारी करने", "Bonus देने", "Dividend घोषित करने"],
             "answer": 0,
             "explanation": "Realisation Account में assets की बिक्री और liabilities के भुगतान का हिसाब होता है।"},
        ],
    },
    "6": {
        "title": "Ch 6: कम्पनी लेखे — अंशों का निर्गमन",
        "questions": [
            {"q": "100 Shares, प्रति Share ₹10 देय हो तो कुल राशि?",
             "options": ["₹1,000", "₹100", "₹10", "₹10,000"],
             "answer": 0,
             "explanation": "Amount Due = 100 × 10 = ₹1,000।"},
            {"q": "Share Capital का सही अर्थ क्या है?",
             "options": ["कंपनी की पूँजी का वह भाग जो shares में बँटा हो", "Partner का वेतन", "Debenture पर ब्याज", "Bank loan"],
             "answer": 0,
             "explanation": "Share Capital कंपनी की कुल पूँजी का वह हिस्सा है जो shares में विभाजित है।"},
        ],
    },
    "7": {
        "title": "Ch 7: अंशों का हरण एवं पुनर्निर्गमन",
        "questions": [
            {"q": "Shares को Forfeit क्यों किया जाता है?",
             "options": ["Calls या देय राशि समय पर न देने पर", "Dividend बढ़ाने के लिए", "Bonus देने के लिए", "Debentures redeem करने के लिए"],
             "answer": 0,
             "explanation": "देय राशि न चुकाने पर कंपनी shares को forfeit कर सकती है।"},
            {"q": "Forfeited Amount ₹5,000 और Reissue Discount ₹2,000 है। Capital Reserve कितना?",
             "options": ["₹3,000", "₹7,000", "₹5,000", "₹2,000"],
             "answer": 0,
             "explanation": "Capital Reserve = 5,000 − 2,000 = ₹3,000।"},
        ],
    },
    "8": {
        "title": "Ch 8: ऋणपत्रों का निर्गमन",
        "questions": [
            {"q": "Face Value ₹1,00,000 के Debenture पर 10% ब्याज हो तो वार्षिक ब्याज?",
             "options": ["₹10,000", "₹1,000", "₹1,00,000", "₹5,000"],
             "answer": 0,
             "explanation": "Interest = 1,00,000 × 10 / 100 = ₹10,000।"},
            {"q": "Debenture holder कंपनी के लिए क्या होता है?",
             "options": ["Creditor (ऋणदाता)", "Owner (मालिक)", "Partner (साझेदार)", "Auditor (लेखा-परीक्षक)"],
             "answer": 0,
             "explanation": "Debenture holder कंपनी को ऋण देता है, इसलिए वह creditor होता है।"},
        ],
    },
    "9": {
        "title": "Ch 9: कम्पनी के वित्तीय विवरण",
        "questions": [
            {"q": "Balance Sheet का मूल समीकरण क्या है?",
             "options": ["Assets = Equity + Liabilities", "Assets = Equity − Liabilities", "Assets = Liabilities − Equity", "Assets = Revenue + Expenses"],
             "answer": 0,
             "explanation": "Balance Sheet में Assets = Equity + Liabilities होता है।"},
            {"q": "Statement of Profit and Loss किसे दिखाता है?",
             "options": ["कंपनी का लाभ या हानि", "केवल Cash flow", "Shares की संख्या", "Debentures की संख्या"],
             "answer": 0,
             "explanation": "P&L Statement से अवधि में कंपनी का लाभ या हानि पता चलता है।"},
        ],
    },
    "10": {
        "title": "Ch 10: लेखांकन अनुपात",
        "questions": [
            {"q": "Current Assets ₹80,000 और Current Liabilities ₹40,000 हैं। Current Ratio?",
             "options": ["2 : 1", "1 : 2", "4 : 1", "1 : 1"],
             "answer": 0,
             "explanation": "Current Ratio = 80,000 / 40,000 = 2 : 1।"},
            {"q": "Gross Profit Ratio किस पहलू को मापता है?",
             "options": ["Profitability (लाभप्रदता)", "Liquidity (तरलता)", "Solvency (ऋण-चुकौती क्षमता)", "Efficiency (दक्षता)"],
             "answer": 0,
             "explanation": "Gross Profit Ratio profitability से संबंधित है।"},
        ],
    },
    "11": {
        "title": "Ch 11: रोकड़ प्रवाह विवरण",
        "questions": [
            {"q": "Operating ₹50,000, Investing −₹20,000, Financing ₹10,000 हैं। Net Cash Flow?",
             "options": ["₹40,000", "₹80,000", "₹20,000", "₹60,000"],
             "answer": 0,
             "explanation": "Net Cash Flow = 50,000 − 20,000 + 10,000 = ₹40,000।"},
            {"q": "Investing Activities में क्या शामिल होता है?",
             "options": ["Assets और investments की खरीद-बिक्री", "Salary भुगतान", "Dividend घोषणा", "Share capital का अंकन"],
             "answer": 0,
             "explanation": "Investing Activities में assets और investments की खरीद-बिक्री आती है।"},
        ],
    },
}

BASE = """<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{% block title %}Vishwas Mehra Accountancy{% endblock %}</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,"Noto Sans Devanagari",sans-serif;background:#eef2f7;color:#222;line-height:1.6}
header{background:linear-gradient(135deg,#0f766e,#2563eb);color:#fff;padding:20px 15px}
header .brand{font-size:26px;font-weight:bold;margin:0 0 10px}
nav{display:flex;flex-wrap:wrap;gap:8px}
nav a{color:#fff;text-decoration:none;background:rgba(255,255,255,.18);padding:6px 12px;border-radius:8px;font-size:14px}
nav a:hover{background:rgba(255,255,255,.35)}
.container{max-width:960px;margin:auto;padding:20px}
.card{background:#fff;padding:20px;border-radius:16px;box-shadow:0 4px 12px #0002;margin:15px 0}
.card h2{margin:0 0 8px;color:#2563eb;font-size:20px}
.card p{color:#555;margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:15px}
.btn{display:inline-block;background:#2563eb;color:#fff;border:none;padding:10px 16px;border-radius:10px;text-decoration:none;cursor:pointer;font-size:15px}
.btn-green{background:#059669}
.btn-red{background:#ef4444}
.flash{padding:12px;border-radius:10px;margin:10px 0}
.flash.error{background:#fee2e2;color:#991b1b}
.flash.success{background:#dcfce7;color:#166534}
label{display:block;margin:12px 0 4px;font-weight:bold}
input,select{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;font-size:15px}
.box{background:#f8fafc;padding:15px;border-radius:12px;margin:12px 0}
.question{background:#fff7ed;padding:12px;border-radius:10px;margin:8px 0}
.formula{background:#eff6ff;padding:12px;border-radius:10px;margin:6px 0;font-family:monospace}
.correct{background:#dcfce7}
.wrong{background:#fee2e2}
.muted{color:#888;font-style:italic}
table{width:100%;border-collapse:collapse;background:#fff}
th,td{padding:10px;border-bottom:1px solid #e2e8f0;text-align:left}
footer{text-align:center;padding:25px 15px;color:#555;font-size:14px;margin-top:30px}
footer a{color:#2563eb;text-decoration:none;margin:0 6px}
@media(max-width:600px){header .brand{font-size:20px}.card h2{font-size:18px}}
</style>
</head>
<body>
<header>
  <div class="brand">📚 Vishwas Mehra Accountancy</div>
  <nav>
    <a href="{{ url_for('home_page') }}">Home</a>
    <a href="{{ url_for('class11_page') }}">Class 11</a>
    <a href="{{ url_for('class12_page') }}">Class 12</a>
    <a href="{{ url_for('material_page') }}">Study Material</a>
    {% if current_user() %}
      <a href="{{ url_for('dashboard_page') }}">Dashboard</a>
      <a href="{{ url_for('quizzes_page') }}">Online Test</a>
      <a href="{{ url_for('results_page') }}">Results</a>
    {% else %}
      <a href="{{ url_for('register_page') }}">Registration</a>
      <a href="{{ url_for('login_page') }}">Login</a>
    {% endif %}
    <a href="{{ url_for('about_page') }}">About</a>
    <a href="{{ url_for('contact_page') }}">Contact</a>
  </nav>
</header>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
      <div class="flash {{ cat }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>
<footer>
  © Vishwas Mehra Accountancy · <a href="{{ url_for('home_page') }}">Home</a> · <a href="{{ url_for('contact_page') }}">Contact</a>
</footer>
</body>
</html>
"""

INDEX = """{% extends "base.html" %}
{% block title %}Home | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<div class="card">
  <h2>स्वागत है! / Welcome!</h2>
  <p>Class 11–12 Accountancy की theory, formulas, solved numericals, MCQ और Online Test — हिंदी व English में।</p>
  <a class="btn" href="{{ url_for('class12_page') }}">Class 12 Accountancy</a>
  <a class="btn btn-green" href="{{ url_for('class11_page') }}">Class 11 Accountancy</a>
</div>
<div class="grid">
  <div class="card"><h2>📖 Chapter-wise Study Material</h2><p>हर अध्याय की theory और formulas।</p><a href="{{ url_for('material_page') }}">देखें →</a></div>
  <div class="card"><h2>📝 Online Test / Quiz</h2><p>MCQ टेस्ट दें और तुरंत स्कोर देखें।</p><a href="{{ url_for('quizzes_page') }}">शुरू करें →</a></div>
  <div class="card"><h2>👤 Student Registration</h2><p>नया अकाउंट बनाएँ और अपने results सुरक्षित रखें।</p><a href="{{ url_for('register_page') }}">Register →</a></div>
  <div class="card"><h2>🔐 Student Login</h2><p>Dashboard और results देखने के लिए Login करें।</p><a href="{{ url_for('login_page') }}">Login →</a></div>
</div>
{% endblock %}
"""

CLASS11 = """{% extends "base.html" %}
{% block title %}Class 11 Accountancy | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<div class="card">
  <h2>Class 11 Accountancy</h2>
  <p class="muted">Class 11 की अध्यायवार सामग्री यहाँ जोड़ी जाएगी। (Theory, Definitions, Examples, Questions, MCQ)</p>
</div>
<a class="btn" href="{{ url_for('home_page') }}">← Home</a>
{% endblock %}
"""

CLASS12 = """{% extends "base.html" %}
{% block title %}Class 12 Accountancy | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<h2>Class 12 Accountancy — अध्याय</h2>
<div class="grid">
{% for ch in chapters %}
  <a href="{{ url_for('chapter_page', number=loop.index) }}" style="text-decoration:none;color:inherit">
    <div class="card">
      <h2>{{ ch.title }}</h2>
      <p>{{ ch.english }}</p>
      <span class="btn">पूरा Chapter देखें</span>
    </div>
  </a>
{% endfor %}
</div>
{% endblock %}
"""

MATERIAL = """{% extends "base.html" %}
{% block title %}Study Material | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<h2>Chapter-wise Study Material</h2>
<div class="grid">
{% for ch in chapters %}
  <div class="card">
    <h2>{{ ch.title }}</h2>
    <p>{{ ch.english }}</p>
    <a class="btn" href="{{ url_for('chapter_page', number=loop.index) }}">खोलें</a>
  </div>
{% endfor %}
</div>
{% endblock %}
"""

CHAPTER = """{% extends "base.html" %}
{% block title %}{{ chapter.title }} | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<h1>{{ chapter.title }}</h1>
<p class="muted">{{ chapter.english }}</p>

{% for key, label in sections %}
  <div class="card">
    <h2>{{ label }}</h2>
    {% if key == 'theory' and chapter.theory %}
      <div class="box"><ul>{% for t in chapter.theory %}<li>{{ t }}</li>{% endfor %}</ul></div>
    {% elif key == 'formulas' and chapter.formulas %}
      {% for f in chapter.formulas %}<div class="formula">{{ f }}</div>{% endfor %}
    {% elif key == 'exam' and chapter.questions %}
      {% for q in chapter.questions %}<div class="question"><b>Q{{ loop.index }}.</b> {{ q }}</div>{% endfor %}
    {% elif key == 'mcq' and quiz %}
      <p>इस अध्याय के MCQ का Online Test दें।</p>
      <a class="btn btn-green" href="{{ url_for('quiz_page', quiz_id=number|string) }}">Test शुरू करें</a>
    {% else %}
      <p class="muted">इस सेक्शन की सामग्री जल्द जोड़ी जाएगी। (Content coming soon)</p>
    {% endif %}
  </div>
{% endfor %}

<a class="btn" href="{{ url_for('home_page') }}">← Home</a>
{% endblock %}
"""

ABOUT = """{% extends "base.html" %}
{% block title %}About | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<div class="card">
  <h2>About</h2>
  <p>Vishwas Mehra Accountancy का उद्देश्य Class 11–12 के विद्यार्थियों को हिंदी और English में सरल, व्यवस्थित accountancy सामग्री, अभ्यास प्रश्न और Online Test उपलब्ध कराना है, ताकि परीक्षा की तैयारी आसान हो।</p>
</div>
{% endblock %}
"""

CONTACT = """{% extends "base.html" %}
{% block title %}Contact | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<div class="card">
  <h2>Contact</h2>
  <p class="muted">संपर्क जानकारी यहाँ जोड़ें: [ईमेल / फ़ोन / पता]</p>
</div>
{% endblock %}
"""

REGISTER = """{% extends "base.html" %}
{% block title %}Registration | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<div class="card" style="max-width:520px;margin:auto">
  <h2>Student Registration</h2>
  <form method="post" action="{{ url_for('register_page') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Full Name / पूरा नाम</label>
    <input name="full_name" value="{{ form.get('full_name','') }}" required maxlength="100">
    <label>Email या Username</label>
    <input name="username" value="{{ form.get('username','') }}" required maxlength="120">
    <label>Class</label>
    <select name="class_level" required>
      <option value="">-- चुनें --</option>
      <option value="11" {% if form.get('class_level')=='11' %}selected{% endif %}>Class 11</option>
      <option value="12" {% if form.get('class_level')=='12' %}selected{% endif %}>Class 12</option>
    </select>
    <label>Password (कम से कम 8 अक्षर)</label>
    <input type="password" name="password" required minlength="8">
    <label>Confirm Password</label>
    <input type="password" name="confirm_password" required minlength="8">
    <p></p>
    <button class="btn" type="submit">Register</button>
  </form>
  <p>पहले से अकाउंट है? <a href="{{ url_for('login_page') }}">Login करें</a></p>
</div>
{% endblock %}
"""

LOGIN = """{% extends "base.html" %}
{% block title %}Login | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<div class="card" style="max-width:480px;margin:auto">
  <h2>Student Login</h2>
  <form method="post" action="{{ url_for('login_page') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Email या Username</label>
    <input name="username" required>
    <label>Password</label>
    <input type="password" name="password" required>
    <p></p>
    <button class="btn" type="submit">Login</button>
  </form>
  <p>नया अकाउंट? <a href="{{ url_for('register_page') }}">Register करें</a></p>
</div>
{% endblock %}
"""

DASHBOARD = """{% extends "base.html" %}
{% block title %}Dashboard | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<div class="card">
  <h2>नमस्ते, {{ user['full_name'] }}!</h2>
  <p>Class: {{ user['class_level'] }}</p>
  <form method="post" action="{{ url_for('logout_page') }}" style="display:inline">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <button class="btn btn-red" type="submit">Logout</button>
  </form>
</div>
<div class="grid">
  <div class="card"><h2>उपलब्ध अध्याय</h2><p>{{ chapters|length }} अध्याय</p><a href="{{ url_for('material_page') }}">देखें →</a></div>
  <div class="card"><h2>उपलब्ध Online Tests</h2><p>{{ quizzes|length }} टेस्ट</p><a href="{{ url_for('quizzes_page') }}">शुरू करें →</a></div>
  <div class="card"><h2>दिए गए टेस्ट</h2><p>{{ results|length }} (हाल के)</p><a href="{{ url_for('results_page') }}">सभी results →</a></div>
</div>
<div class="card">
  <h2>पिछले परिणाम</h2>
  {% if results %}
  <table>
    <tr><th>टेस्ट</th><th>अंक</th><th>तारीख</th></tr>
    {% for r in results %}
    <tr>
      <td><a href="{{ url_for('result_detail_page', result_id=r['id']) }}">{{ quiz_titles.get(r['quiz_id'], r['quiz_id']) }}</a></td>
      <td>{{ r['correct'] }}/{{ r['total'] }} ({{ r['score'] }}%)</td>
      <td>{{ r['created_at'] }}</td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <p class="muted">अभी तक कोई टेस्ट नहीं दिया गया।</p>
  {% endif %}
</div>
{% endblock %}
"""

QUIZZES = """{% extends "base.html" %}
{% block title %}Online Test | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<h2>Online Test / Quiz</h2>
<div class="grid">
{% for qid, q in quizzes.items() %}
  <div class="card">
    <h2>{{ q.title }}</h2>
    <p>{{ q.questions|length }} प्रश्न</p>
    <a class="btn btn-green" href="{{ url_for('quiz_page', quiz_id=qid) }}">Test दें</a>
  </div>
{% endfor %}
</div>
{% endblock %}
"""

QUIZ = """{% extends "base.html" %}
{% block title %}{{ quiz.title }} | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<h2>{{ quiz.title }}</h2>
<form method="post" action="{{ url_for('quiz_page', quiz_id=quiz_id) }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  {% for q in quiz.questions %}
  <div class="card">
    <p><b>Q{{ loop.index }}. {{ q.q }}</b></p>
    {% for opt in q.options %}
      <label style="font-weight:normal;display:block;margin:6px 0">
        <input type="radio" name="q{{ loop.index0 }}" value="{{ loop.index0 }}" style="width:auto"> {{ opt }}
      </label>
    {% endfor %}
  </div>
  {% endfor %}
  <button class="btn btn-green" type="submit">Submit Test</button>
</form>
{% endblock %}
"""

RESULTS = """{% extends "base.html" %}
{% block title %}Results | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<h2>मेरे Results</h2>
<div class="card">
{% if results %}
<table>
  <tr><th>टेस्ट</th><th>सही</th><th>गलत</th><th>स्कोर</th><th>तारीख</th></tr>
  {% for r in results %}
  <tr>
    <td><a href="{{ url_for('result_detail_page', result_id=r['id']) }}">{{ quiz_titles.get(r['quiz_id'], r['quiz_id']) }}</a></td>
    <td>{{ r['correct'] }}</td>
    <td>{{ r['wrong'] }}</td>
    <td>{{ r['score'] }}%</td>
    <td>{{ r['created_at'] }}</td>
  </tr>
  {% endfor %}
</table>
{% else %}
<p class="muted">अभी कोई result नहीं है।</p>
{% endif %}
</div>
{% endblock %}
"""

RESULT_DETAIL = """{% extends "base.html" %}
{% block title %}Result | Vishwas Mehra Accountancy{% endblock %}
{% block content %}
<div class="card">
  <h2>{{ quiz.title }} — Result</h2>
  <p>Total Questions: <b>{{ result['total'] }}</b></p>
  <p>Correct Answers: <b>{{ result['correct'] }}</b></p>
  <p>Wrong Answers: <b>{{ result['wrong'] }}</b></p>
  <p>Unanswered: <b>{{ result['unanswered'] }}</b></p>
  <p>Score: <b>{{ result['score'] }}%</b></p>
  <p class="muted">तारीख: {{ result['created_at'] }}</p>
</div>
{% for r in review %}
  <div class="card {{ 'correct' if r.is_correct else 'wrong' }}">
    <p><b>Q{{ loop.index }}. {{ r.question }}</b></p>
    <ul>
    {% for opt in r.options %}
      <li>{{ opt }}
        {% if loop.index0 == r.answer %} ✅ (सही उत्तर){% endif %}
        {% if loop.index0 == r.chosen and not r.is_correct %} ❌ (आपका उत्तर){% endif %}
      </li>
    {% endfor %}
    </ul>
    {% if r.chosen is none %}<p class="muted">आपने इसका उत्तर नहीं दिया।</p>{% endif %}
    <p><i>Explanation:</i> {{ r.explanation }}</p>
  </div>
{% endfor %}
<a class="btn" href="{{ url_for('results_page') }}">← सभी Results</a>
{% endblock %}

    
