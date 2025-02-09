import streamlit as st
import os
import tempfile
import ffmpeg
from openai import OpenAI
from dotenv import load_dotenv
import assemblyai as aai

# Load environment variables
load_dotenv()

# Initialize clients - get API keys from environment variables
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
aai.settings.api_key = st.secrets["ASSEMBLYAI_API_KEY"]

def extract_audio(video_file):
    # Create a temporary file for the uploaded video
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        temp_video_path = temp_video.name

    # Create a temporary file for the output audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
        output_path = audio_file.name
        
        try:
            stream = ffmpeg.input(temp_video_path)
            stream = ffmpeg.output(stream, output_path, acodec='libmp3lame')
            ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
        except ffmpeg.Error as e:
            st.error(f"An error occurred while processing the video: {str(e.stderr.decode('utf-8'))}")
            return None
        finally:
            os.unlink(temp_video_path)
            
    return output_path

def transcribe_audio(audio_path):
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_path)
        return transcript.text
    except Exception as e:
        st.error(f"An error occurred during transcription: {str(e)}")
        return None

def analyze_transcript(transcript):
    prompt = f"""
    You are an AI that extracts structured BRDs from meeting transcripts.
    Extract business discussions from the following transcript and generate a structured Business Requirement Document (BRD):
    {transcript}
    """
    response = client.chat.completions.create(
        model="o1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def main():
    st.markdown("<h1 style='text-align: center;'>BRD Extractor</h1>", unsafe_allow_html=True)
    
    if not os.getenv('OPENAI_API_KEY') or not os.getenv('ASSEMBLYAI_API_KEY'):
        st.error("API keys not found! Please check your .env file.")
        return
    
    with st.form("brd_form"):
        uploaded_file = st.file_uploader("Upload a meeting video", type=["mp4", "mkv", "mov"])
        output_format = st.selectbox("Select Output Format", ["Markdown", "JSON"])
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            submit_button = st.form_submit_button("Submit", use_container_width=True, type="primary")
    
    if submit_button and uploaded_file:
        with st.spinner("Processing your video..."):
            st.write("Extracting audio...")
            audio_path = extract_audio(uploaded_file)
            
            if audio_path:
                st.success("Audio extracted successfully!")
                
                st.write("Generating transcript...")
                transcript = transcribe_audio(audio_path)
                if transcript:
                    st.text_area("Transcript", transcript, height=300)
                    
                    st.write("Analyzing transcript...")
                    brd = analyze_transcript(transcript)
                    st.text_area("Business Requirement Document", brd, height=500)
                    
                    col1, col2, col3 = st.columns([2, 1, 2])
                    with col2:
                        st.download_button(
                            "Download",
                            brd.encode(),
                            file_name=f"BRD.{output_format.lower()}",
                            use_container_width=True,
                            type="primary"
                        )
                
                os.unlink(audio_path)
    
    elif submit_button and not uploaded_file:
        st.error("Please upload a video file first!")

if __name__ == "__main__":
    main()
