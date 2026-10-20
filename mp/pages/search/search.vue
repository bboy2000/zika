<template>
  <view class="page-wrap">
    <view class="hero">
      <view class="page-title">搜索</view>
      <view class="page-sub">按汉字、拼音、词语检索全部 12 册</view>
    </view>

    <view class="search-box">
      <input
        class="search-input"
        v-model="q"
        placeholder="输入汉字或拼音"
        confirm-type="search"
        placeholder-class="ph"
      />
    </view>

    <view class="panel">
      <view class="placeholder">
        搜索结果占位\nP7 阶段接入全库搜索（只匹配字本身）
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return { q: '' }
  }
}
</script>

<style>
.hero {
  padding: 8rpx 0 4rpx;
}
.search-box {
  margin-top: 24rpx;
  background: #FFFFFF;
  border-radius: 999rpx;
  padding: 0 32rpx;
  height: 88rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 2rpx 12rpx rgba(120, 100, 80, 0.06);
}
.search-input {
  flex: 1;
  font-size: 28rpx;
}
.ph {
  color: #B5AEA2;
}
</style>
