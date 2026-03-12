# 支付模块

## 覆盖范围

订单创建（`POST /api/payment/create`）+ 支付宝回调（`POST /api/payment/alipay/notify`）+ 状态查询（`GET /api/payment/status/{order_id}`）+ confirm 兼容（`POST /api/payment/confirm`）。

## 测试用例

### 订单创建
| 用例 | 输入 | 预期 |
|------|------|------|
| 缺 token | 无 token | 400 |
| 不存在 token | token=nonexist9 | 404 |
| 非法渠道 | channel=invalid | 400 |
| 微信 H5 暂封 | channel=wechat_h5 | 400 + "审核" |
| 支付宝 H5 | basic + alipay_h5 | 200 + order_id 以 PAY 开头 + amount=19 |
| 高级订阅 | premium + alipay_h5 | 200 + amount=99 |
| 微信扫码 | wechat_native | 200 + channel=wechat_native |
| 订单写入 DB | 创建后查 DB | status=pending |
| 渠道报错不落库 | 支付渠道抛 RuntimeError | 500 且 payments 无新记录 |

### 状态查询
| 用例 | 预期 |
|------|------|
| 不存在的订单 | 404 |
| 待支付订单 | status=pending |

### confirm 兼容
| 用例 | 预期 |
|------|------|
| 用 order_id 查询（未支付）| paid=false |
| 用 token 查询（无订单）| paid=false |
| 用 token + plan_type 查询 | 仅按该 plan_type 判断 paid |
| 不传 order_id 和 token | 400 |

### 支付宝回调
| 用例 | 预期 |
|------|------|
| 验签成功 + TRADE_SUCCESS | DB 更新 status=paid + trade_no |
| 验签失败 | 返回 "fail" |

---

## 集成测试（`@pytest.mark.integration`）

命中真实 HK 服务器 `https://clawschool.teamolab.com`（不触发真实支付渠道）。

### 订单创建
| 用例 | 预期 |
|------|------|
| 缺 token | 400 |
| 非法渠道 | 400 |
| 微信 H5 暂封 | 400 + "审核" |
| 不存在的 token | 本地修复后应拒绝（404）；线上按部署阶段可能 200/500 |

### 状态查询
| 用例 | 预期 |
|------|------|
| 不存在的订单 | 404 |

### confirm 兼容
| 用例 | 预期 |
|------|------|
| 不传 order_id 和 token | 400 |
| 用 token 查询（无订单）| paid=false |
