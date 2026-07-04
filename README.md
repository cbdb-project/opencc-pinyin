# opencc-pinyin

通過 [OpenCC](https://github.com/BYVoid/OpenCC) 的匹配機制，將繁體及簡體中文漢字轉換為漢語拼音。

拼音數據來源：[mozillazg/pinyin-data](https://github.com/mozillazg/pinyin-data/blob/master/zdic.txt)（抓取自漢典網 zdic.net），放在 `third_party/pinyin-data/`，並保留其上游授權文件。
詞語拼音數據來源：[mozillazg/phrase-pinyin-data](https://github.com/mozillazg/phrase-pinyin-data)，放在 `third_party/phrase-pinyin-data/`，並保留其上游授權文件；目前僅作為後續多音字短語過濾的原始資料，尚未接入 OpenCC 配置。
多音字會保留 `third_party/pinyin-data/zdic.txt` 原始讀音順序，並寫成 OpenCC 的多值格式（空格分隔）。
例如：`U+548C: hé,hè,huó,huò,hú` 會生成 `和\thé hè huó huò hú`，OpenCC 轉換時默認取第一個讀音。

---

## 文件說明

| 文件 | 說明 |
|------|------|
| `pinyin.json` | OpenCC 轉換配置文件（輸出**帶聲調**拼音） |
| `pinyin_notone.json` | OpenCC 轉換配置文件（輸出**無聲調**拼音） |
| `pinyin.txt` | OpenCC 文本格式字典（每行：`漢字 TAB 拼音`） |
| `tone_removal.txt` | 聲調去除字典（帶調韻母 → 無調韻母，ü 保持不變） |
| `third_party/pinyin-data/zdic.txt` | 原始拼音數據，來自 mozillazg/pinyin-data |
| `third_party/pinyin-data/LICENSE` | 上游 pinyin-data 的 MIT 授權文件 |
| `third_party/phrase-pinyin-data/large_pinyin.txt` | 上游詞語拼音合併產物，來自 mozillazg/phrase-pinyin-data，後續用於多音字短語過濾 |
| `third_party/phrase-pinyin-data/LICENSE` | 上游 phrase-pinyin-data 的 MIT 授權文件 |
| `third_party/OpenCC/CJK_Compatibility_Ideographs.txt` | CJK 兼容表意文字正規化字典，來自 OpenCC |
| `third_party/OpenCC/LICENSE` | 上游 OpenCC 的 Apache License 2.0 授權文件 |
| `gen_dict.py` | 從 `third_party/pinyin-data/zdic.txt` 生成 `pinyin.txt` 的腳本 |

---

## 使用方法

**前提條件**：已安裝 OpenCC CLI 工具，版本 ≥ 1.3.2。

### 基本用法

使用 `-c` 參數指定配置文件的**絕對路徑**或相對路徑：

```sh
# 帶聲調（ā á ǎ à …）
echo "你好世界" | opencc -c /path/to/opencc-pinyin/pinyin.json

# 無聲調（ü 保持不變，不會變成 u）
echo "你好世界" | opencc -c /path/to/opencc-pinyin/pinyin_notone.json

# 從文件讀取，輸出到文件
opencc -c /path/to/opencc-pinyin/pinyin_notone.json -i input.txt -o output.txt
```

### 示例

```
輸入（多音字）：和好世界
帶聲調輸出：    héhǎoshìjiè
無聲調輸出：    hehaoshijie

輸入（單音字）：山川日月
帶聲調輸出：    shānchuānrìyuè
無聲調輸出：    shanchuanriyue

輸入（含 ü）：魚驢旅呂女
帶聲調輸出：  yúlǘlǚlǚnǚ
無聲調輸出：  yulülülünü   （ü ≠ u）

輸入（混合）：山川 English 日月123
無聲調輸出：  shanchuan English riyue123
```

### 注意事項

- 每個漢字的拼音**直接拼接**，字間無空格。非漢字字符（英文、數字、標點等）原樣保留。
- 若需在每個字的拼音之間加空格，可用 `tr` 等工具進行後處理，但需注意這會影響英文詞間空格。
- 本字典為**字符級**（character-level）字典，不進行詞語分詞，僅使用 OpenCC 的最長匹配算法按字逐一查找。

---

## 重新生成字典

若需從最新版 `zdic.txt` 重新生成 `pinyin.txt`：

```sh
# 1. 下載最新的 zdic.txt
mkdir -p third_party/pinyin-data
curl -fsSL https://raw.githubusercontent.com/mozillazg/pinyin-data/master/zdic.txt -o third_party/pinyin-data/zdic.txt

# 2. 下載或更新上游授權文件
curl -fsSL https://raw.githubusercontent.com/mozillazg/pinyin-data/master/LICENSE -o third_party/pinyin-data/LICENSE

# 3. 生成字典
python3 gen_dict.py
```

`gen_dict.py` 腳本接受可選參數：

```sh
python3 gen_dict.py [zdic.txt 路徑] [輸出字典路徑]
```

若需更新詞語拼音原始資料：

```sh
mkdir -p third_party/phrase-pinyin-data
curl -fsSL https://raw.githubusercontent.com/mozillazg/phrase-pinyin-data/master/large_pinyin.txt -o third_party/phrase-pinyin-data/large_pinyin.txt
curl -fsSL https://raw.githubusercontent.com/mozillazg/phrase-pinyin-data/master/LICENSE -o third_party/phrase-pinyin-data/LICENSE
```

---

## 算法說明

本項目利用 OpenCC 的**最長匹配**（Longest Match）字典查找機制，以正規化前處理和字典管道實現帶調或無調拼音輸出：

1. **正規化前處理**（`third_party/OpenCC/CJK_Compatibility_Ideographs.txt`）：先將 CJK 兼容表意文字映射到 UnicodeData 對應的統一表意文字，例如兼容字形會先歸一化，再進入拼音字典查找。
2. **拼音轉換**（`pinyin.txt`）：OpenCC 從左到右掃描輸入文本，將漢字替換為對應拼音（帶聲調）。對於多音字，字典值會保留多個讀音（空格分隔），而 OpenCC 轉換時默認使用第一個讀音。未匹配的字符（英文、數字、標點等）原樣保留。
3. **去聲調轉換**（`tone_removal.txt`，僅 `pinyin_notone.json`）：將帶調韻母替換為無調形式（ā→a、ǎ→a … ǖ/ǘ/ǚ/ǜ→ü）。ü 不會被替換為 u。

字典涵蓋以下 Unicode 範圍：

- CJK 基本：U+4E00–9FFF
- CJK 擴展 A：U+3400–4DBF
- CJK 擴展 B：U+20000–2A6DF
- CJK 擴展 C/D：U+2A700–2B81D
- CJK 兼容擴展：U+2F800–2FA1F
- 以及其他部首、筆畫範圍

共收錄約 42,000 個漢字。
