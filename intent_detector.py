import re
from typing import List, Dict
from spellchecker import SpellChecker
from difflib import get_close_matches
import string
from Levenshtein import distance as levenshtein_distance

class IntentDetector:
    def __init__(self, ticker_mapping: Dict[str, str], industry_mapping: Dict[str, str]):
        self.ticker_mapping = ticker_mapping
        self.industry_mapping = industry_mapping
        self.company_names = list(ticker_mapping.keys())
        self.intent_keywords = {
            "industry_values": ["actual values", "industry", "companies in industry", "all"],
            "compare": ["compare", "comparison", "between", "difference between", "versus", "vs", "with", "and", "&", ","],
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
    def suggest_closest_matches(self, input_name: str, candidates: List[str], n=3):
        input_cleaned = self.clean_name(input_name)
        suggestions = sorted(
            candidates,
            key=lambda x: levenshtein_distance(input_cleaned, self.clean_name(x))
        )
        return suggestions[:n]


    def fuzzy_contains_keyword(self, user_input: str, keyword_list: List[str]) -> str:
        words = user_input.lower().split()
        for word in words:
            corrected = self.spell_correct(word)
            if corrected in keyword_list:
                return corrected
        return None
    
    def fuzzy_match_company(self, name: str) -> str:
        name = self.clean_name(name)

        # All known names: company names + ticker symbols
        all_names = list(set(self.company_names + list(self.ticker_mapping.values())))

        # 1. Direct fuzzy match
        close_matches = get_close_matches(name, all_names, n=1, cutoff=0.8)
        if close_matches:
            return close_matches[0]

        # 2. Try spelling correction, then fuzzy match again
        corrected = self.spell.correction(name.lower()).upper()
        close_matches = get_close_matches(corrected, all_names, n=1, cutoff=0.8)
        if close_matches:
            return close_matches[0]

        # 3. Still not found → suggest closest matches and raise error
        suggestions = self.suggest_closest_matches(name, self.company_names)
        raise ValueError(f"Company '{name}' not found. Did you mean: {', '.join(suggestions)}?")




    def fuzzy_match_industry(self, name: str) -> str:
        name = name.lower().strip()
        name = re.sub(r"[-_:,&]", " ", name)
        name = re.sub(r"\s+", " ", name).strip()


        for industry_key, canonical in self.industry_mapping.items():
            if name in industry_key:
                return canonical

        # If not found, suggest alternatives
        suggestions = self.suggest_closest_matches(name, list(self.industry_mapping.keys()))
        print(f"[DEBUG] Cleaned industry input: '{name}'")
        print(f"[DEBUG] Known industries: {list(self.industry_mapping.keys())[:5]} ...")
        raise ValueError(f"Industry '{name}' not recognized. Did you mean: {', '.join(suggestions)}?")


    def detect(self, user_input: str, last_intent: str = None) -> dict:
        user_input = self.normalize_text(user_input)
        words = [self.clean_name(w) for w in user_input.split()]
        print(words)

        matched_companies = [name for name in words if name in self.company_names]
        matched_tickers = [t for t in words if t in self.ticker_mapping.values()]
        # 🔧 Try matching full industry names based on substrings in the input
        normalized_input = user_input.lower()

        matched_industries = [
            key for key in self.industry_mapping.keys()
            if key in user_input
        ]


        total_companies = list(set(matched_companies + [
            k for k, v in self.ticker_mapping.items() if v in matched_tickers
        ]))

        # 🔷 Intent by matches
        if len(total_companies) >= 2:
            return {"intent": "compare", "companies": total_companies}
        elif len(total_companies) == 1:
            return {"intent": "graph", "company": total_companies[0]}
        elif len(matched_industries) >= 2:
            return {"intent": "sector_comparison", "industries": matched_industries}
        elif len(matched_industries) == 1:
            return {"intent": "industry_values", "industry": matched_industries[0]}

        # ⬇️ Fallback to keywords if nothing matched
        if self.fuzzy_contains_keyword(user_input, self.intent_keywords["industry_values"]):
            return {"intent": "industry_values", "industry": self.extract_industry_name(user_input)}
        if self.fuzzy_contains_keyword(user_input, self.intent_keywords["compare"]):
            return {"intent": "compare", "companies": self.extract_company_names(user_input)}
        if self.fuzzy_contains_keyword(user_input, self.intent_keywords["graph"]):
            return {"intent": "graph", "company": self.extract_company_name(user_input)}

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

    def resolve_ticker(self, company_or_ticker: str) -> str:
        key = company_or_ticker.strip().upper()

        # Try company name → ticker
        if key in self.ticker_mapping:
            return self.ticker_mapping[key]

        # Try ticker itself (reverse map)
        reverse_map = {v: k for k, v in self.ticker_mapping.items()}
        if key in reverse_map:
            return key  # already a valid ticker

        raise ValueError(f"Company or Ticker '{company_or_ticker}' not found in mapping.")

