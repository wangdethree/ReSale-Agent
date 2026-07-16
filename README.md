# ReSale Agent

ReSale Agent 是一个 AI 二手物品出售助手 Demo。用户上传闲置物品图片并补充少量信息后，系统会完成商品识别、缺失信息追问、本地相似商品检索、规则估价、出售文案生成和模拟议价回复。

V1 支持数码产品、图书、小家电三类商品，V2 已扩展服装和家具类。项目不会登录或操作真实二手平台，也不会承诺估价等于真实成交价。

## 功能范围

- FastAPI 后端接口与 Streamlit 前端演示。
- SQLite 本地模拟商品库，初始化后包含数码、图书、小家电、服装、家具五类模拟数据。
- Agent 状态流转、缺失字段检查和执行轨迹记录。
- 确定性规则估价，文本模型只用于可选文案和议价回复增强。
- 商品标题、描述、关键词、瑕疵说明、拍照建议和 Markdown 报告导出。
- 闲鱼、转转、小红书三类平台风格文案生成，但不执行真实发布。
- 成交反馈记录，可对比最终成交价和系统估价区间。
- 成交复盘汇总，支持按商品类别和成交渠道筛选命中比例与成交偏差。
- 模拟买家议价回复，保证不会主动低于用户最低接受价。
- 图片识别服务支持 OpenAI 兼容多模态接口，并带安全降级：没有模型密钥或模型失败时返回可编辑的结构化初稿。

## 快速启动

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m backend.app.db.init_db
uvicorn backend.app.main:app --reload
```

另开一个终端启动前端：

```bash
source .venv/bin/activate
streamlit run frontend/app.py
```

默认后端地址是 `http://localhost:8000`，前端会读取 `RESALE_AGENT_API_BASE_URL`，未配置时使用 `http://localhost:8000/api/v1`。

## 模型配置

图片识别默认可不配置模型，系统会根据类别和文件名生成可编辑初稿。需要接入真实多模态模型时，在 `.env` 中配置：

```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_VISION_MODEL=gpt-4.1-mini
OPENAI_TEXT_MODEL=gpt-4.1-mini
```

模型返回内容会被结构化校验；如果接口失败或返回结构不合法，图片识别、文案生成和议价回复都会自动回到本地降级模板，不影响后续手动确认和估价流程。

当前 V1 验收记录见 [docs/v1-acceptance.md](docs/v1-acceptance.md)，后续版本规划见 [docs/roadmap.md](docs/roadmap.md)。V1 优先收口稳定演示，不做真实平台发布、支付、物流或复杂权限系统。

## 常用接口

- `GET /health`：健康检查。
- `GET /api/v1/sessions`：查看最近草稿。
- `GET /api/v1/sessions/outcomes/summary`：查看成交反馈汇总，可按 `category`、`sold_channel` 筛选。
- `POST /api/v1/sessions`：创建出售会话。
- `GET /api/v1/sessions/{session_id}`：恢复指定草稿。
- `DELETE /api/v1/sessions/{session_id}`：删除指定草稿。
- `POST /api/v1/sessions/{session_id}/images/analyze`：上传并分析图片。
- `POST /api/v1/sessions/{session_id}/confirm`：确认或修改识别结果。
- `GET /api/v1/sessions/{session_id}/questions/next`：获取下一条追问。
- `POST /api/v1/sessions/{session_id}/answers`：提交补充信息。
- `POST /api/v1/sessions/{session_id}/listing/generate`：生成出售方案。
- `POST /api/v1/sessions/{session_id}/outcome`：记录最终成交反馈。
- `POST /api/v1/sessions/{session_id}/negotiation/reply`：生成模拟议价回复。
- `GET /api/v1/sessions/{session_id}/export`：导出 Markdown 报告。

## 测试

```bash
pytest
```

测试覆盖字段检查、估价规则、相似商品检索、一条完整 API 链路和五个固定演示案例。测试数据库会放在临时目录，不会污染 `data/resale.db`。

也可以直接运行固定商品的演示链路：

```bash
python scripts/run_demo_cases.py
```

该脚本默认使用本地降级链路以保证输出稳定；如需试跑真实模型链路，可先设置 `RESALE_AGENT_DEMO_USE_MODEL=1`。

## 演示建议

1. 选择“数码产品”，上传机械键盘图片。
2. 确认识别结果并补充原价、购买时间、功能状态、维修记录和配件。
3. 生成出售方案，查看相似商品、价格区间和 Markdown 报告。
4. 输入“150 包邮行不行”，观察系统如何识别低价砍价并保护最低接受价。

## 设计原则

核心估价逻辑使用普通 Python 规则实现，便于测试和解释；模型输出必须经过结构化校验，且用户确认后的信息优先级高于模型识别结果。这样可以把 Demo 做成一条稳定、可讲清楚、可扩展的 Agent 工作流。
