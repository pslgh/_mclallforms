"""
Helper module for currency-related functions.
Provides mappings between countries and currencies.
"""
"""Currency and country mapping for the expense module.

This module provides a simple predefined list of countries and their currencies
for use in the expense reimbursement form.
"""

# Predefined list of countries and their currency codes
# Format: country name as key, currency code as value
COUNTRY_CURRENCY_MAP = {
    # Default country
    "Thailand": "THB",
    
    # ASEAN countries
    "Brunei": "BND",
    "Cambodia": "KHR",
    "Indonesia": "IDR",
    "Laos": "LAK",
    "Malaysia": "MYR",
    "Myanmar": "MMK",
    "Philippines": "PHP",
    "Singapore": "SGD",
    "Vietnam": "VND",
    
    # Major economies - USD
    "United States": "USD",
    "Ecuador": "USD",
    "El Salvador": "USD",
    "Panama": "USD",
    "Zimbabwe": "USD",
    
    # Major economies - Euro
    "Austria": "EUR",
    "Belgium": "EUR",
    "Cyprus": "EUR",
    "Estonia": "EUR",
    "Finland": "EUR",
    "France": "EUR",
    "Germany": "EUR",
    "Greece": "EUR",
    "Ireland": "EUR",
    "Italy": "EUR",
    "Latvia": "EUR",
    "Lithuania": "EUR",
    "Luxembourg": "EUR",
    "Malta": "EUR",
    "Netherlands": "EUR",
    "Portugal": "EUR",
    "Slovakia": "EUR",
    "Slovenia": "EUR",
    "Spain": "EUR",
    
    # Other major currencies
    "Australia": "AUD",
    "Brazil": "BRL",
    "Canada": "CAD",
    "Switzerland": "CHF",
    "China": "CNY",
    "United Kingdom": "GBP",
    "Hong Kong": "HKD",
    "India": "INR",
    "Japan": "JPY",
    "South Korea": "KRW",
    "Mexico": "MXN",
    "Norway": "NOK",
    "New Zealand": "NZD",
    "Poland": "PLN",
    "Russia": "RUB",
    "Sweden": "SEK",
    "Turkey": "TRY",
    
    # Other countries
    "Argentina": "ARS",
    "Bangladesh": "BDT",
    "Egypt": "EGP",
    "Israel": "ILS",
    "Iran": "IRR",
    "Sri Lanka": "LKR",
    "Nigeria": "NGN",
    "Nepal": "NPR",
    "Pakistan": "PKR",
    "Saudi Arabia": "SAR",
    "Taiwan": "TWD",
    "Ukraine": "UAH",
    "United Arab Emirates": "AED",
    "South Africa": "ZAR",
    
    # Countries with special situations
    "Afghanistan": "No Currency",
    "Venezuela": "No Currency",
    "Cuba": "No Currency",
    "North Korea": "No Currency",
    "Somalia": "No Currency",
    "Syria": "No Currency",
}

# List of country names for the dropdown (sorted alphabetically)
COUNTRY_LIST = sorted(list(COUNTRY_CURRENCY_MAP.keys()))

# List of unique currency codes from the country mapping (sorted alphabetically)
CURRENCY_VALUES = sorted(list(set([code for code in COUNTRY_CURRENCY_MAP.values()])))

# Dictionary of currency codes to their names
CURRENCY_NAMES = {
    "No Currency": "No Standard Currency",
    "AED": "UAE Dirham",
    "ARS": "Argentine Peso",
    "AUD": "Australian Dollar",
    "BDT": "Bangladeshi Taka",
    "BND": "Brunei Dollar",
    "BRL": "Brazilian Real",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "EGP": "Egyptian Pound",
    "EUR": "Euro",
    "GBP": "British Pound",
    "HKD": "Hong Kong Dollar",
    "IDR": "Indonesian Rupiah",
    "ILS": "Israeli New Shekel",
    "INR": "Indian Rupee",
    "IRR": "Iranian Rial",
    "JPY": "Japanese Yen",
    "KHR": "Cambodian Riel",
    "KRW": "South Korean Won",
    "LAK": "Lao Kip",
    "LKR": "Sri Lankan Rupee",
    "MMK": "Myanmar Kyat",
    "MXN": "Mexican Peso",
    "MYR": "Malaysian Ringgit",
    "NGN": "Nigerian Naira",
    "NOK": "Norwegian Krone",
    "NPR": "Nepalese Rupee",
    "NZD": "New Zealand Dollar",
    "PHP": "Philippine Peso",
    "PKR": "Pakistani Rupee",
    "PLN": "Polish Złoty",
    "RUB": "Russian Ruble",
    "SAR": "Saudi Riyal",
    "SEK": "Swedish Krona",
    "SGD": "Singapore Dollar",
    "THB": "Thai Baht",
    "TRY": "Turkish Lira",
    "TWD": "Taiwan Dollar",
    "UAH": "Ukrainian Hryvnia",
    "USD": "US Dollar",
    "VND": "Vietnamese Dong",
    "ZAR": "South African Rand",
}

# List of all available currency codes (including any from CURRENCY_NAMES not in COUNTRY_CURRENCY_MAP)
CURRENCY_LIST = sorted(list(set(list(CURRENCY_NAMES.keys()) + CURRENCY_VALUES)))

def get_currency_name(code):
    """
    Get the name of a currency from its code.
    
    Args:
        code (str): Currency code (e.g., 'USD')
        
    Returns:
        str: Currency name or code if not found
    """
    return CURRENCY_NAMES.get(code, code)

def get_main_currencies():
    """
    Get a list of commonly used currencies
    
    Returns:
        list: List of common currency codes
    """
    return CURRENCY_LIST


