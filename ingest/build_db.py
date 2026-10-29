"""SA Embroidery: non-destructive Qdrant catalog index builder.

Usage:
    python build_db.py --source cache
    python build_db.py --source api

Creates a new timestamped collection. Never deletes an existing one.
Uses the SAME embedding model that your retriever must use.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

ROOT = Path(__file__).resolve().parent
API_URL = os.getenv("PRODUCTS_API", "https://sa-embroidery-backend.onrender.com/api/read/Products")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_PREFIX = "sa_embroidery"
SITE = "https://saembroidery.com"


def parse_json(value, default):
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return default
    return default


def clean(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", str(value)))).strip()


def normalize(raw):
    """Accept either your API's raw product records or the v4 normalized cache."""
    if not isinstance(raw, dict) or raw.get("active") is False or raw.get("archive") is True:
        return None
    name = clean(raw.get("product_name") or raw.get("name"))
    if not name:
        return None
    schema = parse_json(raw.get("schema_markup"), {})
    schema_sku = schema.get("sku") if isinstance(schema, dict) else None
    sku = raw.get("sku") or schema_sku
    # Never silently label database record id as a manufacturer's SKU.
    image_urls = []
    for item in parse_json(raw.get("product_images") or raw.get("images"), []):
        url = item.get("edited_url") or item.get("url") if isinstance(item, dict) else item
        if isinstance(url, str) and url.startswith("https://") and url not in image_urls:
            image_urls.append(url)
    if not image_urls and isinstance(raw.get("image_url"), str):
        image_urls.append(raw["image_url"])
    slug = raw.get("url_slug")
    url = raw.get("url") or raw.get("source") or (f"{SITE}/products/{str(slug).strip('/')}" if slug else "")
    return {
        "id": str(raw.get("id") or ""),
        "sku": clean(sku),
        "name": name,
        "category": clean(raw.get("category_name") or raw.get("category") or raw.get("category1")),
        "description": clean(raw.get("description")),
        "short_description": clean(raw.get("short_description")),
        "price": clean(raw.get("price")),
        "stock": clean(raw.get("stock") if "stock" in raw else raw.get("available_stock")),
        "availability": clean(raw.get("availability") or raw.get("stock_status")),
        "compatible": clean(raw.get("compatible")),
        "keywords": clean(raw.get("meta_keywords") or raw.get("keywords")),
        "specifications": clean(raw.get("specifications")),
        "features": clean(raw.get("features")),
        "faqs": parse_json(raw.get("faqs"), []),
        "image_url": image_urls[0] if image_urls else "",
        "url": url,
    }


def load_products(source, cache):
    if source == "api":
        headers = {"Accept": "application/json", "User-Agent": "SAEmbroidery-Indexer/2.0"}
        key = os.getenv("PRODUCTS_API_KEY")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        request = urllib.request.Request(API_URL, headers=headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    else:
        if not cache.exists():
            raise FileNotFoundError(f"No cache at {cache}; use --source api or pass --cache")
        with cache.open(encoding="utf-8") as file:
            payload = json.load(file)
    rows = payload if isinstance(payload, list) else payload.get("data", [])
    if isinstance(rows, dict):
        rows = rows.get("products", rows.get("rows", []))
    if not isinstance(rows, list):
        raise ValueError("Unexpected API/cache data shape; expected product list")
    normalized = [x for row in rows if (x := normalize(row))]
    if not normalized:
        raise ValueError("No valid active products. Existing Qdrant collections remain untouched.")
    return normalized


def to_document(product):
    fields = ("name", "sku", "id", "category", "description", "short_description",
              "compatible", "keywords", "specifications", "features", "price", "stock", "availability")
    lines = [f"{field}: {product[field]}" for field in fields if product.get(field)]
    for faq in product.get("faqs", [])[:8]:
        if isinstance(faq, dict):
            lines.append(f"FAQ: {clean(faq.get('question'))} Answer: {clean(faq.get('answer'))}")
    return Document(page_content="\n".join(lines), metadata={
        "product_id": product["id"], "sku": product["sku"], "name": product["name"],
        "category": product["category"], "image_url": product["image_url"],
        "url": product["url"], "source": product["url"],
    })


def main():
    parser = argparse.ArgumentParser(description="Safely index SA Embroidery products")
    parser.add_argument("--source", choices=["api", "cache"], default="cache")
    parser.add_argument("--cache", type=Path, default=ROOT / "data" / "knowledge_base.json")
    parser.add_argument("--collection", help="Name for NEW collection (must not already exist)")
    args = parser.parse_args()
    products = load_products(args.source, args.cache)
    docs = [to_document(p) for p in products]
    collection = args.collection or f"{COLLECTION_PREFIX}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    client = QdrantClient(url=QDRANT_URL, timeout=60)
    client.get_collections()  # Fail explicitly if Docker/Qdrant isn't running
    if client.collection_exists(collection):
        raise RuntimeError(f"Collection '{collection}' already exists. No collections were changed. Choose another name.")
    print(f"Indexing {len(docs)} products into NEW collection '{collection}' with {EMBEDDING_MODEL}")
    embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    # A new collection is created; existing live index is never deleted.
    store = QdrantVectorStore.from_documents(
        documents=docs,
        embedding=embedder,
        url=QDRANT_URL,
        collection_name=collection,
        batch_size=64,
    )
    count = client.count(collection_name=collection, exact=True).count
    if count != len(docs):
        raise RuntimeError(f"Incomplete index: expected {len(docs)}, Qdrant has {count}. Do not switch retrievers.")
    test = store.similarity_search("Juki tension post sewing machine part", k=1)
    if not test:
        raise RuntimeError("Search smoke test returned no documents. Do not switch retrievers.")
    settings = {"collection_name": collection, "embedding_model": EMBEDDING_MODEL, "products_indexed": count}
    output = ROOT / "qdrant_index_config.json"
    output.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"SUCCESS: {count} products indexed. Search test: {test[0].metadata.get('name')}")
    print(f"Config saved: {output}")
    print(f"Set QDRANT_COLLECTION={collection} in your retrieval backend AFTER testing it.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)