import datetime
import json
import os

import ollama
from faster_whisper import WhisperModel
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy import VideoFileClip

# Configuration
VIDEO_FOLDER = "videos"
STATE_FILE = "schedule_state.json"
CLIENT_SECRETS_FILE = "client_secrets.json"
OLLAMA_MODEL = "gemma3:1b"  # Text-only model
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing access token...")
            creds.refresh(Request())
        else:
            print("Fetching new tokens...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    print("Authentication successful!")
    return build("youtube", "v3", credentials=creds)

def get_next_schedule_time():
    # Load state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        last_date = datetime.datetime.fromisoformat(state['last_scheduled_date'])
        next_date = last_date + datetime.timedelta(days=1)
    else:
        # Start from today if no state exists
        next_date = datetime.datetime.now()

    # Force 12:00 PM (noon) roughly matches CEST noon depending on your local time
    # YouTube expects ISO 8601 (YYYY-MM-DDThh:mm:ss.sZ)
    scheduled_time = next_date.replace(hour=12, minute=0, second=0, microsecond=0)
    
    return scheduled_time

def get_transcript(video_path):
    print("Extracting video transcript...")

    # Extract audio from video temporarily
    try:
        video = VideoFileClip(video_path)
        audio_path = "temp_audio.mp3"
        video.audio.write_audiofile(audio_path, logger=None)
    finally:
        if 'video' in locals():
            video.close()
    
    # Load lightweight model ('tiny' or 'base' is enough for context)
    # run on cpu always, the model is small so gpu acceleration is not needed
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    # Transcribe
    segments, _ = model.transcribe(audio_path, beam_size=5)
    
    # Clean up
    transcript = " ".join([segment.text for segment in segments])
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    return transcript

def generate_metadata(video_path):
    print("Generating metadata...")

    # Get transcript
    transcript = get_transcript(video_path)

    # Ask Ollama 
    print("Asking Ollama to generate title/description...")
    prompt = f"""
    You are a YouTube Shorts creator. The text below is the spoken content of your video.
    CONTENT: "{transcript}"

    TASK:
    Write a viral Title and Description to post on YouTube.

    CRITICAL RULES:
    1. Speak directly to the audience (use "You", "Your").
    2. STRICTLY FORBIDDEN: Do not use words like "transcript", "video", "audio", "summary", or "text".
    3. Make it sound immediate and urgent.

    EXAMPLE OUTPUT (Follow this style):
    {{"title": "Your Phone is DIRTY 🦠", "description": "You won't believe how much bacteria is crawling on your screen right now."}}

    OUTPUT FORMAT:
    Return ONLY valid JSON.
    """
    
    # Initialize client explicitly
    try:
        host = os.environ.get('OLLAMA_HOST', 'http://host.docker.internal:11434')
        if "127.0.0.1" in host or "localhost" in host:
             # Fallback if env var is weird, but try to use what's given
             pass
        
        client = ollama.Client(host=host)
        
        response = client.chat(model=OLLAMA_MODEL, messages=[
            {'role': 'user', 'content': prompt}
        ], format='json', options={'num_gpu': 0}) # Force CPU to save memory
        content = response['message']['content']
        print(f"Ollama response: {content}")
        
        data = json.loads(content)
        if 'title' in data and 'description' in data:
            title = data['title']
            desc = data['description']
        else:
            title = "Daily Short"
            desc = "Cool video #shorts"
            
        return title.strip(), desc.strip() + " #shorts"
    except Exception as e:
        print(f"Metadata generation failed: {e}")
        return "Daily Upload", "Check this out! #shorts"

def upload_video(youtube, path, date_time):
    title, description = generate_metadata(path)
    print(f"Uploading: {title} for {date_time}")

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "28", # Science & Technology
        },
        "status": {
            "privacyStatus": "private", # Must be private to schedule via API
            "publishAt": date_time.isoformat() + "Z", # UTC time
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )
    response = request.execute()
    return response

def main():
    print("Starting script...")
    youtube = get_authenticated_service()
    videos = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith(('.mp4', '.mov'))]
    print(f"Found {len(videos)} videos to process.")
    print(f"Estimated time on CPU: {len(videos)} minutes.") # 1 min per video
    # print(f"Estimated time on GPU: {len(videos) / 12} minutes.") # 20s per video, but usually does not use gpu acceleration

    current_schedule = get_next_schedule_time()

    for video in videos:
        print(f"Processing video: {video}. This may take a while.")
        video_path = os.path.join(VIDEO_FOLDER, video)
        
        # If upload fails, video will not be deleted
        try:
            upload_video(youtube, video_path, current_schedule)
            
            # Delete video after upload
            os.remove(video_path)
            
            # Update Schedule State
            with open(STATE_FILE, 'w') as f:
                json.dump({'last_scheduled_date': current_schedule.isoformat()}, f)
            
            # Increment for next loop
            current_schedule += datetime.timedelta(days=1)
            
        except Exception as e:
            print(f"Failed to upload {video}: {e}")
            # break the loop if upload fails
            break

if __name__ == "__main__":
    main()