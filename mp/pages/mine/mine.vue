<template>
  <view class="page-wrap">
    <view class="hero">
      <view class="page-title">我的</view>
      <view class="page-sub">账号与设置</view>
    </view>

    <view class="panel">
      <view class="cell" @click="toast('P6 阶段接入微信登录')">
        <text>微信登录</text>
        <text class="cell-arrow">›</text>
      </view>
      <view class="cell" @click="toast('P5 阶段接入练习本')">
        <text>练习本</text>
        <text class="cell-arrow">›</text>
      </view>
      <view class="cell" @click="toast('P4 阶段接入练字课程入口')">
        <text>练字课程</text>
        <text class="cell-arrow">›</text>
      </view>
      <view class="cell no-line">
        <text>版本</text>
        <text class="cell-value">{{ version }}</text>
      </view>
    </view>

    <view class="version-line">数据：统编版 2026 秋 1-6 年级《写字表》</view>
  </view>
</template>

<script>
import { APP_VERSION } from '@/common/version.js'

export default {
  data() {
    return { version: APP_VERSION }
  },
  methods: {
    toast(t) {
      uni.showToast({ title: t, icon: 'none' })
    }
  }
}
</script>

<style>
.hero {
  padding: 8rpx 0 4rpx;
}
.cell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 0;
  border-bottom: 1rpx solid #EDE6DA;
  font-size: 28rpx;
}
.no-line {
  border-bottom: none;
}
.cell-arrow {
  color: #C4BDB0;
  font-size: 32rpx;
}
.cell-value {
  color: #8A8378;
}
</style>
