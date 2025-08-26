import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from crypto_tax_calculator import CryptoTaxCalculator
from csv_parser import CSVParser

# Page configuration
st.set_page_config(
    page_title="Crypto Tax Calculator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🚀 Crypto Tax Calculator")
    st.markdown("**Stop the crypto tax nightmare.** Upload your trade history CSV and instantly see your profit, loss, and estimated taxes.")
    
    # Disclaimer
    with st.expander("⚠️ Important Disclaimer - Please Read"):
        st.warning("""
        **This tool is for informational purposes only and does not constitute tax advice.**
        
        - Consult with a qualified tax professional for your specific situation
        - Tax laws vary by jurisdiction and change frequently
        - This calculator uses basic US tax assumptions and FIFO methodology
        - Always verify calculations with your tax advisor
        - The creators are not responsible for any tax-related decisions based on this tool
        """)
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        **Step 1:** Upload your CSV file with trade history
        
        **Step 2:** Review the parsed data
        
        **Step 3:** View your tax calculations
        
        **Step 4:** Download your results
        """)
        
        st.header("📁 Supported CSV Format")
        st.markdown("""
        Your CSV should contain columns like:
        - Date/Timestamp
        - Symbol/Coin
        - Type (buy/sell)
        - Quantity/Amount
        - Price/Rate
        
        Common exchange formats are automatically detected.
        """)
    
    # File upload
    st.header("📤 Upload Trade History")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Upload your cryptocurrency trading history from exchanges like Coinbase, Binance, Kraken, etc."
    )
    
    if uploaded_file is not None:
        try:
            # Parse the CSV
            parser = CSVParser()
            df = parser.parse_csv(uploaded_file)
            
            if df is not None and not df.empty:
                st.success(f"✅ Successfully loaded {len(df)} transactions")
                
                # Display parsed data
                st.header("📊 Parsed Trade Data")
                st.dataframe(df, use_container_width=True)
                
                # Basic statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Transactions", len(df))
                with col2:
                    buy_count = len(df[df['type'].str.lower() == 'buy'])
                    st.metric("Buy Orders", buy_count)
                with col3:
                    sell_count = len(df[df['type'].str.lower() == 'sell'])
                    st.metric("Sell Orders", sell_count)
                with col4:
                    unique_symbols = df['symbol'].nunique()
                    st.metric("Unique Coins", unique_symbols)
                
                # Tax calculations
                st.header("💰 Tax Calculations")
                
                with st.spinner("Calculating taxes using FIFO method..."):
                    calculator = CryptoTaxCalculator()
                    results = calculator.calculate_taxes(df)
                
                if results:
                    # Display results
                    display_tax_results(results)
                    
                    # Export functionality
                    st.header("📥 Export Results")
                    export_results(results, df)
                
            else:
                st.error("❌ Could not parse the CSV file. Please check the format and try again.")
                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("💡 Please ensure your CSV contains the required columns: date, symbol, type, quantity, price")

def display_tax_results(results):
    """Display tax calculation results with charts and breakdowns"""
    
    # Overview metrics
    st.subheader("📈 Tax Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_gain_loss = results['short_term_gain'] + results['long_term_gain']
        color = "normal" if total_gain_loss >= 0 else "inverse"
        st.metric(
            "Total Gain/Loss", 
            f"${total_gain_loss:,.2f}",
            delta=None,
            delta_color=color
        )
    
    with col2:
        st.metric(
            "Short-term Gain/Loss", 
            f"${results['short_term_gain']:,.2f}"
        )
    
    with col3:
        st.metric(
            "Long-term Gain/Loss", 
            f"${results['long_term_gain']:,.2f}"
        )
    
    with col4:
        estimated_tax = results['estimated_tax']
        st.metric(
            "Estimated Tax Owed", 
            f"${estimated_tax:,.2f}"
        )
    
    # Tax rate assumptions
    with st.expander("📋 Tax Rate Assumptions"):
        st.info("""
        **Tax rates used in calculations:**
        - Short-term capital gains: 22% (ordinary income rate assumption)
        - Long-term capital gains: 15% (for most taxpayers)
        
        **Note:** Actual rates depend on your total income and filing status. 
        Consult a tax professional for accurate rates.
        """)
    
    # Detailed breakdown
    if results.get('transactions_detail'):
        st.subheader("📋 Transaction Details")
        
        # Convert to DataFrame for display
        detail_df = pd.DataFrame(results['transactions_detail'])
        if not detail_df.empty:
            # Format the display
            detail_df['gain_loss'] = detail_df['gain_loss'].apply(lambda x: f"${x:,.2f}")
            detail_df['proceeds'] = detail_df['proceeds'].apply(lambda x: f"${x:,.2f}")
            detail_df['cost_basis'] = detail_df['cost_basis'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(detail_df, use_container_width=True)
    
    # Charts
    st.subheader("📊 Visualizations")
    
    # Gain/Loss breakdown chart
    if results['short_term_gain'] != 0 or results['long_term_gain'] != 0:
        fig = go.Figure(data=[
            go.Bar(
                x=['Short-term', 'Long-term'],
                y=[results['short_term_gain'], results['long_term_gain']],
                marker_color=['red' if results['short_term_gain'] < 0 else 'green',
                             'red' if results['long_term_gain'] < 0 else 'green']
            )
        ])
        fig.update_layout(
            title="Capital Gains/Loss Breakdown",
            yaxis_title="Amount ($)",
            xaxis_title="Holding Period"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Holdings summary if available
    if results.get('holdings_summary'):
        st.subheader("💼 Current Holdings")
        holdings_df = pd.DataFrame(results['holdings_summary'])
        if not holdings_df.empty:
            st.dataframe(holdings_df, use_container_width=True)

def export_results(results, original_df):
    """Provide export functionality for results"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export summary as CSV
        summary_data = {
            'Metric': [
                'Total Gain/Loss',
                'Short-term Gain/Loss', 
                'Long-term Gain/Loss',
                'Estimated Tax Owed'
            ],
            'Amount': [
                results['short_term_gain'] + results['long_term_gain'],
                results['short_term_gain'],
                results['long_term_gain'],
                results['estimated_tax']
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        csv_summary = summary_df.to_csv(index=False)
        st.download_button(
            label="📄 Download Tax Summary (CSV)",
            data=csv_summary,
            file_name=f"crypto_tax_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export detailed transactions if available
        if results.get('transactions_detail'):
            detail_df = pd.DataFrame(results['transactions_detail'])
            csv_detail = detail_df.to_csv(index=False)
            st.download_button(
                label="📊 Download Detailed Report (CSV)",
                data=csv_detail,
                file_name=f"crypto_tax_detail_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
