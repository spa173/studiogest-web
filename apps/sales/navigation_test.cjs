const assert = require('node:assert/strict');
const test = require('node:test');
const {startNavigation} = require('../../static/js/navigation.js');

function button(dialogId, close = false) {
  return {dataset: close ? {closeDialog: dialogId} : {openDialog: dialogId},
    attributes: {'aria-expanded': 'false'}, events: {},
    addEventListener(event, handler) { this.events[event] = handler; },
    setAttribute(name, value) { this.attributes[name] = value; }};
}

function setup({search = '', appointmentPage = false, readyState = 'complete', withPanels = true} = {}) {
  const listeners = {}, ready = {}, media = {};
  let modalCalls = 0;
  const elements = {};
  const openers = [], closers = [], dialogs = [];
  if (withPanels) {
    for (const id of ['mobile-menu', 'notifications-panel']) {
      const link = {addEventListener: (event, handler) => { listeners[id + '-link-' + event] = handler; }};
      const dialog = {id, open: false, events: {},
        addEventListener(event, handler) { this.events[event] = handler; },
        showModal() { this.open = true; },
        close() { this.open = false; this.events.close(); },
        getBoundingClientRect: () => ({left: 10, top: 10, right: 200, bottom: 200}),
        querySelectorAll: () => [link]};
      elements[id] = dialog;
      dialogs.push(dialog);
      openers.push(button(id));
      closers.push(button(id, true));
    }
  }
  const document = {readyState,
    addEventListener: (event, handler) => { ready[event] = handler; },
    querySelectorAll(selector) {
      const groups = {'[data-open-dialog]': openers, '[data-close-dialog]': closers};
      return groups[selector] ?? dialogs;
    },
    getElementById: id => elements[id]};
  const window = {location: {search}, matchMedia: () => ({addEventListener: (event, handler) => { media[event] = handler; }})};
  if (appointmentPage) window.openAppointmentModal = () => { modalCalls++; };
  startNavigation(document, window);
  return {elements, openers, closers, listeners, media, ready, modalCalls: () => modalCalls};
}

test('abre y cierra el menú móvil actualizando aria-expanded', () => {
  const state = setup();
  state.openers[0].events.click();
  assert.equal(state.elements['mobile-menu'].open, true);
  assert.equal(state.openers[0].attributes['aria-expanded'], 'true');
  state.closers[0].events.click();
  assert.equal(state.elements['mobile-menu'].open, false);
  assert.equal(state.openers[0].attributes['aria-expanded'], 'false');
});
test('notificaciones cierra el otro panel y permite cerrar con el fondo', () => {
  const state = setup();
  state.openers[0].events.click();
  state.openers[1].events.click();
  assert.equal(state.elements['mobile-menu'].open, false);
  const dialog = state.elements['notifications-panel'];
  assert.equal(dialog.open, true);
  dialog.events.click({target: dialog, clientX: 100, clientY: 100});
  assert.equal(dialog.open, true);
  dialog.events.click({target: dialog, clientX: 0, clientY: 0});
  assert.equal(dialog.open, false);
  assert.equal(state.openers[1].attributes['aria-expanded'], 'false');
});
test('los enlaces y el cambio a escritorio cierran el menú', () => {
  const state = setup();
  state.openers[0].events.click();
  state.listeners['mobile-menu-link-click']();
  assert.equal(state.elements['mobile-menu'].open, false);
  state.openers[0].events.click();
  state.media.change({matches: true});
  assert.equal(state.elements['mobile-menu'].open, false);
});
test('action=new abre el modal existente de Agenda una sola vez', () => {
  const state = setup({search: '?date=2026-11-02&action=new', appointmentPage: true});
  assert.equal(state.modalCalls(), 1);
});
test('no abre citas sin action=new ni falla en otras pantallas', () => {
  assert.equal(setup({search: '?action=other', appointmentPage: true}).modalCalls(), 0);
  assert.equal(setup({search: '?action=new'}).modalCalls(), 0);
  assert.equal(setup({withPanels: false}).modalCalls(), 0);
});
test('espera al DOM cuando el script todavía se está cargando', () => {
  const state = setup({readyState: 'loading', search: '?action=new', appointmentPage: true});
  assert.equal(state.modalCalls(), 0);
  state.ready.DOMContentLoaded();
  assert.equal(state.modalCalls(), 1);
});
