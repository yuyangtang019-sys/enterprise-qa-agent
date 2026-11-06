# 05 复盘

## 2026-11-06 GitHub 学习改进验收（当前版本）

本轮由 GPT-6.1 Sol high 完成两轮分析，Sol medium 实施；Astra 本轮额度失败后用户明确调整模型，不记为 Astra 成功研究。研究来源及固定commit见 PLANNING.md、examples/github-research-sources.json。采用 Ragas 的断言分层、Haystack 的融合去重、RAGFlow 的候选/TopN分离、LlamaIndex 的细粒度来源思想，独立标准库实现。

当前工程测试55/55；真实CLI8/8；真实HTTP39/39（23业务、16协议）；检索压力3个离线排列和1个真实冲突用例通过。准确新证据目录与保护核查见 examples/improvement-summary.json，最近一轮入口 examples/latest-evaluation.json。下文旧测试数及 examples/http、real 路径是保留的历史版本证据，不代表当前协议。

finish v2 的 answer 必须为空；模型选择完整句quote、替代方向或绑定事实ID的算术claims，运行器验证后生成展示答案，阻止自由正文对调城市金额。负对照见 examples/requirements-audit/structured-negative-control.json。read返回源文生成的numeric_facts；Decimal带符号差额及合计，等额不同来源也可计算。旧自由finish仅allow_legacy=True显式工程兼容并标source_only_legacy，真实默认不接受。

search按片段二元组与轻量词频两路RRF排序，候选/每页6项分离；返回总数、has_more、next_offset、ranking及related_candidates。翻页必须携带dataset_digest，越界/摘要变化明确失败，不按日期裁定冲突。压力实验代码 examples/retrieval_stress.py 使用临时14篇资料、随机ID及3排列；原始data不变。

两个真实验收脚本使用共享acceptance_checks.py和run_artifacts.py，写入examples/runs唯一目录；未知/空选择器退出2，manifest记录requested/expanded/executed/skipped，漏执行/重复执行不能成功。中断保留incomplete。业务、协议、离线实验分别计数。

已知边界：extractive完整句防止篡改原文，不证明任意制度适用性；数字提取仅有限句型，不是通用NLI。通用缺口模板尚不能标识混合问题中每项未回答主题。真实模型非确定；这些通过结果不等于普遍准确率。个人贡献/实际用时仍由本人如实填写，Git身份/远程缺失，未提交或推送。


真实运行比离线模拟暴露更多细节：模型会补充原文没有的背景常识、引用金额句却顺带断言替代、把工具故障归为资料不足。工程已将观察反馈、状态约束和引用支持检查落实，并以真实业务请求重跑。

测试本身也要审查：提问“如何设置”却期待“必须启用”属于预期不一致；否认历史9999并非采信；引用知识库范围说明不等于伪造津贴金额；回答深圳缺口时合法对比其他城市不等于类推。均阅读实际答案后修正断言，保留失败记录与正反回归，没有用删掉失败场景代替修复。

过强金额检查曾拒绝合法650-600=50和600+650=1250。现只支持明确且实际可计算的两数差额/合计，写入verified_calculations，错误80差额回归拒绝。替代语句检查处理显式否认，但仍是有限启发式。完整语义支持、适用范围和算术语义方向仍需人工审核，不能宣传为已解决普遍蕴含。

最终采用真实DeepSeek CLI验收与完整HTTP复杂场景，工程日志、首轮失败、修复和独立定向回归可复查。HTTP/API严格输入、无客户端路径/凭据、loopback默认、测试故障显式开放，会话有界隔离。

剩余限制：模型服务别名不能锁定具体权重快照；中文二元组召回可能漏文档；安全提示和引用真伪不能保证所有语义或注入抵抗；资料并发写无事务隔离；HTTP无认证且串行，只适合本地演示；trace包含业务文本。应在生产前加入权限、审查、检索评测与保留策略。Git作者身份未配置，未提交/推送；候选人个人贡献待本人填写。
