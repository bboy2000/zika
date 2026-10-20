<script>
export default {
  onLaunch() {
    // P6 起在此初始化云开发：wx.cloud.init({ env: 'xxx' })
  },
  onShow() {},
  onHide() {}
}
</script>

<style>
/* 全局基础样式 */
page {
  background-color: #FDF9F3;
  color: #2B2B2B;
  font-family: -apple-system, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
  font-size: 28rpx;
  line-height: 1.6;
}

.page-wrap {
  padding: 24rpx 24rpx 40rpx;
  box-sizing: border-box;
}

.page-title {
  font-size: 40rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

.page-sub {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #8A8378;
}

.panel {
  margin-top: 24rpx;
  background: #FFFFFF;
  border-radius: 20rpx;
  padding: 32rpx;
  box-shadow: 0 2rpx 12rpx rgba(120, 100, 80, 0.06);
}

.placeholder {
  padding: 60rpx 0;
  text-align: center;
  color: #A9A296;
  font-size: 26rpx;
}

.version-line {
  margin-top: 40rpx;
  text-align: center;
  font-size: 22rpx;
  color: #B5AEA2;
}
</style>
