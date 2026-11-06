# 02 方案

## 2026-11-06 GitHub 学习改进验收（当前版本）

本轮由 GPT-6.1 Sol high 完成两轮分析，Sol medium 实施；Astra 本轮额度失败后用户明确调整模型，不记为 Astra 成功研究。研究来源及固定commit见 PLANNING.md、examples/github-research-sources.json。采用 Ragas 的断言分层、Haystack 的融合去重、RAGFlow 的候选/TopN分离、LlamaIndex 的细粒度来源思想，独立标准库实现。

当前工程测试55/55；真实CLI8/8；真实HTTP39/39（23业务、16协议）；检索压力3个离线排列和1个真实冲突用例通过。准确新证据目录与保护核查见 examples/improvement-summary.json，最近一轮入口 examples/latest-evaluation.json。下文旧测试数及 examples/http、real 路径是保留的历史版本证据，不代表当前协议。

finish v2 的 answer 必须为空；模型选择完整句quote、替代方向或绑定事实ID的算术claims，运行器验证后生成展示答案，阻止自由正文对调城市金额。负对照见 examples/requirements-audit/structured-negative-control.json。read返回源文生成的numeric_facts；Decimal带符号差额及合计，等额不同来源也可计算。旧自由finish仅allow_legacy=True显式工程兼容并标source_only_legacy，真实默认不接受。

search按片段二元组与轻量词频两路RRF排序，候选/每页6项分离；返回总数、has_more、next_offset、ranking及related_candidates。翻页必须携带dataset_digest，越界/摘要变化明确失败，不按日期裁定冲突。压力实验代码 examples/retrieval_stress.py 使用临时14篇资料、随机ID及3排列；原始data不变。

两个真实验收脚本使用共享acceptance_checks.py和run_artifacts.py，写入examples/runs唯一目录；未知/空选择器退出2，manifest记录requested/expanded/executed/skipped，漏执行/重复执行不能成功。中断保留incomplete。业务、协议、离线实验分别计数。

已知边界：extractive完整句防止篡改原文，不证明任意制度适用性；数字提取仅有限句型，不是通用NLI。通用缺口模板尚不能标识混合问题中每项未回答主题。真实模型非确定；这些通过结果不等于普遍准确率。个人贡献/实际用时仍由本人如实填写，Git身份/远程缺失，未提交或推送。


run.py为源码CLI入口，serve.py为loopback HTTP入口。agent.py是有限步调度器，只校验和执行模型动作，不根据业务关键词路由。每轮将固定安全指令、问题、可选历史、当前数据摘要与以前动作/实际观察交给模型，由模型决定下一步。默认CLI8步、HTTP/验收12步，允许1–20；非法动作也消耗一步。

knowledge.py提供中文二元组search（最多6条）与read，read返回原文、稳定片段ID、版本、生效日期、状态、适用范围和替代元数据。每步刷新SHA256，资料改变时清除已读证据，结束前再核验；单进程文件演示不提供并发写事务。历史仅保存问题、回答和摘要，每轮从空证据重新read。

protocol.py拒绝未知动作/字段、错误类型、超限参数。evidence.py校验本轮成功read、当前摘要、ID/版本/片段/连续子串、正文标记。有限启发式要求肯定替代断言有替代引句；显式否认不作肯定断言。数字金额要有引用或可核验的两数差额/合计；按引用中金额实际计算，不执行模型代码，finish观察记录verified_calculations。这些规则不等于普遍语义蕴含证明，语义仍须人工核查。错误返回固定安全代码，模型可纠正。

工具故障不由程序预设重试动作。模型可再读、换检索或停止；若原文读取失败尚未解决，insufficient_evidence不能掩盖未完成，即使读过其他资料也需诚实报告tool_failure。若有效证据已足够回答，仍允许answered。模型服务故障则有限网络重试后停止。状态与结果分离：completed对应本轮结束（含资料不足、冲突），awaiting_user对应澄清，incomplete对应工具失败/上限。

DeepSeek适配：HTTPS POST /chat/completions，system/user消息，JSON输出、非流式、thinking disabled、max_tokens=3000；只取message.content，不记录reasoning_content。默认deepseek-flash，记录指定版本名与服务返回名。30秒超时，429/500/502/503/504默认额外重试一次，401/403不重试，拒绝重定向。不输出服务端错误正文。官方依据：[Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)、[1017发布](https://api-docs.deepseek.com/news/news261017/)。可选OpenAI Responses适配依据[文本生成](https://developers.openai.com/api/docs/guides/text)。

HTTP严格JSON、重复字段拒绝、body32768字节、问题2000字、会话最多100个且每个20轮；不接受客户端路径/端点/密钥。会话更新加锁避免串话，当前串行处理。默认仅loopback、无认证，不能当公网多租户服务。错误返回4xx/503安全JSON。故障注入只在显式测试模式开放，实际决策仍真实模型。

trace记录模式、模型、run_id、UTC时间、数据摘要、输入/历史、动作参数与purpose、观察、耗时、尝试数和终态。不记录内部思维。配置密钥/Bearer/sk形状字符串脱敏；业务文本本身仍需访问控制。
