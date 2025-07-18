# Query Search

Query Search帮助EC-RAG在进入retrival和reranking阶段之前，对用户query进行预处理，为了使用Query Search，您需要vllm作为后端推理引擎。

## 1. 子问题文件样例

用于保存子问题的文件需要以`.json`结尾，同时需要遵守json文件的格式：主问题作为json键，子问题作为json值，比如：

```json
{
  "问题1": "子问题1.1？子问题1.2？",
  "问题2": "子问题2.1？子问题2.2？子问题2.3？"
}
```

> 请您注意：1. Query Search至少需要一个子问题文件。2. 增加问题数量会增加EC-RAG的整体查询时间。

## 2. 子问题文件位置

所有子问题文件应该放在`${TMPFILE_PATH}/configs/search_dir`路径下。

## 3. 配置文件样例

配置文件里定义了Query Search需要的prompts、temperature等参数：

`instruction`, `input_template`, `output_template`会影响最终进行Query Search的提示词；
`json_key` 和 `json_levels` 两个参数相互关联，比如，如果`json_key`设置为"similarity"，`json_levels`需要列出和其匹配的选项，像"Low, Medium, High"。

对于DeesSeep-R1-Distill-Qwen-32B模型，一个配置样例如下:

```yaml
query_matcher:
  instructions: "Decide similarity of two queries. For exactly the same, mark as High, for totally different, mark as Low.\n"
  input_template: "<query> {} </query>\n<query> {} </query>\n"
  output_template: "output from {json_levels}.\n"
  json_key: "similarity"
  json_levels: ["Low", "Medium", "High"]
  temperature: 3.7
```

## 4. 配置文件位置

配置文件应该放在`${TMPFILE_PATH}/configs`路径下，并且被命名为`search_config.yaml`, 所以完整路径为`${TMPFILE_PATH}/configs/search_config.yaml`。
