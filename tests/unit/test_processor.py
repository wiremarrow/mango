"""
Unit tests for data processor.
"""

import pytest
import pandas as pd
from io import StringIO
from datetime import datetime
from pathlib import Path

from polymarket.utils.processor import DataProcessor
from polymarket.models.models import (
    Market, PriceHistory, PricePoint, MarketHistoricalData, 
    Event, EventHistoricalData
)
from polymarket.utils.exceptions import DataProcessingError, ExportError


class TestDataProcessor:
    """Test DataProcessor class."""
    
    def test_merge_price_histories(self, sample_market):
        """Test merging price histories into DataFrame."""
        # Create price histories for two outcomes
        price_points_yes = [
            PricePoint(timestamp=datetime(2024, 1, 1, i), price=0.45 + i * 0.01)
            for i in range(3)
        ]
        price_points_no = [
            PricePoint(timestamp=datetime(2024, 1, 1, i), price=0.55 - i * 0.01)
            for i in range(3)
        ]
        
        histories = {
            "Yes": PriceHistory(
                market_id="1",
                token_id="0x1",
                outcome="Yes",
                interval="1h",
                price_points=price_points_yes
            ),
            "No": PriceHistory(
                market_id="1",
                token_id="0x2",
                outcome="No",
                interval="1h",
                price_points=price_points_no
            )
        }
        
        df = DataProcessor.merge_price_histories(histories)
        
        assert len(df) == 3
        assert "timestamp" in df.columns
        assert "Yes_price" in df.columns
        assert "No_price" in df.columns
        assert df["Yes_price"].iloc[0] == 0.45
        assert df["No_price"].iloc[0] == 0.55
    
    def test_merge_price_histories_with_missing_data(self):
        """Test merging with missing data points."""
        # Create histories with different timestamps
        histories = {
            "Yes": PriceHistory(
                market_id="1",
                token_id="0x1",
                outcome="Yes",
                interval="1h",
                price_points=[
                    PricePoint(timestamp=datetime(2024, 1, 1, 0), price=0.45),
                    PricePoint(timestamp=datetime(2024, 1, 1, 2), price=0.47),
                ]
            ),
            "No": PriceHistory(
                market_id="1",
                token_id="0x2",
                outcome="No",
                interval="1h",
                price_points=[
                    PricePoint(timestamp=datetime(2024, 1, 1, 1), price=0.54),
                    PricePoint(timestamp=datetime(2024, 1, 1, 2), price=0.53),
                ]
            )
        }
        
        df = DataProcessor.merge_price_histories(histories)
        
        # Should have all timestamps
        assert len(df) == 3
        
        # Check forward filling
        assert pd.notna(df["Yes_price"].iloc[1])  # Forward filled
        assert pd.isna(df["No_price"].iloc[0])  # No previous value to fill
    
    def test_calculate_statistics(self):
        """Test statistical calculations."""
        price_points = [
            PricePoint(timestamp=datetime(2024, 1, 1, i), price=0.40 + i * 0.05)
            for i in range(5)
        ]
        
        history = PriceHistory(
            market_id="1",
            token_id="0x1",
            outcome="Yes",
            interval="1h",
            price_points=price_points
        )
        
        stats = DataProcessor.calculate_statistics(history)
        
        assert stats['count'] == 5
        assert stats['mean'] == 0.5  # (0.4 + 0.45 + 0.5 + 0.55 + 0.6) / 5
        assert stats['min'] == 0.4
        assert stats['max'] == 0.6
        assert stats['latest'] == 0.6
        assert stats['oldest'] == 0.4
        assert stats['change'] == 0.2
        assert stats['change_percent'] == 50.0
    
    def test_calculate_statistics_empty_history(self):
        """Test statistics with empty history."""
        history = PriceHistory(
            market_id="1",
            token_id="0x1",
            outcome="Yes",
            interval="1h",
            price_points=[]
        )
        
        stats = DataProcessor.calculate_statistics(history)
        
        assert stats['count'] == 0
        assert stats['mean'] == 0
        assert stats['min'] == 0
        assert stats['max'] == 0
    
    def test_to_csv(self, sample_market, sample_price_history):
        """Test CSV generation."""
        data = MarketHistoricalData(
            market=sample_market,
            price_histories={"Yes": sample_price_history}
        )
        
        csv_string = DataProcessor.to_csv(data, include_metadata=True)
        
        # Check metadata section
        assert "# Market Metadata" in csv_string
        assert sample_market.question in csv_string
        assert sample_market.condition_id in csv_string
        
        # Check data section
        assert "timestamp,Yes_price" in csv_string
        assert "2024-01-01" in csv_string
        assert "0.45" in csv_string
    
    def test_save_to_file(self, tmp_path, sample_market, sample_price_history):
        """Test saving to file."""
        data = MarketHistoricalData(
            market=sample_market,
            price_histories={"Yes": sample_price_history}
        )
        
        output_path = tmp_path / "test_output.csv"
        DataProcessor.save_to_file(data, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "# Market Metadata" in content
        assert "timestamp,Yes_price" in content
    
    def test_merge_event_price_histories(self, sample_event):
        """Test merging event price histories."""
        # Create two markets with price histories
        market1 = Market(
            id="1",
            slug="team-a-win",
            condition_id="0x1",
            question="Will Team A win?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"],
            group_item_title="Team A"
        )
        
        market2 = Market(
            id="2",
            slug="team-b-win",
            condition_id="0x2",
            question="Will Team B win?",
            outcomes=["Yes", "No"],
            token_ids=["0x3", "0x4"],
            group_item_title="Team B"
        )
        
        # Create price histories
        price_points = [
            PricePoint(timestamp=datetime(2024, 1, 1, i), price=0.3 + i * 0.05)
            for i in range(3)
        ]
        
        market1_data = MarketHistoricalData(
            market=market1,
            price_histories={
                "Yes": PriceHistory(
                    market_id="1",
                    token_id="0x1",
                    outcome="Yes",
                    interval="1h",
                    price_points=price_points
                )
            }
        )
        
        market2_data = MarketHistoricalData(
            market=market2,
            price_histories={
                "Yes": PriceHistory(
                    market_id="2",
                    token_id="0x3",
                    outcome="Yes",
                    interval="1h",
                    price_points=price_points
                )
            }
        )
        
        event_data = EventHistoricalData(event=sample_event)
        event_data.market_data = {
            "team-a-win": market1_data,
            "team-b-win": market2_data
        }
        
        df = DataProcessor.merge_event_price_histories(event_data)
        
        assert "team_a_yes" in df.columns
        assert "team_b_yes" in df.columns
        assert len(df) == 3
    
    def test_stream_event_to_csv(self, tmp_path, sample_event):
        """Test streaming event data to CSV."""
        # Create a simple event with one market
        market = Market(
            id="1",
            slug="test-market",
            condition_id="0x1",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"]
        )
        
        price_points = [
            PricePoint(timestamp=datetime(2024, 1, 1, i), price=0.5)
            for i in range(3)
        ]
        
        market_data = MarketHistoricalData(
            market=market,
            price_histories={
                "Yes": PriceHistory(
                    market_id="1",
                    token_id="0x1",
                    outcome="Yes",
                    interval="1h",
                    price_points=price_points
                )
            }
        )
        
        event_data = EventHistoricalData(event=sample_event)
        event_data.market_data = {"test-market": market_data}
        
        output_path = tmp_path / "event_data.csv"
        DataProcessor.stream_event_to_csv(event_data, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "timestamp,test-market_yes" in content
        assert "2024-01-01" in content