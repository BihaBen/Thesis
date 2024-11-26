from transformers import AutoTokenizer

def create_summary_prompt(sum_style:str, title:str) -> str:
    """
    Szövegösszefoglaló prompt készítése.
    
    :param text: Az összefoglalni kívánt szöveg.
    :return: A LLM számára megadott prompt.
    """

    # Tokenizáló betöltése
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B")

    # Szöveg, amit tokenizálni szeretnénk
    text = "Ez egy példa szöveg, amit tokenekre szeretnénk bontani."

    # Tokenizálás és tokenek száma
    


    if sum_style == "expert":
        prompt = (
                    "Magyar nyelven válaszolj, szakértői szinten, precíz technikai terminológiával, részletes magyarázatokkal.\n"
                    "Koncentrálj az összetett technikai kihívásokra, specifikus részletekkel, számadatokkal és műszaki betekintéssel.\n"
                    "Tartsd meg a formális, szakmai hangnemet, amely megfelel egy technikai jelentés stílusának.\n"
                    "Az összefoglaló maximum 5-6 mondat legyen, ne használj „összefoglaló” nevű címet."
                )
    elif sum_style == "student":
        prompt = (
                    "You are an AI assistant helping a student understand complex documents. Your task is to write a simple and easy-to-understand summary based on the following information in Markdown format:\n\n"
                    "Your answer should always be in Hungarian!\n"
                    "When writing the summary, please consider the following:\n"
                    "- Explain complicated terms in an easy-to-understand way.\n"
                    "- Avoid using technical jargon unless necessary, and provide definitions when you do.\n"
                    "- Focus on the main points and key takeaways.\n"
                    "- Keep the language simple and clear, as if writing notes for a beginner.\n"
                    "- Write the summary using Markdown formatting, including headings, and bold text for emphasis. Often use bullet points.\n\n"
                    "Based on this, please generate an easy-to-understand summary in Markdown format and never make a headline with the title 'summary'."
                )
    elif sum_style == "clear":
        prompt = (
                    "You are an AI assistant tasked with writing a clear and straightforward summary based on the following information. The summary should be written in Markdown format:\n\n"
                    "Your answer should always be in Hungarian!\n"
                    "When writing the summary, please consider the following:\n"
                    "- Use simple, direct language that anyone can understand.\n"
                    "- Focus on the main ideas without unnecessary details.\n"
                    "- Avoid complex terminology and explain any key terms clearly.\n"
                    "- Provide a concise overview that captures the essential points.\n"
                    "- Write the summary using Markdown formatting, including headings, lists, and bold text for key points.\n\n"
                    "Based on this information, please generate a clear and easy-to-read summary in Markdown format."
                    
                )
    else:
        prompt = (
                    f"Start with: '# I would like to share some information about the contents of the {title} file.'"
                    "When writing the summary, please consider the following:\n"
                    "- Write the summary using Markdown formatting, including headings, lists, and bold text for key points.\n"
                    "- Always write the summary in Hungarian!\n"
                    "- Try to keep all the content\n"
                )

    return prompt

def cannotBeInterpreted(question:str) -> str:
    prompt = (
                    "Apologize to the user, but let them know that you did not receive enough information to answer this question and do all this with markdown style."
                    "Your answer should always be in Hungarian!\n"
                    "Draw the user's attention to the fact that you cannot give a hundred precent sure answer, but you have looked for possible solutions on the Internet, which are the following."
                    "Really try to provide a very relevant answer to this: {question}"
                )
    return ""