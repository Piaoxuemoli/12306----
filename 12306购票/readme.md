### 12306爬虫购票项目 README

## 项目简介

本项目是一个基于Python的12306购票爬虫，通过模拟用户操作实现自动化购票流程。项目包含抓包分析、验证码处理、车站信息解析、订单提交等完整功能模块。

## 核心功能
1. 用户登录与验证码处理
2. 车站信息查询与编码转换
3. 列车信息查询与筛选
4. 订单初始化与乘客信息处理
5. 购票请求提交与排队处理

## 技术栈
- Python 3.x
- requests库 (HTTP请求)
- json (数据解析)
- urllib.parse (URL编码处理)
- datetime (时间参数构造)

## 使用指南

### 1. 环境准备
确保已安装Python 3.x及相关依赖：
```bash
pip install -r requirements.txt
```

### 2. 启动程序

#### 2.1 正常购票模式
```bash
cd 12306购票
python main.py
```

#### 2.2 测试模式（不提交真实订单）
```bash
cd 12306购票
python main.py --test
```
> 测试模式会模拟完整购票流程，但不会提交真实订单，适合功能验证

### 3. 操作流程

#### 3.1 账号登录阶段
```
请输入12306账号：[您的12306账号]
请输入12306密码：[您的12306密码]
```
> 系统会自动下载验证码图片并尝试打开，图片保存路径会显示在控制台
> 如无法自动打开图片，请手动访问提示路径

#### 3.2 行程信息输入阶段
```
请输入出发站：北京西
请输入到达站：上海虹桥
请输入乘车日期(YYYY-MM-DD)：2023-10-01
请输入坐席类型(一等座/二等座/硬座/硬卧)：二等座
```
> 系统会验证日期格式和车站信息有效性

#### 3.3 乘客选择阶段
```
获取乘客信息有：
[0] 张三 (身份证:110********1234)
[1] 李四 (身份证:310********5678)
输入要购票的乘车人的下标：0
```

#### 3.4 订单处理阶段
- 测试模式：仅模拟订单提交流程，显示订单信息后结束
- 正常模式：提交真实订单并监控订单状态

## 技术实现细节

### 1. 核心API接口
- 车票查询接口：`https://kyfw.12306.cn/otn/leftTicket/query`
- 订单提交接口：`https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue`
- 排队查询接口：`https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime`
- 车站信息接口：`https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9076`
- 登录接口：`https://kyfw.12306.cn/otn/login/userLogin`

### 2. 关键代码示例

#### 2.1 车票查询实现
```python
url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=%s&leftTicketDTO.from_station=%s&leftTicketDTO.to_station=%s&purpose_codes=ADULT' % (train_date, from_station_code, to_station_code)
response = self.s.get(url)
```

#### 2.2 乘客信息处理
```python
passenger_list = parsePassenger(json.loads(response.content))
print('获取乘客信息有：')
pprint(passenger_list)
passenger_info_dict = passenger_list[int(input('输入要购票的乘车人的下标'))]
```

## 项目结构
```
12306购票/
├── __pycache__/
│   └── funk12306.cpython-311.pyc
├── funk12306.py          # 核心功能实现
├── main.py               # 程序入口
├── readme.md             # 项目文档
├── requirements.txt      # 依赖库列表
└── 流程介绍.md           # 操作流程说明
```

## 异常处理
1. **登录失败**：检查账号密码或验证码是否正确
2. **无可用车次**：尝试修改查询条件或日期
3. **订单提交失败**：通常是余票不足或网络问题，建议重试

## 注意事项
1. 本项目仅供学习参考，请勿用于商业用途
2. 12306网站有反爬机制，使用时需注意请求频率
3. 部分接口可能随网站更新而变化，需要定期维护
4. 验证码处理可能需要手动干预
        