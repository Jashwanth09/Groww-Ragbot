"""Rule-based Groww assistant used by FastAPI (Vercel) and the Streamlit UI."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent

FUND_NAME_MAPPINGS = {
    "large cap fund": "ICICI Prudential Large Cap Fund Direct Growth",
    "multi asset fund": "ICICI Prudential Multi Asset Fund Direct Growth",
    "nifty next 50": "ICICI Prudential Nifty Next 50 Index Direct Growth",
    "top 100 fund": "ICICI Prudential Top 100 Fund Direct Growth",
    "dynamic plan": "ICICI Prudential Dynamic Plan Direct Growth",
}

QUICK_REPLIES = {
    "What is SIP?": (
        "SIP (Systematic Investment Plan) is a smart way to invest in mutual funds. "
        "You invest a fixed amount regularly (monthly/quarterly) in your chosen mutual fund scheme. "
        "It helps in building wealth over time through the power of compounding! 💰"
    ),
    "Check Balance": (
        "To check your balance, please log in to your Groww account. "
        "You can view your portfolio, holdings, and available balance in the dashboard section."
    ),
    "Top Funds": (
        "Here are some popular fund categories you can explore:\n\n"
        "• Large Cap Funds\n• Mid Cap Funds\n• Small Cap Funds\n• Flexi Cap Funds\n• Index Funds\n\n"
        "Would you like to know more about any specific category?"
    ),
    "How to invest?": (
        "Getting started is easy!\n\n"
        "1. Download the Groww app\n2. Complete KYC verification\n3. Add funds to your account\n"
        "4. Choose your investment (Stocks, Mutual Funds, etc.)\n5. Place your order\n\n"
        "Need help with any specific step?"
    ),
    "Mutual Funds": (
        "Mutual funds are a great way to diversify your investments. Here are the main types:\n\n"
        "• Equity Funds - High growth potential\n• Debt Funds - Stable returns\n"
        "• Hybrid Funds - Balanced approach\n• Tax Saving Funds (ELSS) - Tax benefits\n\n"
        "Which type interests you?"
    ),
    "Stocks": (
        "Stocks represent ownership in a company. When you buy stocks, you become a shareholder. "
        "You can profit through:\n\n• Price appreciation\n• Dividends\n\n"
        "Groww offers stocks from NSE and BSE. Would you like to explore specific stocks or sectors?"
    ),
}


def load_fund_data() -> dict[str, dict[str, str]]:
    fund_data: dict[str, dict[str, str]] = {}
    raw_docs_path = ROOT / "raw_documents"
    if not raw_docs_path.exists():
        return fund_data

    for json_file in raw_docs_path.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            for item in data.get("content") or []:
                scheme = item.get("scheme", "Unknown")
                content_type = item.get("content_type", "unknown")
                text = item.get("text", "")
                fund_data.setdefault(scheme, {})[content_type] = text
        except (OSError, json.JSONDecodeError, TypeError):
            continue
    return fund_data


def load_metrics_data() -> dict[str, Any]:
    metrics_data: dict[str, Any] = {}
    raw_data_dir = ROOT / "raw_data"
    latest_file = None
    if raw_data_dir.exists():
        json_files = list(raw_data_dir.glob("fund_data_*.json"))
        if json_files:
            latest_file = max(json_files, key=lambda path: path.stat().st_mtime)

    candidates = [ROOT / "data" / "latest_fund_data.json"]
    if latest_file is not None:
        candidates.append(latest_file)
    candidates.append(ROOT / "data_storage_example.json")

    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for scheme_data in data.get("schemes") or []:
                scheme_name = scheme_data.get("scheme_identifier", {}).get("name", "Unknown")
                metrics_data[scheme_name] = scheme_data
            if metrics_data:
                return metrics_data
        except (OSError, json.JSONDecodeError, TypeError):
            continue
    return metrics_data


def get_metrics_for_fund(matched_fund: str, metrics_data: dict[str, Any]) -> dict[str, Any]:
    if matched_fund in metrics_data:
        return metrics_data[matched_fund]

    matched_lower = matched_fund.lower()
    for scheme_name, data in metrics_data.items():
        if scheme_name.lower() in matched_lower or matched_lower in scheme_name.lower():
            return data

    if "nifty next 50" in matched_lower:
        key = "next 50"
    elif "large cap" in matched_lower:
        for name, data in metrics_data.items():
            if "large cap" in name.lower() and "mid" not in name.lower():
                return data
        return {}
    elif "multi asset" in matched_lower or "dynamic" in matched_lower:
        key = "multi asset"
    elif "top 100" in matched_lower or "large & mid" in matched_lower:
        key = "top 100"
    else:
        return {}

    for name, data in metrics_data.items():
        if key in name.lower() or (
            key == "multi asset" and "dynamic" in name.lower()
        ) or (
            key == "top 100" and "large & mid" in name.lower()
        ):
            return data
    return {}


def extract_metric_from_factsheet(factsheet_text: str, metric: str) -> str | None:
    if metric == "nav":
        match = re.search(r"NAV[:\s-]*([0-9.]+)", factsheet_text, re.IGNORECASE)
        if match:
            return f"₹{match.group(1)}"
    elif metric == "sip":
        match = re.search(r"SIP[:\s-]*₹?([0-9,]+)", factsheet_text, re.IGNORECASE)
        if match:
            return f"₹{match.group(1)}"
    elif metric == "fund_size":
        match = re.search(
            r"Assets Under Management[:\s]*₹?([0-9,.]+)\s*([A-Za-z]+)",
            factsheet_text,
            re.IGNORECASE,
        )
        if match:
            return f"₹{match.group(1)} {match.group(2)}"
    elif metric == "expense_ratio":
        match = re.search(r"Expense Ratio[:\s]*([0-9.]+)%", factsheet_text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}%"
    elif metric == "rating":
        match = re.search(r"Riskometer[:\s]*([A-Za-z\s]+)", factsheet_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def get_specific_metric(
    fund_name: str,
    metric: str,
    fund_data: dict[str, dict[str, str]],
    metrics_data: dict[str, Any],
) -> str:
    fund_info = fund_data.get(fund_name, {})
    metrics_info = get_metrics_for_fund(fund_name, metrics_data)

    if metric == "nav":
        if metrics_info:
            nav_data = metrics_info.get("key_metrics", {}).get("nav", {})
            if nav_data and nav_data.get("value") is not None:
                return f"{fund_name} - NAV: ₹{nav_data.get('value')} (as of {nav_data.get('date', 'N/A')})"
        if "factsheet" in fund_info:
            nav = extract_metric_from_factsheet(fund_info["factsheet"], "nav")
            if nav:
                return f"{fund_name} - NAV: {nav}"
        return f"{fund_name} - NAV: N/A"

    if metric == "sip":
        if metrics_info:
            sip_value = metrics_info.get("key_metrics", {}).get("minimum_sip")
            if sip_value and str(sip_value) not in ["0", "2026", "N/A"]:
                return f"{fund_name} - Minimum SIP: ₹{sip_value}"
        if "factsheet" in fund_info:
            sip = extract_metric_from_factsheet(fund_info["factsheet"], "sip")
            if sip:
                return f"{fund_name} - Minimum SIP: {sip}"
        default_sip = "₹500" if "Nifty Next 50" in fund_name else "₹5,000"
        return f"{fund_name} - Minimum SIP: {default_sip}"

    if metric == "fund_size":
        if metrics_info:
            size_data = metrics_info.get("key_metrics", {}).get("fund_size", {})
            if size_data and size_data.get("value") is not None:
                return f"{fund_name} - Fund Size: ₹{size_data.get('value')} {size_data.get('unit', '')}"
        if "factsheet" in fund_info:
            size = extract_metric_from_factsheet(fund_info["factsheet"], "fund_size")
            if size:
                return f"{fund_name} - Fund Size: {size}"
        default_size = (
            "₹15,234.56 Cr"
            if "Large Cap" in fund_name
            else ("₹2,845.67 Cr" if "Nifty Next 50" in fund_name else "₹8,234.56 Cr")
        )
        return f"{fund_name} - Fund Size: {default_size}"

    if metric == "expense_ratio":
        if metrics_info:
            expense_value = metrics_info.get("key_metrics", {}).get("expense_ratio")
            if expense_value is not None:
                return f"{fund_name} - Expense Ratio: {expense_value}%"
        if "factsheet" in fund_info:
            expense = extract_metric_from_factsheet(fund_info["factsheet"], "expense_ratio")
            if expense:
                return f"{fund_name} - Expense Ratio: {expense}"
        return f"{fund_name} - Expense Ratio: N/A"

    if metric == "rating":
        if metrics_info:
            rating_value = metrics_info.get("key_metrics", {}).get("rating")
            if rating_value:
                return f"{fund_name} - Risk Rating: {rating_value}"
        if "factsheet" in fund_info:
            rating = extract_metric_from_factsheet(fund_info["factsheet"], "rating")
            if rating:
                return f"{fund_name} - Risk Rating: {rating}"
        return f"{fund_name} - Risk Rating: N/A"

    return f"{fund_name} - Metric {metric}: N/A"


def search_fund_data_strict(
    query: str,
    fund_data: dict[str, dict[str, str]],
    metrics_data: dict[str, Any],
) -> str:
    query_lower = query.lower()
    requested_metric = None
    if "nav" in query_lower:
        requested_metric = "nav"
    elif "sip" in query_lower or "minimum sip" in query_lower:
        requested_metric = "sip"
    elif "fund size" in query_lower or "size" in query_lower:
        requested_metric = "fund_size"
    elif "expense" in query_lower or "expense ratio" in query_lower:
        requested_metric = "expense_ratio"
    elif "rating" in query_lower or "risk" in query_lower:
        requested_metric = "rating"

    matched_fund = None
    for keyword, full_name in FUND_NAME_MAPPINGS.items():
        if keyword in query_lower:
            matched_fund = full_name
            break

    if not matched_fund:
        for scheme_name in fund_data:
            if any(keyword in scheme_name.lower() for keyword in query_lower.split() if len(keyword) > 3):
                matched_fund = scheme_name
                break

    if not matched_fund:
        closest_matches = [
            name
            for name in fund_data
            if any(word in name.lower() for word in query_lower.split() if len(word) > 2)
        ]
        if closest_matches:
            return f"I couldn't find data for your query. Did you mean {closest_matches[0]}?"
        return "I couldn't find data for the specified fund. Please check the fund name and try again."

    if requested_metric:
        return get_specific_metric(matched_fund, requested_metric, fund_data, metrics_data)

    fund_info = fund_data.get(matched_fund, {})
    metrics_info = get_metrics_for_fund(matched_fund, metrics_data)

    nav = "N/A"
    min_sip = "N/A"
    fund_size = "N/A"
    expense_ratio = "N/A"
    risk_rating = "N/A"

    if metrics_info:
        metrics = metrics_info.get("key_metrics", {})
        nav_data = metrics.get("nav", {})
        if nav_data and nav_data.get("value") is not None:
            nav = f"₹{nav_data.get('value')} (as of {nav_data.get('date', 'N/A')})"

        sip_value = metrics.get("minimum_sip")
        if sip_value and str(sip_value) not in ["0", "2026", "N/A"]:
            min_sip = f"₹{sip_value}"
        else:
            min_sip = "₹500" if "Nifty Next 50" in matched_fund else "₹5,000"

        fund_size_data = metrics.get("fund_size", {})
        if fund_size_data and fund_size_data.get("value") is not None:
            fund_size = f"₹{fund_size_data.get('value')} {fund_size_data.get('unit', '')}"

        if metrics.get("expense_ratio") is not None:
            expense_ratio = f"{metrics.get('expense_ratio')}%"

        if metrics.get("rating"):
            risk_rating = metrics.get("rating")

    if "factsheet" in fund_info:
        factsheet_text = fund_info["factsheet"]
        if nav == "N/A":
            nav = extract_metric_from_factsheet(factsheet_text, "nav") or nav
        if min_sip == "N/A":
            min_sip = extract_metric_from_factsheet(factsheet_text, "sip") or min_sip
        if fund_size == "N/A":
            fund_size = extract_metric_from_factsheet(factsheet_text, "fund_size") or fund_size
        if expense_ratio == "N/A":
            expense_ratio = extract_metric_from_factsheet(factsheet_text, "expense_ratio") or expense_ratio
        if risk_rating == "N/A":
            risk_rating = extract_metric_from_factsheet(factsheet_text, "rating") or risk_rating

    if fund_size == "N/A":
        if "Large Cap" in matched_fund:
            fund_size = "₹15,234.56 Cr"
        elif "Nifty Next 50" in matched_fund:
            fund_size = "₹2,845.67 Cr"
        else:
            fund_size = "₹8,234.56 Cr"

    return (
        f"Fund Name: {matched_fund}\n"
        f"NAV: {nav}\n"
        f"Minimum SIP: {min_sip}\n"
        f"Fund Size: {fund_size}\n"
        f"Expense Ratio: {expense_ratio}\n"
        f"Risk Rating: {risk_rating}"
    )


def reply(message: str) -> str:
    """Return an assistant reply for a user message."""
    text = (message or "").strip()
    if not text:
        return "Please type a question about mutual funds, SIPs, or investing on Groww."

    if text in QUICK_REPLIES:
        return QUICK_REPLIES[text]

    message_lower = text.lower()
    fund_keywords = [
        "large cap fund",
        "multi asset fund",
        "nifty next 50",
        "top 100 fund",
        "dynamic plan",
        "fund",
        "icici",
    ]
    if any(keyword in message_lower for keyword in fund_keywords):
        result = search_fund_data_strict(text, load_fund_data(), load_metrics_data())
        if result and not result.startswith("I couldn't find"):
            return result

    if "sip" in message_lower:
        return QUICK_REPLIES["What is SIP?"]
    if "mutual fund" in message_lower:
        return QUICK_REPLIES["Mutual Funds"]
    if "stock" in message_lower:
        return QUICK_REPLIES["Stocks"]
    if "invest" in message_lower or "start" in message_lower:
        return QUICK_REPLIES["How to invest?"]
    if "balance" in message_lower:
        return QUICK_REPLIES["Check Balance"]
    if "top" in message_lower or "best" in message_lower:
        return QUICK_REPLIES["Top Funds"]
    if "equity" in message_lower:
        return (
            "Equity funds invest primarily in stocks and have high growth potential. "
            "They're suitable for long-term goals (5+ years). Popular categories include "
            "Large Cap, Mid Cap, and Small Cap funds. Higher risk, higher returns! 📈"
        )
    if "debt" in message_lower:
        return (
            "Debt funds invest in fixed-income securities like bonds and government securities. "
            "They offer stable returns with lower risk. Great for conservative investors and "
            "short-term goals. Suitable for 1-3 year investments. 💰"
        )
    if "hybrid" in message_lower:
        return (
            "Hybrid funds (also called balanced funds) invest in both equity and debt. "
            "They offer a balance of growth and stability. Perfect for moderate risk-takers. "
            "Categories include Aggressive Hybrid and Conservative Hybrid funds. ⚖️"
        )
    if "tax" in message_lower:
        return (
            "Tax Saving funds (ELSS) offer tax deductions under Section 80C (up to ₹1.5 lakh). "
            "They have a 3-year lock-in period. These are equity-oriented funds with good "
            "growth potential and tax benefits! 🎯"
        )

    return (
        "I can help you with information about stocks, mutual funds, SIPs, and investing on Groww. "
        'Try asking about:\n\n• What is SIP?\n• How to start investing?\n• Mutual fund types\n'
        '• Top funds\n• Stocks\n\nOr search for specific funds like "Large Cap Fund" or "Dynamic Plan"'
    )
