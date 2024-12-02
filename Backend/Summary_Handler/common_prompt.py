class PromptGenerator:
    @staticmethod
    def create_short_summary_prompt_hu(sum_style: str) -> str:
        if sum_style == "expert":
            prompt = (
                f"Kérlek, készíts egy rövid, 4-5 mondatos összefoglalót a következő szövegről, szakértői szókincset "
                f"és diplomatikus stílust használva. Az összefoglaló legyen precíz, pontos, és kerülje a szubjektív megállapításokat."
                f"Válaszod mindig magyar nyelven add vissza!"
            )
        elif sum_style == "student":
            prompt = (
                f"Kérlek, írj egy rövid, 4-5 mondatos összefoglalót, amely lelkes és segítőkész hangnemet tükröz. "
                f"Az összefoglaló legyen érthető, de mutasson alapos ismereteket a témáról."
                f"Válaszod mindig magyar nyelven add vissza!"
            )
        elif sum_style == "clear":
            prompt = (
                f"Kérlek, írj egy közérthető, 4-5 mondatos összefoglalót, amely egyszerű nyelvezettel, de részletesen "
                f"magyarázza el a lényeget, hogy mindenki számára érthető legyen."
                f"Válaszod mindig magyar nyelven add vissza!"
            )
        else:
            prompt = (
                f"Kérlek, készíts egy rövid, 4-5 mondatos összefoglalót a szöveg alapján."
                f"Válaszod mindig magyar nyelven add vissza!"
            )
        return prompt

    @staticmethod
    def create_long_summary_prompt_hu(sum_style: str) -> str:
        if sum_style == "expert":
            prompt = (
                f"Kérlek, készíts egy átfogó és részletes összefoglalót.\n"
                f"A választ Markdown formázásban, rövid blokkokba rendezve, címekkel (`#`), listákkal.\n"
                f"Használj szakértői szókincset és diplomatikus stílust. Az összefoglaló legyen jól strukturált, "
                f"pontosan tükrözze a szöveg tartalmát, és kerülje az általánosításokat."
                f"Válaszod mindig magyar nyelven add vissza!"
            )
        elif sum_style == "student":
            prompt = (
                f"Kérlek, készíts egy átfogó és részletes összefoglalót\n "
                f"A választ Markdown formázásban, rövid blokkokba rendezve, címekkel (`#`), listákkal.\n"
                f"Az összefoglaló legyen lelkes és segítőkész hangvételű, mutassa meg, hogy alaposan megértetted a témát, miközben közérthető marad."
                f"Válaszod mindig magyar nyelven add vissza!"
            )
        elif sum_style == "clear":
            prompt = (
                f"Kérlek, készíts egy átfogó és részletes összefoglalót.\n"
                f"A választ Markdown formázásban, rövid blokkokba rendezve, címekkel (`#`), listákkal.\n"
                f"Az összefoglaló egyszerű nyelvezettel magyarázza el a főbb pontokat, hogy mindenki számára érthető legyen."
                f"Válaszod mindig magyar nyelven add vissza!"
            )
        else:
            prompt = (
                f"Kérlek, készíts egy részletes összefoglalót, "
                f"A választ Markdown formázásban, rövid blokkokba rendezve, címekkel (`#`), listákkal.\n"
                f"Válaszod mindig magyar nyelven add vissza!"
            )
        return prompt

    @staticmethod
    def create_short_summary_prompt_en(sum_style: str) -> str:
        if sum_style == "expert":
            prompt = (
                "Please create a short summary of 4-5 sentences for the following text using expert vocabulary "
                "and a diplomatic tone. The summary should be precise, accurate, and avoid subjective statements."
            )
        elif sum_style == "student":
            prompt = (
                f"Write a detailed summary of the following text in 4-5 sentences:"
                f"[chunk szöveg]"
                f"Summary:"
            )
        elif sum_style == "clear":
            prompt = (
                "Please write a concise and clear summary of 4-5 sentences that explains the main points in simple terms, "
                "making it understandable for everyone."
            )
        else:
            prompt = (
                "Please create a short summary of 4-5 sentences based on the text."
            )
        return prompt

    @staticmethod
    def create_long_summary_prompt_en(sum_style: str) -> str:
        if sum_style == "expert":
            prompt = (
                f"Please create a comprehensive and detailed summary.\n"
                f"The answer is in Markdown format, organized into short blocks, with headings (`#`), lists.\n"
                "Use expert vocabulary and a diplomatic tone. "
                "The summary should be well-structured, accurately reflect the content of the text, and avoid generalizations."
            )
        elif sum_style == "student":
            prompt = (
                f"Focus on the main ideas and avoid unnecessary repetition.\n"
                f"Highlight key concepts and implications.\n"
                f"Please write a concise and coherent summary of the following text:\n\n"
            )
        elif sum_style == "clear":
            prompt = (
                f"Please create a detailed yet clear summary.\n"
                f"The answer is in Markdown format, organized into short blocks, with headings (`#`), lists.\n"
                f"The summary should explain the main points in simple language.\n"
                f"making it easy to understand for everyone."
            )
        else:
            prompt = (
                f"Please create a detailed summary.\n"
                f"The answer is in Markdown format, organized into short blocks, with headings (`#`), lists.\n"
            )
        return prompt

    #f"Please create a detailed and thorough summary. \n"
    #f"The answer is in Markdown format, organized into short blocks, with headings (`#`), lists.\n"
    #f"The summary should have an enthusiastic and helpful tone.\n" 
    #f"Demonstrating that you have a deep understanding of the topic while remaining easy to understand."