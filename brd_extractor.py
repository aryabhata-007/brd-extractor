import streamlit as st
import os
import tempfile
import ffmpeg
from openai import OpenAI
from dotenv import load_dotenv
import assemblyai as aai
import time

# Page configuration
st.set_page_config(
    page_title="BizSpec Pro",
    page_icon="📄",
    layout="centered"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    
    .header-style {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #ffffff;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
    }
    
    .title-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin: 1rem 0 2.5rem 0;
    }
    
    .title {
        font-size: 1.8rem;
        color: #ffffff;
        text-align: center;
        max-width: 800px;
        line-height: 1.4;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin: 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    .processing-status {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        margin-top: 1rem !important;
        margin-bottom: 1rem;
    }
    
    .step-text {
        color: #ffffff;
        margin: 10px 0;
    }
    
    /* Custom button styles */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(to right, #FF4B2B, #FF416C);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 5px;
        transition: all 0.3s ease;
        font-size: 1.1rem;
        font-weight: 500;
        white-space: nowrap;
    }
    
    /* Clear button specific style */
    .stButton > button[data-testid="clear"] {
        background: linear-gradient(to right, #4B4B4B, #2B2B2B);
    }
    
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(255, 75, 43, 0.4);
    }
    
    /* Clear button hover */
    .stButton > button[data-testid="clear"]:hover {
        box-shadow: 0 5px 15px rgba(75, 75, 75, 0.4);
    }
    
    /* Remove any default container margins */
    .stContainer {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Function to get API keys from either environment
def get_api_keys():
    # Try to get from Streamlit secrets first (for Cloud deployment)
    # Only load from .env file if SYSTEM=LOCAL
    load_dotenv()
    if os.getenv('SYSTEM') == 'LOCAL':
        print("Loading from .env file")
        openai_key = os.getenv('OPENAI_API_KEY')
        assemblyai_key = os.getenv('ASSEMBLYAI_API_KEY')
    else:
        print("Loading from Streamlit secrets")
        openai_key = st.secrets["OPENAI_API_KEY"]
        assemblyai_key = st.secrets["ASSEMBLYAI_API_KEY"]
    return openai_key, assemblyai_key

# Initialize clients
openai_api_key, assemblyai_api_key = get_api_keys()
client = OpenAI(api_key=openai_api_key)
aai.settings.api_key = assemblyai_api_key

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
            st.error("❌ Video processing failed. Please check your video file.")
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
        st.error("❌ Transcription failed. Please try again.")
        return None

def analyze_transcript(transcript):
    prompt = """
    As an expert Business Analyst, analyze the following meeting transcript and create a detailed Business Requirements Document (BRD).
    Structure the document with the following sections:
    1. Project Overview
    2. Business Objectives
    3. Functional Requirements
    4. Technical Requirements
    5. Constraints and Assumptions
    6. Timeline and Milestones

    Meeting Transcript:
    {transcript}
    """
    try:
        response = client.chat.completions.create(
            model="o1-mini",
            messages=[
                {"role": "user", "content": prompt.format(transcript=transcript)}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        # st.error("❌ BRD generation failed. Please try again.", e)
        st.error(e)
        return None

def main():
    # Initialize session state
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'results' not in st.session_state:
        st.session_state.results = None

    # Header
    st.markdown("""
        <div class="header-style">
            <span>📄</span>
            <span>BizSpec Pro</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("""
        <div class="title-container">
            <p class="title">Transform Your Meeting Recordings Into Structured Business Requirements</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Check for API keys
    if not openai_api_key or not assemblyai_api_key:
        st.error("🔑 API keys not found! Please check your configuration.")
        return
    
    with st.form("brd_form", clear_on_submit=False):
        uploaded_file = st.file_uploader(
            "📁 Upload your meeting recording",
            type=["mp4", "mkv", "mov"],
            help="Supported formats: MP4, MKV, MOV"
        )
        
        output_format = st.selectbox(
            "📋 Select Output Format",
            ["Markdown", "JSON"],
            help="Choose the format for your BRD document"
        )
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            submit_button = st.form_submit_button("🚀 Process", use_container_width=True, type="primary")
    

    if submit_button and uploaded_file:
        st.session_state.processing_complete = False
        st.session_state.current_step = 0
        
        with st.container():
            progress_container = st.container()
            with progress_container:
                st.markdown("<div class='processing-status'>", unsafe_allow_html=True)
                st.markdown("### 🔄 Processing Status")
                progress_bar = st.progress(0)
                status_text = st.empty()
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Step 1: Extract Audio
            status_text.markdown("<p class='step-text'>⏳ **Step 1/3:** Extracting audio from video...</p>", unsafe_allow_html=True)
            progress_bar.progress(33)
            audio_path = extract_audio(uploaded_file)
            
            if audio_path:
                st.session_state.current_step = 1
                
                # Step 2: Generate Transcript
                status_text.markdown("<p class='step-text'>⏳ **Step 2/3:** Generating transcript...</p>", unsafe_allow_html=True)
                progress_bar.progress(66)
                transcript = transcribe_audio(audio_path)
                
                if transcript:
                    st.session_state.current_step = 2
                    
                    # Step 3: Generate BRD
                    status_text.markdown("<p class='step-text'>⏳ **Step 3/3:** Creating Business Requirements Document...</p>", unsafe_allow_html=True)
                    progress_bar.progress(100)
                    brd = analyze_transcript(transcript)
                    
                    if brd:
                        st.session_state.current_step = 3
                        st.session_state.processing_complete = True
                        status_text.markdown("<p class='step-text'>✅ **Processing Complete!**</p>", unsafe_allow_html=True)
                        
                        # After processing is complete, store results in session state
                        st.session_state.results = {
                            'transcript': transcript,
                            'brd': brd,
                            'output_format': output_format
                        }
                        
                        # Display Results
                        with st.expander("📝 Meeting Transcript", expanded=True):
                            st.text_area(
                                "Review the generated transcript",
                                st.session_state.results['transcript'],
                                height=200
                            )
                        
                        with st.expander("📋 Business Requirements Document", expanded=True):
                            st.text_area(
                                "Review the generated BRD",
                                st.session_state.results['brd'],
                                height=400
                            )
                        
                        # Action buttons container
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                        with col2:
                            st.download_button(
                                "💾 Download",
                                st.session_state.results['brd'].encode(),
                                file_name=f"BRD.{st.session_state.results['output_format'].lower()}",
                                use_container_width=True,
                                type="primary"
                            )
                        with col3:
                            if st.button("🔄 Clear", use_container_width=True):
                                # Reset the session state
                                st.session_state.processing_complete = False
                                st.session_state.current_step = 0
                                st.session_state.results = None
                                st.rerun()
                
                os.unlink(audio_path)
    
    elif submit_button and not uploaded_file:
        st.error("⚠️ Please upload a video file to begin processing")
    
    # Display helpful information when no file is being processed
    if not st.session_state.processing_complete:
        with st.container():
            st.markdown("### 🎯 How It Works")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                    #### 1️⃣ Upload
                    Upload your meeting recording in MP4, MKV, or MOV format
                """)
            
            with col2:
                st.markdown("""
                    #### 2️⃣ Process
                    Our AI extracts audio and generates accurate transcripts
                """)
            
            with col3:
                st.markdown("""
                    #### 3️⃣ Generate
                    Get a professionally structured BRD document
                """)

if __name__ == "__main__":
    main()
