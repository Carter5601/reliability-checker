from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
load_dotenv(dotenv_path=Path(".env"))

# Initialize OpenAI and SerpAPI keys
client = OpenAI()
serp_api_key = os.getenv("SERP_API_KEY")
print("🔑 Loaded SERP_API_KEY:", serp_api_key)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")

def search_reviews(query):
    url = "https://serpapi.com/search"
    params = {
        "q": f"{query} reviews",
        "api_key": serp_api_key,
        "hl": "en",
        "gl": "us"
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ SerpAPI request failed: {response.status_code}")
        return []
    data = response.json()
    results = data.get("organic_results", [])
    snippets = [r['snippet'] for r in results if 'snippet' in r]
    return snippets[:10]

def summarize_reviews(reviews):
    joined = "\n".join(reviews)
    prompt = (
        "You're an AI trust analyst. Based on the following user reviews, do the following:\n"
        "1. Provide a reliability score as a percentage (0% = scam, 100% = completely trustworthy).\n"
        "2. Give a brief overall explanation of the score.\n"
        "3. Then rate each review individually from 0-100% and give a one-sentence reason why.\n\n"
        f"Reviews:\n{joined}"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a security and trust analyst."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

@app.route("/analyze", methods=["POST"])
def analyze():
    print("✅ Received POST to /analyze")

    data = request.json
    print("📥 Payload received:", data)

    query = data.get("query") if data else None
    if not query:
        print("❌ No query provided.")
        return jsonify({"error": "No query provided."}), 400

    reviews = search_reviews(query)
    print(f"🔍 Found {len(reviews)} review snippets.")

    if not reviews:
        print("⚠️ No reviews found for query.")
        return jsonify({"error": "No reviews found."}), 404

    summary = summarize_reviews(reviews)
    print("✅ Summary generated.")

    return jsonify({"summary": summary})

if __name__ == "__main__":
    print("🔎 ROUTES REGISTERED:")
    print(app.url_map)
    app.run(debug=True)





