"""
Data processing module for Polymarket data.

This module handles data formatting, aggregation, statistical analysis,
and export functionality for market historical data.
"""

import pandas as pd
import json
import csv
import io
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .models import MarketHistoricalData, PriceHistory, EventHistoricalData
from .config import (
    EXCEL_ENGINE, MAX_CSV_SIZE_MB, MAX_JSON_SIZE_MB,
    PRICE_PRECISION, DEFAULT_EXPORT_FORMAT
)
from .exceptions import ExportError, DataProcessingError


logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes and formats Polymarket historical data."""
    
    @staticmethod
    def merge_price_histories(histories: Dict[str, PriceHistory]) -> pd.DataFrame:
        """
        Merge multiple price histories into a single DataFrame.
        
        Args:
            histories: Dictionary mapping outcome names to PriceHistory objects
            
        Returns:
            DataFrame with columns: timestamp, outcome_1_price, outcome_2_price, etc.
            
        Raises:
            DataProcessingError: If merging fails
        """
        if not histories:
            return pd.DataFrame()
            
        try:
            # Create individual DataFrames for each outcome
            dfs = []
            for outcome, history in histories.items():
                if history.price_points:
                    df = pd.DataFrame([
                        {
                            'timestamp': point.timestamp,
                            f'{outcome}_price': point.price
                        }
                        for point in history.price_points
                    ])
                    df.set_index('timestamp', inplace=True)
                    dfs.append(df)
            
            if not dfs:
                return pd.DataFrame()
                
            # Merge all DataFrames on timestamp
            result = dfs[0]
            for df in dfs[1:]:
                result = result.join(df, how='outer')
                
            # Forward fill missing values
            result.ffill(inplace=True)
            result.reset_index(inplace=True)
            
            return result
            
        except Exception as e:
            raise DataProcessingError(f"Failed to merge price histories: {e}")
    
    @staticmethod
    def merge_event_price_histories(event_data: EventHistoricalData, 
                                  column_format: str = 'short') -> pd.DataFrame:
        """
        Merge all market price histories from an event into a single DataFrame.
        
        Args:
            event_data: EventHistoricalData containing all market data
            column_format: Column naming format ('short', 'full', 'descriptive')
            
        Returns:
            DataFrame with timestamp index and columns for each market/outcome combination
        """
        if not event_data.market_data:
            return pd.DataFrame()
            
        try:
            # Collect all DataFrames
            all_dfs = []
            
            for market_slug, market_data in event_data.market_data.items():
                market = market_data.market
                
                # Determine column prefix based on format
                if column_format == 'short':
                    # Use group_item_title if available, otherwise extract from slug
                    if market.group_item_title:
                        prefix = market.group_item_title.lower().replace(' ', '_')
                    else:
                        # Extract key part from slug (e.g., "will-liverpool-win" -> "liverpool")
                        parts = market_slug.split('-')
                        if 'will' in parts:
                            idx = parts.index('will')
                            if idx + 1 < len(parts):
                                prefix = parts[idx + 1]
                            else:
                                prefix = market_slug[:20]
                        else:
                            prefix = market_slug[:20]
                elif column_format == 'full':
                    prefix = market_slug
                else:  # descriptive
                    if market.group_item_title:
                        prefix = market.group_item_title.replace(' ', '_')
                    else:
                        # Use question but clean it up
                        prefix = market.question[:50].replace(' ', '_').replace('?', '')
                
                # Create DataFrame for this market
                for outcome, history in market_data.price_histories.items():
                    if history.price_points:
                        df = pd.DataFrame([
                            {
                                'timestamp': point.timestamp,
                                f'{prefix}_{outcome.lower()}': point.price
                            }
                            for point in history.price_points
                        ])
                        df.set_index('timestamp', inplace=True)
                        all_dfs.append(df)
            
            if not all_dfs:
                return pd.DataFrame()
                
            # Merge all DataFrames
            result = all_dfs[0]
            for df in all_dfs[1:]:
                result = result.join(df, how='outer')
                
            # Forward fill missing values
            result.ffill(inplace=True)
            result.reset_index(inplace=True)
            
            return result
            
        except Exception as e:
            raise DataProcessingError(f"Failed to merge event price histories: {e}")
    
    @staticmethod
    def calculate_statistics(history: PriceHistory) -> Dict[str, Any]:
        """
        Calculate statistical metrics for a price history.
        
        Args:
            history: PriceHistory object
            
        Returns:
            Dictionary with statistical metrics
        """
        if not history.price_points:
            return {}
            
        prices = [point.price for point in history.price_points]
        df = pd.DataFrame(prices, columns=['price'])
        
        # Calculate returns for volatility
        returns = df['price'].pct_change().dropna()
        
        return {
            'count': len(prices),
            'mean': round(df['price'].mean(), PRICE_PRECISION),
            'std': round(df['price'].std(), PRICE_PRECISION),
            'min': round(df['price'].min(), PRICE_PRECISION),
            'max': round(df['price'].max(), PRICE_PRECISION),
            'median': round(df['price'].median(), PRICE_PRECISION),
            'volatility': round(returns.std(), PRICE_PRECISION) if len(returns) > 0 else 0,
            'latest': history.latest_price,
            'oldest': history.oldest_price,
            'change': history.price_change,
            'change_percent': history.price_change_percent,
            'data_points': history.data_points_count
        }
    
    @staticmethod
    def to_csv(data: MarketHistoricalData, include_metadata: bool = True) -> str:
        """
        Convert market historical data to CSV format.
        
        Args:
            data: MarketHistoricalData object
            include_metadata: Whether to include market metadata
            
        Returns:
            CSV string
            
        Raises:
            ExportError: If CSV generation fails
        """
        try:
            output = io.StringIO()
            
            # Write metadata if requested
            if include_metadata:
                writer = csv.writer(output)
                writer.writerow(['# Market Metadata'])
                writer.writerow(['Market ID', data.market.id])
                writer.writerow(['Market Slug', data.market.slug])
                writer.writerow(['Question', data.market.question])
                writer.writerow(['Condition ID', data.market.condition_id])
                writer.writerow(['Outcomes', ', '.join(data.market.outcomes)])
                writer.writerow(['Active', data.market.active])
                writer.writerow(['Volume', f"${data.market.volume:,.2f}"])
                writer.writerow(['Liquidity', f"${data.market.liquidity:,.2f}"])
                writer.writerow([])
                writer.writerow(['# Price History'])
            
            # Convert price histories to DataFrame
            df = DataProcessor.merge_price_histories(data.price_histories)
            
            if not df.empty:
                # Round prices to specified precision
                price_columns = [col for col in df.columns if col.endswith('_price')]
                df[price_columns] = df[price_columns].round(PRICE_PRECISION)
                
                df.to_csv(output, index=False)
            
            return output.getvalue()
            
        except Exception as e:
            raise ExportError(f"Failed to generate CSV: {e}")
    
    @staticmethod
    def to_json(data: MarketHistoricalData, pretty: bool = True) -> str:
        """
        Convert market historical data to JSON format.
        
        Args:
            data: MarketHistoricalData object
            pretty: Whether to pretty-print the JSON
            
        Returns:
            JSON string
            
        Raises:
            ExportError: If JSON generation fails
        """
        try:
            data_dict = data.to_dict()
            
            if pretty:
                return json.dumps(data_dict, indent=2, default=str)
            else:
                return json.dumps(data_dict, default=str)
                
        except Exception as e:
            raise ExportError(f"Failed to generate JSON: {e}")
    
    @staticmethod
    def to_dataframe(data: MarketHistoricalData) -> pd.DataFrame:
        """
        Convert market historical data to pandas DataFrame.
        
        Args:
            data: MarketHistoricalData object
            
        Returns:
            DataFrame with price history
        """
        return DataProcessor.merge_price_histories(data.price_histories)
    
    @staticmethod
    def save_to_file(data: MarketHistoricalData, 
                    filepath: Union[str, Path],
                    format: str = DEFAULT_EXPORT_FORMAT,
                    **kwargs) -> None:
        """
        Save market historical data to a file.
        
        Args:
            data: MarketHistoricalData object
            filepath: Output file path
            format: Output format ('csv', 'json', 'parquet', 'excel')
            **kwargs: Additional arguments for the specific format
            
        Raises:
            ExportError: If file save fails
        """
        filepath = Path(filepath)
        # Ensure parent directory exists (including data/ directory)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if format.lower() == 'csv':
                csv_data = DataProcessor.to_csv(data, **kwargs)
                # Check file size
                size_mb = len(csv_data.encode('utf-8')) / (1024 * 1024)
                if size_mb > MAX_CSV_SIZE_MB:
                    raise ExportError(f"CSV file too large: {size_mb:.1f}MB > {MAX_CSV_SIZE_MB}MB")
                filepath.write_text(csv_data)
                
            elif format.lower() == 'json':
                json_data = DataProcessor.to_json(data, **kwargs)
                # Check file size
                size_mb = len(json_data.encode('utf-8')) / (1024 * 1024)
                if size_mb > MAX_JSON_SIZE_MB:
                    raise ExportError(f"JSON file too large: {size_mb:.1f}MB > {MAX_JSON_SIZE_MB}MB")
                filepath.write_text(json_data)
                
            elif format.lower() == 'parquet':
                df = DataProcessor.to_dataframe(data)
                df.to_parquet(filepath, **kwargs)
                
            elif format.lower() == 'excel':
                df = DataProcessor.to_dataframe(data)
                
                # Create Excel writer
                with pd.ExcelWriter(filepath, engine=EXCEL_ENGINE) as writer:
                    # Write price data
                    df.to_excel(writer, sheet_name='Price History', index=False)
                    
                    # Write metadata
                    metadata_df = pd.DataFrame([
                        ['Market ID', data.market.id],
                        ['Market Slug', data.market.slug],
                        ['Question', data.market.question],
                        ['Condition ID', data.market.condition_id],
                        ['Outcomes', ', '.join(data.market.outcomes)],
                        ['Active', data.market.active],
                        ['Volume', f"${data.market.volume:,.2f}"],
                        ['Liquidity', f"${data.market.liquidity:,.2f}"]
                    ], columns=['Property', 'Value'])
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                    
                    # Write statistics for each outcome
                    for outcome, history in data.price_histories.items():
                        stats = DataProcessor.calculate_statistics(history)
                        stats_df = pd.DataFrame(list(stats.items()), columns=['Metric', 'Value'])
                        # Sanitize sheet name (Excel has restrictions)
                        sheet_name = f'{outcome[:28]} Stats' if len(outcome) > 28 else f'{outcome} Stats'
                        stats_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            logger.info(f"Saved {format.upper()} to: {filepath}")
            
        except Exception as e:
            raise ExportError(f"Failed to save {format} file: {e}")
    
    @staticmethod
    def save_event_to_file(data: EventHistoricalData,
                          filepath: Union[str, Path],
                          format: str = DEFAULT_EXPORT_FORMAT,
                          column_format: str = 'short',
                          **kwargs) -> None:
        """
        Save event historical data to a file.
        
        Args:
            data: EventHistoricalData object
            filepath: Output file path
            format: Output format ('csv', 'json', 'parquet', 'excel')
            column_format: Column naming format ('short', 'full', 'descriptive')
            **kwargs: Additional format-specific options
        """
        try:
            filepath = Path(filepath)
            
            if format.lower() == 'csv':
                # Merge all market data into single DataFrame
                df = DataProcessor.merge_event_price_histories(data, column_format)
                df.to_csv(filepath, index=False, **kwargs)
                
            elif format.lower() == 'json':
                # Convert to JSON with nested structure
                json_data = json.dumps(data.to_dict(), indent=2, default=str)
                size_mb = len(json_data.encode()) / (1024 * 1024)
                if size_mb > MAX_JSON_SIZE_MB:
                    raise ExportError(f"JSON file too large: {size_mb:.1f}MB > {MAX_JSON_SIZE_MB}MB")
                filepath.write_text(json_data)
                
            elif format.lower() == 'parquet':
                df = DataProcessor.merge_event_price_histories(data, column_format)
                df.to_parquet(filepath, **kwargs)
                
            elif format.lower() == 'excel':
                # Create Excel with multiple sheets
                with pd.ExcelWriter(filepath, engine=EXCEL_ENGINE) as writer:
                    # Combined sheet
                    combined_df = DataProcessor.merge_event_price_histories(data, column_format)
                    combined_df.to_excel(writer, sheet_name='All Markets', index=False)
                    
                    # Event metadata sheet
                    event_metadata_df = pd.DataFrame([
                        ['Event ID', data.event.id],
                        ['Event Title', data.event.title],
                        ['Event Slug', data.event.slug],
                        ['Total Markets', data.total_markets],
                        ['Extracted At', data.extracted_at],
                        ['Neg Risk', data.event.neg_risk],
                    ], columns=['Property', 'Value'])
                    event_metadata_df.to_excel(writer, sheet_name='Event Info', index=False)
                    
                    # Individual market sheets
                    for market_slug, market_data in data.market_data.items():
                        df = DataProcessor.merge_price_histories(market_data.price_histories)
                        # Sanitize sheet name
                        if market_data.market.group_item_title:
                            sheet_name = market_data.market.group_item_title[:30]
                        else:
                            sheet_name = market_slug[:30]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            logger.info(f"Saved event data ({data.total_markets} markets) to: {filepath}")
            
        except Exception as e:
            raise ExportError(f"Failed to save event {format} file: {e}")
    
    @staticmethod
    def create_summary_report(data: MarketHistoricalData) -> str:
        """
        Create a human-readable summary report of the market data.
        
        Args:
            data: MarketHistoricalData object
            
        Returns:
            Formatted summary report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("POLYMARKET HISTORICAL DATA SUMMARY")
        lines.append("=" * 80)
        lines.append(f"\nMarket: {data.market.question}")
        lines.append(f"Slug: {data.market.slug}")
        lines.append(f"Condition ID: {data.market.condition_id}")
        lines.append(f"Outcomes: {', '.join(data.market.outcomes)}")
        
        lines.append(f"\nMarket Status:")
        lines.append(f"  Active: {data.market.active}")
        lines.append(f"  Closed: {data.market.closed}")
        lines.append(f"  Volume: ${data.market.volume:,.2f}")
        lines.append(f"  Liquidity: ${data.market.liquidity:,.2f}")
        
        lines.append("\n" + "-" * 80)
        lines.append("PRICE STATISTICS")
        lines.append("-" * 80)
        
        for outcome, history in data.price_histories.items():
            if history.price_points:
                stats = DataProcessor.calculate_statistics(history)
                lines.append(f"\n{outcome}:")
                lines.append(f"  Latest Price: ${stats['latest']:.{PRICE_PRECISION}f}")
                lines.append(f"  Change: ${stats.get('change', 0):.{PRICE_PRECISION}f} "
                           f"({stats.get('change_percent', 0):.2f}%)")
                lines.append(f"  High: ${stats['max']:.{PRICE_PRECISION}f}")
                lines.append(f"  Low: ${stats['min']:.{PRICE_PRECISION}f}")
                lines.append(f"  Mean: ${stats['mean']:.{PRICE_PRECISION}f}")
                lines.append(f"  Volatility: {stats.get('volatility', 0):.{PRICE_PRECISION}f}")
                lines.append(f"  Data Points: {stats['count']}")
                
                # Time range
                if history.price_points:
                    start_time = history.price_points[0].timestamp
                    end_time = history.price_points[-1].timestamp
                    lines.append(f"  Time Range: {start_time.strftime('%Y-%m-%d %H:%M')} to "
                               f"{end_time.strftime('%Y-%m-%d %H:%M')}")
        
        lines.append("\n" + "=" * 80)
        lines.append(f"Data extracted at: {data.extracted_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        
        return '\n'.join(lines)