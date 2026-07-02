function shouldStopTemporaryNode(settings = {}) {
  return !settings.backgroundNodeEnabled && !settings.keepNodeRunningAfterClose;
}

function shouldLeaveBackgroundNodeRunning(settings = {}) {
  return Boolean(settings.backgroundNodeEnabled);
}

module.exports = { shouldLeaveBackgroundNodeRunning, shouldStopTemporaryNode };
