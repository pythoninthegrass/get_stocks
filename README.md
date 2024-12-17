# get_stocks

## Minimum Requirements

* [python 3.11+](https://www.python.org/downloads/)

## Setup

```bash
git clone https://github.com/pythoninthegrass/get_stocks.git
cd stocks
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Quickstart

```bash
export TICKERS="tsla,ibm,aapl"  # default: aapl
export DROP_DB=true             # default: false
export TTL=5                    # default: 5 (minutes)

λ ./get_stocks.py 
Ticker: tsla   Price:   479.86
Ticker: ibm    Price:   228.97
Ticker: aapl   Price:   253.48
```

## Further Reading

* [PatzEdi/Stockstir: Easily gather stock data of any company in any of your Python projects](https://github.com/PatzEdi/Stockstir)
