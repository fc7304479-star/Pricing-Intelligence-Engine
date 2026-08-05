import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)


class LLMSelector:

    def __init__(self):

        self.model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

    def find_price_selector(self, html):

        prompt = f"""
You are an expert web scraping engineer.

You are given HTML from an ecommerce product page.

Your task is to identify ONLY the CSS selector that points to the product price.

Rules:

- Return ONLY one CSS selector.
- No explanation.
- No markdown.
- No code block.
- No extra text.

HTML:

{html}
"""

        try:

            response = self.model.generate_content(prompt)

            selector = response.text.strip()

            # Remove markdown if Gemini returns it
            selector = selector.replace("```css", "")
            selector = selector.replace("```", "")
            selector = selector.strip()

            # remove quotes
            selector = selector.strip('"')
            selector = selector.strip("'")

            print(f"[LLM] Suggested Selector -> {selector}")

            return selector

        except Exception as e:

            print(f"[LLM ERROR] {e}")

            return None