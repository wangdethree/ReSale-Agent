# V1 验收记录

更新时间：2026-07-16

## 验收结论

V1 已经达到可演示状态，可以围绕“三类商品、本地模拟数据、用户确认优先、规则估价、可选模型增强”的边界继续收口。后续开发应优先进入 V2 规划，不再把 V1 扩展成真实平台代发、支付、物流或复杂账号权限系统。

## 已验证范围

- 后端基础接口：健康检查、会话创建、图片分析降级、识别确认、缺失信息追问、补充答案、出售方案生成、模拟议价回复、Markdown 导出。
- 核心 Agent 流程：状态流转、执行轨迹记录、字段缺失检查、相似商品检索、规则估价、底价保护。
- 三类固定演示案例：数码产品、图书、小家电均可跑完整本地链路。
- 前端首屏：`streamlit run frontend/app.py` 可打开 ReSale Agent V1 Demo，展示步骤导航、商品类别、图片上传、开始识别和本地模拟数据说明。

## 本轮发现与修复

- 问题：直接运行 `streamlit run frontend/app.py` 时，页面显示 `ModuleNotFoundError: No module named 'frontend'`。
- 原因：Streamlit 直跑脚本时优先把 `frontend/` 作为导入起点，项目根目录没有稳定进入 `sys.path`。
- 处理：前端入口启动时补入项目根目录，保持 `frontend.*` 包导入方式不变。

## 验收命令

```bash
pytest
python scripts/run_demo_cases.py
uvicorn backend.app.main:app --host 127.0.0.1 --port 8004
RESALE_AGENT_API_BASE_URL=http://127.0.0.1:8004/api/v1 streamlit run frontend/app.py --server.address=127.0.0.1 --server.port=8504
```

## V2 建议

- 做轻量商品草稿管理：保存历史会话、重新打开草稿、删除草稿。
- 加强价格解释：展示相似商品命中依据、成色折扣和议价空间。
- 增强图片识别：支持真实多模态模型配置验证、失败原因可视化和用户可编辑字段对比。
- 保持不接入真实平台交易动作，先把“生成可发布内容”和“议价辅助”做扎实。
