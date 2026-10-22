# zika 字卡小程序 · DESIGN.md

> 版本：v2.03
> 日期：2026-10-22
> 适用范围：微信小程序（手机 375-430px / 平板 iPad 10.2" 810-1080px）
> 配套：zika小程序开发方案_v1.05.md、design/preview.html（可视化稿）
>
> **v2.02 → v2.03**：①**组词单一来源**（5.6）：多音字区块的「本课读音」不再自己采词，直接照搬小卡片那份，消除「小卡片写一个/半个/个子、详情写一个/两个/几个」；②多音字从 185 字增至 192 字（本课读音不再因"采不到词"被丢）；③主库修掉 18 个字的坏组词（百度/勾践/阿金/隆中/吆喝/一溜/拓扑/征辟/胶塞/劲力/累死/折子奏折/苔原/薄壁）。
> **v2.01 → v2.02**：①释义整体重采（5.7），旧库古汉语字典残留换成《现代汉语词典》体例的短义项；②详情弹层释义由单字符串改为**义项数组**，多条分行显示 + 朱砂圆圈序号，单条不加序号；③释义数据独立成 `static/data/defs_v2.json`，与 `dict.json` 解耦（旧 `cleanExplanation` 闸门已删——新数据不需要闸门）。
> **v2.00 → v2.01**：①详情弹层 body 新增**多音字区块**（5.6）：一读音一张分组卡，本课读音朱砂淡底高亮 + 「本课」小标签，每读音独立展示四线三格拼音、组词胶囊、出处课次；②多音字数据与主库分离（`static/data/multi_v2.json`），主库仍只标本课读音，小卡片不受影响；③拼音格 `sm` 规格直接复用 3.3，不新增字号。
> **v1.03 → v2.00**：视觉基线**回到 Web 版 v3.52 的「纸卷」体系**（原 `public/index.html` 的 `:root` 令牌），之前那套"现代白卡"整体废弃。①色板换成米黄纸底 `#F6F1E5` / 纸白卡 `#FFFDF7` / 朱红 `#C93A2B` / 金 `#C9973F` / 暖棕描边 `#E6DDC8`，投影也换成暖棕（纸感全在这两样上）；②卡片恢复竖排结构（大字 → 四线三格拼音 + 金色喇叭圈 → 组词金色胶囊），主字手机 44 / 平板 72；③详情改回**居中弹窗**（原版 `#modal` 形态），顺带解决底栏按钮被原生 tabBar 压住的问题；④田字格改**米字格**（十字 `#D9C69A` + 对角 `#EFE4C4`），对齐原版 `#writerBox`；⑤列数两端统一 **4 列**——课本每课 4 或 8 字，只有 4 列能让这两种课都排满。
> **v1.02 → v1.03**：①列表列数定为手机 4 列 / 平板 6 列（原表写 2/3 列，与实际排版不符）；②断点实现禁用 `@media`，统一由 JS 判宽后挂 `.pad` 或内联宽度（见 9.6）；③四线三格增加最小宽度，短拼音不再缩成一条；④田字格改 flex 居中并上抬 1.5% 校正楷体视觉重心。
> **v1.01 → v1.02**：①四线三格四条线改为统一的 1px 背景层（旧版 border+渐变线导致中间两条显粗），格高取 3 的倍数；②详情页由"整页/平板分栏"改为**弹出式弹层**，手机底部弹出、平板居中限宽 560，两端共用一套结构；③新增弹层组件规范（5.5）。
> **v1.00 → v1.01**：①汉字字体由黑体改回楷体，新增 3.4 外挂路线；②四线三格给出唯一正确实现（四线≠三线、字号按 x-height 定、文字禁止加底色）；③明确汉字大字号不加重（楷体加粗会糊掉笔锋）；④新增格线色 `--c-py` / `--c-grid`。

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

> **本表是唯一色源**，逐值取自原 Web 版 `public/index.html` 的 `:root`，不要凭感觉调。

### 2.1 Primary — 朱砂

| 名称 | HEX | SCSS 变量 | 用途 |
|---|---|---|---|
| Primary | `#C93A2B` | `$zk-primary` | 印章底、实心按钮、选中态、课文标题字 |
| Primary Deep | `#A3281C` | `$zk-primary-deep` | 按下态、弹层主字、正文强调 |
| Primary Light | `#F9E9E4` | `$zk-primary-light` | 浅底标签、选中背景 |
| Primary Wash | `#FCF2EE` | `$zk-primary-wash` | 极浅区块底 |

### 2.2 Reward — 奖励金（激励系统 + 组词徽章）

| 名称 | HEX | SCSS 变量 | 用途 |
|---|---|---|---|
| Gold | `#C9973F` | `$zk-gold` | 课文标题左侧竖条、喇叭圈描边、"学会啦"按钮 |
| Gold Deep | `#A87C2C` | `$zk-gold-deep` | 金色文字（保证对比度）、喇叭图标 |
| Gold Light | `#F7ECD6` | `$zk-gold-light` | 组词胶囊底、课文标题渐变起点、喇叭圈底 |
| Gold Line | `#F0DFBC` | `$zk-gold-line` | 组词胶囊描边、字数胶囊描边 |

### 2.3 Neutral — 纸与墨

| 名称 | HEX | SCSS 变量 | 用途 |
|---|---|---|---|
| Paper | `#F6F1E5` | `$zk-bg` | 全局背景（米黄，不是米白） |
| Surface | `#FFFDF7` | `$zk-card` | 卡片、弹层（纸白，不是纯白） |
| Ink | `#33322E` | `$zk-text` | 正文、汉字主色 |
| Ink Soft | `#6B675C` | `$zk-text-2` | 次要文字、释义、提示 |
| Gray | `#8A8378` | `$zk-sub` | 占位符、极弱说明 |
| Line | `#E6DDC8` | `$zk-line` | **卡片描边（必须可见）**、分割线 |
| Line Soft | `#F0E9D8` | `$zk-line-soft` | 内部分割 |
| Grid 十字 | `#D9C69A` | `$zk-grid` | 米字格十字线、外框 `#DFD0AB` |
| Grid 对角 | `#EFE4C4` | `$zk-grid-diag` | 米字格两条对角斜线 |
| Py Line 四线三格 | `#B8C8DC` | `$zk-py-line` | 拼音四线三格的 4 根线（淡钢蓝） |
| Py Ink 拼音字 | `#2B2F36` | `$zk-py-ink` | 四线格里的拼音字（**深墨，不是灰褐**） |

> **纸感 = 米黄底 + 暖棕描边 + 暖棕投影**。三者缺一就退回"现代白卡"，这是 v2.00 返工的根因。
> 拼音字色必须是深墨 `#2B2F36`——用灰褐会让拼音显得虚、不像课本印刷。

### 2.4 Semantic — 语义色

| 名称 | HEX | SCSS 变量 | 用途 |
|---|---|---|---|
| Success 竹青 | `#5D8A66` | `$zk-success` | 答对、已学标记、进度达标 |
| Success Light | `#E7F0E6` | `$zk-success-light` | 成功态浅底 |
| Warn 杏橙 | `#C9973F` | `$zk-warn` | 提示、"再试一次"（复用金色，不再引入新色） |

> **儿童场景禁用刺眼错误红**。答错不用红色报警，用金橙 + "再看看"文案。

### 2.5 Shadow

投影必须带暖棕，不能用中性灰（`rgba(43,43,43,.x)` 是旧方案，已废弃）。

| 名称 | 值 | SCSS 变量 |
|---|---|---|
| shadow-sm | `0 2px 6px rgba(90,70,30,.05)` | `$zk-sh-sm` |
| shadow-md | `0 6px 18px rgba(90,70,30,.10)` | `$zk-sh-md` |
| shadow-lg（弹窗） | `0 24px 60px rgba(0,0,0,.30)` | `$zk-sh-lg` |
| shadow-seal（印章） | `0 4px 10px rgba(163,40,28,.28)` | `$zk-sh-seal` |

---

## 3. Typography Rules

### 3.1 Font Family

```css
/* 汉字（认字与写字）—— 楷体，字体文件随包外挂，见 3.3 */
--font-hanzi: "zika-kai", "Kaiti SC", "STKaiti", "KaiTi", "楷体", serif;

/* 正文 / UI —— 系统黑体族 */
--font-ui: "PingFang SC", "HarmonyOS Sans SC", "Source Han Sans SC",
           "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;

/* 拼音 —— 必须字面清晰、声调符号完整 */
--font-py: Arial, Helvetica, "Helvetica Neue", sans-serif;

/* 数字 —— 等宽数字特性 */
font-variant-numeric: tabular-nums;
```

**汉字必须用楷体（v1.01 修正）**：v1.00 曾决定大字用黑体、楷体只用于 canvas 笔顺，理由是「Android 不保证有楷体」。这个理由只说明了「系统楷体不可靠」，结论却错了——**生字用黑体是识字教学上的硬错误**：黑体笔画粗细齐平、无顿笔无收锋，「口」在楷体里是竖—横折—横三笔有起收的笔画，在黑体里就是三根等宽线条，孩子看不出笔形，也对应不上笔顺动画。原版 Web 用的就是楷体（`.hanzi-font`），v1.00 是我改错了。

正确做法不是「退回黑体」，而是**把楷体字体文件带进小程序**（wx.loadFontFace + 子集化），见 3.3。

### 3.2 Type Scale

| 层级 | Size | Weight | Line Height | 用途 |
|---|---|---|---|---|
| Hanzi Grid（米字格内） | 180px 格的 72% | 400 | 1 | 详情页书写区主字 |
| Hanzi Card | 52px | 400 | 1.08 | 列表卡片字 |
| Hanzi Inline | 15px | 400 | 1.6 | 组词、释义里的汉字 |
| Display | 22px | 700 | 1.35 | 页面主标题 |
| Title | 17px | 600 | 1.4 | 区块标题、课名 |
| Body | 15px | 400 | 1.65 | 正文、释义 |
| Body Strong | 15px | 600 | 1.6 | 强调项 |
| Caption | 13px | 400 | 1.5 | 辅助说明 |
| Micro | 11px | 400 | 1.4 | 版本号、角标 |

**汉字不用 600/700 字重**：楷体加粗会被合成器「糊」掉笔锋，反而丢失楷体最重要的起收笔信息。大字一律 400。

**排版哲学**：字重只用 400 / 600 / 700 三档；中文不加字距（会散），只在 13px 以下微加 0.3-0.4px 防糊。

### 3.3 四线三格（拼音格，唯一正确实现）

四线三格是**四根线、三个格**，不是「三根线」——这是最常被写错的地方。

```
────────────  线1  ← 上格上沿（声调所在）
   ˉ 声调
────────────  线2  ← 上格下沿 / 中格上沿
   k ǒ u      ← 中格：字母主体（x-height 应正好填满）
────────────  线3  ← 中格下沿 / 下格上沿（拼音基线）
   g p y      ← 下格：下伸部分
────────────  线4  ← 下格下沿
```

实现要点（踩过的坑，别再踩）：

**四条线必须全部由背景层绘制，且都是 1px 纯色。** v1.01 用 `border-top/bottom` + 两条渐变线，结果中间两条明显比上下粗——渐变线落在 33.3% / 66.7% 的亚像素位置，被抗锯齿摊成 1.5-2px 的半透明带。改成 4 层纯色渐变、位置写 px 后，四条线粗细完全一致。

```css
.pg{
  display:inline-flex; align-items:flex-start;
  background-repeat:no-repeat; background-size:100% 1px;
  background-image:
    linear-gradient(var(--c-py),var(--c-py)), linear-gradient(var(--c-py),var(--c-py)),
    linear-gradient(var(--c-py),var(--c-py)), linear-gradient(var(--c-py),var(--c-py));
  background-position:0 0, 0 var(--l1), 0 var(--l2), 0 var(--l3);
}
.pg.sm{height:27px;--l1:9px; --l2:18px;--l3:26px}
.pg.md{height:36px;--l1:12px;--l2:24px;--l3:35px}
.pg.lg{height:45px;--l1:15px;--l2:30px;--l3:44px}
.pg i{ background:transparent; }         /* ← 关键：文字绝不能有底色 */
```

| 尺寸 | 格高 | 四线位置（1/2/3/4） | 字号 | line-height | top 微调 |
|---|---|---|---|---|---|
| sm（列表卡片） | 27px | 0 / 9 / 18 / 26 | 16.5px | 26px | -1.3px |
| md（详情/搜索） | 36px | 0 / 12 / 24 / 35 | 21.5px | 34px | -0.3px |
| lg（大字场景） | 45px | 0 / 15 / 30 / 44 | 28px | 44px | -1.4px |

**四条铁律**：
1. **格高取 3 的倍数**（27 / 36 / 45），线的位置才是整像素；否则线又一次被抗锯齿摊粗。
2. **文字不能有背景色**。v1.00 给拼音加了 `background:var(--c-bg)`，直接把格线盖出一圈空白——这是必须避免的错法。
3. **字号按 x-height 定**：`字号 = 中格高 ÷ 0.519`（Arial x-height 比例），这样中格刚好被字母填满，而不是飘在格子里。
4. **基线压在线 3**：靠 `top` 微调。实测值（Chrome + Arial）：md 档基线 23.70 / 线 3 在 24，sm 档 17.70 / 18，各留 0.3px 呼吸。**改字号或 line-height 后必须用 `getBoundingClientRect` + canvas 字体度量重测**，目测不可靠。

**最小宽度**：`.pg` 宽度随拼音长度自适应，但必须给下限（sm 40px / md 52px / lg 64px）并 `text-align:center`。否则 `yī` 这类短拼音会缩成一条与格线同宽的窄条，一列卡片看过去参差不齐。

**线色**：`$zk-py-line: #B8C8DC`（淡钢蓝）。灰度太高会看不清、太艳会抢字，课本用的就是这个色域。
**字色**：`$zk-py-ink: #2B2F36`（深墨）——不要用灰褐 `#6B675C`，会让拼音显得虚、不像课本印刷。
米字格十字线用 `$zk-grid: #D9C69A`、对角 `$zk-grid-diag: #EFE4C4`，与四线三格的蓝形成区分。

### 3.4 字体外挂路线（待拍板）

小程序不能直接读包内字体，必须有网络字体文件。三条路线：

| 路线 | 做法 | 判定 |
|---|---|---|
| A 系统楷体兜底 | `font-family:"KaiTi","Kaiti SC",…,sans-serif` | 零成本，Android 端实际回落黑体，两端不一致。**只作兜底** |
| **B 字体子集 + loadFontFace**（推荐） | 只保留本库 2307 字的 woff，约 600-900KB，放云存储，启动时 `wx.loadFontFace({global:true})` 加载一次 | 全端统一楷体；原生排版，列表滚动最流畅；组词/释义/页眉都能用 |
| C canvas 逐字绘制 | 用 hanzi-writer-data 的笔画路径直接画 | 与笔顺动画完全同源；但列表多 canvas 有性能风险，且文字不能被排版使用。**只用于米字格/笔顺** |

**推荐组合：B 为主 + C 专用于田字格。** 字体选型首选 **文鼎 PL 楷（AR PL UKai）**——开源可商用（Arphic Public License，明确允许嵌入与子集化），且 hanzi-writer 的汉字数据正出自这款楷体，**与笔顺动画 100% 同源**，不会出现「认的字」和「写的字」两个样子。备选霞鹜文楷（OFL，更秀气，但与笔顺数据不同源）。

> 待用户拍板：AR PL UKai（同源）还是霞鹜文楷（更好看）。定了在 P1 一并产出子集化脚本。

**排版哲学**：汉字与拼音是两套字体，不要混写在同一 run 里；拼音永远走 `--font-py`，汉字永远走 `--font-hanzi`。

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

### 4.2 Cards（字卡列表项，纸白竖卡）

结构自上而下：**楷体大字 → 四线三格拼音 + 金色喇叭圈 → 组词金色胶囊**，全部居中竖排。

```css
.card {
  background: #FFFDF7;              /* 纸白，不是纯白 */
  border: 1.5px solid #E6DDC8;      /* 暖棕描边，必须看得见 */
  border-radius: 12px;              /* 平板 14px */
  padding: 14px 4px 12px;           /* 左右只有 4px，见下方列宽说明 */
  min-height: 152px;                /* 平板 206px */
  box-shadow: 0 2px 6px rgba(90,70,30,.05);   /* 暖棕投影 */
  display: flex; flex-direction: column; align-items: center;
}
.card:active { transform: translateY(-2px); border-color: #D8C9A6; }

.card .big {                        /* 生字，必须楷体 */
  font-family: "zika-kai","Kaiti SC","KaiTi",serif;
  font-size: 44px; line-height: 54px; font-weight: 700; color: #33322E;
}
.card .sound {                      /* 喇叭：金色圈 + 金底 */
  width: 20px; height: 20px; border-radius: 50%;
  border: 1.5px solid #C9973F; background: #F7ECD6;
}
.card .w {                          /* 组词胶囊 */
  font-size: 10px; line-height: 14px; color: #7A7465;
  background: #F7ECD6; border: 1px solid #F0DFBC;
  border-radius: 999px; padding: 1px 4px; margin: 2px 1px 0;
}
/* 已学：右上角绿点（小程序新增，原版无） */
.card.on::after {
  content:""; position:absolute; top:6px; right:7px;
  width:7px; height:7px; border-radius:50%; background:#5D8A66;
}
```

**尺寸铁律**：手机单格 77px，组词胶囊必须能一行放两个——`font-size 10px / padding 1px 4px / margin 1px` 是三个一起调出来的值，单独放大任何一个都会退化成"一字一行"。

**喇叭图标**：小程序不支持内联 SVG，用 base64 data-URI 作 `background-image`（金色 `#8A6420` 版给列表、朱红 `#C93A2B` 版给弹层）。

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

### 4.6 Modals / Dialogs（居中弹窗，唯一形态）

```css
.mask { background: rgba(46,38,24,.45); }   /* 暖棕遮罩，不是冷灰 */

.modal {
  background: #FFFDF7;
  border-radius: 16px;              /* 平板 20px */
  max-width: 100%;                  /* 平板 520px */
  max-height: 86%;
  box-shadow: 0 24px 60px rgba(0,0,0,.30);
  animation: pop .22s ease both;
}
@keyframes pop {
  from { transform: scale(.94); opacity: 0; }
  to   { transform: scale(1);   opacity: 1; }
}
```

**必须居中，不要贴底**：小程序原生 tabBar 永远在最上层，`position:fixed` 的贴底弹层会被它压住底栏按钮（实测「学会啦」被切掉一半）。居中弹窗四周留 16px，天然躲开 tabBar。

### 4.7 米字格（核心自绘组件）

**格型是米字格**（十字 + 两条对角线），对齐原版 Web 的 `#writerBox`；早期方案写的"田字格"作废。

```css
.tzg {
  background: #FFFEF8;                /* 格子底比卡片再白一点，从纸底"浮"出来 */
  border: 1.5px solid #DFD0AB;
  border-radius: 12px;
  overflow: hidden;
}
/* 十字：暖金实线 */
.tzg-h { position:absolute; left:0; right:0; top:50%; height:1px; margin-top:-.5px; background:#D9C69A; }
.tzg-v { position:absolute; top:0; bottom:0; left:50%; width:1px; margin-left:-.5px; background:#D9C69A; }
/* 对角线：长度 = 格宽 × √2，绕中心旋转 */
.tzg-d { position:absolute; left:50%; top:50%; width:141.42%; height:1px;
         margin-left:-70.71%; margin-top:-.5px; background:#EFE4C4; }
.tzg-d1 { transform: rotate(45deg); }
.tzg-d2 { transform: rotate(-45deg); }
```

- 对角斜线**必须用元素 + rotate 画**，不能用 `linear-gradient(45deg,…)`：斜向渐变在非整数像素上会被抗锯齿摊粗，四条线会粗细不一（四线三格踩过同样的坑）。
- 字占格 72%，`display:flex` 居中后再 `translateY(-1.5%)`——楷体字形在 em 框内重心偏下，不校正会显得字"坐"在格底。
- 尺寸：手机 180px，平板 250px。

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

- **列数两端都是 4 列**。课本每课就是 4 或 8 个字，只有 4 列能让这两种课都排满；6 列时 4 字课空两格、8 字课断成 6+2。
- 手机：单格 `calc(25% - 8px)`，卡片间距 8px，左右边距 12px。
- 平板：单格 `calc(25% - 14px)`，卡片间距 14px，左右边距 24px，主字放大到 72px。
- **列宽必须内联**（`:style="cellStyle"`），不要写进 wxss：小程序 wxss 的媒体查询在部分机型不生效（见 9.6）。
- **详情两端都是居中弹窗**，一套结构，不做左右分栏。

### 5.3 Container

```css
.page { padding: 0 16px calc(16px + env(safe-area-inset-bottom)); }
@media (min-width: 768px) {
  .page { max-width: 720px; margin: 0 auto; padding: 0 24px; }
}
```

### 5.4 留白哲学

**一屏一个焦点。** 详情页除主字外的所有信息都降一档字号、加 24px 上间距。字卡列表每行最多 4 个格子（手机 2 个），宁可行少也不塞满。

### 5.5 详情弹层（字卡详情唯一形态）

**居中弹窗，不是底部抽屉。** 结构三段：

| 段 | 内容 | 行为 |
|---|---|---|
| head | 朱红大字（手机 60px / 平板 72px）+ 四线三格拼音（md）+ 金色喇叭 + 部首·结构·出处 + 右上角朱红关闭钮 | 固定 |
| body | 米字格 → 上一字/下一字 → 组词胶囊 → **多音字（仅多音字出现）** → 释义 | 内部 `scroll-view` 滚动 |
| foot | 「学会啦 +1★」实心金按钮 + 「加入生字本」描边按钮 | **固定，不可滚** |

**为什么居中而不是贴底**：贴底会被原生 tabBar 压住 foot（实测「学会啦」被切掉一半）。居中后四周留 16px，问题消失，且平板不用再单独算位置。

**大字必须包一层 view**：`<view class="zd-big"><text>字</text></view>`。直接把 text 当 flex item 会被压窄，字变瘦长（实测 60px 的字被压到 56px 宽）。

**组件形态**：整块做成 `components/zk-detail`，不用"容器组件 + slot"——小程序组件默认样式隔离，slot 里的类名会全部失效。

### 5.6 多音字区块（P2）

只在多音字出现，位置在「组词」之后、「释义」之前。

**为什么不做读音 tab**：孩子点 tab 要额外一步，且只看一个音时看不到另一个音，对比关系丢失。改成**一读音一行的分组卡**，几个读音一次看全。

| 元素 | 规格 |
|---|---|
| 容器 `.zd-multi` | 底 `#FFFDF7`，边框 `1.5px #E6DDC8`，圆角 12px，`overflow:hidden` |
| 分组行 `.zd-mrow` | `padding 10px 12px 8px`，行间 `1px dashed #ECE3CF`（首行无线） |
| 本课读音高亮 `.zd-mrow.on` | 底 `#FCF2EE`（朱砂洗色），左侧不描边——靠底色区分就够，两道装饰会打架 |
| 拼音 `.zd-mpy` | 复用 3.3 的 `zk-py size="sm"`（高 27 / 字号 16 / 基线 top -2px） |
| 「本课」标签 `.zd-mtag` | 字号 10，`line-height 14`，`padding 1px 5px`，圆角 3，字 `#C93A2B` 底 `#F9E9E4` 边 `#F0D5CD` |
| 组词胶囊 `.zd-mword` | 同 4.2 组词徽章：底 `#F7ECD6` 边 `#F0DFBC` 圆角 999，字号 13（平板 15） |
| 出处 `.zd-mfrom` | 字号 11（平板 12），色 `#A9A296`，格式「二上 · 课文18 古诗二首」 |

**排序**：本课读音永远排第一（`isLesson` 优先），其余按词表支撑度降序，最多 3 个读音。

**数据来源**：`tools/build-multi.py` 产出 `multi_v2.json`，与主数据分离。主库每字只留本课读音，多音字表只被详情页读，小卡片完全不受影响（方案 5.5 C 的"小卡片只显示本课读音"）。

**本课读音的组词只有一个来源**：直接取 `chars.json` 里那份（`lesson_words()`），不再二次采词。两处各算一遍曾导致 72 个字对不上——小卡片写「一个、半个、个子」，点开详情却是「一个、两个、几个」。同课同音同词是硬约束，`multi-override.json` 里也不再允许出现本课读音的条目（写了会把主库覆盖回去）。

### 5.7 释义区块（P2.5）

位置在「多音字」之后，是弹层 body 的最后一块。

**为什么整块重采**：旧库 `explanations` 是古汉语字典的 HTML 抓取残留，2307 字里 111 字完全缺失、130 条开头带拼音残片（`上` = `àng；位置在高处的…`）、328 条含〈古〉〈引〉〈喻〉字典标记、307 条中文引号错位成 `长”`、33 条混入说文解字体例（`(象形。甲骨文字形…)`）。这些不是清洗能救的，规则越补越像打补丁，直接换源。

**数据源**：搜狗汉语 `shiyiBase[].shiyiHtml`（《现代汉语词典》体例，按读音分组）。
百度 `add_mean` 是同一上游，结构等价，作容灾——但百度 `search_list` 接口连发 7 次就限流且十几分钟不恢复，搜狗 0.3 秒连发 26 次无压力，所以主源选搜狗。

| 元素 | 规格 |
|---|---|
| 容器 `.zd-defs` | 纵向 flex，列间距 3px |
| 义项行 `.zd-def-row` | 横向 flex，`align-items: flex-start` |
| 序号 `.zd-def-no` | 朱砂 `#C93A2B`，字号 13，`line-height 1.75`，右距 4px |
| 正文 `.zd-def-t` | 字号 13（平板同），`line-height 1.75`，色 `#6b675c` |

**序号规则**：`defs.length > 1` 才显示 ①②，单条释义不加序号——单条还挂个①是多余装饰。序号用圆圈数字而非「1.」，贴近课本习惯。

**每字最多 2 条义项**，优先本课读音、优先本义。

**清洗规则**（`tools/build-defs.py` 的 `clean_seg`，顺序不能乱）：
1. 去条序号 `1.` **必须在**识别字母子项 `a）` 之前——原文是 `1.a）在`
2. 词头标记 `〔葫芦〕` **必须在**识别条首 `a.` 之前——原文是 `〔～璃〕a.一种…`
3. 例词在 `<span>` 或 `：` 之后，只留释义主干
4. 超过 32 字的整条义项优先跳过，但**第一条不跳**——词典第一条通常是本义，丢了会让「电」取到「触电」、「牛」取到「比喻固执」
5. 旧库兜底洗完还带 `【】〖〗`、拼音、方括号的一律不要——宁可不显示也不给孩子看乱码

**人工定稿**：`tools/def-override.json`，自动采词仍会错的字（极常用字词典释义最啰嗦、数据源缺读音）手写覆盖，进了该表不参与自动采词。

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
| < 600px | 全部手机（375 为基准） | 边距 12px，列表 **4 列**，主字 44px，卡片间距 8px |
| ≥ 600px | 平板（iPad 10.2" 竖屏 810 / 横屏 1080） | 边距 24px，列表 **4 列**，主字 72px，卡片间距 14px，弹窗限宽 520 |

**为什么平板也是 4 列**：810px 宽时 6 列会让 4 字课（低年级）空两格、8 字课（中高年级）断成 6+2，两种课都不整齐；4 列则 4 字满行、8 字两行满。原版 Web 的 `minmax(148px,1fr)` 在 810 宽算下来同样是 4 列。

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
| 详情页 | 底部弹层 | 居中弹层（限宽 560），内容不变 |
| 组词列表 | 竖排 | 2 列并排 |
| 集章册 | 3 列 | 6 列 |
| 听写核对 | 单列大按钮 | 2 列网格 |

---

### 9.6 断点实现方式（禁用 @media）

**不要用 `@media` 做断点。** 小程序 wxss 的媒体查询在部分机型/端上不生效（同一份规则在 H5 与真机上表现不一致，排查成本极高）。统一做法：

```js
measure() {
  let w = 375
  // #ifdef H5
  w = window.innerWidth || 375
  // #endif
  // #ifndef H5
  try { w = uni.getSystemInfoSync().windowWidth || 375 } catch (e) {}
  // #endif
  this.isPad = w >= 600
}
```

- 布局开关挂 class：`<view class="page" :class="{ pad: isPad }">`，平板样式写成 `.page.pad .xxx`。
- **列宽这类关键尺寸用内联 style**（`:style="cellStyle"`），优先级最高，不受任何层叠影响。
- `onReady` 里再调一次 `measure()`：首屏布局完成前的视口宽可能还是初始值；平板横竖屏切换靠 `wx.onWindowResize` 复测。
- 弹层尺寸同理：`zk-detail` 通过 `isPad` prop 切换 180/250 米字格与尺寸，不用媒体查询。

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
2. 「做一个字卡详情弹窗：**居中弹窗**（不要贴底，会被原生 tabBar 压住底栏），纸白 #FFFDF7、圆角 16、四周留白 16、阴影 0 24px 60px rgba(0,0,0,.3)、pop 动画（scale .94→1）。head：朱红 60px 楷体大字 + 四线三格拼音(md) + 金色喇叭圈 + 「部首 · 结构 · 课名」，右上角 30px 朱红圆形关闭钮。body 滚动：180px 米字格（十字 #D9C69A、对角 #EFE4C4）→ ‹上一字/下一字› → 组词金色胶囊 → 释义。foot 固定：学会啦 +1★（实心金）+ 加入生字本（描边）」
3. 「平板端复用同一个详情弹窗：#F6F1E5 列表背景（4 列字卡，主字 72px）+ 遮罩 rgba(46,38,24,.45)，弹窗居中限宽 520、圆角 20、米字格放大到 250、head 大字 72px。不要另做分栏布局」
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
9. 平板端禁止把手机布局等比放大，只允许"排更多列"或"弹层限宽居中"，不要为平板单独设计第二套布局
10. 交付前对一遍安全区与 44px 热区
