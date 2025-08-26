from tax_calculations import TaxCalculations
import pandas as pd
import streamlit as st

class CryptoTaxCalculator:
    """Main calculator class that orchestrates tax calculations"""
    
    def __init__(self):
        self.tax_calc = TaxCalculations()
    
    def calculate_taxes(self, df):
        """
        Calculate taxes for the provided trade data
        
        Args:
            df: DataFrame with columns: date, symbol, type, quantity, price
            
        Returns:
            Dictionary with tax calculation results
        """
        try:
            # Validate input data
            if not self._validate_input(df):
                return None
            
            # Perform tax calculations
            results = self.tax_calc.calculate_fifo_taxes(df)
            
            # Add metadata
            results['calculation_date'] = pd.Timestamp.now()
            results['total_transactions'] = len(df)
            results['tax_method'] = 'FIFO'
            results['tax_rates'] = self.tax_calc.get_tax_rate_info()
            
            return results
            
        except Exception as e:
            st.error(f"Error in tax calculations: {str(e)}")
            return None
    
    def _validate_input(self, df):
        """Validate input DataFrame"""
        
        if df is None or df.empty:
            st.error("No transaction data provided")
            return False
        
        required_columns = ['date', 'symbol', 'type', 'quantity', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            return False
        
        # Check for valid transaction types
        valid_types = ['buy', 'sell']
        invalid_types = df[~df['type'].str.lower().isin(valid_types)]['type'].unique()
        
        if len(invalid_types) > 0:
            st.warning(f"Found unexpected transaction types that will be ignored: {', '.join(invalid_types)}")
            # Filter to only valid types
            df = df[df['type'].str.lower().isin(valid_types)]
        
        # Check for negative quantities or prices
        if (df['quantity'] <= 0).any() or (df['price'] <= 0).any():
            st.warning("Found transactions with zero or negative quantities/prices. These will be filtered out.")
            df = df[(df['quantity'] > 0) & (df['price'] > 0)]
        
        if df.empty:
            st.error("No valid transactions found after filtering")
            return False
        
        return True
    
    def get_supported_exchanges(self):
        """Return list of supported exchanges"""
        return [
            "Coinbase",
            "Coinbase Pro",
            "Binance",
            "Kraken",
            "Gemini",
            "KuCoin",
            "Huobi",
            "Bittrex",
            "And many others with standard CSV format"
        ]
    
    def get_sample_csv_format(self):
        """Return sample CSV format for user reference"""
        sample_data = {
            'date': ['2023-01-15 10:30:00', '2023-01-20 14:25:00', '2023-02-01 09:15:00'],
            'symbol': ['BTC', 'BTC', 'BTC'],
            'type': ['buy', 'buy', 'sell'],
            'quantity': [0.5, 0.25, 0.3],
            'price': [25000.00, 24500.00, 26000.00]
        }
        return pd.DataFrame(sample_data)
