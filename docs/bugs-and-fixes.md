# 实际发现、修复与回归

## 2026-11-06 GitHub 学习改进验收（当前版本）

本轮由 GPT-6.1 Sol high 完成两轮分析，Sol medium 实施；Astra 本轮额度失败后用户明确调整模型，不记为 Astra 成功研究。研究来源及固定commit见 PLANNING.md、examples/github-research-sources.json。采用 Ragas 的断言分层、Haystack 的融合去重、RAGFlow 的候选/TopN分离、LlamaIndex 的细粒度来源思想，独立标准库实现。

当前工程测试55/55；真实CLI8/8；真实HTTP39/39（23业务、16协议）；检索压力3个离线排列和1个真实冲突用例通过。准确新证据目录与保护核查见 examples/improvement-summary.json，最近一轮入口 examples/latest-evaluation.json。下文旧测试数及 examples/http、real 路径是保留的历史版本证据，不代表当前协议。

finish v2 的 answer 必须为空；模型选择完整句quote、替代方向或绑定事实ID的算术claims，运行器验证后生成展示答案，阻止自由正文对调城市金额。负对照见 examples/requirements-audit/structured-negative-control.json。read返回源文生成的numeric_facts；Decimal带符号差额及合计，等额不同来源也可计算。旧自由finish仅allow_legacy=True显式工程兼容并标source_only_legacy，真实默认不接受。

search按片段二元组与轻量词频两路RRF排序，候选/每页6项分离；返回总数、has_more、next_offset、ranking及related_candidates。翻页必须携带dataset_digest，越界/摘要变化明确失败，不按日期裁定冲突。压力实验代码 examples/retrieval_stress.py 使用临时14篇资料、随机ID及3排列；原始data不变。

两个真实验收脚本使用共享acceptance_checks.py和run_artifacts.py，写入examples/runs唯一目录；未知/空选择器退出2，manifest记录requested/expanded/executed/skipped，漏执行/重复执行不能成功。中断保留incomplete。业务、协议、离线实验分别计数。

已知边界：extractive完整句防止篡改原文，不证明任意制度适用性；数字提取仅有限句型，不是通用NLI。通用缺口模板尚不能标识混合问题中每项未回答主题。真实模型非确定；这些通过结果不等于普遍准确率。个人贡献/实际用时仍由本人如实填写，Git身份/远程缺失，未提交或推送。


|问题/触发|根因与修复|证据|
|---|---|---|
|首轮双因素“如何设置”预期answered失败|原文只有启用要求，没有操作步骤；问题改为资料确有内容的“是否必须/遗失找谁”，缺配置步骤仍应不足|examples/first-run/tool-retry.json与examples/real/tool-retry.json|
|持续read失败却completed|模型归为insufficient_evidence；加入原文失败未解决时的状态反馈，不因无关read就掩盖；足够证据answered仍允许|first-run/tool-failure.json、tests/test_api.py、examples/http/persistent.json|
|替代断言只引用金额句|子串真伪不保证引句支持额外断言；提示聚焦断言，有限替代引句校验、否认例外及回归|tests/test_agent.py、examples/http/normal.json、synthesis.json|
|历史时点答案额外提600却不引其原文|加入有限数字金额支持检查；未支持金额反馈模型补引句/删多余事实|http-regression-*中的historical.json、tests/test_agent.py|
|合法50差额被误拒，模型反复finish耗尽|过强“金额都逐字出现”规则；按真实引文操作数核验两数差额和合计，trace记录计算；错误80回归拒绝|examples/http-before-arithmetic-fix/cross-city.json、最终calculation.json及tests/test_agent.py|
|9999、其他城市和范围引句被测试误判|否认不等于采用、引用SCOPE不等于编造、深圳缺口附带其他城市原文不等于类推；审阅原答并加入更准确正反断言|http-first-run/forged-history.json、http-second-run、http-regression-*、tests/test_api.py|
|HTTP200空对象可误报通过|强制业务result/trace完整、一致、real模式及模型元数据|tests/test_api.py与http_selftest.response_checks|
|定向追问缺前置、覆盖完整汇总风险|自动建立session-a/clarify前置，定向结果写独立时间戳目录|examples/http_selftest.py、http-regression-*|
|HTTP错误连接未释放/Windows超时断连噪声|显式关闭HTTPError与处理预期断连；认证不重试，保留安全类型|tests/test_http.py、test-results.txt|

这些是有目的的有限测试、反馈、修复与回归，不是无监督修改生产策略的“自我进化”系统。最终完整结果保留成功与失败历史，不能以最后一次成功覆盖而隐瞒已知限制。
