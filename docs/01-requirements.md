# 01 需求

## 2026-11-06 GitHub 学习改进验收（当前版本）

本轮由 GPT-6.1 Sol high 完成两轮分析，Sol medium 实施；Astra 本轮额度失败后用户明确调整模型，不记为 Astra 成功研究。研究来源及固定commit见 PLANNING.md、examples/github-research-sources.json。采用 Ragas 的断言分层、Haystack 的融合去重、RAGFlow 的候选/TopN分离、LlamaIndex 的细粒度来源思想，独立标准库实现。

当前工程测试55/55；真实CLI8/8；真实HTTP39/39（23业务、16协议）；检索压力3个离线排列和1个真实冲突用例通过。准确新证据目录与保护核查见 examples/improvement-summary.json，最近一轮入口 examples/latest-evaluation.json。下文旧测试数及 examples/http、real 路径是保留的历史版本证据，不代表当前协议。

finish v2 的 answer 必须为空；模型选择完整句quote、替代方向或绑定事实ID的算术claims，运行器验证后生成展示答案，阻止自由正文对调城市金额。负对照见 examples/requirements-audit/structured-negative-control.json。read返回源文生成的numeric_facts；Decimal带符号差额及合计，等额不同来源也可计算。旧自由finish仅allow_legacy=True显式工程兼容并标source_only_legacy，真实默认不接受。

search按片段二元组与轻量词频两路RRF排序，候选/每页6项分离；返回总数、has_more、next_offset、ranking及related_candidates。翻页必须携带dataset_digest，越界/摘要变化明确失败，不按日期裁定冲突。压力实验代码 examples/retrieval_stress.py 使用临时14篇资料、随机ID及3排列；原始data不变。

两个真实验收脚本使用共享acceptance_checks.py和run_artifacts.py，写入examples/runs唯一目录；未知/空选择器退出2，manifest记录requested/expanded/executed/skipped，漏执行/重复执行不能成功。中断保留incomplete。业务、协议、离线实验分别计数。

已知边界：extractive完整句防止篡改原文，不证明任意制度适用性；数字提取仅有限句型，不是通用NLI。通用缺口模板尚不能标识混合问题中每项未回答主题。真实模型非确定；这些通过结果不等于普遍准确率。个人贡献/实际用时仍由本人如实填写，Git身份/远程缺失，未提交或推送。


帮助员工得到可靠的企业制度答案。输入问题及可选历史，输出引用文档ID、版本日期、原文、资料缺口、task_status/outcome。合成数据10篇，含差旅、报销、年假、采购、安全、设备与知识库范围。

必须实现真实模型选择动作→工具执行→观察→模型调整下一步或结束的循环，不能用固定问题分支充当ReAct。白名单动作search/read/ask_user/finish；支持动态补检索、读原文、澄清、停止。失败与非法引用作为观察交模型纠正；有限上限耗尽明确未完成。

冲突查证范围和优先/替代依据；新日期不是优先的充分条件。住宿新版明确替代旧版，采购两份制度在同范围有效且真正互斥，另有无裁决说明。资料外与混合问题应列缺口，不编造。

六类验收：明确答案、冲突、资料外、改写、上下文追问、工具失败；现已使用真实DeepSeek执行，见examples/real。新增业务HTTP接口和真实请求自测，覆盖复杂场景与严格输入校验，见examples/http。

用户最终指定DeepSeek-V4.1-Flash-1017，密钥由用户在本机配置。Mock仅作历史工程记录；真实业务验收不使用Mock。交付CLI、HTTP、源码、测试、数据、五份文档和实际trace；不包含生产权限系统、向量数据库或公网部署。
