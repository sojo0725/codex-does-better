# codex-does-better

> **Codex 都比你強，要你何用？**

一個 Claude Code plugin，讓 Claude 在沒把握時去查證，而不是用「應該是」帶過。包含兩個部分：

| 部分 | 作用 |
|---|---|
| Skill `codex-does-better` | Claude 沒把握、或你質疑它（「你確定嗎」「codex 做的比你好」）時啟動。流程是：先自己查第一手證據，查不出來再問真的 Codex CLI，最後用固定格式回報結論、依據和還不確定的地方。 |
| Stop hook `hedge-stop.py` | Claude 每次回覆結束時檢查內容。出現含糊說法就擋下這次結束，要求它用上面的 skill 查完再重新回答。 |

兩者可以分開用：只裝 skill 時要靠 Claude 自己判斷或你手動呼叫，加上 Stop hook 才會自動攔截。

## 需求

- Claude Code
- `python3`（Stop hook 用，只用標準函式庫）
- [Codex CLI](https://github.com/openai/codex)（選用。沒裝時 skill 會回報「Codex 沒跑成」並照常完成其他步驟）

## 安裝方式一：當 plugin 裝（建議）

在 Claude Code 裡執行：

```
/plugin marketplace add joe888777/codex-does-better
/plugin install codex-does-better@codex-does-better
```

這樣 skill 和 Stop hook 會一起裝好，**不需要自己改 `settings.json`**。裝完後重開 session 就會生效。

## 安裝方式二：手動裝

適合不想用 plugin、或只想要其中一部分的情況。

### 1. 裝 skill

```bash
git clone https://github.com/joe888777/codex-does-better.git
cp -R codex-does-better/skills/codex-does-better ~/.claude/skills/
```

Stop hook 的腳本就在 skill 資料夾裡（`hooks/hedge-stop.py`），所以這一步會一起複製過去。

### 2. 註冊 Stop hook

打開 `~/.claude/settings.json`（只想在單一專案生效就改該專案的 `.claude/settings.json`），在 `hooks.Stop` 陣列裡加一項：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$HOME/.claude/skills/codex-does-better/hooks/hedge-stop.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

如果 `Stop` 裡已經有別的 hook，把上面那個 `{ "hooks": [...] }` 物件加進現有陣列，不要整段覆蓋。

不要同時用兩種方式安裝，否則 Stop hook 會跑兩次。

## 確認 Stop hook 有裝好

1. 在 Claude Code 執行 `/hooks`，`Stop` 底下應該看得到 `hedge-stop.py`。
2. 直接測腳本，餵一段含糊的回覆給它：

   ```bash
   echo '{"last_assistant_message":"版本應該是 3.12"}' \
     | python3 ~/.claude/skills/codex-does-better/hooks/hedge-stop.py
   ```

   有輸出 `{"decision": "block", ...}` 就是正常。換成沒有含糊說法的句子則不會有任何輸出。

   用 plugin 安裝的話，腳本位置在 `~/.claude/plugins/cache/` 底下，用 `/hooks` 確認即可。

## Stop hook 的行為

會觸發的字詞：

- 中文：應該是、可能是、大概是、我不確定、不太確定、我猜、印象中、我記得
- 英文：probably、I think、I believe、not sure、if I recall

不會觸發的情況：

- 單獨的「可能」。它幾乎每則長回覆都會出現（「可能的原因」「不可能」），攔它等於每次都多跑一輪。
- 程式碼區塊、行內程式碼、引號（「」『』“”）和引用區塊（`>`）裡的字詞，這些是在引述，不是 Claude 自己在含糊。
- 已經照 skill 格式回答過的回覆（帶有開頭那句口號）。
- 連續第二次。同一輪只擋一次，不會卡成無限迴圈。

要調整字詞，改 `skills/codex-does-better/hooks/hedge-stop.py` 開頭的 `HEDGES` 清單。

## 使用

- 自動：Claude 回覆含糊時，Stop hook 會把它送回去查。
- 手動：輸入 `/codex-does-better`，或直接說「你確定嗎」「codex 做的比你好」。

最後的回答會是這個格式：

```markdown
> **Codex 都比你強，要你何用？**

**結論：** 一句話。查不出來就寫「不知道」。
**依據：** 跑了什麼、看到什麼。
**Codex：** 沒問／同意／不同意，以及怎麼裁決。
**還不確定：** 剩下哪裡沒確認、要怎麼確認。
```

## 要注意的事

- **會多花 token。** 被攔下的回覆會多跑一輪；真的問到 Codex 時，每次會用掉你 Codex 額度 2 萬多 token。
- **問 Codex 會把資料送到 OpenAI。** 問題本身和 Codex 讀到的檔案都會送出去。Skill 會在涉及密鑰、病患資料這類內容時跳過這步，但你自己也要留意。
- **Codex 只以唯讀模式執行**（`--sandbox read-only`），不會改你的檔案。

## 停用或移除

- Plugin：`/plugin disable codex-does-better@codex-does-better`，或 `/plugin uninstall codex-does-better@codex-does-better`。
- 手動安裝：從 `settings.json` 刪掉那段 Stop hook，再刪除 `~/.claude/skills/codex-does-better`。
- 只想關掉自動攔截、保留 skill：手動安裝時只刪 Stop hook 那段即可。

## 目錄結構

```
.claude-plugin/
  plugin.json          plugin 資訊
  marketplace.json     讓這個 repo 可以直接當 marketplace 加入
hooks/
  hooks.json           plugin 的 Stop hook 註冊
skills/
  codex-does-better/
    SKILL.md           skill 本體
    hooks/
      hedge-stop.py    Stop hook 腳本
```
