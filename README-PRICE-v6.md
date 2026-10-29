# SA Embroidery price display fix v6

The Products API has numeric `price` and `sale_price` but does not consistently provide an explicit currency field. Previously, the backend discarded any positive price when `PRICE_CURRENCY` was unset.

## What changed
- Positive API prices now always appear in chat responses and product cards.
- Sale price is used when `sale=true` and a valid discounted `sale_price` exists.
- Missing or 0 price still requests a quotation, never displays 0 as the price.
- Without an explicitly configured currency, the UI shows `160 (currency not specified)` to avoid false USD/PKR claims.
- Backend and frontend both support setting currency when confirmed.

## After confirming the catalog currency
Set `PRICE_CURRENCY=PKR` (or the correct code) in backend environment, and set `priceCurrency: 'PKR'` in `frontend/Sa-Chat-PRO.html`. Restart FastAPI and hard refresh the page. Do not set a currency until it is confirmed with the website owner; some schema prices conflict with numeric API prices.

## Install
Replace `backend/main.py`, `backend/prompts.py`, `frontend/widget.js`, `frontend/Sa-Chat-PRO.html`. Keep the Groq key in backend environment only.

The script was syntax-checked, but live end-to-end testing was not performed.
