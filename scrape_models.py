#!/usr/bin/env python3
"""
Scrape NVIDIA NIM models from the public API catalog.
Updates docs/models.json and docs/index.html for GitHub Pages.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request

API_MODELS_URL = "https://integrate.api.nvidia.com/v1/models"
CATALOG_BASE = "https://build.nvidia.com"
DOCS_DIR = Path(__file__).parent / "docs"
MODELS_JSON = DOCS_DIR / "models.json"
INDEX_HTML = DOCS_DIR / "index.html"

# Known free endpoint models (from build.nvidia.com "Free Endpoint" badge)
# These have hosted free API endpoints. Others may be downloadable-only.
FREE_ENDPOINT_MODELS = {
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/nemotron-3.5-super-vl-120b-a12b",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "nvidia/nemotron-3.5-bolt-e4b",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "nvidia/nemotron-3.5-embed-1b",
    "nvidia/nemotron-3.5-embed-8b",
    "nvidia/nemotron-3.5-rerank-8b",
    "nvidia/nemotron-3.5-parse",
    "nvidia/nemotron-3.5-content-safety",
    "nvidia/cosmos-reason2-8b",
    "nvidia/riva-translate-4b-instruct-v2",
    "google/gemma-4-31b-it",
    "google/gemma-3-12b-it",
    "meta/muse-glimmer-30b",
    "mistralai/mistral-large-4-1t-a52b",
    "minimaxai/minimax-m3.1-flash",
    "stepfun-ai/step-5-preview",
    "z-ai/glm-5.3-flash",
    "moonshotai/kimi-k3.1-pro",
    "poolside/laguna-xs-2.1",
    "fastino/gliner2-pii",
    "bigcode/starcoder2-15b",
    "snowflake/arctic-embed-l",
}

# Models that are no longer free (moved to paid/enterprise)
DEPRECATED_FREE_MODELS = {
    "deepseek-ai/deepseek-v4.1-flash",
    "deepseek-ai/deepseek-v4-pro-0813",
    "meta/llama-3.2-90b-vision-instruct",
    "nvidia/llama-3.1-nemotron-ultra-253b-v1",
    "nvidia/nemotron-nano-3-30b-a3b",
    "nvidia/nemotron-3-super-120b-a12b",
    "openai/gpt-oss-20b",
    "moonshotai/kimi-k2.6",
    "moonshotai/kimi-k3",
    "meta/llama-4-scout-17b-16e-instruct",
    "deepseek-ai/deepseek-r1",
    "google/diffusiongemma-26b-a4b-it",
    "writer/palmyra-creative-122b",
}

# Comprehensive categorization map: model_id -> {category, model_type, modalities, capabilities}
# This is the authoritative source since API list endpoint lacks detailed fields.
MODEL_CATEGORIES = {
    # NVIDIA Nemotron family
    "nvidia/nemotron-3-ultra-550b-a55b": {"category": "reasoning", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},
    "nvidia/nemotron-3.5-super-vl-120b-a12b": {"category": "vision-language", "model_type": "vlm", "modalities": ["text", "image"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},
    "nvidia/nemotron-3.5-lightning-30b-a3b": {"category": "reasoning", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},
    "nvidia/nemotron-3.5-bolt-e4b": {"category": "reasoning", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": {"category": "vision-language", "model_type": "vlm", "modalities": ["text", "image", "audio"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},
    "nvidia/nemotron-3.5-embed-1b": {"category": "embedding", "model_type": "embedding", "modalities": ["text"], "capabilities": ["embedding"]},
    "nvidia/nemotron-3.5-embed-8b": {"category": "embedding", "model_type": "embedding", "modalities": ["text"], "capabilities": ["embedding"]},
    "nvidia/nemotron-3.5-rerank-8b": {"category": "reranking", "model_type": "rerank", "modalities": ["text"], "capabilities": ["reranking"]},
    "nvidia/nemotron-3.5-parse": {"category": "vision-language", "model_type": "vlm", "modalities": ["text", "image"], "capabilities": ["tools", "coding"]},
    "nvidia/nemotron-3.5-content-safety": {"category": "chat", "model_type": "llm", "modalities": ["text"], "capabilities": []},
    "nvidia/cosmos-reason2-8b": {"category": "vision-language", "model_type": "vlm", "modalities": ["text", "image", "video"], "capabilities": ["tools", "reasoning"]},
    "nvidia/riva-translate-4b-instruct-v2": {"category": "chat", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools"]},
    "nvidia/nemotron-3-embed-1b": {"category": "embedding", "model_type": "embedding", "modalities": ["text"], "capabilities": ["embedding"]},

    # NVIDIA other models
    "nvidia/ai-synthetic-video-detector": {"category": "vision-language", "model_type": "vlm", "modalities": ["text", "video"], "capabilities": []},
    "nvidia/embed-qa-4": {"category": "embedding", "model_type": "embedding", "modalities": ["text"], "capabilities": ["embedding"]},
    "nvidia/ising-calibration-1.5-31b": {"category": "vision-language", "model_type": "vlm", "modalities": ["text", "image"], "capabilities": ["tools", "coding"]},
    "nvidia/llama-3.1-nemoguard-8b-topic-control": {"category": "chat", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools"]},
    "nvidia/llama-3.1-nemotron-safety-guard-8b-v3": {"category": "chat", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools"]},
    "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1": {"category": "embedding", "model_type": "embedding", "modalities": ["text", "image"], "capabilities": ["embedding"]},
    "nvidia/llama-3.2-nv-embedqa-1b-v1": {"category": "embedding", "model_type": "embedding", "modalities": ["text"], "capabilities": ["embedding"]},
    "nvidia/nv-embedqa-mistral-7b-v2": {"category": "embedding", "model_type": "embedding", "modalities": ["text"], "capabilities": ["embedding"]},
    "nvidia/nvclip": {"category": "embedding", "model_type": "embedding", "modalities": ["text", "image"], "capabilities": ["embedding"]},

    # Google
    "google/gemma-4-31b-it": {"category": "reasoning", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},
    "google/gemma-3-12b-it": {"category": "chat", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "structured_output"]},
    "google/gemma-3-4b-it": {"category": "chat", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "structured_output"]},

    # Meta
    "meta/muse-glimmer-30b": {"category": "vision-language", "model_type": "vlm", "modalities": ["text", "image"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},

    # Mistral
    "mistralai/mistral-large-4-1t-a52b": {"category": "chat", "model_type": "llm", "modalities": ["text", "image"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},

    # Minimax
    "minimaxai/minimax-m3.1-flash": {"category": "chat", "model_type": "llm", "modalities": ["text", "image"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},

    # Moonshot
    "moonshotai/kimi-k3.1-pro": {"category": "vision-language", "model_type": "vlm", "modalities": ["text", "image"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},

    # Poolside
    "poolside/laguna-xs-2.1": {"category": "coding", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},

    # StepFun
    "stepfun-ai/step-5-preview": {"category": "vision-language", "model_type": "vlm", "modalities": ["text", "image"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},

    # Z.ai
    "z-ai/glm-5.3-flash": {"category": "chat", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "coding", "reasoning", "structured_output"]},

    # Others
    "bigcode/starcoder2-15b": {"category": "coding", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "coding"]},
    "fastino/gliner2-pii": {"category": "chat", "model_type": "llm", "modalities": ["text"], "capabilities": ["tools", "structured_output"]},
    "snowflake/arctic-embed-l": {"category": "embedding", "model_type": "embedding", "modalities": ["text"], "capabilities": ["embedding"]},
}


def fetch_models():
    """Fetch model list from NVIDIA public API."""
    req = Request(API_MODELS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data.get("data", [])


def categorize_model(model_id, api_data):
    """Determine model category and free status from API data + manual map."""
    is_free_endpoint = model_id in FREE_ENDPOINT_MODELS
    is_deprecated_free = model_id in DEPRECATED_FREE_MODELS

    if is_deprecated_free:
        tier = "deprecated_free"
        status = "已移除免費端點"
    elif is_free_endpoint:
        tier = "free_endpoint"
        status = "免費託管端點"
    else:
        tier = "downloadable"
        status = "可下載自架"

    # Use manual categorization map
    cat_info = MODEL_CATEGORIES.get(model_id, {})
    category = cat_info.get("category", "chat")
    model_type = cat_info.get("model_type", "llm")
    modalities = cat_info.get("modalities", ["text"])
    capabilities = cat_info.get("capabilities", [])

    # Override with API data if available (for models with detailed fields)
    api_model_type = (api_data.get("model_type") or "").lower()
    if api_model_type in ("embedding", "rerank", "vlm", "audio"):
        model_type = api_model_type
        if api_model_type == "embedding":
            category = "embedding"
            modalities = ["text"]
            capabilities = ["embedding"]
        elif api_model_type == "rerank":
            category = "reranking"
            modalities = ["text"]
            capabilities = ["reranking"]
        elif api_model_type == "vlm":
            category = "vision-language"
            modalities = ["text", "image"]
        elif api_model_type == "audio":
            category = "audio"
            modalities = ["text", "audio"]

    api_supports_tools = api_data.get("supports_tools", False)
    api_supports_thinking = api_data.get("supports_thinking", False)
    api_supports_structured = api_data.get("supports_structured_output", False)

    if api_supports_tools and "tools" not in capabilities:
        capabilities.append("tools")
    if api_supports_structured and "structured_output" not in capabilities:
        capabilities.append("structured_output")
    if api_supports_thinking and "reasoning" not in capabilities:
        capabilities.append("reasoning")

    return {
        "tier": tier,
        "status": status,
        "category": category,
        "model_type": model_type,
        "modalities": modalities,
        "capabilities": capabilities,
        "is_free": is_free_endpoint or tier == "downloadable",
    }


def build_model_record(model_id, api_data, meta):
    """Build the enriched model record from API data."""
    owned_by = api_data.get("owned_by", "")
    context_window = api_data.get("context_window")

    # Generate a readable name from model_id
    name = model_id.split("/")[-1].replace("-", " ").title()

    # Description placeholder
    description = f"{name} from {owned_by}"

    record = {
        "id": model_id,
        "name": name,
        "provider": owned_by,
        "tier": meta["tier"],
        "status": meta["status"],
        "category": meta["category"],
        "context_window": context_window,
        "model_type": meta["model_type"],
        "modalities": meta["modalities"],
        "capabilities": meta["capabilities"],
        "description": description,
        "api_endpoint": "https://integrate.api.nvidia.com/v1/chat/completions" if meta["tier"] == "free_endpoint" else None,
        "catalog_url": f"{CATALOG_BASE}/{model_id}",
        "deprecated": "No longer free on hosted endpoint" if meta["tier"] == "deprecated_free" else None,
        "deprecation_date": None,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return record


def load_existing_models():
    """Load existing models.json to preserve deprecation dates."""
    if MODELS_JSON.exists():
        with open(MODELS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {m["id"]: m for m in data.get("models", [])}
    return {}


def save_models(models):
    """Save models to JSON with metadata."""
    output = {
        "metadata": {
            "source": "NVIDIA NIM API Catalog",
            "api_url": API_MODELS_URL,
            "catalog_url": CATALOG_BASE,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_models": len(models),
            "free_endpoint_count": sum(1 for m in models if m["tier"] == "free_endpoint"),
            "downloadable_count": sum(1 for m in models if m["tier"] == "downloadable"),
            "deprecated_count": sum(1 for m in models if m["tier"] == "deprecated_free"),
            "note": "All models free for prototyping (rate limited ~40 RPM). Free Endpoint = hosted API. Downloadable = self-host only.",
        },
        "models": models,
    }
    DOCS_DIR.mkdir(exist_ok=True)
    with open(MODELS_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def generate_html(models):
    """Generate index.html for GitHub Pages."""
    tier_order = {"free_endpoint": 0, "downloadable": 1, "deprecated_free": 2}
    models_sorted = sorted(models, key=lambda m: (tier_order.get(m["tier"], 99), m["provider"], m["name"]))

    categories = sorted(set(m["category"] for m in models))
    providers = sorted(set(m["provider"] for m in models))

    tier_labels = {
        "free_endpoint": "🟢 免費託管端點",
        "downloadable": "🔵 可下載自架",
        "deprecated_free": "🔴 已移除免費端點",
    }

    rows = []
    for m in models_sorted:
        ctx = f"{m['context_window']:,}" if m["context_window"] else "—"
        caps = ", ".join(m["capabilities"]) if m["capabilities"] else "—"
        mod = ", ".join(m["modalities"])
        deprecated_badge = ""
        if m["deprecated"]:
            deprecated_badge = f'<span class="badge deprecated" title="{m["deprecated"]}">{m["deprecation_date"] or "已棄用"}</span>'

        rows.append(f"""
        <tr data-tier="{m['tier']}" data-category="{m['category']}" data-provider="{m['provider']}">
            <td><code>{m['id']}</code></td>
            <td>{m['name']}</td>
            <td>{m['provider']}</td>
            <td><span class="badge {m['tier']}">{tier_labels[m['tier']]}</span> {deprecated_badge}</td>
            <td>{m['category']}</td>
            <td>{ctx}</td>
            <td>{mod}</td>
            <td>{caps}</td>
            <td>{m['description'][:120]}{'…' if len(m['description']) > 120 else ''}</td>
            <td><a href="{m['catalog_url']}" target="_blank">開啟</a></td>
        </tr>""")

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NVIDIA NIM 免費模型對照表</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC", sans-serif; margin: 0; padding: 20px; background: #0d1117; color: #e6edf3; line-height: 1.5; }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #8b949e; margin-bottom: 1.5rem; }}
        .stats {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
        .stat {{ background: #161b22; border: 1px solid #30363d; padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.9rem; }}
        .stat strong {{ color: #76B900; }}
        .filters {{ display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }}
        .filter-btn {{ background: #21262d; border: 1px solid #30363d; color: #e6edf3; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: all 0.15s; }}
        .filter-btn:hover, .filter-btn.active {{ background: #76B900; color: #000; border-color: #76B900; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; }}
        th, td {{ padding: 0.6rem; text-align: left; border-bottom: 1px solid #21262d; vertical-align: top; }}
        th {{ background: #161b22; position: sticky; top: 0; z-index: 1; font-weight: 600; color: #8b949e; }}
        tr:hover td {{ background: #161b22; }}
        code {{ background: #161b22; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.85em; color: #76B900; }}
        .badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.7rem; font-weight: 600; }}
        .badge.free_endpoint {{ background: #1a4d1a; color: #76B900; border: 1px solid #76B900; }}
        .badge.downloadable {{ background: #1a3a4d; color: #58a6ff; border: 1px solid #58a6ff; }}
        .badge.deprecated_free {{ background: #4d1a1a; color: #f85149; border: 1px solid #f85149; }}
        .badge.deprecated {{ background: #4d1a1a; color: #f85149; border: 1px solid #f85149; margin-left: 0.25rem; }}
        a {{ color: #58a6ff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .hidden {{ display: none !important; }}
        .footer {{ margin-top: 2rem; padding: 1rem; background: #161b22; border: 1px solid #30363d; border-radius: 6px; font-size: 0.8rem; color: #8b949e; }}
        .footer a {{ color: #76B900; }}
        @media (max-width: 900px) {{ table {{ display: block; overflow-x: auto; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NVIDIA NIM 免費模型對照表</h1>
        <p class="subtitle">資料來源：<a href="https://integrate.api.nvidia.com/v1/models" target="_blank">NVIDIA NIM Public Models API</a> | 更新時間：{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}</p>

        <div class="stats">
            <div class="stat">總模型數：<strong>{len(models)}</strong></div>
            <div class="stat">免費託管端點：<strong>{sum(1 for m in models if m["tier"] == "free_endpoint")}</strong></div>
            <div class="stat">可下載自架：<strong>{sum(1 for m in models if m["tier"] == "downloadable")}</strong></div>
            <div class="stat">已移除免費端點：<strong>{sum(1 for m in models if m["tier"] == "deprecated_free")}</strong></div>
        </div>

        <div class="filters">
            <button class="filter-btn active" data-filter="all">全部</button>
            <button class="filter-btn" data-filter="free_endpoint">免費託管端點</button>
            <button class="filter-btn" data-filter="downloadable">可下載自架</button>
            <button class="filter-btn" data-filter="deprecated_free">已移除免費端點</button>
            {"".join(f'<button class="filter-btn" data-filter="cat:{c}">{c}</button>' for c in categories)}
            {"".join(f'<button class="filter-btn" data-filter="prov:{p}">{p}</button>' for p in providers)}
        </div>

        <table id="modelsTable">
            <thead>
                <tr>
                    <th>模型 ID</th>
                    <th>名稱</th>
                    <th>提供商</th>
                    <th>層級</th>
                    <th>分類</th>
                    <th>Context Window</th>
                    <th>模態</th>
                    <th>能力</th>
                    <th>描述</th>
                    <th>目錄頁</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>

        <div class="footer">
            <strong>說明：</strong> 所有模型皆可免費原型開發（速率限制約 40 RPM，不計 token）。
            <br>🟢 <strong>免費託管端點</strong>：NVIDIA 提供雲端 API 端點，可直接呼叫 <code>https://integrate.api.nvidia.com/v1/chat/completions</code>
            <br>🔵 <strong>可下載自架</strong>：需自行部署 NIM 容器到自有 GPU
            <br>🔴 <strong>已移除免費端點</strong>：原有免費端點已下線，僅限企業授權或合作夥伴端點
            <br>資料每日自動更新 via GitHub Actions | <a href="https://github.com/om0504bot/nvidia-nim-free-models" target="_blank">原始碼</a> | <a href="models.json" target="_blank">JSON</a>
        </div>
    </div>

    <script>
        const buttons = document.querySelectorAll('.filter-btn');
        const rows = document.querySelectorAll('#modelsTable tbody tr');

        buttons.forEach(btn => {{
            btn.addEventListener('click', () => {{
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const filter = btn.dataset.filter;
                rows.forEach(row => {{
                    if (filter === 'all') {{
                        row.classList.remove('hidden');
                    }} else if (filter.startsWith('cat:')) {{
                        row.classList.toggle('hidden', row.dataset.category !== filter.slice(4));
                    }} else if (filter.startsWith('prov:')) {{
                        row.classList.toggle('hidden', row.dataset.provider !== filter.slice(5));
                    }} else {{
                        row.classList.toggle('hidden', row.dataset.tier !== filter);
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>"""

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    print("Fetching models from NVIDIA API...")
    api_models = fetch_models()
    print(f"Found {len(api_models)} models from API")

    existing = load_existing_models()
    enriched_models = []

    for i, api_data in enumerate(api_models):
        model_id = api_data.get("id", "")
        if not model_id:
            continue

        print(f"  [{i+1}/{len(api_models)}] Processing {model_id}...")

        meta = categorize_model(model_id, api_data)
        record = build_model_record(model_id, api_data, meta)
        enriched_models.append(record)

    # Sort by tier, provider, name
    tier_order = {"free_endpoint": 0, "downloadable": 1, "deprecated_free": 2}
    enriched_models.sort(key=lambda m: (tier_order.get(m["tier"], 99), m["provider"], m["name"]))

    save_models(enriched_models)
    generate_html(enriched_models)

    print(f"\nDone! Saved {len(enriched_models)} models to {MODELS_JSON}")
    print(f"HTML generated at {INDEX_HTML}")


if __name__ == "__main__":
    main()