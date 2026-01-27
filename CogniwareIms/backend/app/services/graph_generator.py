# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Graph Generation Service Generates data for charts and visualizations."""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class GraphGenerator:
    """Generate data structures for frontend charts and graphs."""

    async def generate_stock_trend(self, product_sku: str, days: int = 30) -> Dict[str, Any]:
        """Generate stock level trend data for time-series charts."""
        # In production, this would query actual historical data
        # For now, generate realistic sample data

        data_points = []
        base_stock = 250

        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            # Simulate realistic stock fluctuations
            stock = base_stock + random.randint(-30, 50)

            data_points.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "stock": max(0, stock),
                    "reserved": random.randint(20, 40),
                    "in_transit": random.randint(10, 25),
                }
            )

        return {
            "product_sku": product_sku,
            "period": f"{days} days",
            "data": data_points,
            "chart_type": "line",
        }

    async def generate_category_distribution(self) -> Dict[str, Any]:
        """Generate product category distribution for pie/bar charts."""
        categories = [
            {"category": "Processors", "count": 436, "value": 261600, "percentage": 31},
            {"category": "GPUs", "count": 45, "value": 1349955, "percentage": 3},
            {"category": "Memory", "count": 523, "value": 156877, "percentage": 37},
            {"category": "Storage", "count": 312, "value": 93600, "percentage": 22},
            {"category": "Motherboards", "count": 89, "value": 44500, "percentage": 6},
        ]

        return {
            "data": categories,
            "total_items": sum(c["count"] for c in categories),
            "total_value": sum(c["value"] for c in categories),
            "chart_type": "pie",
        }

    async def generate_warehouse_comparison(self) -> Dict[str, Any]:
        """Generate warehouse utilization comparison for bar charts."""
        warehouses = [
            {
                "name": "San Jose",
                "utilization": 78,
                "capacity": 15000,
                "items": 2847,
                "categories": {
                    "Processors": 145,
                    "GPUs": 20,
                    "Memory": 180,
                    "Storage": 95,
                },
            },
            {
                "name": "Austin",
                "utilization": 65,
                "capacity": 12000,
                "items": 1923,
                "categories": {
                    "Processors": 120,
                    "GPUs": 15,
                    "Memory": 150,
                    "Storage": 80,
                },
            },
            {
                "name": "Portland",
                "utilization": 82,
                "capacity": 18000,
                "items": 3456,
                "categories": {
                    "Processors": 171,
                    "GPUs": 10,
                    "Memory": 193,
                    "Storage": 137,
                },
            },
        ]

        return {
            "data": warehouses,
            "chart_type": "bar",
            "metrics": ["utilization", "items", "capacity"],
        }

    async def generate_allocation_timeline(self, days: int = 14) -> Dict[str, Any]:
        """Generate allocation activity timeline."""
        timeline = []

        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            timeline.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "pending": random.randint(5, 15),
                    "confirmed": random.randint(10, 25),
                    "shipped": random.randint(8, 20),
                    "total": random.randint(25, 55),
                }
            )

        return {"period": f"{days} days", "data": timeline, "chart_type": "area"}

    async def generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate KPI metrics for dashboard."""
        metrics = [
            {
                "name": "Inventory Turnover",
                "value": 4.2,
                "unit": "x",
                "trend": "+12%",
                "trend_direction": "up",
                "description": "Times inventory sold and replaced",
                "history": [3.8, 3.9, 4.0, 4.1, 4.2],
            },
            {
                "name": "Order Fulfillment Rate",
                "value": 96.8,
                "unit": "%",
                "trend": "+3.2%",
                "trend_direction": "up",
                "description": "Orders fulfilled on time",
                "history": [94.2, 95.1, 95.8, 96.3, 96.8],
            },
            {
                "name": "Average Delivery Time",
                "value": 2.4,
                "unit": "days",
                "trend": "-0.3 days",
                "trend_direction": "down",
                "description": "Average time from order to delivery",
                "history": [2.9, 2.7, 2.6, 2.5, 2.4],
            },
            {
                "name": "Stock Accuracy",
                "value": 99.2,
                "unit": "%",
                "trend": "+0.5%",
                "trend_direction": "up",
                "description": "Inventory count accuracy",
                "history": [98.5, 98.7, 98.9, 99.0, 99.2],
            },
        ]

        return {"metrics": metrics, "chart_type": "kpi_cards"}

    async def generate_heatmap_data(self) -> Dict[str, Any]:
        """Generate heatmap data for warehouse activity."""
        # Days of week x hours of day
        heatmap = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for day_idx, day in enumerate(days):
            for hour in range(24):
                activity = random.randint(5, 95) if 8 <= hour <= 18 else random.randint(0, 30)
                heatmap.append({"day": day, "hour": hour, "activity": activity})

        return {
            "data": heatmap,
            "chart_type": "heatmap",
            "dimensions": {"days": days, "hours": 24},
        }

    async def generate_forecast(self, product_sku: str, forecast_days: int = 30) -> Dict[str, Any]:
        """Generate demand forecast using simple moving average In production, would use ML models."""
        # Get historical data (simulated)
        historical = []
        base_demand = 50

        for i in range(30):
            date = datetime.now() - timedelta(days=30 - i)
            demand = base_demand + random.randint(-15, 20)
            historical.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "actual": max(0, demand),
                    "type": "historical",
                }
            )

        # Generate forecast
        forecast = []
        avg_demand = sum(h["actual"] for h in historical[-7:]) / 7  # 7-day moving average

        for i in range(forecast_days):
            date = datetime.now() + timedelta(days=i + 1)
            # Add some variation
            forecasted = avg_demand + random.randint(-10, 15)
            forecast.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "forecasted": max(0, int(forecasted)),
                    "confidence_low": max(0, int(forecasted * 0.8)),
                    "confidence_high": int(forecasted * 1.2),
                    "type": "forecast",
                }
            )

        return {
            "product_sku": product_sku,
            "historical": historical,
            "forecast": forecast,
            "chart_type": "forecast",
            "method": "moving_average",
        }

    async def generate_comparison_chart(self, items: List[str], metric: str = "stock_level") -> Dict[str, Any]:
        """Generate comparison data for multiple items."""
        comparison_data = []

        for item in items:
            comparison_data.append(
                {
                    "item": item,
                    "current": random.randint(50, 500),
                    "target": random.randint(100, 600),
                    "last_month": random.randint(40, 450),
                    "percentage": random.randint(60, 95),
                }
            )

        return {
            "metric": metric,
            "data": comparison_data,
            "chart_type": "comparison_bar",
        }


# Global instance
graph_generator = GraphGenerator()
