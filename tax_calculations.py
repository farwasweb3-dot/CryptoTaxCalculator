import pandas as pd
from datetime import datetime, timedelta
from collections import deque
import numpy as np

class TaxCalculations:
    """Handles crypto tax calculations using FIFO methodology"""
    
    def __init__(self):
        # Tax rates (these are assumptions - actual rates vary by taxpayer)
        self.short_term_tax_rate = 0.22  # 22% for short-term gains
        self.long_term_tax_rate = 0.15   # 15% for long-term gains
        self.long_term_threshold_days = 365  # Days to qualify for long-term
    
    def calculate_fifo_taxes(self, df):
        """
        Calculate taxes using FIFO (First In, First Out) method
        """
        try:
            results = {
                'short_term_gain': 0.0,
                'long_term_gain': 0.0,
                'estimated_tax': 0.0,
                'transactions_detail': [],
                'holdings_summary': []
            }
            
            # Group by symbol for separate FIFO calculations
            symbols = df['symbol'].unique()
            
            for symbol in symbols:
                symbol_df = df[df['symbol'] == symbol].sort_values('date')
                symbol_results = self._calculate_symbol_fifo(symbol, symbol_df)
                
                # Aggregate results
                results['short_term_gain'] += symbol_results['short_term_gain']
                results['long_term_gain'] += symbol_results['long_term_gain']
                results['transactions_detail'].extend(symbol_results['transactions_detail'])
                
                # Add remaining holdings
                if symbol_results['remaining_holdings']:
                    results['holdings_summary'].extend(symbol_results['remaining_holdings'])
            
            # Calculate estimated tax
            short_term_tax = max(0, results['short_term_gain']) * self.short_term_tax_rate
            long_term_tax = max(0, results['long_term_gain']) * self.long_term_tax_rate
            results['estimated_tax'] = short_term_tax + long_term_tax
            
            return results
            
        except Exception as e:
            raise Exception(f"Error in tax calculations: {str(e)}")
    
    def _calculate_symbol_fifo(self, symbol, symbol_df):
        """Calculate FIFO for a specific cryptocurrency symbol"""
        
        results = {
            'short_term_gain': 0.0,
            'long_term_gain': 0.0,
            'transactions_detail': [],
            'remaining_holdings': []
        }
        
        # FIFO queue to track purchases (lots)
        fifo_queue = deque()
        
        for _, transaction in symbol_df.iterrows():
            if transaction['type'].lower() == 'buy':
                # Add to FIFO queue
                lot = {
                    'symbol': symbol,
                    'date': transaction['date'],
                    'quantity': transaction['quantity'],
                    'price': transaction['price'],
                    'cost_basis': transaction['quantity'] * transaction['price']
                }
                fifo_queue.append(lot)
                
            elif transaction['type'].lower() == 'sell':
                # Process sale using FIFO
                sale_results = self._process_sale(
                    fifo_queue, 
                    symbol,
                    transaction['date'],
                    transaction['quantity'],
                    transaction['price']
                )
                
                results['short_term_gain'] += sale_results['short_term_gain']
                results['long_term_gain'] += sale_results['long_term_gain']
                results['transactions_detail'].extend(sale_results['transactions_detail'])
        
        # Add remaining holdings to summary
        for lot in fifo_queue:
            if lot['quantity'] > 0:
                results['remaining_holdings'].append({
                    'symbol': lot['symbol'],
                    'quantity': lot['quantity'],
                    'avg_cost': lot['price'],
                    'total_cost_basis': lot['cost_basis'],
                    'purchase_date': lot['date']
                })
        
        return results
    
    def _process_sale(self, fifo_queue, symbol, sale_date, sale_quantity, sale_price):
        """Process a sale transaction using FIFO"""
        
        results = {
            'short_term_gain': 0.0,
            'long_term_gain': 0.0,
            'transactions_detail': []
        }
        
        remaining_to_sell = sale_quantity
        total_proceeds = sale_quantity * sale_price
        
        while remaining_to_sell > 0 and fifo_queue:
            # Get the oldest lot
            oldest_lot = fifo_queue[0]
            
            if oldest_lot['quantity'] <= remaining_to_sell:
                # Sell entire lot
                quantity_sold = oldest_lot['quantity']
                cost_basis = oldest_lot['cost_basis']
                fifo_queue.popleft()  # Remove the lot
            else:
                # Partial sale of lot
                quantity_sold = remaining_to_sell
                cost_basis = (oldest_lot['cost_basis'] / oldest_lot['quantity']) * quantity_sold
                
                # Update the remaining lot
                oldest_lot['quantity'] -= quantity_sold
                oldest_lot['cost_basis'] -= cost_basis
            
            # Calculate gain/loss for this portion
            proceeds = quantity_sold * sale_price
            gain_loss = proceeds - cost_basis
            
            # Determine if short-term or long-term
            holding_period = (sale_date - oldest_lot['date']).days
            is_long_term = holding_period >= self.long_term_threshold_days
            
            if is_long_term:
                results['long_term_gain'] += gain_loss
                term_type = 'Long-term'
            else:
                results['short_term_gain'] += gain_loss
                term_type = 'Short-term'
            
            # Add to transaction details
            results['transactions_detail'].append({
                'symbol': symbol,
                'sale_date': sale_date,
                'purchase_date': oldest_lot['date'],
                'quantity': quantity_sold,
                'proceeds': proceeds,
                'cost_basis': cost_basis,
                'gain_loss': gain_loss,
                'holding_period_days': holding_period,
                'term_type': term_type
            })
            
            remaining_to_sell -= quantity_sold
        
        if remaining_to_sell > 0:
            # Not enough purchases to cover the sale - this shouldn't happen with good data
            # But we'll handle it gracefully
            pass
        
        return results
    
    def get_tax_rate_info(self):
        """Return information about tax rates used"""
        return {
            'short_term_rate': self.short_term_tax_rate,
            'long_term_rate': self.long_term_tax_rate,
            'long_term_threshold_days': self.long_term_threshold_days,
            'note': 'These are approximate rates. Actual rates depend on your income and filing status.'
        }
