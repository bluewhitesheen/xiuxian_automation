# 地圖規則

## 概述
這張地圖是一個 13 行 × 7 列的 2D grid。每個格子可能是以下四種之一：

- `.`：空地，可以自由通行
- `P`：玩家所在的格子；每局地圖一開始，玩家固定在 0-indexed 的 `(12, 3)`
- `M`：monster；在打倒之前會被阻擋，無法通行，打倒後會變成 `.`
- `I`：item；可以通行，經過時會拾取寶物，拾取後會變成 `.`

## 戰鬥規則
只有當玩家站在 monster 的相鄰四格時，才可以與 monster 戰鬥：

- 上
- 下
- 左
- 右

斜對角不算相鄰。

## 移動規則
- `.` 和 `I` 都可以通行。
- `M` 在被打倒前不可通行。
- monster 被打倒後，或 item 被拾取後，該格都會變成 `.`。

## 固定地圖模板
目前觀察到遊戲地圖有幾個固定列，可作為路線規劃與分類結果的背景規則：

- 前三列固定為：

```text
.M.M.M.
MIM.MIM
.M...M.
```

- 第 5 row（0-indexed）通常包含固定寶物位置，常見模板為 `...I..I`，但該列也可能出現動態 monster。
- 最後一列固定為 `IM.P..I`，玩家起始位置固定在 `(12, 3)`。
- 因為第 0 row 是固定頂部模板區，目前 route planner 可以不把第 0 row 本身納入 event point 掃描。

## 給 Agent 的備註
- 請把這份文件視為人類可讀的地圖規格來源。
- 在規劃路線或分類地圖格子時，以這份文件為準。
- 請保持這些規則和 route planner、classifier 的實作一致。

## 座標校準說明

BlueStacks 畫面上的 grid 邊界座標是用 adb command 手動 click 測出來的，不是從遊戲 API 取得。

目前校準時使用的畫面解析度是 `1280x540`。

目前每一格是 `60x60` pixel，所以從格子的左上角換算成可點擊位置時，會加上 `+30, +30`，讓 adb tap 落在該格正中央：

```text
cell_center_x = grid_left + col * 60 + 30
cell_center_y = grid_top + row * 60 + 30
```

因此：

- `60` 是單格寬高。
- `30` 是半格偏移，用來點擊格子中心。
- `grid_left` / `grid_top` 是用 adb 實測出來的 grid 起始邊界。

如果 BlueStacks 視窗大小、解析度、DPI、遊戲畫面位置有變，應該重新校準 `grid_left` / `grid_top`，但通常不需要改 `+30`，除非單格大小不再是 `60x60`。

## 檔案讀寫環境設定（避免亂碼）

這份專案在 Windows PowerShell 下維護時，請固定使用 UTF-8 編碼進行檔案 I/O。

### 讀檔

- 使用：`Get-Content -Raw -Encoding UTF8 <path>`
- 建議：避免使用預設 encoding 版本依賴行為。
- 適用檔案：`README.md`、`map_rule.md`、程式碼檔。

### 寫檔

- 使用：`Set-Content -Path <path> -Encoding utf8 -Value <content>`
- 避免：使用會被 OS 預設改成 Unicode 的寫入方式。
- 建議：必要時補 `-NoNewline` 保持原始換行一致性。

### 目前環境

- 專案根目錄：`C:\Users\terry\Desktop\bluestack-automation`
- 權限模式：workspace-write，限制寫在工作目錄下。
- 取得 remote 檔案版本：使用 `git show origin/main:<file>` 再 `Set-Content` 寫回，以避免 `.git/index.lock` 相關問題。
