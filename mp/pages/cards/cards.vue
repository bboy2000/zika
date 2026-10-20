<template>
  <view class="page-wrap">
    <view class="hero">
      <view class="page-title">写字表字卡</view>
      <view class="page-sub">统编版 1-6 年级 · 12 册</view>
    </view>

    <view class="panel">
      <view class="row-between">
        <text class="label">当前册次</text>
        <text class="value">一年级上册</text>
      </view>
    </view>

    <view class="panel">
      <view class="placeholder">
        字卡列表占位\nP1 阶段接入 chars.json 拆册数据
      </view>
    </view>

    <view class="version-line">{{ $version }} · 骨架版</view>
  </view>
</template>

<script>
import { APP_VERSION } from '@/common/version.js'

export default {
  data() {
    return { version: APP_VERSION }
  }
}
</script>

<style>
.hero {
  padding: 8rpx 0 4rpx;
}
.row-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.label {
  font-size: 28rpx;
  color: #8A8378;
}
.value {
  font-size: 28rpx;
  font-weight: 600;
}
</style>
