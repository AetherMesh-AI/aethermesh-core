function isDestroyedElectronObject(value) {
  return Boolean(value && typeof value.isDestroyed === 'function' && value.isDestroyed());
}

function isDestroyedError(error) {
  return /object has been destroyed/i.test(error?.message || '');
}

function sendWindowState(window, channel, state) {
  if (!window || isDestroyedElectronObject(window)) {
    return false;
  }

  try {
    const { webContents } = window;
    if (!webContents || isDestroyedElectronObject(webContents) || typeof webContents.send !== 'function') {
      return false;
    }

    webContents.send(channel, state);
    return true;
  } catch (error) {
    if (isDestroyedError(error)) {
      return false;
    }
    throw error;
  }
}

module.exports = { isDestroyedElectronObject, sendWindowState };
