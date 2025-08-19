# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from textwrap import dedent
from typing import Annotated, Any, List, Optional

import pandas as pd

finnhub_client = None

try:
    if os.environ.get("FINNHUB_API_KEY") is None:
        print("Please set the environment variable FINNHUB_API_KEY to use the Finnhub API.")
    else:
        import finnhub

        finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])
        print("Finnhub client initialized")

except:
    pass


# https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/utilities/financial_datasets.py
"""
Util that calls several of financial datasets stock market REST APIs.
Docs: https://docs.financialdatasets.ai/
"""

import requests
from pydantic import BaseModel

FINANCIAL_DATASETS_BASE_URL = "https://api.financialdatasets.ai/"


class FinancialDatasetsAPIWrapper(BaseModel):
    """Wrapper for financial datasets API."""

    financial_datasets_api_key: Optional[str] = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.financial_datasets_api_key = data["api_key"]

    @property
    def _api_key(self) -> str:
        if self.financial_datasets_api_key is None:
            raise ValueError(
                "API key is required for the FinancialDatasetsAPIWrapper. "
                "Please provide the API key by either:\n"
                "1. Manually specifying it when initializing the wrapper: "
                "FinancialDatasetsAPIWrapper(financial_datasets_api_key='your_api_key')\n"
                "2. Setting it as an environment variable: FINANCIAL_DATASETS_API_KEY"
            )
        return self.financial_datasets_api_key

    def get_income_statements(
        self,
        ticker: str,
        period: str,
        limit: Optional[int],
    ) -> Optional[dict]:
        """Get the income statements for a stock `ticker` over a `period` of time.

        :param ticker: the stock ticker
        :param period: the period of time to get the balance sheets for.
            Possible values are: annual, quarterly, ttm.
        :param limit: the number of results to return, default is 10
        :return: a list of income statements
        """
        url = (
            f"{FINANCIAL_DATASETS_BASE_URL}financials/income-statements/"
            f"?ticker={ticker}"
            f"&period={period}"
            f"&limit={limit if limit else 10}"
        )

        # Add the api key to the headers
        headers = {"X-API-KEY": self._api_key}

        # Execute the request
        response = requests.get(url, headers=headers)
        data = response.json()

        return data.get("income_statements", None)

    def get_balance_sheets(
        self,
        ticker: str,
        period: str,
        limit: Optional[int],
    ) -> List[dict]:
        """Get the balance sheets for a stock `ticker` over a `period` of time.

        :param ticker: the stock ticker
        :param period: the period of time to get the balance sheets for.
            Possible values are: annual, quarterly, ttm.
        :param limit: the number of results to return, default is 10
        :return: a list of balance sheets
        """
        url = (
            f"{FINANCIAL_DATASETS_BASE_URL}financials/balance-sheets/"
            f"?ticker={ticker}"
            f"&period={period}"
            f"&limit={limit if limit else 10}"
        )

        # Add the api key to the headers
        headers = {"X-API-KEY": self._api_key}

        # Execute the request
        response = requests.get(url, headers=headers)
        data = response.json()

        return data.get("balance_sheets", None)

    def get_cash_flow_statements(
        self,
        ticker: str,
        period: str,
        limit: Optional[int],
    ) -> List[dict]:
        """Get the cash flow statements for a stock `ticker` over a `period` of time.

        :param ticker: the stock ticker
        :param period: the period of time to get the balance sheets for.
            Possible values are: annual, quarterly, ttm.
        :param limit: the number of results to return, default is 10
        :return: a list of cash flow statements
        """

        url = (
            f"{FINANCIAL_DATASETS_BASE_URL}financials/cash-flow-statements/"
            f"?ticker={ticker}"
            f"&period={period}"
            f"&limit={limit if limit else 10}"
        )

        # Add the api key to the headers
        headers = {"X-API-KEY": self._api_key}

        # Execute the request
        response = requests.get(url, headers=headers)
        data = response.json()

        return data.get("cash_flow_statements", None)

    def run(self, mode: str, ticker: str, **kwargs: Any) -> str:
        if mode == "get_income_statements":
            period = kwargs.get("period", "annual")
            limit = kwargs.get("limit", 10)
            return json.dumps(self.get_income_statements(ticker, period, limit))
        elif mode == "get_balance_sheets":
            period = kwargs.get("period", "annual")
            limit = kwargs.get("limit", 10)
            return json.dumps(self.get_balance_sheets(ticker, period, limit))
        elif mode == "get_cash_flow_statements":
            period = kwargs.get("period", "annual")
            limit = kwargs.get("limit", 10)
            return json.dumps(self.get_cash_flow_statements(ticker, period, limit))
        else:
            raise ValueError(f"Invalid mode {mode} for financial datasets API.")


financial_datasets_client = None

try:
    if os.environ.get("FINANCIAL_DATASETS_API_KEY") is None:
        print("Please set the environment variable FINANCIAL_DATASETS_API_KEY to use the financialdatasets.ai data.")
    else:
        financial_datasets_client = FinancialDatasetsAPIWrapper(api_key=os.environ["FINANCIAL_DATASETS_API_KEY"])
        print("FINANCIAL DATASETS client initialized")

except Exception as e:
    print(str(e))


def get_company_profile(symbol: Annotated[str, "ticker symbol"]) -> str:
    """Get a company's profile information."""
    profile = finnhub_client.company_profile2(symbol=symbol)
    if not profile:
        return f"Failed to find company profile for symbol {symbol} from finnhub!"

    formatted_str = (
        "[Company Introduction]:\n\n{name} is a leading entity in the {finnhubIndustry} sector. "
        "Incorporated and publicly traded since {ipo}, the company has established its reputation as "
        "one of the key players in the market. As of today, {name} has a market capitalization "
        "of {marketCapitalization:.2f} in {currency}, with {shareOutstanding:.2f} shares outstanding."
        "\n\n{name} operates primarily in the {country}, trading under the ticker {ticker} on the {exchange}. "
        "As a dominant force in the {finnhubIndustry} space, the company continues to innovate and drive "
        "progress within the industry."
    ).format(**profile)

    return formatted_str


def get_company_news(
    symbol: Annotated[str, "ticker symbol"],
    start_date: Annotated[
        str,
        "start date of the search period for the company's basic financials, yyyy-mm-dd",
    ],
    end_date: Annotated[
        str,
        "end date of the search period for the company's basic financials, yyyy-mm-dd",
    ],
    max_news_num: Annotated[int, "maximum number of news to return, default to 10"] = 10,
):
    """Retrieve market news related to designated company."""
    news = finnhub_client.company_news(symbol, _from=start_date, to=end_date)
    if len(news) == 0:
        print(f"No company news found for symbol {symbol} from finnhub!")
    news = [
        {
            "date": datetime.fromtimestamp(n["datetime"]).strftime("%Y%m%d%H%M%S"),
            "headline": n["headline"],
            "summary": n["summary"],
        }
        for n in news
    ]
    # Randomly select a subset of news if the number of news exceeds the maximum
    if len(news) > max_news_num:
        news = random.choices(news, k=max_news_num)
    news.sort(key=lambda x: x["date"])
    output = pd.DataFrame(news)

    return output.to_json(orient="split")


def get_basic_financials_history(
    symbol: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's basic financials: annual / quarterly",
    ],
    start_date: Annotated[
        str,
        "start date of the search period for the company's basic financials, yyyy-mm-dd",
    ],
    end_date: Annotated[
        str,
        "end date of the search period for the company's basic financials, yyyy-mm-dd",
    ],
    selected_columns: Annotated[
        list[str] | None,
        "List of column names of news to return, should be chosen from 'assetTurnoverTTM', 'bookValue', 'cashRatio', 'currentRatio', 'ebitPerShare', 'eps', 'ev', 'fcfMargin', 'fcfPerShareTTM', 'grossMargin', 'inventoryTurnoverTTM', 'longtermDebtTotalAsset', 'longtermDebtTotalCapital', 'longtermDebtTotalEquity', 'netDebtToTotalCapital', 'netDebtToTotalEquity', 'netMargin', 'operatingMargin', 'payoutRatioTTM', 'pb', 'peTTM', 'pfcfTTM', 'pretaxMargin', 'psTTM', 'ptbv', 'quickRatio', 'receivablesTurnoverTTM', 'roaTTM', 'roeTTM', 'roicTTM', 'rotcTTM', 'salesPerShare', 'sgaToSale', 'tangibleBookValue', 'totalDebtToEquity', 'totalDebtToTotalAsset', 'totalDebtToTotalCapital', 'totalRatio'",
    ] = None,
) -> str:

    if freq not in ["annual", "quarterly"]:
        return f"Invalid reporting frequency {freq}. Please specify either 'annual' or 'quarterly'."

    basic_financials = finnhub_client.company_basic_financials(symbol, "all")
    if not basic_financials["series"]:
        return f"Failed to find basic financials for symbol {symbol} from finnhub! Try a different symbol."

    output_dict = defaultdict(dict)
    for metric, value_list in basic_financials["series"][freq].items():
        if selected_columns and metric not in selected_columns:
            continue
        for value in value_list:
            if value["period"] >= start_date and value["period"] <= end_date:
                output_dict[metric].update({value["period"]: value["v"]})

    financials_output = pd.DataFrame(output_dict)
    financials_output = financials_output.rename_axis(index="date")

    return financials_output.to_json(orient="split")


def get_basic_financials(
    symbol: Annotated[str, "ticker symbol"],
    selected_columns: Annotated[
        list[str] | None,
        "List of column names of news to return, should be chosen from 'assetTurnoverTTM', 'bookValue', 'cashRatio', 'currentRatio', 'ebitPerShare', 'eps', 'ev', 'fcfMargin', 'fcfPerShareTTM', 'grossMargin', 'inventoryTurnoverTTM', 'longtermDebtTotalAsset', 'longtermDebtTotalCapital', 'longtermDebtTotalEquity', 'netDebtToTotalCapital', 'netDebtToTotalEquity', 'netMargin', 'operatingMargin', 'payoutRatioTTM', 'pb', 'peTTM', 'pfcfTTM', 'pretaxMargin', 'psTTM', 'ptbv', 'quickRatio', 'receivablesTurnoverTTM', 'roaTTM', 'roeTTM', 'roicTTM', 'rotcTTM', 'salesPerShare', 'sgaToSale', 'tangibleBookValue', 'totalDebtToEquity', 'totalDebtToTotalAsset', 'totalDebtToTotalCapital', 'totalRatio','10DayAverageTradingVolume', '13WeekPriceReturnDaily', '26WeekPriceReturnDaily', '3MonthADReturnStd', '3MonthAverageTradingVolume', '52WeekHigh', '52WeekHighDate', '52WeekLow', '52WeekLowDate', '52WeekPriceReturnDaily', '5DayPriceReturnDaily', 'assetTurnoverAnnual', 'assetTurnoverTTM', 'beta', 'bookValuePerShareAnnual', 'bookValuePerShareQuarterly', 'bookValueShareGrowth5Y', 'capexCagr5Y', 'cashFlowPerShareAnnual', 'cashFlowPerShareQuarterly', 'cashFlowPerShareTTM', 'cashPerSharePerShareAnnual', 'cashPerSharePerShareQuarterly', 'currentDividendYieldTTM', 'currentEv/freeCashFlowAnnual', 'currentEv/freeCashFlowTTM', 'currentRatioAnnual', 'currentRatioQuarterly', 'dividendGrowthRate5Y', 'dividendPerShareAnnual', 'dividendPerShareTTM', 'dividendYieldIndicatedAnnual', 'ebitdPerShareAnnual', 'ebitdPerShareTTM', 'ebitdaCagr5Y', 'ebitdaInterimCagr5Y', 'enterpriseValue', 'epsAnnual', 'epsBasicExclExtraItemsAnnual', 'epsBasicExclExtraItemsTTM', 'epsExclExtraItemsAnnual', 'epsExclExtraItemsTTM', 'epsGrowth3Y', 'epsGrowth5Y', 'epsGrowthQuarterlyYoy', 'epsGrowthTTMYoy', 'epsInclExtraItemsAnnual', 'epsInclExtraItemsTTM', 'epsNormalizedAnnual', 'epsTTM', 'focfCagr5Y', 'grossMargin5Y', 'grossMarginAnnual', 'grossMarginTTM', 'inventoryTurnoverAnnual', 'inventoryTurnoverTTM', 'longTermDebt/equityAnnual', 'longTermDebt/equityQuarterly', 'marketCapitalization', 'monthToDatePriceReturnDaily', 'netIncomeEmployeeAnnual', 'netIncomeEmployeeTTM', 'netInterestCoverageAnnual', 'netInterestCoverageTTM', 'netMarginGrowth5Y', 'netProfitMargin5Y', 'netProfitMarginAnnual', 'netProfitMarginTTM', 'operatingMargin5Y', 'operatingMarginAnnual', 'operatingMarginTTM', 'payoutRatioAnnual', 'payoutRatioTTM', 'pbAnnual', 'pbQuarterly', 'pcfShareAnnual', 'pcfShareTTM', 'peAnnual', 'peBasicExclExtraTTM', 'peExclExtraAnnual', 'peExclExtraTTM', 'peInclExtraTTM', 'peNormalizedAnnual', 'peTTM', 'pfcfShareAnnual', 'pfcfShareTTM', 'pretaxMargin5Y', 'pretaxMarginAnnual', 'pretaxMarginTTM', 'priceRelativeToS&P50013Week', 'priceRelativeToS&P50026Week', 'priceRelativeToS&P5004Week', 'priceRelativeToS&P50052Week', 'priceRelativeToS&P500Ytd', 'psAnnual', 'psTTM', 'ptbvAnnual', 'ptbvQuarterly', 'quickRatioAnnual', 'quickRatioQuarterly', 'receivablesTurnoverAnnual', 'receivablesTurnoverTTM', 'revenueEmployeeAnnual', 'revenueEmployeeTTM', 'revenueGrowth3Y', 'revenueGrowth5Y', 'revenueGrowthQuarterlyYoy', 'revenueGrowthTTMYoy', 'revenuePerShareAnnual', 'revenuePerShareTTM', 'revenueShareGrowth5Y', 'roa5Y', 'roaRfy', 'roaTTM', 'roe5Y', 'roeRfy', 'roeTTM', 'roi5Y', 'roiAnnual', 'roiTTM', 'tangibleBookValuePerShareAnnual', 'tangibleBookValuePerShareQuarterly', 'tbvCagr5Y', 'totalDebt/totalEquityAnnual', 'totalDebt/totalEquityQuarterly', 'yearToDatePriceReturnDaily'",
    ] = None,
) -> str:
    """Get latest basic financials for a designated company."""
    basic_financials = finnhub_client.company_basic_financials(symbol, "all")
    if not basic_financials["series"]:
        return f"Failed to find basic financials for symbol {symbol} from finnhub! Try a different symbol."

    output_dict = basic_financials["metric"]
    for metric, value_list in basic_financials["series"]["quarterly"].items():
        value = value_list[0]
        output_dict.update({metric: value["v"]})

    results = {}
    for k in selected_columns:
        if k in output_dict:
            results[k] = output_dict[k]

    return json.dumps(results, indent=2)


def get_current_date():
    return date.today().strftime("%Y-%m-%d")


def combine_prompt(instruction, resource):
    prompt = f"Resource: {resource}\n\nInstruction: {instruction}"
    return prompt


def analyze_balance_sheet(
    symbol: Annotated[str, "ticker symbol"],
    period: Annotated[
        str, "the period of time to get the balance sheets for. Possible values are: annual, quarterly, ttm."
    ],
    limit: int = 10,
) -> str:
    """Retrieve the balance sheet for the given ticker symbol with the related section of its 10-K report.

    Then return with an instruction on how to analyze the balance sheet.
    """

    balance_sheet = financial_datasets_client.run(
        mode="get_balance_sheets",
        ticker=symbol,
        period=period,
        limit=limit,
    )

    df_string = "Balance sheet:\n" + balance_sheet

    instruction = dedent(
        """
        Delve into a detailed scrutiny of the company's balance sheet for the most recent fiscal year, pinpointing
        the structure of assets, liabilities, and shareholders' equity to decode the firm's financial stability and
        operational efficiency. Focus on evaluating the liquidity through current assets versus current liabilities,
        the solvency via long-term debt ratios, and the equity position to gauge long-term investment potential.
        Contrast these metrics with previous years' data to highlight financial trends, improvements, or deteriorations.
        Finalize with a strategic assessment of the company's financial leverage, asset management, and capital structure,
        providing insights into its fiscal health and future prospects in a single paragraph. Less than 130 words.
        """
    )

    prompt = combine_prompt(instruction, df_string)
    return prompt


def analyze_income_stmt(
    symbol: Annotated[str, "ticker symbol"],
    period: Annotated[
        str, "the period of time to get the balance sheets for. Possible values are: annual, quarterly, ttm."
    ],
    limit: int = 10,
) -> str:
    """Retrieve the income statement for the given ticker symbol with the related section of its 10-K report.

    Then return with an instruction on how to analyze the income statement.
    """
    # Retrieve the income statement
    income_stmt = financial_datasets_client.run(
        mode="get_income_statements",
        ticker=symbol,
        period=period,
        limit=limit,
    )
    df_string = "Income statement:\n" + income_stmt

    # Analysis instruction
    instruction = dedent(
        """
        Conduct a comprehensive analysis of the company's income statement for the current fiscal year.
        Start with an overall revenue record, including Year-over-Year or Quarter-over-Quarter comparisons,
        and break down revenue sources to identify primary contributors and trends. Examine the Cost of
        Goods Sold for potential cost control issues. Review profit margins such as gross, operating,
        and net profit margins to evaluate cost efficiency, operational effectiveness, and overall profitability.
        Analyze Earnings Per Share to understand investor perspectives. Compare these metrics with historical
        data and industry or competitor benchmarks to identify growth patterns, profitability trends, and
        operational challenges. The output should be a strategic overview of the company’s financial health
        in a single paragraph, less than 130 words, summarizing the previous analysis into 4-5 key points under
        respective subheadings with specific discussion and strong data support.
        """
    )

    # Combine the instruction, section text, and income statement
    prompt = combine_prompt(instruction, df_string)

    return prompt


def analyze_cash_flow(
    symbol: Annotated[str, "ticker symbol"],
    period: Annotated[
        str, "the period of time to get the balance sheets for. Possible values are: annual, quarterly, ttm."
    ],
    limit: int = 10,
) -> str:
    """Retrieve the cash flow statement for the given ticker symbol with the related section of its 10-K report.

    Then return with an instruction on how to analyze the cash flow statement.
    """

    cash_flow = financial_datasets_client.run(
        mode="get_cash_flow_statements",
        ticker=symbol,
        period=period,
        limit=limit,
    )

    df_string = "Cash flow statement:\n" + cash_flow

    instruction = dedent(
        """
        Dive into a comprehensive evaluation of the company's cash flow for the latest fiscal year, focusing on cash inflows
        and outflows across operating, investing, and financing activities. Examine the operational cash flow to assess the
        core business profitability, scrutinize investing activities for insights into capital expenditures and investments,
        and review financing activities to understand debt, equity movements, and dividend policies. Compare these cash movements
        to prior periods to discern trends, sustainability, and liquidity risks. Conclude with an informed analysis of the company's
        cash management effectiveness, liquidity position, and potential for future growth or financial challenges in a single paragraph.
        Less than 130 words.
        """
    )

    prompt = combine_prompt(instruction, df_string)
    return prompt


def get_share_performance(
    symbol: Annotated[str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"],
    end_date: Annotated[
        str,
        "end date of the search period for the company's basic financials, yyyy-mm-dd",
    ],
) -> str:
    """Plot the stock performance of a company compared to the S&P 500 over the past year."""
    filing_date = datetime.strptime(end_date, "%Y-%m-%d")

    start = (filing_date - timedelta(days=60)).strftime("%Y-%m-%d")
    end = filing_date.strftime("%Y-%m-%d")
    interval = "day"  # possible values are {'second', 'minute', 'day', 'week', 'month', 'year'}
    interval_multiplier = 1  # every 1 day

    # create the URL
    url = (
        f"https://api.financialdatasets.ai/prices/"
        f"?ticker={symbol}"
        f"&interval={interval}"
        f"&interval_multiplier={interval_multiplier}"
        f"&start_date={start}"
        f"&end_date={end}"
    )

    headers = {"X-API-KEY": "your_api_key_here"}

    response = requests.get(url, headers=headers)
    # parse prices from the response

    prices = response.json().get("prices")

    df_string = "Past 60 days Stock prices:\n" + json.dumps(prices)

    instruction = dedent(
        """
        Dive into a comprehensive evaluation of the company's stock price for the latest 60 days.
        Less than 130 words.
        """
    )

    prompt = combine_prompt(instruction, df_string)
    return prompt
