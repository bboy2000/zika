<template>
  <view class="pg" :class="size">
    <text class="pg-t">{{ text }}</text>
  </view>
</template>

<script>
/**
 * 四线三格拼音格（DESIGN.md 3.3，唯一正确实现）
 * 四条线 = 4 层 1px 纯色背景，位置写 px；格高取 3 的倍数（27/36/45）
 * 文字绝对不能有底色（否则盖出白圈）
 * 色值回归原版：线 #B8C8DC、字 #2B2F36（深墨，不是灰褐）
 */
export default {
  name: 'zk-py',
  props: {
    text: { type: String, default: '' },
    size: { type: String, default: 'sm' } // sm 列表 | md 详情 | lg 大字
  }
}
</script>

<style>
.pg {
  position: relative;
  display: inline-block;
  box-sizing: border-box;
  padding: 0 3px;
  overflow: hidden;
  vertical-align: middle;
  background-repeat: no-repeat;
  background-size: 100% 1px;
  background-image: linear-gradient(#b8c8dc, #b8c8dc), linear-gradient(#b8c8dc, #b8c8dc),
    linear-gradient(#b8c8dc, #b8c8dc), linear-gradient(#b8c8dc, #b8c8dc);
}
.pg-t {
  display: block;
  white-space: nowrap;
  text-align: center;
  color: #2b2f36;
  font-family: Arial, Helvetica, 'Helvetica Neue', sans-serif;
  font-weight: 500;
  letter-spacing: 0.2px;
}

/* 列表卡片：中格 9px，x-height 填满；基线按原版公式上抬 2px */
.pg.sm {
  height: 27px;
  min-width: 36px;
  background-position: 0 0, 0 9px, 0 18px, 0 26px;
}
.pg.sm .pg-t {
  font-size: 16px;
  line-height: 26px;
  position: relative;
  top: -2px;
}

/* 详情 / 搜索 */
.pg.md {
  height: 36px;
  min-width: 52px;
  background-position: 0 0, 0 12px, 0 24px, 0 35px;
}
.pg.md .pg-t {
  font-size: 21.5px;
  line-height: 34px;
  position: relative;
  top: -0.3px;
}

/* 大字场景 */
.pg.lg {
  height: 45px;
  min-width: 64px;
  background-position: 0 0, 0 15px, 0 30px, 0 44px;
}
.pg.lg .pg-t {
  font-size: 28px;
  line-height: 44px;
  position: relative;
  top: -1.4px;
}
</style>
