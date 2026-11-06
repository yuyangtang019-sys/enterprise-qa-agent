# 开发交接记录

用户指定流程：GPT-6 Astra（high）总体分析 → GPT-6.1 Sol（high）设计细化 → 同项目新会话 GPT-6.1 Sol（medium）实现、自检、修复和交付。

## Astra high 总体分析（已实际执行）

- 范围：题 3 企业知识问答 Agent，优先 Python CLI，不要求 UI、部署、多 Agent 或向量数据库。
- 分层：本地合成知识库、search/read 工具、模型动作决策、有限步运行器、引用与 trace/评测。
- 每轮模型选择一个 search/read/ask_user/finish 动作；业务决策不能由运行器中的固定条件代替。
- search 摘要不能作为最终引用；引用必须来自成功 read 的证据，校验 document_id、version、fragment_id 和原文子串。引用校验失败作为观察交还模型修正。
- 文档日期更晚不代表优先适用；冲突要读取双方并查证生效信息、适用范围与替代关系，缺证据时保留冲突。
- 分开记录 task_status（completed/awaiting_user/incomplete）及 outcome（answered/insufficient_evidence/conflict_unresolved/tool_failure/step_limit）。
- 工具错误交回模型决定恢复或停止；步数上限返回明确未完成状态。
- 历史上下文保存可核验来源；上一轮回答不能成为新的制度原文。
- 真实模型适配器与离线 Mock 分离；Mock 仅验证工程流程，不能宣称真实模型效果。
- 合成文档约 8–12 篇，稳定文档与片段 ID，版本/日期/状态/适用范围显式建模。轻量中文检索可用二元组和关键词。
- 六类业务验收：明确答案、无优先关系冲突、资料外问题、改写相似问题、上下文追问、工具失败。
- 工程测试覆盖动作结构、工具、引用真实性、错误观察、状态、上下文、上限、trace 完整性。
- 至少三组实际运行输入/输出/trace，覆盖正常、资料不足、工具失败；至少两种观察导致不同后续动作。额外进行文档替换实验。
- trace 保存模式、模型标识、时间、配置、数据哈希、动作、参数、简短行动目的、工具观察及最终结果，不记录内部思维。
- 必须具备 README、src、tests、examples、data、docs/01-requirements.md 到 05-retrospective.md、依赖和 .env.example。
- 如实记录 AI 贡献、真实验证结果；候选人的个人贡献和用时未知时待本人填写。

## 当前环境

- 初始项目目录为空，Python 3.14.6、Git 2.55.0 和 gh 可用。
- 2026-11-04 检查 gh auth status：本机现有 GitHub 凭据失效。不得伪造仓库 URL 或已推送状态。
- 项目路径：D:\\enterprise-qa-agent。

## Sol high 细化设计（已实际执行）

- 严格 JSON 判别联合动作，每个动作带 purpose；search(query)、read(document_id,fragment_id)、ask_user(question,reason)、finish(outcome,answer,citations,gaps)。拒绝未知字段、错误类型。
- Citation 字段 citation_id/document_id/version/fragment_id/quote；正文标记 [C1] 与列表一致；原文必须为已读取片段连续子串。结构校验不等于语义支持度证明。
- 合法 finish 的 answered/insufficient_evidence/conflict_unresolved 对应 completed；ask_user 对应 awaiting_user；tool_failure 对应 incomplete；上限对应 incomplete/step_limit。completed 只表示本轮处理结束，展示时同时给 outcome。
- 默认 max_steps=8，可配置1–20；非法 JSON/动作也耗一步；最后一步是读取则记录后直接未完成，不额外请求模型。超时、429和5xx有限重试，401/403直接报错，记录尝试数。
- 统一观察壳 ok/tool/error(code,message,retryable)，避免将凭据、堆栈、本地路径交模型。资料和工具内容是不可信数据，不能改变动作权限。
- 建议10篇合成制度：旧/新差旅住宿（明确替代）、报销材料、年假、双因素远程访问、采购审批与财务付款真正互斥的同范围有效规则、冲突处理说明、设备领用、知识库范围。缺医疗报销/生育津贴以测试资料外。文档包含 version/effective_date/scope/supersedes/fragments。
- 模块：run.py、src/enterprise_qa/{cli,agent,protocol,knowledge,evidence,session,tracing}.py、models/{base,real,mock}.py；优先标准库和unittest，源码无需联网安装能跑Mock。
- 真实模式默认，缺凭据明确失败，绝不自动降级。Mock 必须 --mode mock 且终端/trace/文档都标注。真实API协议选定后核对官方文档，不宣称支持所有模型。
- CLI 支持单问、交互聊天/持久会话、trace、故障注入。一次故障可恢复，持续故障应如实停止。证据随资料摘要变化失效，要求重读。
- trace 包含 run_id/timestamp/mode/provider/model/dataset_digest/user_input/max_steps/step/action/observation/elapsed_ms/终态；不保存 reasoning 或服务商完整原始响应。
- 六场景：上海住宿、采购审批冲突、资料外生育津贴、上海住宿改写、上海→那北京呢上下文、双因素认证读取失败；至少3组实际执行生成，建议六类全部保留。
- 测试覆盖引用、无效动作参数、故障恢复/持续失败、步数不越界、会话资料变化、工具白名单、真实HTTP协议/超时/认证/重试以及不自动降级。
- 资料扰动实验在复制数据上改限额，检查结果随证据变化，保留数据摘要。
- 无模型凭据：实现真实适配器并实际运行HTTP模拟契约测试；记录真实端到端待验证，Mock不证明模型决策效果。

## 主会话校正（开发必须遵守）

- Sol high 提议的文档文件名与考题不一致，最终必须采用考题原名：01-requirements.md、02-solution.md、03-evaluation.md、04-ai-usage.md、05-retrospective.md；可增加其他文档。
- 不将总体分析中 suggested pytest 视为强制，标准库 unittest 可用。
- 用户要求自主完成开发、自检和修复；不得停在计划或仅搭架子。没有真实API密钥和有效GitHub登录时继续完成所有不依赖这些配置的工作，并准确报告剩余限制。

## GitHub 学习改进轮（2026-11-04 至 2026-11-05）

用户原指定 Astra high → Sol high → 新同目录 Sol medium 实施。Astra 本轮实际因工作区额度失败；用户随后明确授权改为 GPT-6.1 Sol high 完成两轮分析，实施仍使用 Sol medium。不得将本轮研究记为 Astra 成功执行。

第一轮已实际读取四个官方仓库的固定 commit 内容，星数来源见 examples/github-research-sources.json（2026-11-04 查询，非永久值）：

- RAGFlow 93,481 stars：候选池与最终 Top N 分离。来源 https://github.com/infiniflow/ragflow/blob/5b54cb0dad44c7bed82d5d9786dd87c50ba7ba8c/docs/guides/agent/agent_workflow/basic_component.md
- Ragas 16,232 stars：先拆断言，再核对上下文支持；空断言不能当全部通过。来源 https://github.com/vibrantlabsai/ragas/blob/298b68274234c060deacab3cf5fb52aa3a20e885/src/ragas/metrics/_faithfulness.py
- Haystack 26,925 stars：融合、去重后实施 top_k。来源 https://github.com/deepset-ai/haystack/blob/176f738f4517dd254cea9ed4c0a101ff079f4a58/haystack/components/joiners/document_joiner.py
- LlamaIndex 52,801 stars：细粒度编号引用节点。来源 https://github.com/run-llama/llama_index/blob/444fdf0684707de62ebb447d658dba137dd9cb99/llama-index-core/llama_index/core/query_engine/citation_query_engine.py

上述是来源事实；以下是本项目取舍，不表示上游承诺解决本题：保留标准库和真实模型逐轮决策，学习设计而非迁入大型框架，不照抄源码。P0 修复主体/时间/单位/替代与计算方向的引用绑定及负对照评估；P1 改善召回和冲突覆盖，添加候选诊断；P1 评测选择器未知或为空必须失败，每轮独立运行目录，不覆盖旧证据，业务/协议/工程分开计数。

已复现的反例：examples/requirements-audit/semantic-negative-control.json（上海/北京金额对调仍通过）；主会话实际运行 --only __unknown_audit_case__ 退出0。改进前21文件SHA256见 examples/github-improvement-baseline.json。

用户其他目录 permission-assistant/、permission-assistant-submit/ 和所有本地配置必须保留且不修改。不得更改全局Git身份或伪造提交。真实回归继续使用用户已配置的 DeepSeek；不打印密钥，Mock不作为业务验收。

### 第二轮 Sol high 已完成：实施契约

1. finish v2新增claims，answer必须为空，由程序根据验证后的claims渲染最终result.answer。默认真实运行不能接受旧自由答案为已验证结果，返回structured_finish_required让模型修正；显式legacy只标source_only_legacy。更新Mock及测试，不改写旧trace。
2. 普通事实使用quote claim引用完整句/整个短片段，由程序呈现来源标题/版本/日期/范围。不得从否定句截出肯定子串。gaps使用有限代码，模板渲染而非显示未验证业务结论。冲突展示双方原文和固定待确认说明，ask_user保持待确认问题属性。
3. read提取有边界的numeric_facts：fact_id、来源ID/version/fragment/digest、source_quote、subject/attribute/value/unit/basis、scope/effective_date/status。先支持『主体+住宿上限+每晚+数字+元』和『报销期限为N天』，主体从源文捕获，不硬编码城市/ID；未知语法仍可逐字引用。不维护独立答案表。
4. replacement claim绑定source_document_id/target_document_id/citation_id，须由直接原句和supersedes一致支持方向。日期新旧不由程序自动裁决，retired不能推定任意历史适用期。
5. arithmetic claim绑定operation=sum/difference、left_fact_id/right_fact_id/expected_value。Decimal计算；difference是left-right，不取绝对值；据符号渲染高/低/相同。两个facts来源被引用且属性/单位/计量周期/语境兼容。相等金额但不同来源不能按数值去重，合计1200及差额0要支持。未知表达式/复杂中文金额不猜测，不执行模型代码。
6. 检索标准库实现片段级两路排名（二元组+轻量TF-IDF/BM25），RRF融合后去重稳定排序。search保留旧query，并允许offset；每页6条，返回total_candidates/has_more/next_offset、元数据及ranking来源；related_candidates可提示同scope和supersedes关系但不作为read或冲突裁决。分页数据变更有安全反馈。默认模型提示补查而非把第一页当全集。
7. 正反矩阵：城市/历史时点互换、反向替代、截掉否定词、错计量单位/周期、比较方向反转、错误数值、少一操作数均拒绝；合法改写/否认/原文、相等金额、正确方向与合计保留。有限结构化校验不是普遍自然语言蕴含证明，不默认新增收费模型裁判。
8. 临时复制语料加入至少12篇高重叠干扰，固定随机种子改所有ID和引用、至少3种排列，验证冲突双方可由分页/相关关系到达；另跑一个真实模型案例验证会补查。原始data不变。
9. 两个验收脚本抽出共享检查。--only未知、空、空白、含空项在建服务/模型前非零退出；零执行失败。自动展开依赖，记录requested/expanded/executed/skipped；缺执行或异常不能成功。
10. 新记录写examples/runs/<UTC时间>-<随机ID>/，每轮独立manifest/trace/results/summary及配置/摘要，中断明确incomplete；旧examples/http、real及审计全部保留，不覆盖。examples/latest-evaluation.json作为最新入口。业务模型/协议/工程分别计数，预期来自fixture而非固定ID和数字出现。
11. 建议新增claims.py、examples/acceptance_checks.py、examples/run_artifacts.py及对应测试；按测试→v2实现→检索实验→评测隔离→定向真实回归→完整真实回归一次→文档与保护核查顺序。max_steps仍1–20，校验失败耗一步，给具体错误码/claim索引/事实ID。
12. 完成需要实际正反例、既有工程能力、冲突覆盖和真实CLI/HTTP证据；更新README和五份考核文档、AI使用与GitHub学习来源/取舍说明，不虚构个人贡献或提交。
