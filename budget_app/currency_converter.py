# currency_converter.py

from forex_python.converter import CurrencyRates, RatesNotAvailableError

# Function to convert amount from one currency to another
def convert_currency(amount, from_currency, to_currency):
    """
    Convert amount from one currency to another using real-time exchange rates.
    
    Parameters:
        amount (float): The amount of money to convert
        from_currency (str): Currency code to convert from (e.g., 'USD')
        to_currency (str): Currency code to convert to (e.g., 'INR')
    
    Returns:
        float: Converted amount in the target currency
    """
    c = CurrencyRates()
    try:
        # Perform the currency conversion
        converted_amount = c.convert(from_currency.upper(), to_currency.upper(), amount)
        return round(converted_amount, 2)
    except RatesNotAvailableError:
        # Handle error if exchange rate not available
        return None
