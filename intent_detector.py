import re
from typing import List, Dict
from spellchecker import SpellChecker
from difflib import get_close_matches
import string

class IntentDetector:
    def __init__(self, ticker_mapping: Dict[str, str], industry_mapping: Dict[str, str]):
        self.ticker_mapping = ticker_mapping
        self.industry_mapping = industry_mapping
        self.company_names = list(ticker_mapping.keys())
        self.intent_keywords = {
            "industry_values": ["actual values", "industry", "companies in industry", "all"],
            "compare": ["compare", "comparison", "difference between", "versus", "vs", "with", "and", "&", ","],
            "graph": ["chart of", "plot of", "graph of", "graph", "plot", "visualize", "chart"]
        }

        self.keyword_vocab = sum(self.intent_keywords.values(), [])
        self.spell = SpellChecker()

        # Build spelling vocab from everything we know
        all_vocab = list(ticker_mapping.keys()) + list(ticker_mapping.values())
        all_vocab += list(industry_mapping.keys()) + self.keyword_vocab
        self.spell.word_frequency.load_words([w.lower() for w in all_vocab])

    def clean_name(self, name: str) -> str:
        return name.strip().translate(str.maketrans('', '', string.punctuation)).upper()
    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[-:]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def spell_correct(self, word: str) -> str:
        return self.spell.correction(word.lower())

    def fuzzy_contains_keyword(self, user_input: str, keyword_list: List[str]) -> str:
        words = user_input.lower().split()
        for word in words:
            corrected = self.spell_correct(word)
            if corrected in keyword_list:
                return corrected
        return None
    
    def fuzzy_match_company(self, name: str) -> str:
        name = self.clean_name(name)


        # Step 1: Try fuzzy match from Excel Company Names
        close_matches = get_close_matches(name, self.company_names, n=1, cutoff=0.8)
        if close_matches:
            return close_matches[0]

        # Step 2: Fallback to SpellChecker
        corrected = self.spell.correction(name.lower()).upper()
        close_matches = get_close_matches(corrected, self.company_names, n=1, cutoff=0.8)
        if close_matches:
            return close_matches[0]

        raise ValueError(f"Company '{name}' not found in mapping.")

    def fuzzy_match_industry(self, name: str) -> str:
        name = self.clean_name(name)
        name = self.spell_correct(name)
        for industry in self.industry_mapping:
            if name in industry.lower():
                return self.industry_mapping[industry]
        raise ValueError(f"Industry '{name}' not recognized.")

    def detect(self, user_input: str, last_intent: str = None) -> dict:
        user_input = self.normalize_text(user_input)
        # 🔁 1. Handle 'add <company>'
        if user_input.startswith("add "):
            name = self.clean_name(user_input.replace("add ", ""))
            return {"intent": "compare", "add_company": self.fuzzy_match_company(name)}

        # 🔁 2. Handle 'compare with <company>'
        if user_input.startswith("compare with "):
            name = self.clean_name(user_input.replace("compare with ", ""))
            try:
                return {"intent": "compare", "add_company": self.fuzzy_match_company(name)}
            except:
                return {"intent": "sector_comparison", "add_industry": self.fuzzy_match_industry(name)}
        if self.fuzzy_contains_keyword(user_input, self.intent_keywords["industry_values"]):
            industry_name = self.extract_industry_name(user_input)
            return {"intent": "industry_values", "industry": industry_name}

        if self.fuzzy_contains_keyword(user_input, self.intent_keywords["compare"]):
            return {"intent": "compare", "companies": self.extract_company_names(user_input)}

        if self.fuzzy_contains_keyword(user_input, self.intent_keywords["graph"]):
            if self.fuzzy_contains_keyword(user_input, self.intent_keywords["compare"]):
                return {"intent": "compare", "companies": self.extract_company_names(user_input)}
            return {"intent": "graph", "company": self.extract_company_name(user_input)}

        # ⬇️ New: fallback to last intent
        if last_intent == "graph":
            try:
                return {"intent": "graph", "company": self.extract_company_name(user_input)}
            except:
                pass
        if last_intent == "compare":
            try:
                return {"intent": "compare", "companies": self.extract_company_names(user_input)}
            except:
                pass
        if last_intent == "industry_values":
            try:
                return {"intent": "industry_values", "industry": self.extract_industry_name(user_input)}
            except:
                pass

        return {"intent": "text"}


    def extract_industry_name(self, user_input: str) -> str:
        for keyword in self.intent_keywords["industry_values"]:
            if keyword in user_input:
                after = user_input.split(keyword)[-1].strip()
                return self.fuzzy_match_industry(after)
        raise ValueError("Could not recognize the industry name.")

    def extract_company_name(self, user_input: str) -> str:
        for keyword in self.intent_keywords["graph"]:
            if keyword in user_input:
                after = user_input.split(keyword)[-1].strip()
                return self.fuzzy_match_company(after)
        return self.fuzzy_match_company(user_input.split()[-1])

    def extract_company_names(self, user_input: str) -> list:
        for keyword in self.intent_keywords["compare"]:
            if keyword in user_input:
                user_input = user_input.split(keyword, 1)[-1]
                break

        for delim in self.intent_keywords["compare"]:
            user_input = user_input.replace(delim, ",")

        companies = [c.strip() for c in user_input.split(",") if c.strip()]
        matched = []
        for c in companies:
            c = self.clean_name(c)
            try:
                matched_name = self.fuzzy_match_company(c)
                matched.append(matched_name)
            except ValueError:
                continue

        if len(matched) < 2:
            raise ValueError("At least two valid companies required.")
        return list(set(matched))

    def resolve_ticker(self, user_input: str) -> str:
        user_input = self.clean_name(user_input)
        for company_name, ticker in self.ticker_mapping.items():
            if user_input in company_name or user_input == ticker:
                return ticker
        raise ValueError(f"Ticker or company name '{user_input}' not found.")
