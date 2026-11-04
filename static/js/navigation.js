(() => {
  'use strict';

  function initializeNavigation(document, window) {
    const openers = document.querySelectorAll('[data-open-dialog]');
    const closers = document.querySelectorAll('[data-close-dialog]');
    const dialogs = document.querySelectorAll('#mobile-menu, #notifications-panel');

    openers.forEach(button => {
      const dialog = document.getElementById(button.dataset.openDialog);
      if (!dialog) return;
      button.addEventListener('click', () => {
        dialogs.forEach(other => { if (other !== dialog && other.open) other.close(); });
        if (!dialog.open) dialog.showModal();
        button.setAttribute('aria-expanded', 'true');
      });
    });
    closers.forEach(button => {
      const dialog = document.getElementById(button.dataset.closeDialog);
      if (dialog) button.addEventListener('click', () => dialog.close());
    });
    dialogs.forEach(dialog => {
      dialog.addEventListener('close', () => {
        openers.forEach(button => {
          if (button.dataset.openDialog === dialog.id) button.setAttribute('aria-expanded', 'false');
        });
      });
      // El diálogo nativo gestiona Escape, el foco inicial y su restauración.
      dialog.addEventListener('click', event => {
        if (event.target !== dialog) return;
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right ||
            event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
      });
      dialog.querySelectorAll('a[href]').forEach(link => {
        link.addEventListener('click', () => dialog.close());
      });
    });

    const desktop = window.matchMedia('(min-width: 1024px)');
    desktop.addEventListener('change', event => {
      const mobileMenu = document.getElementById('mobile-menu');
      if (event.matches && mobileMenu?.open) mobileMenu.close();
    });

    if (new URLSearchParams(window.location.search).get('action') === 'new' &&
        typeof window.openAppointmentModal === 'function') {
      window.openAppointmentModal();
    }
  }

  function startNavigation(document, window) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => initializeNavigation(document, window), {once: true});
    } else {
      initializeNavigation(document, window);
    }
  }
  if (typeof module !== 'undefined') {
    module.exports = {startNavigation};
  }
  if (typeof document !== 'undefined') {
    startNavigation(document, window);
  }
})();
