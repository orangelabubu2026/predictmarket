import streamlit as st
import requests

#BACKEND_URL = 'http://localhost:8000'
BACKEND_URL = 'https://predictmarket-v1.onrender.com'


st.title('Stock Market Prediction App')

file_path = st.text_input('Enter full file path (CSV or Excel)')
price_col = st.text_input('Price column name', value='Close')

if st.button('Get Summary & Insights'):
    params = {'path': file_path, 'price_col': price_col}
    resp = requests.get(f'{BACKEND_URL}/insights', params=params)

    if resp.status_code == 200:
        data = resp.json()
        st.subheader('Summary')
        st.json(data['summary'])

        st.subheader('EMA-Based Recommendation')
        st.write(data['recommendation'])
    else:
        st.error('Backend error.')

st.markdown('---')
st.subheader('Download Summary')

if st.button('Download CSV'):
    params = {'path': file_path, 'price_col': price_col}
    resp = requests.get(f'{BACKEND_URL}/download/csv', params=params)
    st.download_button('Save CSV', resp.content, 'stock_market_prediction_summary.csv')

if st.button('Download PDF'):
    params = {'path': file_path, 'price_col': price_col}
    resp = requests.get(f'{BACKEND_URL}/download/pdf', params=params)
    st.download_button('Save PDF', resp.content, 'stock_market_prediction_summary.pdf')

@app.route("/", methods=["GET"])
def home():
    return {"status": "running", "message": "API is live"}

