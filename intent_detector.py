import re
from typing import List, Dict
from spellchecker import SpellChecker
from difflib import get_close_matches
import streamlit as st
import string
from Levenshtein import distance as levenshtein_distance
import pandas as pd

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

        all_vocab = list(ticker_mapping.keys()) + list(ticker_mapping.values())
        all_vocab += list(industry_mapping.keys()) + self.keyword_vocab
        self.spell.word_frequency.load_words([w.lower() for w in all_vocab])

        # ===== Hebrew-to-English mapping =====
        self.hebrew_to_english_company = {}
        self.hebrew_to_english_industry = {}

        df_companies = pd.read_excel("company_name_to_ticker.xlsx")
        if "HebrewCompanyName" in df_companies.columns:
            for _, row in df_companies.iterrows():
                heb = str(row["HebrewCompanyName"]).strip()
                eng = str(row["CompanyName"]).strip().upper()
                if heb:
                    self.hebrew_to_english_company[heb] = eng

        df_sectors = pd.read_csv("sectors_df.csv")
        if "HebrewIndustryName" in df_sectors.columns:
            for _, row in df_sectors.iterrows():
                heb = str(row["HebrewIndustryName"]).strip()
                eng = str(row["Industry"]).strip()
                if heb:
                    self.hebrew_to_english_industry[heb] = eng

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
        all_names = list(set(self.company_names + list(self.ticker_mapping.values())))
        close_matches = get_close_matches(name, all_names, n=1, cutoff=0.8)
        if close_matches:
            return close_matches[0]
        corrected = self.spell.correction(name.lower()).upper()
        close_matches = get_close_matches(corrected, all_names, n=1, cutoff=0.8)
        if close_matches:
            return close_matches[0]
        suggestions = self.suggest_closest_matches(name, self.company_names)
        raise ValueError(f"Company '{name}' not found. Did you mean: {', '.join(suggestions)}?")

    def fuzzy_match_industry(self, name: str) -> str:
        name = name.lower().strip()
        name = re.sub(r"[-_:,&]", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        for industry_key, canonical in self.industry_mapping.items():
            if name in industry_key:
                return canonical
        suggestions = self.suggest_closest_matches(name, list(self.industry_mapping.keys()))
        raise ValueError(f"Industry '{name}' not recognized. Did you mean: {', '.join(suggestions)}?")

    def detect(self, user_input: str, last_intent: str = None) -> dict:
        # 🔄 Translate Hebrew company/industry names to English before detection
        for heb, eng in self.hebrew_to_english_company.items():
            if heb in user_input:
                user_input = user_input.replace(heb, eng)
        for heb, eng in self.hebrew_to_english_industry.items():
            if heb in user_input:
                user_input = user_input.replace(heb, eng)

        user_input = self.normalize_text(user_input)
        words = [self.clean_name(w) for w in user_input.split()]
        user_words = [w.upper() for w in user_input.split()]
        all_companies = list(self.ticker_mapping.keys())
        all_tickers = list(self.ticker_mapping.values())
        all_industries = list(self.industry_mapping.values())
        all_known_entities = all_companies + all_industries

        last_word = user_words[-1]
        is_stock_related = any(w in all_known_entities for w in user_words)

        if not is_stock_related:
            best_match = min(all_known_entities, key=lambda x: levenshtein_distance(x, last_word))
            if levenshtein_distance(best_match, last_word) <= 1:
                st.session_state["suggested_correction"] = best_match
                st.session_state["original_prompt"] = user_input
                tokens = user_input.split()
                tokens[-1] = best_match
                corrected_input = " ".join(tokens)
                words = [self.clean_name(w) for w in corrected_input.split()]

        additive_keywords = {
            "add", "also", "compare", "with", "vs", "versus", "too", "as well",
            "along", "plus", "include", "including", "alongside", "next to", "and",
            "another", "more", "combine", "in addition"
        }
        normalized_input = user_input.lower()
        is_additive = any(kw in normalized_input for kw in additive_keywords)
        prev_intent = last_intent

        matched_companies = [name for name in words if name in self.company_names]
        matched_tickers = [t for t in words if t in self.ticker_mapping.values()]
        matched_industries = [
            key for key in self.industry_mapping.keys()
            if key in normalized_input
        ]

        total_companies = list(set(matched_companies + [
            k for k, v in self.ticker_mapping.items() if v in matched_tickers
        ]))

        if prev_intent in {"graph", "compare"} and is_additive:
            prev_company = st.session_state.get("last_company")
            if prev_company and prev_company not in total_companies:
                total_companies.append(prev_company)
            prev_companies = st.session_state.get("last_companies", [])
            for pc in prev_companies:
                if pc not in total_companies:
                    total_companies.append(pc)
            if len(total_companies) >= 2:
                st.session_state.last_companies = total_companies
                return {"intent": "compare", "companies": list(set(total_companies))}

        if prev_intent in {"industry_values", "sector_comparison"} and is_additive:
            prev_industry = st.session_state.get("last_industry")
            if prev_industry and prev_industry not in matched_industries:
                matched_industries.append(prev_industry)
            prev_industries = st.session_state.get("last_industries", [])
            for pi in prev_industries:
                if pi not in matched_industries:
                    matched_industries.append(pi)
            if len(matched_industries) >= 2:
                st.session_state.last_industries = matched_industries
                return {"intent": "sector_comparison", "industries": list(set(matched_industries))}

        if len(total_companies) >= 2:
            st.session_state.last_companies = total_companies
            return {"intent": "compare", "companies": total_companies}
        elif len(total_companies) == 1:
            st.session_state.last_company = total_companies[0]
            return {"intent": "graph", "company": total_companies[0]}
        elif len(matched_industries) >= 2:
            st.session_state.last_industries = matched_industries
            return {"intent": "sector_comparison", "industries": matched_industries}
        elif len(matched_industries) == 1:
            st.session_state.last_industry = matched_industries[0]
            return {"intent": "industry_values", "industry": matched_industries[0]}

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
        if key in self.ticker_mapping:
            return self.ticker_mapping[key]
        reverse_map = {v: k for k, v in self.ticker_mapping.items()}
        if key in reverse_map:
            return key
        raise ValueError(f"Company or Ticker '{company_or_ticker}' not found in mapping.")
