"""
Data processing module for Polymarket data.

This module handles data formatting, aggregation, statistical analysis,
and CSV export functionality for market historical data. Includes both
DataFrame-based processing and memory-efficient streaming for large datasets.
"""

import pandas as pd
import csv
import io
import logging
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Iterator, Tuple
from datetime import datetime
from collections import defaultdict
from tabulate import tabulate

from ..models import MarketHistoricalData, PriceHistory, EventHistoricalData
from .config import (
    MAX_CSV_SIZE_MB, PRICE_PRECISION
)
from .exceptions import ExportError, DataProcessingError
from .utils import get_column_prefix


logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes and formats Polymarket historical data for CSV export."""
    
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
    def merge_event_price_histories(event_data: EventHistoricalData) -> pd.DataFrame:
        """
        Merge all market price histories from an event into a single DataFrame.
        
        Args:
            event_data: EventHistoricalData containing all market data
            
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
                
                # Determine column prefix using utility function
                prefix = get_column_prefix(market, market_slug)
                
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
    def calculate_statistics(history: PriceHistory) -> Dict[str, float]:
        """
        Calculate statistical metrics for a price history.
        
        Args:
            history: PriceHistory object
            
        Returns:
            Dictionary with statistical metrics
        """
        if not history.price_points:
            return {
                'count': 0,
                'mean': 0,
                'std': 0,
                'min': 0,
                'max': 0,
                'median': 0,
                'volatility': 0
            }
        
        prices = [p.price for p in history.price_points]
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
    def create_summary_report(data: MarketHistoricalData) -> str:
        """
        Create a human-readable summary report of market historical data.
        
        Args:
            data: MarketHistoricalData object
            
        Returns:
            Formatted summary report string
        """
        try:
            lines = []
            lines.append("\n" + "=" * 80)
            lines.append("MARKET SUMMARY REPORT")
            lines.append("=" * 80)
            lines.append("")
            
            # Market info table
            market_info = [
                ["Question", data.market.question],
                ["Slug", data.market.slug],
                ["Status", "Active" if data.market.active else "Inactive"],
                ["Volume", f"${data.market.volume:,.2f}"],
                ["Liquidity", f"${data.market.liquidity:,.2f}"]
            ]
            lines.append(tabulate(market_info, tablefmt="simple", colalign=("left", "left")))
            lines.append("")
            
            # Price statistics for each outcome
            for outcome, history in data.price_histories.items():
                if history.price_points:
                    stats = DataProcessor.calculate_statistics(history)
                    
                    lines.append(f"\n{outcome} Outcome Statistics")
                    lines.append("-" * 40)
                    
                    stats_table = [
                        ["Metric", "Value"],
                        ["Data Points", f"{stats['data_points']:,}"],
                        ["Latest Price", f"${stats['latest']:.4f}"],
                        ["Oldest Price", f"${stats['oldest']:.4f}"],
                    ]
                    
                    if stats['change'] is not None:
                        stats_table.append(["Price Change", f"${stats['change']:.4f} ({stats['change_percent']:.2f}%)"])
                    
                    stats_table.extend([
                        ["Mean Price", f"${stats['mean']:.4f}"],
                        ["Std Deviation", f"${stats['std']:.4f}"],
                        ["Min Price", f"${stats['min']:.4f}"],
                        ["Max Price", f"${stats['max']:.4f}"],
                        ["Median Price", f"${stats['median']:.4f}"],
                        ["Volatility", f"{stats['volatility']:.4f}"]
                    ])
                    
                    lines.append(tabulate(stats_table, headers="firstrow", tablefmt="github", floatfmt=".4f"))
            
            lines.append("\n" + "=" * 80)
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Failed to create summary report: {e}")
            return f"Error creating summary report: {e}"
    
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
    def save_to_file(data: MarketHistoricalData, 
                    filepath: Union[str, Path],
                    include_metadata: bool = True) -> None:
        """
        Save market historical data to a CSV file.
        
        Args:
            data: MarketHistoricalData object
            filepath: Output file path
            include_metadata: Whether to include market metadata
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            csv_data = DataProcessor.to_csv(data, include_metadata=include_metadata)
            filepath.write_text(csv_data)
                
            logger.info(f"Saved CSV to: {filepath}")
            
        except Exception as e:
            raise ExportError(f"Failed to save CSV file: {e}")
    
    @staticmethod
    def save_event_to_file(data: EventHistoricalData,
                          filepath: Union[str, Path]) -> None:
        """
        Save event historical data to a CSV file.
        
        Args:
            data: EventHistoricalData object
            filepath: Output file path
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Use streaming for better memory efficiency
            DataProcessor.stream_event_to_csv(data, filepath)
                
            logger.info(f"Saved event data ({data.total_markets} markets) to: {filepath}")
            
        except Exception as e:
            raise ExportError(f"Failed to save event CSV file: {e}")
    
    @staticmethod
    def stream_event_to_csv(event_data: EventHistoricalData,
                           filepath: Union[str, Path]) -> None:
        """
        Stream event data directly to CSV without loading all data into memory.
        
        This method processes one timestamp at a time across all markets,
        dramatically reducing memory usage for large events.
        
        Args:
            event_data: EventHistoricalData containing all market data
            filepath: Output CSV file path
            
        Raises:
            ExportError: If streaming fails
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Starting streaming CSV export for {event_data.total_markets} markets")
            
            # Step 1: Collect all unique timestamps across all markets
            logger.debug("Collecting timestamps...")
            timestamp_data = defaultdict(dict)  # timestamp -> {column: price}
            
            # Process each market
            for market_slug, market_data in event_data.market_data.items():
                market = market_data.market
                
                # Determine column prefix using utility function
                prefix = get_column_prefix(market, market_slug)
                
                # Process each outcome's price history
                for outcome, history in market_data.price_histories.items():
                    column_name = f'{prefix}_{outcome.lower()}'
                    
                    # Add each price point to our timestamp map
                    for point in history.price_points:
                        timestamp_data[point.timestamp][column_name] = point.price
            
            # Step 2: Get sorted timestamps and column names
            timestamps = sorted(timestamp_data.keys())
            all_columns = set()
            for ts_data in timestamp_data.values():
                all_columns.update(ts_data.keys())
            columns = sorted(all_columns)
            
            logger.info(f"Writing {len(timestamps)} timestamps with {len(columns)} columns")
            
            # Step 3: Write CSV file row by row
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                # Write header
                writer = csv.writer(csvfile)
                writer.writerow(['timestamp'] + columns)
                
                # Write data rows
                prev_row = {}  # For forward-filling
                for timestamp in timestamps:
                    row_data = timestamp_data[timestamp]
                    
                    # Forward-fill missing values
                    for col in columns:
                        if col in row_data:
                            prev_row[col] = row_data[col]
                        else:
                            row_data[col] = prev_row.get(col, '')
                    
                    # Write row
                    row = [timestamp.isoformat()]
                    for col in columns:
                        value = row_data.get(col, '')
                        if isinstance(value, float):
                            value = round(value, PRICE_PRECISION)
                        row.append(value)
                    writer.writerow(row)
                    
                    # Clear row data to free memory
                    del row_data
                    
            # Clear the timestamp data
            del timestamp_data
            gc.collect()
            
            logger.info(f"Successfully streamed {len(timestamps)} rows to {filepath}")
            
        except Exception as e:
            raise ExportError(f"Failed to stream event data to CSV: {e}")
    
    @staticmethod
    def iterate_event_rows(event_data: EventHistoricalData) -> Iterator[Tuple[datetime, Dict[str, float]]]:
        """
        Iterate through event data row by row without loading all into memory.
        
        Args:
            event_data: EventHistoricalData containing all market data
            
        Yields:
            Tuples of (timestamp, price_dict) for each row
        """
        # Collect all timestamps and organize data
        timestamp_data = defaultdict(dict)
        
        for market_slug, market_data in event_data.market_data.items():
            market = market_data.market
            
            # Determine column prefix using utility function
            prefix = get_column_prefix(market, market_slug)
            
            # Process each outcome
            for outcome, history in market_data.price_histories.items():
                column_name = f'{prefix}_{outcome.lower()}'
                
                for point in history.price_points:
                    timestamp_data[point.timestamp][column_name] = point.price
        
        # Yield rows in chronological order
        prev_values = {}
        for timestamp in sorted(timestamp_data.keys()):
            current_row = timestamp_data[timestamp].copy()
            
            # Forward-fill missing values
            for col, val in prev_values.items():
                if col not in current_row:
                    current_row[col] = val
            
            # Update previous values
            prev_values.update(current_row)
            
            yield timestamp, current_row