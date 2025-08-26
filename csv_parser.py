import pandas as pd
import streamlit as st
from datetime import datetime
import re

class CSVParser:
    """Handles parsing of CSV files from various crypto exchanges"""
    
    def __init__(self):
        self.common_date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S'
        ]
    
    def parse_csv(self, uploaded_file):
        """Parse uploaded CSV file and standardize format"""
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            if df.empty:
                st.error("The uploaded file is empty.")
                return None
            
            # Standardize column names
            df = self._standardize_columns(df)
            
            # Validate required columns exist
            if not self._validate_columns(df):
                return None
            
            # Clean and standardize data
            df = self._clean_data(df)
            
            # Parse dates
            df = self._parse_dates(df)
            
            # Check if date parsing failed
            if df is None:
                return None
            
            # Sort by date
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            return None
    
    def _standardize_columns(self, df):
        """Standardize column names across different exchange formats"""
        
        # Convert all column names to lowercase for easier matching
        df.columns = df.columns.str.lower().str.strip()
        
        # Common column name mappings
        column_mappings = {
            # Date columns
            'timestamp': 'date',
            'time': 'date',
            'datetime': 'date',
            'created_at': 'date',
            'trade_time': 'date',
            'order_time': 'date',
            
            # Symbol columns
            'coin': 'symbol',
            'asset': 'symbol',
            'currency': 'symbol',
            'pair': 'symbol',
            'base_asset': 'symbol',
            'product': 'symbol',
            
            # Type columns
            'side': 'type',
            'transaction_type': 'type',
            'order_type': 'type',
            'trade_type': 'type',
            'action': 'type',
            
            # Quantity columns
            'amount': 'quantity',
            'size': 'quantity',
            'volume': 'quantity',
            'filled_size': 'quantity',
            'base_amount': 'quantity',
            'qty': 'quantity',
            
            # Price columns
            'rate': 'price',
            'unit_price': 'price',
            'price_per_unit': 'price',
            'fill_price': 'price',
            'executed_price': 'price',
            'avg_price': 'price'
        }
        
        # Apply mappings
        for old_name, new_name in column_mappings.items():
            if old_name in df.columns:
                df.rename(columns={old_name: new_name}, inplace=True)
        
        return df
    
    def _validate_columns(self, df):
        """Validate that required columns exist"""
        required_columns = ['date', 'symbol', 'type', 'quantity', 'price']
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.info("Available columns: " + ", ".join(df.columns.tolist()))
            st.info("""
            Please ensure your CSV contains columns for:
            - Date/Timestamp
            - Symbol/Coin
            - Type (buy/sell)
            - Quantity/Amount
            - Price/Rate
            """)
            return False
        
        return True
    
    def _clean_data(self, df):
        """Clean and standardize data values"""
        
        # Clean symbol column - remove quotes, spaces, convert to uppercase
        if 'symbol' in df.columns:
            df['symbol'] = df['symbol'].astype(str).str.strip().str.upper()
            # Remove common suffixes like /USD, -USD, etc.
            df['symbol'] = df['symbol'].str.replace(r'[/-]USD.*', '', regex=True)
            df['symbol'] = df['symbol'].str.replace(r'[/-]USDT.*', '', regex=True)
            df['symbol'] = df['symbol'].str.replace(r'[/-]EUR.*', '', regex=True)
        
        # Clean type column - standardize buy/sell
        if 'type' in df.columns:
            df['type'] = df['type'].astype(str).str.lower().str.strip()
            # Map common variations
            type_mappings = {
                'purchase': 'buy',
                'bought': 'buy',
                'acquire': 'buy',
                'deposit': 'buy',
                'sold': 'sell',
                'sale': 'sell',
                'dispose': 'sell',
                'withdrawal': 'sell'
            }
            df['type'] = df['type'].replace(type_mappings)
        
        # Convert numeric columns
        numeric_columns = ['quantity', 'price']
        for col in numeric_columns:
            if col in df.columns:
                # Remove currency symbols and commas
                df[col] = df[col].astype(str).str.replace(r'[$,€£]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with missing critical data
        df = df.dropna(subset=['date', 'symbol', 'type', 'quantity', 'price'])
        
        # Filter out zero quantities and prices
        df = df[(df['quantity'] > 0) & (df['price'] > 0)]
        
        return df
    
    def _parse_dates(self, df):
        """Parse date column using various formats"""
        
        if 'date' not in df.columns:
            return df
        
        # Try to parse dates with multiple formats
        date_parsed = False
        
        for date_format in self.common_date_formats:
            try:
                df['date'] = pd.to_datetime(df['date'], format=date_format, errors='raise')
                date_parsed = True
                break
            except (ValueError, TypeError):
                continue
        
        # If specific formats fail, try pandas auto-detection
        if not date_parsed:
            try:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                date_parsed = True
            except:
                pass
        
        if not date_parsed:
            st.error("Could not parse date column. Please ensure dates are in a standard format.")
            return None
        
        # Remove rows with invalid dates
        df = df.dropna(subset=['date'])
        
        return df
