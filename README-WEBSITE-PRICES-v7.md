# SA Embroidery Chatbot — Website Price Alignment v7

**No website code is changed.** Only chatbot files are included.

Product pricing rule: use `schema_markup.offers.price` **when** its `priceCurrency` is explicitly `USD` (including `@graph` entries); otherwise use the positive API `price`, with active valid `sale_price` preferred. Format as `$0.90`, `$5.50`, etc. If there is no valid price, request a quote instead of inventing one. Product cards and chat use the same rule.

**Important:** This is an evidence-based approximation of website pricing, not verified pixel-for-pixel parity: the live product page and API were inaccessible to the testing environment. The published schema may sometimes be stale or inconsistent with actual visible prices. Conflicts are indicated by `price_conflict` and `price_source` in the normalized backend product record and should be reviewed. If the storefront calculates price differently, update `website_price()` and `websitePrice()` to match that rule.

Installation: Replace `backend/main.py`, `backend/prompts.py`, `frontend/widget.js`, `frontend/Sa-Chat-PRO.html` in the chatbot only; keep GROQ_API_KEY private. Restart uvicorn. Refresh page using Ctrl+Shift+R.

Validation includes Python syntax, JavaScript syntax and synthetic cases; live parity remains unverified.
