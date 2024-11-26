from transformers import pipeline, AutoTokenizer
from langdetect import detect
import nltk

# Download NLTK sentence slicer if it is not already installed
nltk.download('punkt')

class Local_TranslationAgent:
    def __init__(self):
        # Initialize translation pipelines and tokenizers
        self.en_to_hu_translator = pipeline("translation_en_to_hu", model="Helsinki-NLP/opus-mt-en-hu")
        self.hu_to_en_translator = pipeline("translation_hu_to_en", model="Helsinki-NLP/opus-mt-hu-en")
        self.en_to_hu_tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-hu")
        self.hu_to_en_tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-hu-en")

    def get_translator(self, lang_pair):
        if lang_pair == "en_to_hu" and not self.en_to_hu_translator:
            self.en_to_hu_translator = pipeline("translation_en_to_hu", model="Helsinki-NLP/opus-mt-en-hu")
        elif lang_pair == "hu_to_en" and not self.hu_to_en_translator:
            self.hu_to_en_translator = pipeline("translation_hu_to_en", model="Helsinki-NLP/opus-mt-hu-en")
        return self.en_to_hu_translator if lang_pair == "en_to_hu" else self.hu_to_en_translator

    def translate_to_inverse(self, text: str) -> str:
        try:
            lang = detect(text)
            sentences = nltk.tokenize.sent_tokenize(text)
            translated_sentences = []
            translator = self.get_translator("en_to_hu" if lang == "en" else "hu_to_en")

            for sentence in sentences:
                tokens = self.en_to_hu_tokenizer.encode(sentence, truncation=True, max_length=512)
                sentence = self.en_to_hu_tokenizer.decode(tokens)
                translated = translator(sentence)
                translated_sentences.append(translated[0]['translation_text'])
            
            final_translation = " ".join(sent.strip() for sent in translated_sentences)
            return final_translation
        except Exception as e:
            return f"Hiba történt a szöveg fordítása közben: {e}"



    def split_text_into_chunks(self, text: str, tokenizer, max_length: int = 512):
        """
        Split the text into chunks that do not exceed the max token length.
        """
        tokens = tokenizer.encode(text)
        chunks = []
        for i in range(0, len(tokens), max_length):
            chunk_tokens = tokens[i:i + max_length]
            chunks.append(tokenizer.decode(chunk_tokens))
        return chunks
    
    def instant_translate_to_hungarian(self, text: str) -> str:
        """
        Translate English to Hungarian, handling long texts by splitting into chunks.
        """
        try:
            # Split the text into manageable chunks
            chunks = self.split_text_into_chunks(text, self.en_to_hu_tokenizer, max_length=512)
            translated_chunks = []

            # Translate each chunk
            for chunk in chunks:
                translated = self.en_to_hu_translator(chunk)
                translated_chunks.append(translated[0]['translation_text'])

            # Combine the translated chunks
            return " ".join(translated_chunks)
        except Exception as e:
            return f"An error occurred during English-to-Hungarian translation: {e}"

    def instant_translate_to_english(self, text: str) -> str:
        """
        Translate Hungarian to English, handling long texts by splitting into chunks.
        """
        try:
            # Split the text into manageable chunks
            chunks = self.split_text_into_chunks(text, self.hu_to_en_tokenizer, max_length=512)
            translated_chunks = []

            # Translate each chunk
            for chunk in chunks:
                translated = self.hu_to_en_translator(chunk)
                translated_chunks.append(translated[0]['translation_text'])

            # Combine the translated chunks
            return " ".join(translated_chunks)
        except Exception as e:
            return f"An error occurred during Hungarian-to-English translation: {e}"

