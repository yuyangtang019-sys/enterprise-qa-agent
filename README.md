# 企业知识问答 Agent（题3）

本仓库交付题3企业知识问答 Agent。最终提交 SHA 可用 `git rev-parse HEAD` 获取；文档中“尚未提交”的描述记录了开发时的状态，发布状态以 GitHub 仓库和提交历史为准。候选人个人贡献与实际用时仍须本人如实补充。

## 2026-11-06 GitHub 学习改进验收（当前版本）

本轮由 GPT-6.1 Sol high 完成两轮分析，Sol medium 实施；Astra 本轮额度失败后用户明确调整模型，不记为 Astra 成功研究。研究来源及固定commit见 PLANNING.md、examples/github-research-sources.json。采用 Ragas 的断言分层、Haystack 的融合去重、RAGFlow 的候选/TopN分离、LlamaIndex 的细粒度来源思想，独立标准库实现。

当前工程测试55/55；真实CLI8/8；真实HTTP39/39（23业务、16协议）；检索压力3个离线排列和1个真实冲突用例通过。准确新证据目录与保护核查见 examples/improvement-summary.json，最近一轮入口 examples/latest-evaluation.json。下文旧测试数及 examples/http、real 路径是保留的历史版本证据，不代表当前协议。

finish v2 的 answer 必须为空；模型选择完整句quote、替代方向或绑定事实ID的算术claims，运行器验证后生成展示答案，阻止自由正文对调城市金额。负对照见 examples/requirements-audit/structured-negative-control.json。read返回源文生成的numeric_facts；Decimal带符号差额及合计，等额不同来源也可计算。旧自由finish仅allow_legacy=True显式工程兼容并标source_only_legacy，真实默认不接受。

search按片段二元组与轻量词频两路RRF排序，候选/每页6项分离；返回总数、has_more、next_offset、ranking及related_candidates。翻页必须携带dataset_digest，越界/摘要变化明确失败，不按日期裁定冲突。压力实验代码 examples/retrieval_stress.py 使用临时14篇资料、随机ID及3排列；原始data不变。

两个真实验收脚本使用共享acceptance_checks.py和run_artifacts.py，写入examples/runs唯一目录；未知/空选择器退出2，manifest记录requested/expanded/executed/skipped，漏执行/重复执行不能成功。中断保留incomplete。业务、协议、离线实验分别计数。

已知边界：extractive完整句防止篡改原文，不证明任意制度适用性；数字提取仅有限句型，不是通用NLI。通用缺口模板尚不能标识混合问题中每项未回答主题。真实模型非确定；这些通过结果不等于普遍准确率。个人贡献/实际用时仍由本人如实填写，Git身份/远程缺失，未提交或推送。


企业知识问答 Agent 入口为根目录的 `run.py` / `serve.py`。运行命令均从仓库根目录执行。本机其他项目、本地密钥与虚拟环境不包含在本仓库交付中。


真实模型每轮选择 search/read/ask_user/finish，执行本地资料工具，将实际观察交还模型决定下一步。输出答案、文档ID/版本/原文、资料缺口、任务状态；支持CLI和本地HTTP API。Python 3.10+，只用标准库，无需安装依赖。

```powershell
python configure_deepseek.py
python run.py "上海出差住宿上限？" --trace examples/real-demo.json
python serve.py --port 8765
```

配置脚本在你自己的终端隐藏输入密钥，保存至Git忽略的.env.local，程序只加载允许的三个DeepSeek配置项，不打印密钥；环境变量优先。文件明文留在本机，按需删除。不要将密钥粘贴进聊天。默认真实DeepSeek，无配置报错，绝不自动降级。

用户指定DeepSeek-V4.1-Flash-1017；官方API使用deepseek-flash别名，端点https://api.deepseek.com/chat/completions。实际trace同时记录requested_model、model、response_model；服务返回deepseek-flash，不代表永久锁定权重快照。[官方更新](https://api-docs.deepseek.com/updates/)、[协议](https://api-docs.deepseek.com/api/create-chat-completion/)。保留可选OpenAI Responses适配，使用--provider openai与OPENAI_API_KEY/OPENAI_MODEL。

HTTP默认只监听127.0.0.1。GET /health检查本地进程；POST /ask接收application/json：

```json
{"question":"上海出差住宿限额？","session_id":"employee-a","max_steps":12}
```

也可提供history数组，每项question/answer及可选dataset_digest，与session_id互斥。返回result与完整trace。未知字段、错误JSON/类型、重复字段、越界输入返回4xx；body上限32768字节，问题2000字符，步数1–20。请求不能指定数据文件、端点或凭据。会话最多100个，每个20轮，进程退出即清空；全局锁串行处理，适合本地演示，非生产多租户服务。服务无用户认证，不应暴露公网。健康检查不调用付费模型。

正常服务禁止fault。只有显式--test-mode允许本地文档read故障注入；决策仍由真实DeepSeek作出。工具错误、非法动作或引用都会成为下一轮观察；有限步数耗尽明确incomplete/step_limit。

```powershell
python -m unittest discover -s tests -v
python examples/real_acceptance.py
python examples/http_selftest.py
python examples/http_selftest.py --only cross-city,calculation
```

工程测试43/43通过；真实CLI验收8/8通过；最终完整HTTP自测39/39通过，耗时100.661秒。真实HTTP涵盖正常、新旧替代、跨城/多文档、冲突诱导、资料外/混合、追问与切换主题、会话隔离、伪造历史、忽略引用、暂时/持续工具失败、上限、深圳缺口、历史时点、计算与资料变更，以及HTTP坏请求。每次实际请求、状态码、响应、trace、断言与耗时写入examples/http；定向回归写独立http-regression-*目录且自动建立所需会话前置。最终数量/通过数见examples/delivery-summary.json与各evaluation.json，失败历史保留。

引用须来自本轮成功read，ID/版本/片段/数据摘要一致且quote为原文连续子串，正文标记匹配。补充有限的替代句和数字金额启发式检查；允许来自真实引文金额的两数差额/合计并记录verified_calculations。这些检查不能证明普遍语义蕴含，仍需审阅。历史答案仅用于语境，每轮重新读取；资料变化使旧证据失效。

completed只表示本轮处理结束，可能answered/insufficient_evidence/conflict_unresolved；awaiting_user表示待补充；工具失败及步数上限为incomplete。检索摘要不能作为最终证据，日期新不等于优先。10篇合成制度不能用于真实企业政策决策。

交付目录：src实现；data合成资料；tests工程及本地HTTP协议测试；examples实际证据；docs五份考核文档、变更与修复记录。Mock源码和早期记录只保留为历史工程验证，最终业务验收使用真实DeepSeek，不能以Mock结论替代真实结果。

安全核查见examples/security-check.json。trace不记录内部思维和凭据，但会包含业务问题/原文；需使用者控制访问与保留。Git已初始化；缺少作者身份，提交实际失败，未修改全局身份，无SHA，未推送GitHub。
