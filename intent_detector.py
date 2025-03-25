from typing import List, Dict
class IntentDetector:
    def __init__(self, ticker_mapping):
        self.ticker_mapping = ticker_mapping

    def detect(self, user_input: str) -> dict:
        """
        Detects the user's intent from text.
        """
        user_input = user_input.lower()

        # Sector intent
        sector_keywords = ["actual values", "sector", "companies in sector", "all"]
        if any(keyword in user_input for keyword in sector_keywords):
            sector_name = user_input.split("sector")[1].strip() if "sector" in user_input else None
            if sector_name:
                return {"intent": "sector_values", "sector": sector_name}
            raise ValueError("Please specify the sector name for the query.")

        # Comparison intent
        compare_keywords = ["compare", "comparison", "difference between", "versus",
                            "vs", ",", "&", "and", "compare me the stocks of", "with"]
        if any(keyword in user_input for keyword in compare_keywords):
            return {"intent": "compare", "companies": self.extract_company_names(user_input)}

        # Single stock graph
        graph_keywords = ["graph", "plot", "visualize", "show", "chart of", "chart", "plot of", "graph of"]
        if any(keyword in user_input for keyword in graph_keywords):
            if "compare" in user_input or ("and" in user_input or "," in user_input):
                return {"intent": "compare", "companies": self.extract_company_names(user_input)}
            else:
                return {"intent": "graph", "company": self.extract_company_name(user_input)}

        return {"intent": "text"}

    def extract_company_name(self, user_input: str) -> str:
        """
        Extracts a single company name for graphing.
        """
        user_input = user_input.lower()
        graph_keywords = ["graph of", "graph", "plot of", "plot", "visualize", "show", "chart of", "chart"]

        for keyword in graph_keywords:
            if keyword in user_input:
                return user_input.split(keyword)[-1].strip()

        raise ValueError("No recognizable company name in input.")

    def extract_company_names(self, user_input: str) -> list:
        """
        Extracts multiple company names for comparison.
        """
        user_input = user_input.lower()
        delimiters = ["compare", "comparison", "difference between", "versus", "vs",
                      ",", "&", "and", "compare me the stocks of", "with"]

        for delimiter in delimiters:
            user_input = user_input.replace(delimiter, ",")

        companies = [c.strip() for c in user_input.split(",") if c.strip()]
        words_list = []
        for company in companies:
            words_list += company.split()

        valid_companies = []
        for company in words_list:
            for valid_name in self.ticker_mapping.keys():
                if valid_name in company.upper():
                    valid_companies.append(valid_name)
                    break

        if len(valid_companies) < 2:
            raise ValueError("At least two valid companies are required for comparison.")

        return list(set(valid_companies))

    def resolve_ticker(self, user_input: str) -> str:
        """
        Maps a company name or ticker to the actual ticker symbol.
        """
        user_input = user_input.strip().upper()
        for company_name, ticker in self.ticker_mapping.items():
            if user_input in company_name or user_input == ticker:
                return ticker
        raise ValueError(f"Ticker or company name '{user_input}' not found in mapping.")
