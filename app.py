from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import re
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# Initialize SQLAlchemy globally
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize db with the app
    db.init_app(app)

    return app

# Create the app
app = create_app()

# Define the Summary model
class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_url = db.Column(db.String(255), unique=True, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    summary_type = db.Column(db.String(50), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.get_json()
        youtube_url = data.get('url')
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL provided'})

        # Check if summary already exists in the database
        existing_summary = Summary.query.filter_by(video_url=youtube_url).first()
        if existing_summary:
            return jsonify({'summary': existing_summary.summary})

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        except NoTranscriptFound:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])
            except NoTranscriptFound:
                return jsonify({'error': 'No transcript available for the video.'})

        transcript_text = " ".join([t['text'] for t in transcript])
        if not transcript_text:
            return jsonify({'error': 'Transcript is empty.'})

        tokenizer = AutoTokenizer.from_pretrained("t5-small")
        model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")
        max_token_length = 512
        tokens = tokenizer(transcript_text, return_tensors='pt', truncation=True, max_length=max_token_length)
        input_ids = tokens['input_ids'][0]
        chunk_size = max_token_length - 10
        chunks = [input_ids[i:i + chunk_size] for i in range(0, len(input_ids), chunk_size)]

        summarizer = pipeline('summarization', model=model, tokenizer=tokenizer)
        summary_chunks = []
        for chunk in chunks:
            chunk_text = tokenizer.decode(chunk, skip_special_tokens=True)
            summary = summarizer(chunk_text, max_length=150, min_length=30, do_sample=False)
            if summary and 'summary_text' in summary[0]:
                summary_chunks.append(summary[0]['summary_text'])

        combined_summary = " ".join(summary_chunks)
        if not combined_summary:
            return jsonify({'error': 'Failed to generate summary.'})

        # Return summary without saving for testing purpose
        return jsonify({'summary': combined_summary})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/summary')
def display_summary():
    summary = request.args.get('summary', '')
    return render_template('summary.html', summary=summary)

@app.route('/save_summary', methods=['POST'])
def save_summary():
    try:
        data = request.get_json()
        summary_text = data.get('summary')
        video_url = data.get('video_url')
        summary_type = data.get('type')

        if not summary_text or not video_url or not summary_type:
            return jsonify({'error': 'Summary, video URL, or type missing'})

        # Check if a summary with this video_url already exists
        existing_summary = Summary.query.filter_by(video_url=video_url).first()
        if existing_summary:
            # Update the existing summary
            existing_summary.summary = summary_text
            existing_summary.summary_type = summary_type
        else:
            # Create a new summary
            new_summary = Summary(video_url=video_url, summary=summary_text, summary_type=summary_type)
            db.session.add(new_summary)
        
        db.session.commit()  # Commit changes to the database

        return jsonify({'message': 'Summary saved successfully!'})
    except Exception as e:
        db.session.rollback()  # Rollback changes if an error occurs
        return jsonify({'error': str(e)})

@app.route('/summaries')
def list_summaries():
    summaries = {}
    all_summaries = Summary.query.all()
    
    for summary in all_summaries:
        if summary.summary_type not in summaries:
            summaries[summary.summary_type] = []
        summaries[summary.summary_type].append(summary)
    
    return render_template('data.html', summaries=summaries)

def extract_video_id(url):
    video_id_match = re.search(r'(?<=v=)[^&#]+', url) or re.search(r'(?<=be/)[^&#]+', url)
    return video_id_match.group(0) if video_id_match else None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
