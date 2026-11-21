# NVIDIA NIM 免費模型對照表

每日自動更新的 NVIDIA NIM 模型清單，標註哪些提供**免費託管 API 端點**，哪些僅可**下載自架**。

## 🔗 線上檢視

**GitHub Pages**：https://om0504bot.github.io/nvidia-nim-free-models/

## 📊 模型分層說明

| 層級 | 圖示 | 說明 |
|------|------|------|
| **免費託管端點** | 🟢 | NVIDIA 提供雲端 API，直接呼叫 `https://integrate.api.nvidia.com/v1/chat/completions` |
| **可下載自架** | 🔵 | 需自行部署 NIM 容器到自有 GPU（NGC 容器映像免費下載） |
| **已移除免費端點** | 🔴 | 原有免費端點已下線，僅限企業授權或合作夥伴端點 |

> ⚠️ 所有模型皆可免費原型開發（速率限制約 40 RPM，不計 token 成本）。

## 📁 專案結構

```
.
├── scrape_models.py              # 爬蟲腳本（Python stdlib only）
├── docs/
│   ├── models.json               # 結構化模型資料（給程式用）
│   └── index.html                # GitHub Pages 互動表格（給人看）
├── .github/workflows/
│   └── update-models.yml         # 每日自動更新 GitHub Actions
└── README.md
```

## 🔄 資料來源

- **模型清單**：`https://integrate.api.nvidia.com/v1/models`（公開 API，無需認證）
- **模型目錄**：`https://build.nvidia.com/{model_id}`（詳細規格、部署方式、免費端點徽章）
- **分類依據**：人工維護 `MODEL_CATEGORIES` 對照表（API 缺乏詳細分類欄位）

## 🛠 本地執行

```bash
python scrape_models.py
```

輸出：`docs/models.json`、`docs/index.html`

## 🤖 自動更新

GitHub Actions `.github/workflows/update-models.yml` 每日 UTC 00:00 執行：
1. 呼叫 NVIDIA API 取得最新模型清單
2. 對照 `FREE_ENDPOINT_MODELS` 集合判定免費端點
3. 套用 `MODEL_CATEGORIES` 分類
4. 重新生成 `docs/models.json` 與 `docs/index.html`
5. Commit & Push 觸發 GitHub Pages 重新部署

## 📝 維護指南

### 新增免費端點模型
編輯 `scrape_models.py` 中的 `FREE_ENDPOINT_MODELS` 集合，加入模型 ID（格式：`org/model-name`）。

### 更新分類/能力/模態
編輯 `MODEL_CATEGORIES` 字典，鍵為模型 ID，值包含：
```python
{
    "category": "reasoning|vision-language|embedding|reranking|coding|chat|audio",
    "model_type": "llm|vlm|embedding|rerank|audio",
    "modalities": ["text", "image", "video", "audio"],
    "capabilities": ["tools", "coding", "reasoning", "structured_output", "embedding", "reranking"]
}
```

### 標記已移除免費端點
將模型 ID 加入 `DEPRECATED_FREE_MODELS` 集合。

## 📄 授權

MIT License - 歡迎自由使用、修改、分享。

---

*資料每日自動更新 | 最後更新：見 [models.json](docs/models.json) 中的 `metadata.updated_at`*