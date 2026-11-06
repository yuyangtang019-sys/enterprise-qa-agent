# 04 AI 使用记录

## 2026-11-06 GitHub 学习改进验收（当前版本）

本轮由 GPT-6.1 Sol high 完成两轮分析，Sol medium 实施；Astra 本轮额度失败后用户明确调整模型，不记为 Astra 成功研究。研究来源及固定commit见 PLANNING.md、examples/github-research-sources.json。采用 Ragas 的断言分层、Haystack 的融合去重、RAGFlow 的候选/TopN分离、LlamaIndex 的细粒度来源思想，独立标准库实现。

当前工程测试55/55；真实CLI8/8；真实HTTP39/39（23业务、16协议）；检索压力3个离线排列和1个真实冲突用例通过。准确新证据目录与保护核查见 examples/improvement-summary.json，最近一轮入口 examples/latest-evaluation.json。下文旧测试数及 examples/http、real 路径是保留的历史版本证据，不代表当前协议。

finish v2 的 answer 必须为空；模型选择完整句quote、替代方向或绑定事实ID的算术claims，运行器验证后生成展示答案，阻止自由正文对调城市金额。负对照见 examples/requirements-audit/structured-negative-control.json。read返回源文生成的numeric_facts；Decimal带符号差额及合计，等额不同来源也可计算。旧自由finish仅allow_legacy=True显式工程兼容并标source_only_legacy，真实默认不接受。

search按片段二元组与轻量词频两路RRF排序，候选/每页6项分离；返回总数、has_more、next_offset、ranking及related_candidates。翻页必须携带dataset_digest，越界/摘要变化明确失败，不按日期裁定冲突。压力实验代码 examples/retrieval_stress.py 使用临时14篇资料、随机ID及3排列；原始data不变。

两个真实验收脚本使用共享acceptance_checks.py和run_artifacts.py，写入examples/runs唯一目录；未知/空选择器退出2，manifest记录requested/expanded/executed/skipped，漏执行/重复执行不能成功。中断保留incomplete。业务、协议、离线实验分别计数。

已知边界：extractive完整句防止篡改原文，不证明任意制度适用性；数字提取仅有限句型，不是通用NLI。通用缺口模板尚不能标识混合问题中每项未回答主题。真实模型非确定；这些通过结果不等于普遍准确率。个人贡献/实际用时仍由本人如实填写，Git身份/远程缺失，未提交或推送。


用户指定依次执行GPT-6 Astra high总体分析 → GPT-6.1 Sol high细化 → 新开同项目GPT-6.1 Sol medium实施、自检、修复和交付。前两阶段交接在PLANNING.md；实施阶段未分派子Agent或创建额外会话。主会话进行只读审核并反馈实际引用/测试缺口。

AI工作包括方案落实、Python CLI/HTTP代码、合成数据、单元和本地HTTP契约测试、真实DeepSeek业务请求测试、引用与状态修复、文档和本地交付。用户后续明确要求不用Mock验收、指定DeepSeek模型并自行配置密钥，实施已据此改为真实模式，实际API模型/返回名deepseek-flash，指定名称DeepSeek-V4.1-Flash-1017记录在trace。

密钥由用户在本机隐藏输入，程序运行时加载；没有在聊天/trace/源码打印或提交。实际配置已用于获授权的真实API测试。旧Mock证据保留作历史工程验证，不作为真实模型结果。

候选人本人贡献、个人用时、人工修改及最终审阅内容：待本人填写。不得由AI工作记录推断个人投入。无Git作者身份，提交失败，未修改全局身份；无远程推送，不提供虚构仓库URL或SHA。
