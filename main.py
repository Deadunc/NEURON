import os
import requests
from flask import Flask, request, jsonify

# --- Initialize the Flask App (our server) ---
app = Flask(__name__)

# --- Function to get the latest news headlines ---
def get_gold_news(api_key):
    try:
        # Search for news related to gold, sorting by the most recent
        url = f"https://newsapi.org/v2/everything?q=gold OR usd&sortBy=publishedAt&language=en&apiKey={api_key}"
        response = requests.get(url)
        data = response.json()
        # Extract the titles of the top 3 articles
        headlines = [article['title'] for article in data['articles'][:3]]
        return ", ".join(headlines)
    except Exception as e:
        print(f"Error getting news: {e}")
        return "Could not retrieve news."

# --- Function to ask the AI for a trading signal ---
def get_ai_signal(deepseek_api_key, news_headlines, market_data):
    try:
        # The prompt that describes the market to the AI
        prompt = f"""
        Role: You are an expert financial analyst for a proprietary trading firm specializing in XAU/USD. Your analysis must be based on the data provided.

        Market Context:
        - Asset: XAU/USD (Gold)
        - Timeframe: H1
        - Current Volatility (ATR): {market_data.get('atr', 'N/A')}
        - Long-Term Trend: The price is currently trading {market_data.get('trend', 'N/A')} the 200 EMA.

        Real-Time Data:
        - Current Price: {market_data.get('price', 'N/A')}
        - Recent News Headlines: {news_headlines}

        Your Task:
        Based on all the above information, provide a brief analysis of the immediate outlook. Conclude your entire response with a single word on a new line: BUY, SELL, or HOLD.
        """

        headers = {
            "Authorization": f"Bearer {deepseek_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload)
        ai_response_data = response.json()
        
        # Extract the text content from the AI's response
        full_response_text = ai_response_data['choices'][0]['message']['content']
        
        # Find the last line and extract the signal word
        last_line = full_response_text.strip().split('\n')[-1].upper()
        
        if "BUY" in last_line:
            return "BUY"
        elif "SELL" in last_line:
            return "SELL"
        else:
            return "HOLD"
            
    except Exception as e:
        print(f"Error getting AI signal: {e}")
        return "ERROR"

# --- This is the main endpoint our MQL5 bot will talk to ---
@app.route('/getsignal', methods=['POST'])
def handle_signal_request():
    # Get the API keys from our secure environment variables
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    news_key = os.getenv("NEWS_API_KEY")
    
    if not deepseek_key or not news_key:
        return jsonify({"error": "API keys not configured on server"}), 500

    # Get market data sent from the MQL5 bot
    market_data = request.json
    
    # 1. Get News
    news = get_gold_news(news_key)
    
    # 2. Get AI Signal
    signal = get_ai_signal(deepseek_key, news, market_data)
    
    # 3. Send Signal Back to MQL5 Bot
    return jsonify({"signal": signal})

# --- Run the server ---
if __name__ == '__main__':
    # The port is automatically assigned by the hosting service
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
