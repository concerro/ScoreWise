import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg before importing pyplot

from flask import Flask, render_template, request, jsonify, send_file, make_response, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import PyPDF2
from openai import OpenAI
import json
import markdown2
import matplotlib.pyplot as plt
import io
import base64
import tempfile
from markupsafe import Markup
from urllib.parse import unquote
from weasyprint import HTML
import stripe
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key')

# Use environment variable for API key
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
YOUR_DOMAIN = os.environ.get('APP_URL', 'http://127.0.0.1:5003')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def analyze_credit_report(text):
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": (
                "You are a world-class financial analyst specializing in credit reports. "
                "Analyze the given credit report and provide a detailed summary. "
                "In your output, ensure the following: "
                "1. Give a concise executive summary of the person's credit health and risks. "
                "2. List at least five highly actionable, personalized steps to improve their credit, referencing specific numbers from the report. "
                "3. For each negative item or risk, provide a clear explanation and a step-by-step action plan to resolve it (with links to reputable resources if possible). "
                "4. Provide a 90-day improvement roadmap with monthly milestones. "
                "5. Offer tailored advice for maximizing approval odds for loans, credit cards, or mortgages, based on their profile. "
                "6. Include a myth-busting FAQ section about credit scores and reports. "
                "7. Make the advice practical, detailed, and worth at least $99—do not be generic. "
                "8. Use clear, confident, and encouraging language."
            )},
            {"role": "user", "content": f"Analyze the following credit report:\n\n{text}"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "credit_report_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "credit_score": {"type": "integer"},
                        "credit_utilization": {"type": "number"},
                        "payment_history": {
                            "type": "object",
                            "properties": {
                                "on_time": {"type": "integer"},
                                "late": {"type": "integer"}
                            },
                            "required": ["on_time", "late"],
                            "additionalProperties": False
                        },
                        "avg_account_age": {"type": "number"},
                        "account_types": {
                            "type": "object",
                            "additionalProperties": {"type": "integer"}
                        },
                        "negative_items": {"type": "integer"},
                        "detailed_analysis": {"type": "string"},
                        "improvement_advice": {"type": "string"},
                        "action_steps": {"type": "array", "items": {"type": "string"}},
                        "negative_item_plans": {"type": "array", "items": {"type": "string"}},
                        "roadmap_90_days": {"type": "array", "items": {"type": "string"}},
                        "approval_advice": {"type": "string"},
                        "faq": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": [
                        "credit_score", "credit_utilization", "payment_history", "avg_account_age", "negative_items", "detailed_analysis", "improvement_advice", "action_steps", "negative_item_plans", "roadmap_90_days", "approval_advice", "faq"
                    ],
                    "additionalProperties": False
                }
            }
        }
    )
    return json.loads(response.choices[0].message.content)


def generate_charts(data):
    charts = {}
    
    # Credit Score Chart
    plt.figure(figsize=(8, 4))
    plt.bar(['Credit Score'], [data['credit_score']])
    plt.title('Credit Score')
    plt.ylim(300, 850)
    charts['credit_score'] = get_chart_image()
    plt.close()

    # Credit Utilization Chart
    plt.figure(figsize=(8, 4))
    plt.bar(['Credit Utilization'], [data['credit_utilization']])
    plt.title('Credit Utilization (%)')
    plt.ylim(0, 100)
    charts['credit_utilization'] = get_chart_image()
    plt.close()

    # Payment History Chart
    plt.figure(figsize=(8, 4))
    payment_data = data['payment_history']
    on_time = payment_data.get('on_time', 0)
    late = payment_data.get('late', 0)
    # Avoid pie chart crash if both are zero or NaN
    try:
        on_time = int(on_time) if on_time is not None and not (isinstance(on_time, float) and (on_time != on_time)) else 0
        late = int(late) if late is not None and not (isinstance(late, float) and (late != late)) else 0
    except Exception:
        on_time, late = 0, 0
    if (on_time + late) > 0:
        plt.pie([on_time, late], labels=['On Time', 'Late'], autopct='%1.1f%%')
    else:
        plt.pie([1], labels=['No Data'], colors=['#E5E7EB'])
    plt.title('Payment History')
    charts['payment_history'] = get_chart_image()
    plt.close()

    # Account Types Chart (if available)
    if 'account_types' in data and data['account_types']:
        plt.figure(figsize=(8, 6))
        account_types = data['account_types']
        plt.pie(account_types.values(), labels=account_types.keys(), autopct='%1.1f%%')
        plt.title('Account Types')
        charts['account_types'] = get_chart_image()
        plt.close()

    return charts

def get_chart_image():
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()



@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Generate a unique analysis ID and store in session
        analysis_id = str(uuid.uuid4())
        session['analysis_id'] = analysis_id
        session['filename'] = filename
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid file'})

@app.route('/analysis', methods=['GET'])
def analysis_page():
    filename = session.get('filename')
    analysis_id = session.get('analysis_id')
    if not filename or not analysis_id:
        return redirect(url_for('index'))
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return redirect(url_for('index'))
    # Paths for saving analysis and charts
    user_data_dir = os.path.join('user_data', analysis_id)
    os.makedirs(user_data_dir, exist_ok=True)
    analysis_json_path = os.path.join(user_data_dir, 'analysis.json')
    charts_json_path = os.path.join(user_data_dir, 'charts.json')
    # If analysis already exists, load it
    if os.path.exists(analysis_json_path) and os.path.exists(charts_json_path):
        with open(analysis_json_path, 'r') as f:
            result = json.load(f)
        with open(charts_json_path, 'r') as f:
            charts = json.load(f)
    else:
        text = extract_text_from_pdf(file_path)
        result = analyze_credit_report(text)
        charts = generate_charts(result)
        with open(analysis_json_path, 'w') as f:
            json.dump(result, f)
        with open(charts_json_path, 'w') as f:
            json.dump(charts, f)
    return render_template('analysis.html', analysis=result['detailed_analysis'],
                           improvement_advice=result['improvement_advice'],
                           charts=charts, data=result)

@app.route('/download', methods=['POST'])
def download_pdf():
    import tempfile
    from weasyprint import HTML
    analysis_id = session.get('analysis_id')
    if not analysis_id:
        return redirect(url_for('index'))
    user_data_dir = os.path.join('user_data', analysis_id)
    analysis_json_path = os.path.join(user_data_dir, 'analysis.json')
    charts_json_path = os.path.join(user_data_dir, 'charts.json')
    if not (os.path.exists(analysis_json_path) and os.path.exists(charts_json_path)):
        filename = session.get('filename')
        if not filename:
            return redirect(url_for('index'))
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return redirect(url_for('index'))
        text = extract_text_from_pdf(file_path)
        result = analyze_credit_report(text)
        charts = generate_charts(result)
        os.makedirs(user_data_dir, exist_ok=True)
        with open(analysis_json_path, 'w') as f:
            json.dump(result, f)
        with open(charts_json_path, 'w') as f:
            json.dump(charts, f)
    else:
        with open(analysis_json_path, 'r') as f:
            result = json.load(f)
        with open(charts_json_path, 'r') as f:
            charts = json.load(f)
    rendered = render_template(
        'analysis.html',
        data=result,
        charts=charts
    )
    rendered = rendered.replace('Download PDF', '')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
        HTML(string=rendered).write_pdf(tmp_pdf.name)
        tmp_pdf.seek(0)
        response = send_file(tmp_pdf.name, as_attachment=True, download_name='credit_analysis.pdf')
    return response

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': 9900,
                'product_data': {
                    'name': 'Premium Credit Analysis PDF',
                    'description': 'Personalized, actionable credit analysis and PDF report.'
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=YOUR_DOMAIN + '/success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=YOUR_DOMAIN + '/',
    )
    return jsonify({'id': checkout_session.id})

@app.route('/success')
def payment_success():
    # After payment, redirect to analysis
    return redirect(url_for('analysis_page'))

if __name__ == "__main__":
    import sys
    port = int(os.environ.get("PORT", 5000))
    # Allow port override from command line
    if len(sys.argv) > 1 and sys.argv[1] == '--port' and len(sys.argv) > 2:
        port = int(sys.argv[2])
    app.run(host="0.0.0.0", port=port, debug=True)