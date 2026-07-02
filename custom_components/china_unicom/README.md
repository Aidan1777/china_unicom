# 中国联通话费查询 - Home Assistant 集成

通过联通小程序 OpenID 自动获取话费余额、流量、通话时长、短信用量等数据。单实体承载所有信息，支持多号码。

---

## 原项目

本项目基于 [aNdria19/unicom_ha_integration](https://github.com/aNdria19/unicom_ha_integration) 二次开发。

## 与原项目差异

| 类别 | 原项目 | 本修改版 |
|------|--------|----------|
| **语言** | 纯英文 | 全中文化（界面文案、实体名、设备信息） |
| **实体设计** | 多实体拆分 | 单实体 `sensor.*`，所有数据放入 `extra_state_attributes`，仪表盘引用更简洁 |
| **多实例** | 不支持 | 通过 `entry_id` 隔离，可同时接入多个联通号码 |
| **认证流程** | 基础 ticket | 自动获取 ticket → Cookie（microHallUser / microHallAccessToken）→ 业务 API 完整鉴权链 |
| **数据维度** | 余额 | 余额 + 可用余额 + 实时话费 + 欠费 + 信用额度 + 通话 + 短信 + 流量包列表 |
| **并发控制** | 无 | 实例级 `_auth_lock` + `_api_lock` + 全局 `_class_lock` 防并发冲突 |
| **数据刷新** | 轮询 | `DataUpdateCoordinator` 模式，可配置 1–60 分钟刷新间隔，默认 15 分钟 |
| **设备注册** | 无 | 自动注册 HA 设备（manufacturer: 中国联通），可在「设备」面板查看 |
| **UI 配置** | YAML | Config Flow 图形化添加，搜索即得 |
| **翻译** | 仅英文 strings | `strings.json` + `translations/zh-Hans.json` 双语支持 |
| **错误处理** | 简单 | 异常分类日志、认证失败自动重试、会话生命周期管理 |

---

## 前置条件

- Home Assistant（2024.x 及以上）
- 中国联通手机号
- 微信「中国联通」小程序的 OpenID

## 获取 OpenID

1. 微信打开「中国联通」小程序
2. 登录后进入「我的」→「设置」
3. 在设置页面中查找 OpenID（也可通过抓包小程序网络请求获取）

## 安装

### 方式一：HACS（推荐，支持自动更新）

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

1. 在 HACS 中点击右上角 ⋮ → **自定义存储库**
2. 填入仓库地址：`https://github.com/Aidan1777/china_unicom`
3. 类别选择 **集成**
4. 点击添加，然后在 HACS 中搜索 **中国联通话费查询** 下载安装
5. 重启 Home Assistant

安装后可在 HACS 中收到更新通知，一键升级。

### 方式二：手动安装

将 `custom_components/china_unicom/` 整个文件夹复制到 HA 的 `custom_components/` 目录下，重启 Home Assistant：

```
custom_components/
└── china_unicom/
    ├── __init__.py
    ├── api.py
    ├── config_flow.py
    ├── const.py
    ├── coordinator.py
    ├── hacs.json
    ├── icons.json
    ├── manifest.json
    ├── sensor.py
    ├── strings.json
    ├── translations/
    │   └── zh-Hans.json
    └── README.md
```

## 配置

1. **配置** → **集成** → **添加集成**
2. 搜索 **China Unicom** 或 **中国联通**
3. 填写：

| 字段 | 必填 | 说明 |
|------|:--:|------|
| OpenID | ✅ | 联通小程序 OpenID |
| 手机号 | ❌ | 用于友好显示，如 `133****3691` |
| 刷新间隔 | ❌ | 1–60 分钟，默认 15 分钟 |

## 实体

添加后生成实体 `sensor.zhong_guo_lian_tong_{openid前3}_{openid后4}`。

### State（主数值）

账户余额（单位：元）。

### Attributes（扩展属性）

| 属性 | 类型 | 说明 |
|------|------|------|
| `openid` | string | 小程序 OpenID |
| `balance` | string | 账户余额 |
| `available_balance` | string | 可用余额 |
| `real_time_fee` | string | 实时话费 |
| `total_owed` | string | 欠费金额 |
| `credit_limit` | string | 信用额度 |
| `voice_usage` | string | 通话已用（分钟） |
| `voice_total` | string | 通话总量（分钟） |
| `voice_balance` | string | 通话剩余（分钟） |
| `voice_percent` | string | 通话使用率（%） |
| `sms_usage` | string | 短信已用（条） |
| `sms_total` | string | 短信总量（条） |
| `sms_balance` | string | 短信剩余（条） |
| `sms_percent` | string | 短信使用率（%） |
| `data_items` | list | 流量包列表 |

### 流量包 (data_items) 结构

```json
[
  {
    "addUpItemName": "套餐内通用流量",
    "use": "1024",
    "total": "2048",
    "remain": "1024",
    "usedPercent": "50.0",
    "flowType": "1"
  }
]
```

**flowType 说明：**

| 值 | 含义 |
|:--:|------|
| `1` | 通用流量 |
| `2` | 专属 / App 流量 |
| `3` | 区域 / 公免流量 |

## 模板示例

```yaml
# 余额
话费余额: {{ states('sensor.zhong_guo_lian_tong_abc_7890') }} 元

# 通话
通话已用: {{ state_attr('sensor.zhong_guo_lian_tong_abc_7890', 'voice_usage') }} 分钟
通话剩余: {{ state_attr('sensor.zhong_guo_lian_tong_abc_7890', 'voice_balance') }} 分钟

# 短信
短信已用: {{ state_attr('sensor.zhong_guo_lian_tong_abc_7890', 'sms_usage') }} 条

# 流量（遍历所有流量包）
{% for item in state_attr('sensor.zhong_guo_lian_tong_abc_7890', 'data_items') %}
  {{ item.addUpItemName }}: {{ item.use }} / {{ item.total }} MB（已用 {{ item.usedPercent }}%）
{% endfor %}
```

## API 接口

| 接口 | 用途 |
|------|------|
| `mina.10010.com/wxapplet/weixinNew/getTicket` | 获取认证票据 |
| `mxx.client.10010.com/servicebusiness/wx/serviceEntrance` | 换取 Cookie（microHallUser / microHallAccessToken） |
| `mina.10010.com/wxapplet/weixinNew/sspbigball` | 概览数据 |
| `mxx.client.10010.com/.../accountBalancenew.htm` | 账户余额 |
| `mxx.client.10010.com/.../queryOcsPackageFlowLeftContentRevisedInJune` | 流量 / 语音 / 短信 |
| `mina.10010.com/wxapplet/weixinNew/queryGoodsList` | 获取完整手机号 |

## 鉴权流程

```
1. POST /getTicket   → ticket
2. GET  /serviceEntrance?ticket=xxx
   └─ 从 Set-Cookie 提取 microHallUser + microHallAccessToken
3. 携带 Cookie + ticket 调用余额 / 用量 API
4. coordinator 按配置间隔自动刷新，每次刷新重新走 1–3 流程
```

每次数据刷新都会重新鉴权，不需要持久化 token。

## 常见问题

**Q: 需要短信验证码吗？**
不需要，通过 OpenID + ticket 自动鉴权。

**Q: 数据安全吗？**
所有请求走 HTTPS，凭证仅存于 HA 配置中。

**Q: 多久刷新一次合适？**
建议 15–30 分钟。联通接口对高频请求有限流，太短可能返回空数据。

**Q: 可以添加多个号码吗？**
可以，重复「添加集成」步骤即可，每个号码使用独立 OpenID，互不干扰。

**Q: 实体状态显示 "未知" 怎么办？**
首次添加后稍等片刻等待首次拉取。若持续未知，检查 HA 日志中 `china_unicom` 相关错误，常见原因为 OpenID 过期或网络不通。

## 文件结构

| 文件 | 说明 |
|------|------|
| `__init__.py` | 集成入口，负责 entry 的 setup / unload / cleanup |
| `config_flow.py` | 图形化添加集成界面 |
| `const.py` | 常量定义（API 端点、配置键、默认值） |
| `coordinator.py` | DataUpdateCoordinator 定时拉取数据 |
| `api.py` | 封装联通 6 个 API 的客户端（鉴权 + 数据拉取） |
| `sensor.py` | 单实体传感器，暴露 state + extra_state_attributes |
| `manifest.json` | HA 集成清单（含版本号） |
| `hacs.json` | HACS 商店元数据，用于远程更新 |
| `strings.json` | 英文界面文案 |
| `translations/zh-Hans.json` | 简体中文界面文案 |
| `icons.json` | 图标定义 |

## License

MIT
