# AI 商業開發信產生器（Vue 版，Manifest V3）
**重要：請先把 Vue 3 的 `vue.global.prod.js` 放到本資料夾（覆蓋佔位檔），否則 UI 不會運作。**

## 1) 下載/放置 Vue 3
- 下載 `https://unpkg.com/vue@3/dist/vue.global.prod.js`
- 存成與 `popup.html` 同層的 `vue.global.prod.js`（覆蓋本專案提供的佔位檔）

## 2) 設定後端 URL
- 安裝後在擴充「選項」頁設定後端位址（預設 `http://127.0.0.1:8000`）。

## 3) 載入擴充
- Chrome → `chrome://extensions` → 開「開發人員模式」→ 「載入未封裝項目」→ 選此資料夾。

## 4) 使用
- 啟動你的後端（FastAPI / Java 版皆可）。
- 開啟擴充，貼公司簡介 → 產生英文信。
