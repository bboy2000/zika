# zika 字卡小程序 · DESIGN.md

> 版本：v1.00
> 日期：2026-10-20
> 适用范围：微信小程序（手机 375-430px / 平板 iPad 10.2" 810-1080px）
> 配套：zika小程序开发方案_v1.05.md

---

## 1. Visual Theme & Atmosphere

### 1.1 设计哲学：纸上识字

把"写字本"的实感搬进屏幕。孩子打开不是进入一个"软件"，而是翻开一本**自己的写字本**——米宣纸的底色、朱砂的印记、墨黑的字。所有视觉元素都从这三个东西长出来，不引入任何与"书写"无关的装饰。

克制在两头之间：**不能严肃死板**（孩子不点开），**不能幼稚喧闹**（家长不买单，且分散识字注意力）。判据很简单——任何元素如果抢走了对"字本身"的注意力，就删掉。

### 1.2 核心视觉特征

| 关键词 | 落地 |
|---|---|
| **纸感** | 米白底 `#FDF9F3` 贯穿全局，禁纯白满屏；卡片用纯白浮在纸面上，形成纸张叠放感 |
| **圆润** | 圆角 16-20px，按钮近全圆；转角是孩子的手，不是刀锋 |
| **朱砂点题** | 朱红 `#D94F3D` 只用在"该被点的地方"——选中、主操作、奖励印记，全局占比 ≤ 10% |
| **大留白** | 一屏只讲一件事：一个字。留白率 ≥ 40% |
| **轻弹性** | 动效带轻微回弹（`cubic-bezier(.34,1.56,.64,1)`），像纸被手指按下又弹起 |

### 1.3 光影与质感

- **纯扁平 + 单层柔影**，不用拟物、不用渐变塑料感、不用玻璃拟态
- 阴影只承担"浮起"一件事：卡片浮于纸面 2-4px，弹层浮于卡片 12-24px
- 纸面纹理用极浅的 CSS 点阵（透明度 ≤ 3%），不用图片，省包体

---

## 2. Color Palette & Roles

### 2.1 Primary — 朱砂

| 名称 | HEX | CSS 变量 | 用途 |
|---|---|---|---|
| Primary | `#D94F3D` | `--c-primary` | 主按钮、选中态、重点数字、奖励印记 |
| Primary Deep | `#B53A2B` | `--c-primary-deep` | 按下态、印章描边 |
| Primary Light | `#FBE7E3` | `--c-primary-light` | 浅底标签、选中背景、进度条底 |
| Primary Wash | `#FDF3F0` | `--c-primary-wash` | 极浅区块底（如错题背景） |

### 2.2 Reward — 奖励金（激励系统专属）

| 名称 | HEX | CSS 变量 | 用途 |
|---|---|---|---|
| Gold | `#F2B230` | `--c-gold` | 星星、积分、等级徽章 |
| Gold Deep | `#D9941C` | `--c-gold-deep` | 星星描边、金色文字（保证对比度） |
| Gold Light | `#FEF4DE` | `--c-gold-light` | 奖励条背景、集章册底 |

> 奖励金是**唯一允许发光**的色，且只出现在激励相关元素上。学习主界面不出现金色，形成"看到金色 = 有收获"的条件反射。

### 2.3 Neutral — 纸与墨

| 名称 | HEX | CSS 变量 | 用途 |
|---|---|---|---|
| Paper | `#FDF9F3` | `--c-bg` | 全局背景 |
| Surface | `#FFFFFF` | `--c-surface` | 卡片、弹层 |
| Ink | `#2B2B2B` | `--c-text` | 正文、汉字主色 |
| Ink Soft | `#5C574F` | `--c-text-2` | 次要文字、释义 |
| Gray | `#8A8378` | `--c-text-3` | 辅助说明、占位符 |
| Line | `#EDE6DA` | `--c-line` | 分割线、卡片描边 |
| Line Soft | `#F5EFE5` | `--c-line-soft` | 内部分割 |

### 2.4 Semantic — 语义色

| 名称 | HEX | CSS 变量 | 用途 |
|---|---|---|---|
| Success 竹青 | `#57A88F` | `--c-success` | 答对、完成、进度达标 |
| Success Light | `#E8F4F0` | `--c-success-light` | 成功态浅底 |
| Warn 杏橙 | `#E8A33D` | `--c-warn` | 提示、待办、"再试一次" |
| Warn Light | `#FDF2E0` | `--c-warn-light` | 提示浅底 |

> **儿童场景禁用刺眼错误红**。答错不用红色报警，用杏橙 `#E8A33D` + "再看看" 文案。红色只属于朱砂主色（正向、印记），不与"错误"绑定，避免孩子对红色产生焦虑。

### 2.5 Shadow

| 名称 | 值 | CSS 变量 |
|---|---|---|
| shadow-sm | `0 1px 2px rgba(43,43,43,.04)` | `--sh-sm` |
| shadow-md | `0 2px 8px rgba(43,43,43,.06), 0 1px 2px rgba(43,43,43,.04)` | `--sh-md` |
| shadow-lg | `0 8px 24px rgba(43,43,43,.10), 0 2px 6px rgba(43,43,43,.05)` | `--sh-lg` |
| shadow-gold | `0 4px 14px rgba(242,178,48,.32)` | `--sh-gold` |

---

## 3. Typography Rules

### 3.1 Font Family

```css
/* 汉字展示 —— 小程序不能外挂字体，用系统黑体族 */
--font-hanzi: "PingFang SC", "HarmonyOS Sans SC", "Source Han Sans SC",
              "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;

/* 正文 —— 同上，略降字重 */
--font-body: var(--font-hanzi);

/* 数字 —— 用系统等宽数字特性 */
--font-num: -apple-system, "SF Pro Text", "DIN Alternate", sans-serif;
font-variant-numeric: tabular-nums;
```

**为什么不用楷体**：识字课本用楷体是事实，但小程序无法保证 Android 端有楷体，混用会造成两端字形不一致——对识字教学反而有害。**楷体的正确落点是笔顺与田字格**：P4 的 canvas 用 hanzi-writer-data 的笔画路径绘制，那套数据本身就是楷体字形，课本级准确。列表与详情的大字用系统黑体，保证一致与可读。

**字体的三层分工**：
1. **黑体大字**（纯色）—— 认字、看结构
2. **canvas 楷体**（笔画路径）—— 笔顺、田字格占格、写字
3. **正文黑体**（15px）—— 释义、组词、说明

### 3.2 Type Scale

| 层级 | Size | Weight | Line Height | Letter Spacing | 用途 |
|---|---|---|---|---|---|
| Hanzi Hero | 140px | 600 | 1 | 0 | 详情页主字（iPad 分栏左侧） |
| Hanzi XL | 96px | 600 | 1 | 0 | 详情页主字（手机） |
| Hanzi Card | 56px | 600 | 1.1 | 0 | 列表卡片字 |
| Display | 22px | 700 | 1.35 | 0 | 页面主标题 |
| Title | 17px | 600 | 1.4 | 0 | 区块标题、课名 |
| Body | 15px | 400 | 1.65 | 0.2px | 正文、释义 |
| Body Strong | 15px | 600 | 1.6 | 0.2px | 组词、强调项 |
| Caption | 13px | 400 | 1.5 | 0.3px | 辅助说明、拼音标注 |
| Micro | 11px | 400 | 1.4 | 0.4px | 版本号、角标 |

**拼音专用**：拼音用 18px / 500，颜色 `--c-primary-deep`，与汉字上下对齐留 8px 间距。四线三格用 CSS 背景线绘制（三条 `--c-line` 细线），不占额外 DOM。

**排版哲学**：字重只用 400 / 600 / 700 三档，跨度大、层级清；字距几乎不加（中文加字距会散），只在 13px 以下微加 0.3-0.4px 防糊。

---

## 4. Component Stylings

### 4.1 Buttons

```css
/* Primary —— 主操作，一屏最多一个 */
.btn-primary {
  height: 48px; padding: 0 28px;
  background: #D94F3D; color: #fff;
  border-radius: 999px; border: none;
  font-size: 16px; font-weight: 600;
  box-shadow: 0 2px 8px rgba(217,79,61,.24);
  transition: transform .18s cubic-bezier(.34,1.56,.64,1), background .18s;
}
.btn-primary:active { background:#B53A2B; transform: scale(.96); }
.btn-primary[disabled] { background:#EDE6DA; color:#B8B0A4; box-shadow:none; }

/* Secondary —— 次级操作 */
.btn-secondary {
  height: 48px; padding: 0 28px;
  background: #fff; color: #D94F3D;
  border: 1.5px solid #F3C9C2; border-radius: 999px;
  font-size: 16px; font-weight: 600;
}
.btn-secondary:active { background:#FDF3F0; transform: scale(.96); }

/* Ghost —— 文字类操作 */
.btn-ghost {
  height: 40px; padding: 0 16px;
  background: transparent; color: #5C574F;
  font-size: 15px; border-radius: 12px;
}

/* Reward —— 奖励领取，金色专属 */
.btn-reward {
  height: 48px; padding: 0 28px;
  background: linear-gradient(180deg,#F7C553,#F2B230);
  color: #6B4708; border-radius: 999px;
  font-size: 16px; font-weight: 700;
  box-shadow: 0 4px 14px rgba(242,178,48,.32);
}
```

### 4.2 Cards

```css
.card {
  background: #fff; border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(43,43,43,.06), 0 1px 2px rgba(43,43,43,.04);
  border: 1px solid #F5EFE5;   /* 极细描边，防止白卡在米底上糊边 */
}
.card:active { transform: scale(.98); transition: transform .16s ease; }

/* 字卡列表项 */
.card-char { display:flex; flex-direction:column; align-items:center; gap:6px; padding:18px 8px; }
.card-char .zi { font-size:56px; font-weight:600; color:#2B2B2B; line-height:1; }
.card-char .py { font-size:13px; color:#8A8378; letter-spacing:.3px; }

/* 已学态：右上角小印章，不整卡变色（避免列表花） */
.card-char.learned::after {
  content:""; position:absolute; top:8px; right:8px;
  width:10px; height:10px; border-radius:50%;
  background:#57A88F;
}
```

### 4.3 Inputs

```css
.input {
  height: 46px; padding: 0 16px;
  background: #fff; border: 1.5px solid #EDE6DA;
  border-radius: 14px; font-size: 15px; color:#2B2B2B;
}
.input:focus { border-color:#D94F3D; box-shadow: 0 0 0 3px rgba(217,79,61,.10); }
.input::placeholder { color:#B8B0A4; }
```

### 4.4 Navigation

- **tabBar**：白底 + 顶部 1px `#F5EFE5` 分割；未选 `#8A8378` 线性图标，选中 `#D94F3D` 填充图标 + 文字变粗一档（11px→600）
- **页面导航**：米白底 `#FDF9F3`，标题 17px/600 居左（不用居中，中文长标题居中会换行）
- **返回**：左上角 44×44 热区，箭头 20px `#2B2B2B`

### 4.5 Badges / Tags

```css
.tag {
  height: 24px; padding: 0 10px; border-radius: 8px;
  font-size: 12px; font-weight: 500;
  display:inline-flex; align-items:center;
}
.tag-multi   { background:#FBE7E3; color:#B53A2B; }  /* 多音字 */
.tag-lesson  { background:#F5EFE5; color:#8A8378; }  /* 课次 */
.tag-new     { background:#E8F4F0; color:#3E7F6C; }  /* 新课 */
```

### 4.6 Modals / Dialogs

```css
.mask { background: rgba(43,43,43,.36); backdrop-filter: blur(2px); }
.dialog {
  background:#fff; border-radius: 20px; padding: 24px 20px 20px;
  box-shadow: 0 8px 24px rgba(43,43,43,.10);
  animation: dialog-in .26s cubic-bezier(.34,1.56,.64,1);
}
@keyframes dialog-in {
  from { opacity:0; transform: scale(.92) translateY(8px); }
  to   { opacity:1; transform: scale(1) translateY(0); }
}
```

### 4.7 田字格（核心自绘组件）

```css
.tianzige {
  position: relative; background: #fff;
  border: 1.5px solid #E0A8A0;      /* 朱砂淡描外框 */
  border-radius: 6px;                /* 微圆角，纸的裁切感 */
  overflow: hidden;
}
/* 红色虚线十字 */
.tianzige::before, .tianzige::after {
  content:""; position:absolute; border-color:#E0A8A0;
  border-style: dashed; border-width: 0 0 1px 0;
}
.tianzige::before { left:0; right:0; top:50%; }
.tianzige::after  { top:0; bottom:0; left:50%; border-width:0 1px 0 0; }
```

> 底色用纸白而非米白，让格子从背景中"浮"出来；边框用朱砂 30% 浓度，比纯红虚线更接近课本印刷。

---

## 5. Layout Principles

### 5.1 Spacing System

基数 **4px**，常用档位：

| Token | px | 用途 |
|---|---|---|
| `--sp-1` | 4 | 图标与文字间距 |
| `--sp-2` | 8 | 行内元素间距 |
| `--sp-3` | 12 | 卡片内小间距 |
| `--sp-4` | 16 | **卡片内边距（标准）** |
| `--sp-5` | 24 | 区块间距 |
| `--sp-6` | 32 | 页面左右边距（手机） |
| `--sp-7` | 48 | 大区块分隔 |

### 5.2 Grid

- **手机**：内容单列，左右边距 16px（不是 32，儿童界面信息密度需要略高）
- **平板**：容器 `max-width: 720px` 居中；列表转 4 列 `grid-template-columns: repeat(auto-fill, minmax(150px, 1fr))`，列间距 12px
- **详情页平板**：左 40%（大字 + 田字格）/ 右 60%（拼音/部首/组词），中间 24px 沟槽

### 5.3 Container

```css
.page { padding: 0 16px calc(16px + env(safe-area-inset-bottom)); }
@media (min-width: 768px) {
  .page { max-width: 720px; margin: 0 auto; padding: 0 24px; }
}
```

### 5.4 留白哲学

**一屏一个焦点。** 详情页除主字外的所有信息都降一档字号、加 24px 上间距。字卡列表每行最多 4 个格子（手机 2 个），宁可行少也不塞满。

---

## 6. Depth & Elevation

### 6.1 Shadow System

```css
--sh-sm:    0 1px 2px rgba(43,43,43,.04);
--sh-md:    0 2px 8px rgba(43,43,43,.06), 0 1px 2px rgba(43,43,43,.04);
--sh-lg:    0 8px 24px rgba(43,43,43,.10), 0 2px 6px rgba(43,43,43,.05);
--sh-gold:  0 4px 14px rgba(242,178,48,.32);
--sh-inset: inset 0 1px 0 rgba(255,255,255,.6);
```

### 6.2 Surface Layers

| 层 | 值 | 用途 |
|---|---|---|
| 0 background | `#FDF9F3` | 纸面 |
| 1 surface | `#FFFFFF` + `--sh-sm` | 列表卡片 |
| 2 elevated | `#FFFFFF` + `--sh-md` | 主卡、吸底栏 |
| 3 overlay | `#FFFFFF` + `--sh-lg` | 弹层、奖励弹窗 |

### 6.3 Z-index

```
--z-base: 0; --z-sticky: 10; --z-nav: 100;
--z-mask: 900; --z-dialog: 1000; --z-toast: 1100; --z-reward: 1200;
```

### 6.4 Backdrop

只用于弹层遮罩：`rgba(43,43,43,.36)` + `blur(2px)`。不做毛玻璃卡片。

---

## 7. 激励机制（Incentive System）

> 原则：**只做正反馈，不做压力机制。** 无排行榜、无倒计时惩罚、无连续失败降级。目标是让孩子"想再来一次"，而不是"怕掉下去"。

### 7.1 四层激励

| 层 | 机制 | 触发 | 视觉 |
|---|---|---|---|
| **即时** | 得星 | 学会一个新字 +1 / 听写全对 +5 / 完成练习 +3 | 星星从字面飞出 → 落到顶部计分，`--sh-gold` 光晕 |
| **短期** | 连续打卡 | 每日首次学习 +1 天 | 顶部火苗徽章，天数用 `--c-gold-deep` 数字 |
| **中期** | 集章册 | 每学完一册盖一枚印章（12 册共 12 枚） | 朱红方印，盖章动效：缩放 1.4→1 + 旋转 -8°→-4° + 墨迹扩散 |
| **长期** | 等级称号 | 累计字数达标晋级 | 书签形徽章，五级 |

### 7.2 等级阶梯（科举制，贴合识字主题）

| 等级 | 累计字数 | 称号 | 徽章色 |
|---|---|---|---|
| 1 | 0 | 蒙童 | `#8A8378` |
| 2 | 50 | 学童 | `#57A88F` |
| 3 | 200 | 小秀才 | `#5B8FA8` |
| 4 | 500 | 小举人 | `#D9941C` |
| 5 | 1000 | 小进士 | `#D94F3D` |
| 6 | 2000 | 小状元 | `#B53A2B` + 金色描边 |

晋级时全屏弹窗：印章式大徽章 + 一句鼓励（"你已经是小秀才了，认识 200 个字"），按钮只有一个「继续学」。

### 7.3 星星规范

- 形状：五角星，圆角化（不是尖角，避免攻击感）
- 尺寸：16px（列表）/ 24px（详情）/ 72px（得星动效）
- 颜色：`--c-gold` 填充 + `--c-gold-deep` 1px 描边
- **星星不消费、不兑换**，纯累计。避免游戏化成瘾，也不给家长"这是氪金游戏"的印象

### 7.4 动效与声音

| 事件 | 动效 | 时长 | 声音 |
|---|---|---|---|
| 点击卡片 | `scale(.98)` | 160ms | 无 |
| 得星 | 星星上浮 + 旋转 + 淡出 | 720ms | "叮"（短促清脆） |
| 集章 | 印章落下 + 微震 | 480ms | "咚"（木质） |
| 等级提升 | 徽章放大 + 金粉粒子 | 900ms | 上行三音 |
| 答错 | 卡片左右轻晃 2 次 | 320ms | "啵"（柔和，非警报） |
| 页面切换 | 右进左出 12px 位移 | 260ms | 无 |

缓动统一 `cubic-bezier(.34,1.56,.64,1)`（回弹），仅"答错"用 `ease-in-out`（不回弹，避免像鼓励）。

---

## 8. Do's and Don'ts

### Do's

1. **朱砂只用在该被点的地方**——一屏朱红面积 ≤ 10%，超出就泛滥
2. **大字必须占主导**——详情页主字视觉权重 ≥ 50%，其他都是配角
3. **奖励金只属激励**——学习界面出现金色 = 有收获，形成条件反射
4. **答错用杏橙不用红**——红色留给印记与正向，不制造焦虑
5. **动效 ≤ 300ms**（除奖励动效），不让孩子等动画
6. **每屏一个主动作**——按钮层级严格 Primary / Secondary / Ghost
7. **平板靠留白与列数，不靠放大**——元素尺寸与手机一致，只是排更多
8. **安全区必留**——`env(safe-area-inset-bottom)`，iPad 横条与 iPhone 刘海

### Don'ts

1. **不用卡通 IP 形象**——会喧宾夺主，且拉低家长对"学习工具"的信任
2. **不用渐变塑料感、不用毛玻璃卡片**——廉价感，与纸墨主题冲突
3. **不用纯白满屏**——刺眼，失纸感
4. **不做排行榜 / 好友对比 / 公开分享**——审核红线（UGC），且制造攀比压力
5. **不做连续失败惩罚 / 倒计时压迫**——除听写可选计时外，一律不设时限
6. **不用超过 3 种字重**——400/600/700 之外不用
7. **不在列表卡片上用大面积色块区分状态**——用角标小圆点，避免列表花掉
8. **不用纯黑 `#000`**——用墨黑 `#2B2B2B`，纯黑在纸上像窟窿

---

## 9. Responsive Behavior

### 9.1 Breakpoints

| 断点 | 设备 | 布局 |
|---|---|---|
| < 375px | iPhone SE | 边距 12px，字卡列表 2 列，主字 88px |
| 375-430px | 主流手机（基准） | 边距 16px，列表 2 列，主字 96px |
| 430-768px | 大屏手机 / 折叠展开 | 边距 16px，列表 3 列 |
| 768-1024px | iPad 10.2" 竖屏 810×1080 | 容器 720px 居中，列表 4 列，详情左右分栏 |
| ≥ 1024px | iPad 10.2" 横屏 1080×810 | 容器 900px，练习本整页 A4 |

### 9.2 rpx 换算锁定

```json
// pages.json → globalStyle
"rpxCalcMaxDeviceWidth": 430,
"rpxCalcBaseDeviceWidth": 375
```
设备宽 > 430px 时统一按 375 基准，**平板上 1rpx ≡ 0.5px**，界面尺寸与手机一致。字号一律用 px，不受 rpx 影响。

### 9.3 Touch Targets

- 最小 **44×44px**（微信建议 40px+），字卡列表每格 ≥ 88×88px
- tabBar 单项热区 ≥ 50px 高
- 相邻可点元素间距 ≥ 8px，防误触

### 9.4 Font Scaling

字号全部 px 固定，不随屏宽缩放。系统字号放大设置（微信"字体大小"）下，正文允许 15→17px 自适应，主字与卡片布局不变（避免撑破）。

### 9.5 折叠策略

| 内容 | 手机 | 平板 |
|---|---|---|
| 字卡列表 | 2 列网格 | 4 列网格 |
| 详情页 | 竖排单列 | 左字右信息 |
| 组词列表 | 竖排 | 2 列并排 |
| 集章册 | 3 列 | 6 列 |
| 听写核对 | 单列大按钮 | 2 列网格 |

---

## 10. Agent Prompt Guide

### 10.1 Quick Reference

```
底色 #FDF9F3 · 卡片 #FFFFFF/圆角16/1px #F5EFE5
主色 #D94F3D（占比≤10%）· 奖励金 #F2B230（仅激励）
墨 #2B2B2B · 次级 #8A8378 · 线 #EDE6DA
成功 #57A88F · 提示 #E8A33D（不用红报错）
字重 400/600/700 · 正文15px/1.65 · 主字96px
间距 4/8/12/16/24/32 · 按钮圆角999 · 热区≥44
缓动 cubic-bezier(.34,1.56,.64,1) · 动效≤300ms
```

### 10.2 Component Prompts

1. 「做一个字卡列表页：米白底 #FDF9F3，卡片白底圆角16带1px #F5EFE5描边，每格显示 56px 汉字 + 13px 拼音，手机2列、平板4列（auto-fill minmax(150px,1fr)），已学字右上角加 #57A88F 小圆点」
2. 「做一个字卡详情页手机版：主字 96px 居中，下方拼音 18px #B53A2B，再下田字格 240px，然后组词列表（每个词 15px，右侧小喇叭图标），卡片间距 16px」
3. 「做平板端详情页左右分栏：左侧 40% 放主字 140px + 田字格 320px 居中，右侧 60% 放拼音/部首/结构/组词，中间 24px 沟槽，容器 720px 居中」
4. 「做集章册页面：12 个朱红方印网格，已获得显示实心印章（#D94F3D 边框 + 印文），未获得显示虚线灰框，手机3列平板6列」
5. 「做等级晋级弹窗：白底圆角20卡片，中央 120px 圆形徽章（#D94F3D 底 + 白字称号），下方"你已经是小秀才了，认识 200 个字"，底部单个 Primary 按钮"继续学"」
6. 「做顶部学习概览条：左侧火苗图标 + 连续天数（金色数字），右侧进度环（#D94F3D 到 #F2B230 渐变，环宽 4px），中间显示"本册 32/100"」

### 10.3 Iteration Guide

1. 每次改完**先在 375px 看**，再切 810px，两端都要过
2. 检查朱红面积是否超 10%——超了就把某个红改成灰或浅底
3. 检查是否有第二个 Primary 按钮——有就降级成 Secondary
4. 金色只出现在激励元素上，学习界面出现金色就是错
5. 答错的视觉一律是杏橙，不是红
6. 字卡列表超过 4 列就该增加留白而不是继续塞
7. 动效加了先关掉看能不能用——能用的动效才是好动效
8. 任何"装饰性"元素（花纹、插画、边框）都问一句：它抢字了吗？抢就删
9. 平板端禁止把手机布局等比放大，只允许"排更多列"或"分栏"
10. 交付前对一遍安全区与 44px 热区
