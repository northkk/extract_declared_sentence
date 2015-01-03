extract declared sentence
=========================
抽取宣告刑。

**usage example:** `python3 extract_declared_sentence.py <directory or file path>`

**output example:**
```
[
   "file name", 
   {
      "accused": [
         [
            "charge", 
            "sentence"
         ],
         ...
      ]
      ...
   }
   ...
]
```         

Log file is generated locally.

Description
---
抽取表格的cell內的句子,用regular expression抓取判刑pattern。

統計：
```
{'accused_extraction_fail': 4,
 'doc': 991,
 'output': 75,
 'table': 2146,
 'table_format_exception': 164,
 'table_processing_fail': 166}
```

75個doc有結果。
2146個table裡有166個table無法處理 .(紀錄在LOG)

Known Issue
---

- 多人被告pattern。
see doc of function `extract_accused_names`
- 表格內有表格的無法處理。
see doc of function `parse`
- 判刑pattern的recall rate不明