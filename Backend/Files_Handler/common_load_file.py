import os
import zipfile
import json
import PyPDF2
import docx
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pydub import AudioSegment
import speech_recognition as sr
import pytesseract
from moviepy.editor import VideoFileClip
from PIL import Image
from typing import Dict
import shutil
from Summary_Handler.local_translatorAgent import Local_TranslationAgent

# Set up paths for Tesseract OCR and ffmpeg
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
AudioSegment.converter = r'C:\Program Files\Ffmpeg\ffmpeg.exe'


def process_files_in_directory(file_path: str) -> Dict[str, str]:
    """
    Végigmegy a megadott könyvtáron, feldolgozza az összes fájlt, és egy dictionary-t ad vissza,
    amely tartalmazza a fájlneveket és azok tartalmát.
    """
    if not os.path.isdir(file_path):
        raise FileNotFoundError(f"A megadott könyvtár nem található: {file_path}")

    file_contents = {}

    for filename in os.listdir(file_path):
        full_path = os.path.join(file_path, filename)

        if os.path.isfile(full_path):
            print(f"Fájl feldolgozása: {filename}")
            try:

                content = extract_text_from_file_sync(full_path)
                file_contents[filename] = content
            except Exception as e:
                print(f"Hiba történt a {filename} fájl feldolgozása során: {str(e)}")
                file_contents[filename] = f"Error processing file: {str(e)}"

    try:
        shutil.rmtree(file_path)
        print(f"Sikeresen törölve: {file_path}")
    except Exception as e:
        print(f"Hiba történt a {file_path} törlése során: {str(e)}")

    return file_contents

def extract_text_from_file_sync(file_path: str) -> str:
    """
    Szinkron módon kinyeri a fájl tartalmát a kiterjesztés alapján.
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif file_extension == '.txt':
        return extract_text_from_txt(file_path)
    elif file_extension == '.json':
        return extract_text_from_json(file_path)
    elif file_extension in ['.mp3', '.wav']:
        return extract_text_from_audio(file_path)
    elif file_extension == '.html':
        return extract_text_from_html(file_path)
    elif file_extension == '.epub':
        return extract_text_from_epub(file_path)
    elif file_extension in ['.zip', '.7zip']:
        return extract_text_from_zip(file_path)
    elif file_extension in ['.mp4', '.wmv']:
        return extract_text_from_video(file_path)
    elif file_extension in ['.png', '.jpg', '.jpeg']:
        return extract_text_from_image(file_path)
    else:
        return "Unsupported file format"


# Extract text from PDF
def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

# Extract text from DOCX/DOC
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Extract text from TXT
def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Extract text from JSON
def extract_text_from_json(file_path):
    translator_agent = Local_TranslationAgent()
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        translated_to_eng = translator_agent.instant_translate_to_english(json.dumps(data, indent=2))
    return translated_to_eng

# Extract text from MP3/WAV (Speech to Text)
def extract_text_from_audio(file_path):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(file_path)
    audio.export("temp.wav", format="wav")

    with sr.AudioFile("temp.wav") as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="en-US")
            return text
        except sr.UnknownValueError:
            return "Speech recognition could not understand the audio."
        except sr.RequestError as e:
            return f"Speech recognition service is unavailable: {str(e)}"
        finally:
            os.remove("temp.wav")

# Extract text from video
def extract_text_from_video(file_path):
    try:
        video = VideoFileClip(file_path)
        audio = video.audio
        audio.write_audiofile("temp.wav")
        audio.close()
        video.close()
    except Exception as e:
        return f"Error extracting audio: {str(e)}"

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile("temp.wav") as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="en-US")
            return text
    except sr.UnknownValueError:
        return "Speech recognition could not understand the audio."
    except sr.RequestError as e:
        return f"Speech recognition service is unavailable: {str(e)}"
    finally:
        if os.path.exists("temp.wav"):
            os.remove("temp.wav")

# Extract text from HTML
def extract_text_from_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        return soup.get_text()

# Extract text from EPUB
def extract_text_from_epub(file_path):
    book = epub.read_epub(file_path)
    text = ''
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_body_content(), 'html.parser')
        text += soup.get_text()
    return text

# Extract text from ZIP files
def extract_text_from_zip(file_path):
    text = ""
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall("temp_unzip")
        for root, dirs, files in os.walk("temp_unzip"):
            for file in files:
                extracted_file = os.path.join(root, file)
                # Használjuk a szinkron verziót a fájl tartalmának kinyerésére
                text += extract_text_from_file_sync(extracted_file)
    return text


# Extract text from images (PNG, JPG, JPEG) using OCR
def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from PNG, JPG, JPEG images.
    
    :param file_path: Path to the image file.
    :return: Text extracted from the image.
    """
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")
