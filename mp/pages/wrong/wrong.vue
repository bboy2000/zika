<template>
  <view class="page-wrap">
    <view class="hero">
      <view class="page-title">生字本</view>
      <view class="page-sub">收录不会的字，登录后可跨设备同步</view>
    </view>

    <view class="panel">
      <view class="empty">
        <view class="empty-icon">＋</view>
        <view class="empty-text">生字本还是空的</view>
        <view class="empty-sub">在字卡详情里点「加入生字本」</view>
      </view>
    </view>

    <view class="panel">
      <view class="placeholder">
        一键生成练习纸占位\nP5 练习本阶段接入
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {}
  }
}
</script>

<style>
.hero {
  padding: 8rpx 0 4rpx;
}
.empty {
  padding: 40rpx 0;
  text-align: center;
}
.empty-icon {
  width: 96rpx;
  height: 96rpx;
  line-height: 92rpx;
  margin: 0 auto 20rpx;
  border-radius: 50%;
  background: #FBE7E3;
  color: #D94F3D;
  font-size: 48rpx;
  font-weight: 300;
}
.empty-text {
  font-size: 30rpx;
  font-weight: 600;
}
.empty-sub {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #8A8378;
}
</style>
