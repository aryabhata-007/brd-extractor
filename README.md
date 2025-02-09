# BRD Extractor

## Overview
The BRD Extractor is a Streamlit-based application that allows users to upload meeting videos, extract audio, transcribe the content, and generate a structured Business Requirement Document (BRD). This document provides a step-by-step explanation of how the application functions.

## Features
- **Video Upload:** Users can upload meeting recordings in MP4, MKV, or MOV formats.
- **Audio Extraction:** The uploaded video is processed to extract its audio as an MP3 file.
- **Speech-to-Text Transcription:** The extracted audio is transcribed into text.
- **BRD Generation:** The transcript is analyzed using OpenAI to generate a structured Business Requirement Document.
- **Download Option:** Users can download the BRD in Markdown or JSON format.

---

## Detailed Process

### 1. Video Upload
Users can upload a meeting video through an intuitive interface. Once a file is uploaded, the application processes it for audio extraction.

### 2. Audio Extraction
The application extracts audio from the uploaded video using ffmpeg and saves it as an MP3 file.

### 3. Speech-to-Text Transcription
The extracted MP3 file is sent to whisper model, which converts spoken words into text.

### 4. BRD Analysis
Once the transcript is available, inhouse LLM analyzes it to extract structured business requirements. This step transforms the raw text into a well-organized Business Requirement Document (BRD), capturing key discussions, requirements, and action points.

### 5. Tech Stack Used
Frontend:
Streamlit – A Python-based framework for building interactive web applications.

Backend:
Python – The core programming language used for scripting and automation.
FFmpeg – A multimedia processing tool for extracting audio from video files.
Whisper – A speech-to-text model for converting audio into transcribed text.
Inhouse LLM – For analyzing transcripts and generating structured BRDs.

---
