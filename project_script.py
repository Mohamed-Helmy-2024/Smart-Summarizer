import streamlit as st
import mimetypes
import speech_recognition as sr
import os
import filecmp
import pyttsx3
from transformers import pipeline 
import pdfplumber
from docx import Document
import re
from google import genai

client = genai.Client(api_key="AIzaSyB_wBnzAfz2aUt--Y3u4Em__sRiXcr7__A")

# pipe = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")



st.title("Intelligent Lectures Summarizer")

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + " "
            text = text.replace('\n', ' ')
    return text
def extract_text_from_voice(audio_path):
    filename = audio_path
    r = sr.Recognizer()
    try:
        with sr.AudioFile(filename) as source:
            print("Processing audio file...")
            audio_data = r.record(source)  
            
            text = r.recognize_google(audio_data, language="en-US")  
            return text        

    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))

def save_audio(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 100)   
    engine.setProperty('volume', 1.0)
    engine.save_to_file(text, 'Summary.wav')
    engine.runAndWait() 
    engine.stop()

def clean_text(text):
    return re.sub(r'[#`*]+', '', text)

def save_text(text):
    response_text = clean_text(text)
    survey_title = response_text.splitlines()[0]
    response_body = "\n".join(response_text.splitlines()[1:])

    formatted_summary = f"{survey_title}\n\n{clean_text(text)}"

    doc = Document()
    doc.add_paragraph(formatted_summary)
    file_name = "summary_text.docx"
    doc.save(file_name)

    print(f"Output saved to {file_name}")

def summarize_text(text):

    summarized_chunk = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=f"""
Please read the following text and provide a concise summary that captures the key points clearly and accurately:
{text}
Summarize it in 20 percentage of original sentences.
""")
    return summarized_chunk.text


def split_text(text, max_words=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i+max_words])
        chunks.append(chunk)
    return chunks

def summary(text):
    text_chunks = split_text(text, max_words=500)
    summarized_chunks = [summarize_text(chunk) for chunk in text_chunks]
    final_summary = " ".join(summarized_chunks)
    return final_summary

def main():
    st.sidebar.title("Upload your files(wav or pdf only)")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf","wav"])
    
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension == ".pdf":
            with open("uploaded.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            text = extract_text_from_pdf("uploaded.pdf")
            st.write("Extracted Text from PDF:")
            st.write(text)

        elif file_extension in [".wav"]:
            with open("uploaded.wav", "wb") as f:
                f.write(uploaded_file.getbuffer())
            text = extract_text_from_voice("uploaded.wav")
            st.write("Extracted Text from Audio:")
            st.write(text)
        
        else:
            st.error("Unsupported file type. Please upload a PDF, DOCX, WAV, MP3, or M4A file.")
            return
        
        if text:
            if st.button("Summarize"):
                with st.spinner("Summarizing..."):
                    summarized_text = summary(text)
                    st.subheader("Summarized Text:")
                    st.write(summarized_text)
                    save_text(summarized_text)
                    save_audio(summarized_text)
                    audio_file = open('Summary.wav', 'rb')
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format='audio/wav')
                    st.success("Summary saved as summary.docx and audio saved as summary.wav")


main()

