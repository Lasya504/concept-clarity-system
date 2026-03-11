from flask import Flask, render_template, request, jsonify
from model import generate_explanation
from urllib.parse import quote_plus   # ← NEW

app = Flask(__name__)

# ── NEW FUNCTION ──────────────────────────────────────────────────────────────
def get_learning_resources(term, language='en'):
    encoded = quote_plus(term)
    wiki_lang = language if language in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko'] else 'en'
    return [
        {"name": "Wikipedia",      "url": f"https://{wiki_lang}.wikipedia.org/wiki/Special:Search?search={encoded}", "icon": "📖"},
        {"name": "Britannica",     "url": f"https://www.britannica.com/search?query={encoded}",                      "icon": "🏛️"},
        {"name": "Khan Academy",   "url": f"https://www.khanacademy.org/search?page_search_query={encoded}",         "icon": "🎓"},
        {"name": "Google Scholar", "url": f"https://scholar.google.com/scholar?q={encoded}",                        "icon": "🔬"},
    ]
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/explain', methods=['POST'])
def explain():
    data = request.get_json(silent=True) or {}
    term = (data.get("term") or "").strip()
    language = data.get("language", "en")

    if not term:
        return jsonify({"error": "No term provided"}), 400

    response_data = generate_explanation(term, language)
    response_data["resources"] = get_learning_resources(term, language)  # ← NEW

    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True)
