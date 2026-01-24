import datetime
import json
import os

import cv2
import ollama
from faster_whisper import WhisperModel
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy import VideoFileClip

# Configuration
VIDEO_FOLDER = "videos"
STATE_FILE = "schedule_state.json"
CLIENT_SECRETS_FILE = "client_secrets.json"
OLLAMA_MODEL = "qwen3-vl:2b"  # Needs to be a vision model to see the snapshot
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
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
    video = VideoFileClip(video_path)
    audio_path = "temp_audio.mp3"
    video.audio.write_audiofile(audio_path, logger=None)
    
    # Load lightweight model ('tiny' or 'base' is enough for context)
    # run on cpu always, the model is small so gpu acceleration is not needed
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    # Transcribe
    segments, _ = model.transcribe(audio_path, beam_size=5)
    
    # Clean up
    transcript = " ".join([segment.text for segment in segments])
    os.remove(audio_path)
    
    return transcript

def generate_metadata(video_path):
    print("Generating metadata...")
    # Grab a frame
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return "Daily Short", "Cool video #shorts"
    
    # Save temp frame
    temp_img = "temp_view_test.jpg"
    cv2.imwrite(temp_img, frame)

    # Get transcript
    transcript = get_transcript(video_path)

    # Ask Ollama (est. 4min per video on cpu, 30s on gpu)
    print("Asking Ollama to generate title/description...")
    prompt = prompt = f"""
                        Analyze the image and the transcript below.
                        TRANSCRIPT: "{transcript}"

                        INSTRUCTIONS:
                        1. The transcript contains the actual topic. Use it as your primary source.
                        2. The image just shows the visual style.
                        3. Create a viral YouTube Shorts title and 1-sentence description.

                        OUTPUT FORMAT (Valid JSON only):
                        {{"title": "[Topic] Tips/Tricks/Hacks or Explaining [Topic]", "description": "Explaining how [topic] works with tips."}}
                        """
    
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[
            {'role': 'user', 'content': prompt, 'images': [temp_img]}
        ], format='json', options={'num_gpu': 99})
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
    finally:
        if os.path.exists(temp_img):
            os.remove(temp_img)

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
    print(f"Estimated time on CPU: {len(videos) * 4} minutes.")
    print(f"Estimated time on GPU: {len(videos)} minutes.")

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