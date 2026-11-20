(() => {
  const config = document.getElementById('session-idle');
  if (!config) return;

  const csrf = config.querySelector('[name="csrfmiddlewaretoken"]').value;
  const activityInterval = 60_000;
  let deadline = Date.now() + Number(config.dataset.remaining) * 1000;
  let lastUpdate = Date.now();
  let timer;
  let pendingActivity = false;
  let checking = false;

  function schedule() {
    clearTimeout(timer);
    if (document.hidden) return;
    const nextEvent = pendingActivity ? Math.min(deadline, lastUpdate + activityInterval) : deadline;
    timer = window.setTimeout(() => check(pendingActivity), Math.max(0, nextEvent - Date.now()));
  }

  async function check(recordActivity) {
    if (checking || document.hidden) return;
    checking = true;
    if (recordActivity) pendingActivity = false;
    try {
      const response = await fetch(config.dataset.activityUrl, {
        method: recordActivity ? 'POST' : 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
        headers: recordActivity ? { 'X-CSRFToken': csrf } : {},
      });
      if (response.status === 401) {
        window.location.replace(config.dataset.loginUrl);
        return;
      }
      if (!response.ok) throw new Error('Session check failed');
      const { remaining_seconds: seconds } = await response.json();
      deadline = Date.now() + seconds * 1000;
      if (recordActivity) lastUpdate = Date.now();
      schedule();
    } catch {
      if (recordActivity) pendingActivity = true;
      timer = window.setTimeout(() => check(pendingActivity), 10_000);
    } finally {
      checking = false;
    }
  }

  function onActivity(event) {
    if (!event.isTrusted || document.hidden) return;
    pendingActivity = true;
    if (!checking && Date.now() - lastUpdate >= activityInterval) {
      void check(true);
    } else {
      schedule();
    }
  }

  for (const type of ['pointerdown', 'keydown', 'scroll']) {
    document.addEventListener(type, onActivity, { passive: true });
  }
  document.addEventListener('visibilitychange', () => {
    clearTimeout(timer);
    if (document.hidden) {
      if (pendingActivity) {
        // Preserve the last interaction, but never count time spent in the background.
        void fetch(config.dataset.activityUrl, {
          method: 'POST', credentials: 'same-origin', keepalive: true,
          headers: { 'X-CSRFToken': csrf },
        }).catch(() => {});
      }
      pendingActivity = false;
    } else {
      void check(false);
    }
  });
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) void check(false);
  });
  schedule();
})();
