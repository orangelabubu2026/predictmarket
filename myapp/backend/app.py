from flask import Flask, request, jsonify, send_file
import pandas as pd
import numpy as np
import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

def load_file(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError("File not found at given path")

    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        return pd.read_excel(file_path)
    else:
        raise ValueError('Unsupported file format. Use CSV or Excel.')

def compute_ema(series: pd.Series, window: int = 20) -> pd.Series:
    return series.ewm(span=window, adjust=False).mean()

def build_summary(df: pd.DataFrame, price_col: str = 'Close') -> dict:
    close = df[price_col].astype(float)
    ema20 = compute_ema(close, 20)
    ema50 = compute_ema(close, 50)
    ema200 = compute_ema(close, 200)

    summary = {
        'rows': len(df),
        'min_price': float(close.min()),
        'max_price': float(close.max()),
        'avg_price': float(close.mean()),
        'latest_price': float(close.iloc[-1]),
        'ema20_latest': float(ema20.iloc[-1]),
        'ema50_latest': float(ema50.iloc[-1]),
        'ema200_latest': float(ema200.iloc[-1]),
    }
    return summary

def recommendation_from_ema(summary: dict) -> dict:
    price = summary['latest_price']
    ema20 = summary['ema20_latest']
    ema50 = summary['ema50_latest']
    ema200 = summary['ema200_latest']

    score = 0
    if price > ema20: score += 1
    if price > ema50: score += 1
    if price > ema200: score += 1

    if score == 3:
        decision = 'ADD'
        reason = 'Price above 20/50/200 EMA — strong uptrend.'
    elif score == 2:
        decision = 'HOLD'
        reason = 'Price above most EMAs — moderate uptrend.'
    else:
        decision = 'AVOID'
        reason = 'Price below key EMAs — weak/negative trend.'

    return {'decision': decision, 'reason': reason, 'score': score}

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "Stock Market Prediction API is live",
        "endpoints": ["/summary", "/insights", "/download/csv", "/download/pdf"]
    })


@app.route('/summary', methods=['GET'])
def summary():
    file_path = request.args.get('path')
    price_col = request.args.get('price_col', 'Close')
    df = load_file(file_path)
    summary = build_summary(df, price_col)
    return jsonify(summary)

@app.route('/insights', methods=['GET'])
def insights():
    file_path = request.args.get('path')
    price_col = request.args.get('price_col', 'Close')
    df = load_file(file_path)
    summary = build_summary(df, price_col)
    rec = recommendation_from_ema(summary)
    return jsonify({'summary': summary, 'recommendation': rec})

@app.route('/download/csv', methods=['GET'])
def download_csv():
    file_path = request.args.get('path')
    price_col = request.args.get('price_col', 'Close')
    df = load_file(file_path)
    summary = build_summary(df, price_col)
    out_df = pd.DataFrame([summary])

    buffer = io.StringIO()
    out_df.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(
        io.BytesIO(buffer.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='stock_market_prediction_summary.csv'
    )

@app.route('/download/pdf', methods=['GET'])
def download_pdf():
    file_path = request.args.get('path')
    price_col = request.args.get('price_col', 'Close')
    df = load_file(file_path)
    summary = build_summary(df, price_col)
    rec = recommendation_from_ema(summary)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    text = c.beginText(40, 750)
    text.textLine('Stock Market Prediction App')
    text.textLine('EMA-Based Summary & Insights')
    text.textLine('')

    for k, v in summary.items():
        text.textLine(f'{k}: {v}')

    text.textLine('')
    text.textLine(f"Decision: {rec['decision']}")
    text.textLine(f"Reason: {rec['reason']}")

    c.drawText(text)
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='stock_market_prediction_summary.pdf'
    )


if __name__ == '__main__':
  port = int(os.environ.get("PORT", 8000))
  app.run(host='0.0.0.0', port=port)
