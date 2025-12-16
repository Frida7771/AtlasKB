# Knowledge Base (知识库)

## 核心依赖

+ [OpenAI](https://platform.openai.com/)
+ [FastAPI](https://fastapi.tiangolo.com/)
+ [Elasticsearch](https://www.elastic.co/elasticsearch/)

### 环境安装

+ [Python](https://www.python.org/) (3.8+)
+ [Docker Desktop](https://www.docker.com/products/docker-desktop/)
+ [pip](https://pip.pypa.io/)

### 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key
```

3. 启动 Elasticsearch（使用 Docker）：
```bash
cd deploy
docker-compose up -d
```

4. 运行项目：
```bash
python main.py
```

5. 访问 API 文档：
- Swagger UI: http://localhost:8000/swagger-ui
- ReDoc: http://localhost:8000/redoc

### 系统模块

- [x] 用户模块
  - [x] 用户登录
  - [x] 密码修改
- [ ] 知识库管理
  - [ ] 知识库列表
  - [ ] 知识库新增、修改、删除
  - [ ] OpenAI 联调
- [ ] Chat模块
  - [ ] 对话列表
  - [ ] Chat列表
  - [ ] 发起对话
- [ ] 超管模块
  - [ ] 系统设置
  - [x] 用户管理
    - [x] 创建用户
    - [x] 用户列表
    - [x] 重置密码
  - [ ] 知识库管理
