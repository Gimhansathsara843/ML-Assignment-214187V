from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# Load model and encoder
MODEL_PATH = 'model.joblib'
ENCODER_PATH = 'encoder.joblib'

if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
else:
    model = None
    encoder = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if not model or not encoder:
        return jsonify({'success': False, 'error': 'Model not loaded.'})
    
    try:
        data = request.json
        
        # Prepare input data for the model
        input_df = pd.DataFrame({
            'RAM_GB': [float(data['ram'])],
            'Storage_GB': [float(data['storage'])],
            'Brand': [data['brand']],
            'Operating system': [data['os']],
            'Warranty': [data['warranty']],
            'Condition': [data['condition']],
            'Connectivity': [data['connectivity']]
        })
        
        # Encode categorical features
        cat_cols = ['Brand', 'Operating system', 'Warranty', 'Condition', 'Connectivity']
        input_df[cat_cols] = encoder.transform(input_df[cat_cols])
        
        # Predict
        prediction = model.predict(input_df)[0]
        prediction = max(0, round(float(prediction), -2))
        
        # Simple Insight: compare to an average price for the brand
        # (This is just for UX/Bonus 'details')
        brand_avg = {
            'Apple': 185000, 'Samsung': 95000, 'Xiaomi': 65000, 
            'Vivo': 55000, 'Oppo': 52000, 'Huawei': 45000, 'Realme': 48000
        }
        avg = brand_avg.get(data['brand'], 85000)
        diff = prediction - avg
        insight = f"This is LKR {abs(diff):,.0f} {'above' if diff > 0 else 'below'} the typical {data['brand']} market average."
        
        return jsonify({
            'success': True, 
            'prediction': prediction,
            'insight': insight,
            'confidence': 'Moderate' # Based on R2 ~0.56
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Use host 0.0.0.0 for external access if needed, port 5000
    app.run(debug=True, port=5000)
