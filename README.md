# 三仙修仙誌刷圖腳本

## Enviornment and configuration
* BlueStacks 5 + ADB 
* Screen resolution of phone: 1280x540
* Python 3.12
* 需要將地圖中選擇關卡的石頭的上半部放在 (1450, 2365)
* 需要手動新增一個 bluestack.conf，內容大致是（之後可能會將更多參數掛在 conf file，請自行研究 codebase)：
```
[automation]
stage = 12
patch_count = 1
iter_count = 90

[level_positions]
9 = 80, 800
10 = 350, 560
11 = 90, 400
12 = 22, 220
```

## Others
* 如果其他道友看到這個 Repo 有想要上手玩玩的，請發 Pull Request，我會寫詳細資訊
