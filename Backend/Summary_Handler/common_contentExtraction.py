import spacy
from transformers import pipeline
from gensim import corpora, models
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from keybert import KeyBERT
import nltk
from concurrent.futures import ThreadPoolExecutor, as_completed
from Summary_Handler.local_translatorAgent import Local_TranslationAgent

# NLTK download
nltk.download('punkt')
nltk.download('stopwords')

# Load spaCy language model
nlp = spacy.load("en_core_web_sm")

def extract_entities(text:str):
    """
    NER analysis.
    """
    local_translator = Local_TranslationAgent()

    # Text analysis
    doc = nlp(text)
    
    # List of entities
    persons = []
    norps = []
    facs = []
    orgs = []
    gpes = []
    locs = []
    products = []
    events = []
    laws = []
    works_of_art = []
    languages = []
    times = []
    monies = []
    ordinals = []
    
    
    # Extract entities
    for ent in doc.ents:
        hun_entity= local_translator.instant_translate_to_hungarian(ent.text)
        if ent.label_ == "PERSON":
            if ent.text and ent.text[0].isupper():
                persons.append(hun_entity)
        elif ent.label_ == "NORP":
            norps.append(hun_entity)
        elif ent.label_ == "FAC":
            facs.append(hun_entity)
        elif ent.label_ == "ORG":
            orgs.append(hun_entity)
        elif ent.label_ == "GPE":
            gpes.append(hun_entity)
        elif ent.label_ == "LOC":
            locs.append(hun_entity)
        elif ent.label_ == "PRODUCT":
            products.append(hun_entity)
        elif ent.label_ == "EVENT":
            events.append(hun_entity)
        elif ent.label_ == "LAW":
            laws.append(hun_entity)
        elif ent.label_ == "WORK_OF_ART":
            works_of_art.append(hun_entity)
        elif ent.label_ == "LANGUAGE":
            languages.append(hun_entity)
        elif ent.label_ == "TIME":
            times.append(hun_entity)
        elif ent.label_ == "MONEY":
            monies.append(hun_entity)
        elif ent.label_ == "ORDINAL":
            ordinals.append(hun_entity)
    
    # Dictionary for different categories
    results = {
        "**Nevek:**": set(persons),
        "**Nemzeti, vallási vagy politikai csoportok:**": set(norps),
        "**Épületek, létesítmények:**": set(facs),
        "**Szervezetek, cégek, intézmények:**": set(orgs),
        "**Földrajzi-politikai entitások:**": set(gpes),
        "**Helyek, lokációk:**": set(locs),
        "**Termékek, tárgyak:**": set(products),
        "**Események:**": set(events),
        "**Jogszabályok, törvények nevei:**": set(laws),
        "**Műalkotások:**": set(works_of_art),
        "**Nyelvek:**": set(languages),
        "**Időhöz kapcsolódó kifejezések:**": set(times),
        "**Pénzösszegek:**": set(monies),
        "**Sorszámok:**": set(ordinals),
    }

    # Dynamically generated result string with only non-empty categories
    result = "\n".join(
        f"<u>{key}</u>: {', '.join(values) + "." }\n"
        for key, values in results.items() if values
    )

    return result


def sentiment_analysis_huggingface(text:str, chunk_size:int=500):
    """
    Interpreting the mood of a text.
    """
    sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    
    # Split text into smaller parts
    sentiments = []
    for i in range(0, len(text), chunk_size):
        part = text[i:i + chunk_size]
        if len(part) > 10:
            sentiment = sentiment_pipeline(part)
            sentiments.extend(sentiment)
    
    # Averaging to aggregate sentiment scores
    sentiment_scores = {'POSITIVE': [], 'NEGATIVE': []}
    for sentiment in sentiments:
        label = sentiment['label']
        score = sentiment['score']
        sentiment_scores[label].append(score)
    
    # Calculate average scores
    averaged_scores = {label: (sum(scores) / len(scores)) if scores else 0 for label, scores in sentiment_scores.items()}
    
    # Determining the final result
    if averaged_scores['POSITIVE'] > averaged_scores['NEGATIVE'] and averaged_scores['POSITIVE'] >= 0.6:
        return "A szöveg(ek)nek együttesen **jó** hangulata van."
    elif averaged_scores['NEGATIVE'] > averaged_scores['POSITIVE'] and averaged_scores['NEGATIVE'] >= 0.6:
        return "A szöveg(ek)nek együttesen **szomorú** hangulata van."
    else:
        return "A szöveg(ek)nek összevéve **túl vegyes a hangulata**, ahhoz, hogy feketének vagy fehérnek fessem le.**"



# Aspect-Based Opinion Mining using Hugging Face
def aspect_based_opinion_mining(text:str, aspects):
    """
    Aspect-based opinion mining
    """
    local_translator = Local_TranslationAgent()
    aspect_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    result = aspect_pipeline(text, candidate_labels=aspects)
    
    # Format output for all aspects
    opinions = []
    weight=""
    for aspect, score in zip(result['labels'], result['scores']):
        if  score <= 0.15:
            weight="**kicsi**"
        elif score >=0.151 and score <= 0.30:
            weight="**közepes**"
        else:
            weight="**nagy**"
        aspect= local_translator.instant_translate_to_hungarian(aspect)
        opinions.append(f"A(z) '{aspect}' szempont a szöveg(ek)ben {weight} hangsúlyt kapott.\n")

    # Compile all opinions into a single text
    output = "\n".join(opinions)
    return output

def extract_topics(text:str , num_topics:int=3, num_words:int=3):
    """
    Identifying topics from files
    """
    local_translator = Local_TranslationAgent()
    # Using English stop words
    stop_words = set(stopwords.words('english'))
    
    tokenized_text = [word for word in word_tokenize(text.lower()) if word.isalpha() and word not in stop_words]
    
    if not tokenized_text:
        print("A tokenizálás üres listát eredményezett.")
        return "Nem találtam témát a fájlnak."

    # Create a dictionary and corpus based on the tokenized text
    dictionary = corpora.Dictionary([tokenized_text])
    corpus = [dictionary.doc2bow(tokenized_text)]
    
    # Check: If the corpus is empty, it gives a warning
    if len(corpus[0]) == 0:
        print("A korpusz a feldolgozás után üres.")
        return "Nem találtam témát a fájlnak."
    
    # Create an LDA model
    lda_model = models.LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=15)
    
    # Collecting words for topics
    topic_words = []
    for _, topic in lda_model.show_topics(num_topics=num_topics, num_words=num_words, formatted=False):
        words = [word[0] for word in topic]
        topic_words.extend(words)
    
    # Comma separated list of words
    unique_words = list(dict.fromkeys(topic_words))  # Eltávolítja a duplikátumokat, de megtartja a sorrendet
    text_to_translate = ", ".join(unique_words) + "."
    translated_text = local_translator.instant_translate_to_hungarian(text_to_translate)
    output = "**A szöveg(ek) alapján ezeket a szavakat találtam igéretes témáknak:** " + translated_text
    
    return output


def keyword_extraction(text: str, top_n: int = 10):
    """
    Identifying keywords from files without duplicates, comparing in lowercase.
    """
    local_translator = Local_TranslationAgent()
    kw_model = KeyBERT()
    
    # Extract keywords with KeyBERT
    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), top_n=top_n)
    
    # Extract keywords, convert to lowercase, and remove duplicates
    keyword_set = set(kw[0].lower() for kw in keywords)
    
    # Create formatted text for translation
    text_to_translate = ", ".join(keyword_set) + "."
    translated_text = local_translator.instant_translate_to_hungarian(text_to_translate)
    
    # Create the output
    output = "**A legfontosabb kulcsszavak a szövegben:** " + translated_text
    
    return output


def generate_extract_from_texts(full_text:str):
    """
    Executes text analysis tasks in parallel.
    """
    # constant values
    aspects = ["ethics", "privacy", "security", "automation", "innovation", "future of Work"]

    # Define the tasks to be run in parallel
    tasks = {
        "NER analízis": lambda: extract_entities(full_text),
        "Kulcsszavak a szövegben": lambda: keyword_extraction(full_text),
        "Hangulat analízis": lambda: sentiment_analysis_huggingface(full_text),
        "Lehetséges témák bemutatása": lambda: extract_topics(full_text, 1, 5),
        "Szempont alapú kivonat": lambda: aspect_based_opinion_mining(full_text, aspects or ["AI", "privacy", "danger", "security"])
    }
    
    results = {}
    
    # Execute tasks in parallel
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(func): name for name, func in tasks.items()}
        
        for future in as_completed(futures):
            task_name = futures[future]
            try:
                results[task_name] = future.result()
            except Exception as e:
                results[task_name] = f"Error in {task_name}: {str(e)}"
    
    # Compile results into a single output string
    result_string = "### Átfogó elemzési eredmények:\n"
    for task_name, result in results.items():
        result_string += f"### {task_name}:\n{result}\n\n"

    result_string = result_string.replace("City name (optional, probably does not need a translation)", "").strip()
    return result_string
