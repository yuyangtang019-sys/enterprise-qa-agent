# 03 评估

## 2026-11-06 GitHub 学习改进验收（当前版本）

本轮由 GPT-6.1 Sol high 完成两轮分析，Sol medium 实施；Astra 本轮额度失败后用户明确调整模型，不记为 Astra 成功研究。研究来源及固定commit见 PLANNING.md、examples/github-research-sources.json。采用 Ragas 的断言分层、Haystack 的融合去重、RAGFlow 的候选/TopN分离、LlamaIndex 的细粒度来源思想，独立标准库实现。

当前工程测试55/55；真实CLI8/8；真实HTTP39/39（23业务、16协议）；检索压力3个离线排列和1个真实冲突用例通过。准确新证据目录与保护核查见 examples/improvement-summary.json，最近一轮入口 examples/latest-evaluation.json。下文旧测试数及 examples/http、real 路径是保留的历史版本证据，不代表当前协议。

finish v2 的 answer 必须为空；模型选择完整句quote、替代方向或绑定事实ID的算术claims，运行器验证后生成展示答案，阻止自由正文对调城市金额。负对照见 examples/requirements-audit/structured-negative-control.json。read返回源文生成的numeric_facts；Decimal带符号差额及合计，等额不同来源也可计算。旧自由finish仅allow_legacy=True显式工程兼容并标source_only_legacy，真实默认不接受。

search按片段二元组与轻量词频两路RRF排序，候选/每页6项分离；返回总数、has_more、next_offset、ranking及related_candidates。翻页必须携带dataset_digest，越界/摘要变化明确失败，不按日期裁定冲突。压力实验代码 examples/retrieval_stress.py 使用临时14篇资料、随机ID及3排列；原始data不变。

两个真实验收脚本使用共享acceptance_checks.py和run_artifacts.py，写入examples/runs唯一目录；未知/空选择器退出2，manifest记录requested/expanded/executed/skipped，漏执行/重复执行不能成功。中断保留incomplete。业务、协议、离线实验分别计数。

已知边界：extractive完整句防止篡改原文，不证明任意制度适用性；数字提取仅有限句型，不是通用NLI。通用缺口模板尚不能标识混合问题中每项未回答主题。真实模型非确定；这些通过结果不等于普遍准确率。个人贡献/实际用时仍由本人如实填写，Git身份/远程缺失，未提交或推送。


实际命令：python -m unittest discover -s tests -v；python examples/real_acceptance.py；python examples/http_selftest.py。工程测试43/43通过，完整日志examples/test-results.txt。真实CLI8/8通过；最终完整真实HTTP39/39通过，耗时100.661秒。结果与耗时见examples/delivery-summary.json、examples/real/evaluation.json、examples/http/evaluation.json。所有业务动作由真实DeepSeek生成，底层单元/HTTP契约测试使用测试桩，不计为模型效果。

|业务|实际证据|
|---|---|
|明确答案和新旧替代|examples/real/normal.json、examples/http/normal.json|
|同范围冲突及诱导按日期选一个|examples/real/conflict.json、examples/http/conflict-pressure.json|
|资料外/混合|examples/real/outside.json、examples/http/mixed.json|
|改写|examples/real/paraphrase.json、examples/http/paraphrase.json|
|上下文追问/话题切换/隔离|examples/http/followup.json、topic-switch.json、session-isolation.json|
|工具一次/持续故障|examples/real/tool-retry.json、tool-failure.json；examples/http/retry.json、persistent.json|
|澄清后补充/上限|examples/http/clarify.json、clarify-answer.json、limit.json|
|伪造历史/忽略引用指令|examples/http/forged-history.json、ignore-citations.json|
|跨城/综合/计算|examples/http/cross-city.json、synthesis.json、calculation.json|
|未知深圳/历史时点|examples/http/unknown-city.json、historical.json|
|复制数据600变720|examples/real/mutation.json、examples/http/mutation.json|

金额、引用、状态、模型标识及业务断言均检查，不只比较outcome。冲突检查双方read、RESOLUTION优先依据read、双方及说明的引用与缺口。HTTP200必须有result/trace且一致、real模式、DeepSeek提供商、指定模型与服务返回名正确，不能用空对象冒充通过。每个请求保存输入、状态码、完整响应/trace、断言、耗时，坏JSON/类型/未知字段/重复字段/大body/越界/fault禁用均实际请求。错误后健康检查验证服务仍可用。

不同观察产生不同动作：成功read→finish；暂时失败read→重读后finish；持续失败→查找替代资料后tool_failure；无资料→改写search或澄清。路径是实际模型行为，不预设精确序列。模型非确定，不将有限样例通过视为真实普遍准确率。

首轮失败与修复保留在examples/first-run、http-first-run、http-second-run、http-before-arithmetic-fix及独立http-regression-*目录。定向运行不覆盖完整汇总，依赖会话前置自动执行。细节见docs/bugs-and-fixes.md。手工语义抽查发现并修复替代引句、额外金额断言和合法算术被误拒等问题；仍无完备语义证明。

资料扰动只修改临时副本，当前原始data不变；数据摘要改变，旧历史不作为制度原文，答案随read变720。安全检查对实际配置密钥做程序内相等比对，不打印值，结果examples/security-check.json。
