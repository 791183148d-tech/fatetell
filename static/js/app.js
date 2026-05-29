/**
 * FateTell UI - Production-ready component interactions.
 * Accessible, modular, progressively enhanced.
 */
(function () {
  'use strict';

  /* ── Utilities ──────────────────────────────────────────────────── */
  const $ = (s, ctx) => (ctx || document).querySelector(s);
  const $$ = (s, ctx) => Array.from((ctx || document).querySelectorAll(s));

  function emit(name, detail) {
    document.dispatchEvent(new CustomEvent(name, { detail }));
  }

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Focus Management ────────────────────────────────────────────── */
  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function trapFocus(container) {
    const focusable = $$(FOCUSABLE, container).filter(function (el) { return el.offsetParent !== null; });
    if (!focusable.length) return;
    var firstFocus = focusable[0];
    var lastFocus = focusable[focusable.length - 1];
    firstFocus.focus();

    function handler(e) {
      if (e.key !== 'Tab') return;
      if (e.shiftKey) {
        if (document.activeElement === firstFocus) {
          e.preventDefault();
          lastFocus.focus();
        }
      } else {
        if (document.activeElement === lastFocus) {
          e.preventDefault();
          firstFocus.focus();
        }
      }
    }
    container.addEventListener('keydown', handler);
    // Return cleanup
    return function () { container.removeEventListener('keydown', handler); };
  }

  function getScrollbarWidth() {
    return window.innerWidth - document.documentElement.clientWidth;
  }

  /* ── Modal Manager ──────────────────────────────────────────────── */
  function initModal() {
    var stack = [];

    function open(id) {
      var el = document.getElementById(id);
      if (!el) return;
      var previousActive = document.activeElement;
      var cleanup = trapFocus(el);
      var scrollbarWidth = getScrollbarWidth();

      el.classList.add('is-open');
      el.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
      document.body.style.paddingRight = scrollbarWidth + 'px';

      emit('ft:modal-open', { id: id });

      stack.push({ id: id, el: el, cleanup: cleanup, previousActive: previousActive });
    }

    function close(id) {
      var item;
      if (id) {
        var idx = stack.map(function (s) { return s.id; }).lastIndexOf(id);
        if (idx === -1) return;
        item = stack.splice(idx, 1)[0];
      } else {
        item = stack.pop();
      }
      if (!item) return;
      item.el.classList.remove('is-open');
      item.el.setAttribute('hidden', '');
      if (item.cleanup) item.cleanup();
      if (item.previousActive) item.previousActive.focus();

      if (stack.length === 0) {
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
      }
      emit('ft:modal-close', { id: item.id });
    }

    function closeAll() {
      while (stack.length) close();
    }

    // Click on backdrop or [data-modal-close]
    document.addEventListener('click', function (e) {
      var closeBtn = e.target.closest('[data-modal-close]');
      if (closeBtn) {
        var modal = closeBtn.closest('.ft-modal');
        if (modal) close(modal.id);
      }
    });

    // Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && stack.length) {
        e.preventDefault();
        close();
      }
    });

    // [data-modal-open] triggers
    document.addEventListener('click', function (e) {
      var trigger = e.target.closest('[data-modal-open]');
      if (trigger) {
        e.preventDefault();
        open(trigger.getAttribute('data-modal-open'));
      }
    });

    // Store closeAll for external use
    window.__ftModalCloseAll = closeAll;
  }

  /* ── Toast / Notification System ────────────────────────────────── */
  function initToast() {
    var container = document.getElementById('ft-toast-container');
    if (!container) return;

    var icons = {
      error: '⚠️',
      success: '✔️',
      info: 'ℹ️',
      warning: '⚠️'
    };
    var defaults = { type: 'info', duration: 4000 };

    function show(opts) {
      if (typeof opts === 'string') opts = { message: opts };
      opts = Object.assign({}, defaults, opts);
      var toast = document.createElement('div');
      toast.className = 'ft-toast ft-toast--' + opts.type;
      toast.setAttribute('role', 'alert');
      toast.innerHTML =
        '<span class="ft-toast__icon" aria-hidden="true">' + (icons[opts.type] || '') + '</span>' +
        '<span class="ft-toast__msg">' + opts.message.replace(/</g, '&lt;') + '</span>' +
        '<button class="ft-toast__dismiss" aria-label="Dismiss">&times;</button>';

      var dismissBtn = toast.querySelector('.ft-toast__dismiss');
      dismissBtn.addEventListener('click', function () { dismiss(toast); });

      container.appendChild(toast);

      if (opts.duration > 0 && !prefersReducedMotion) {
        setTimeout(function () { dismiss(toast); }, opts.duration);
      }

      emit('ft:toast-show', opts);
      return toast;
    }

    function dismiss(toast) {
      if (!toast || !toast.parentNode) return;
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      toast.style.transition = 'opacity 0.2s, transform 0.2s';
      setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 200);
    }

    // Listen for custom events
    document.addEventListener('ft-toast', function (e) { show(e.detail); });
    document.addEventListener('ft:toast', function (e) { show(e.detail); });

    window.__ftToast = show;
  }

  /* ── Tooltip handler (keyboard-friendly) ────────────────────────── */
  function initTooltip() {
    $$('[data-tooltip]').forEach(function (el) {
      // On mobile, show on focus as well as hover
      if (!el.getAttribute('tabindex') && el.nodeName !== 'INPUT' && el.nodeName !== 'BUTTON' && el.nodeName !== 'A') {
        el.setAttribute('tabindex', '0');
      }
    });
  }

  /* ── Mobile Nav ─────────────────────────────────────────────────── */
  function initNav() {
    var toggle = $('[data-nav-toggle]');
    var menu = $('[data-nav-menu]');
    if (!toggle || !menu) return;

    toggle.addEventListener('click', function () {
      var open = menu.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');

      if (open) {
        // Focus first link
        var firstLink = $('a', menu);
        if (firstLink) setTimeout(function () { firstLink.focus(); }, 50);
      } else {
        toggle.focus();
      }
    });

    $$('a', menu).forEach(function (link) {
      link.addEventListener('click', function () {
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.classList.contains('is-open')) {
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });

    // Close on click outside
    document.addEventListener('click', function (e) {
      if (menu.classList.contains('is-open') && !menu.contains(e.target) && e.target !== toggle) {
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ── FAQ Accordion ──────────────────────────────────────────────── */
  function initFAQ() {
    $$('.ft-faq__item').forEach(function (details) {
      details.addEventListener('toggle', function () {
        if (this.open) {
          var answer = this.querySelector('.ft-faq__answer');
          if (answer) answer.setAttribute('aria-live', 'polite');
        }
      });
    });
  }

  /* ── Payment Status Polling ──────────────────────────────────────── */
  function initPaymentPoll() {
    var el = $('[data-poll-url]');
    if (!el) return;
    var url = el.getAttribute('data-poll-url');
    var attempts = 0;
    var MAX = 90;

    function poll() {
      if (++attempts > MAX) {
        el.textContent = 'Taking longer than expected. You can refresh the page.';
        return;
      }
      fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.status === 'completed') {
            window.location.href = data.redirect;
          } else if (data.status === 'error') {
            var spinner = $('.ft-spinner');
            if (spinner) spinner.remove();
            el.textContent = 'Error generating report. Please contact support.';
            el.setAttribute('aria-live', 'assertive');
          } else {
            setTimeout(poll, 2000);
          }
        })
        .catch(function () { setTimeout(poll, 3000); });
    }
    poll();
  }

  /* ── Form Validation (enhanced) ─────────────────────────────────── */
  function initFormValidation() {
    $$('form[data-validate]').forEach(function (form) {
      var debounceTimers = {};

      // Real-time validation with debounce
      $$('[required]', form).forEach(function (field) {
        field.addEventListener('input', function () {
          var name = this.name || 'field';
          if (debounceTimers[name]) clearTimeout(debounceTimers[name]);
          debounceTimers[name] = setTimeout(function () {
            validateField(field);
          }, 300);
        });

        field.addEventListener('blur', function () {
          validateField(field);
        });
      });

      form.addEventListener('submit', function (e) {
        var valid = true;
        var firstInvalid = null;

        $$('[required]', form).forEach(function (field) {
          if (!validateField(field)) {
            valid = false;
            if (!firstInvalid) firstInvalid = field;
          }
        });

        if (!valid) {
          e.preventDefault();
          if (firstInvalid) {
            firstInvalid.focus();
            firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }
      });
    });

    function validateField(field) {
      if (!field.value || !field.value.trim()) {
        field.classList.add('ft-input--error');
        field.setAttribute('aria-invalid', 'true');
        showError(field, 'This field is required');
        return false;
      }

      // Pattern validation
      if (field.getAttribute('pattern') && field.value) {
        var regex = new RegExp(field.getAttribute('pattern'));
        if (!regex.test(field.value)) {
          field.classList.add('ft-input--error');
          field.setAttribute('aria-invalid', 'true');
          showError(field, field.getAttribute('data-err-pattern') || 'Invalid format');
          return false;
        }
      }

      // Email validation
      if (field.type === 'email' && field.value) {
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value)) {
          field.classList.add('ft-input--error');
          field.setAttribute('aria-invalid', 'true');
          showError(field, 'Please enter a valid email address');
          return false;
        }
      }

      field.classList.remove('ft-input--error');
      field.setAttribute('aria-invalid', 'false');
      clearError(field);
      return true;
    }

    function showError(field, msg) {
      var group = field.closest('.ft-form-group');
      if (!group) return;
      var err = group.querySelector('.ft-form-error');
      if (!err) {
        err = document.createElement('p');
        err.className = 'ft-form-error';
        err.setAttribute('role', 'alert');
        group.appendChild(err);
      }
      err.textContent = '⚠ ' + msg;
    }

    function clearError(field) {
      var group = field.closest('.ft-form-group');
      if (!group) return;
      var err = group.querySelector('.ft-form-error');
      if (err) err.remove();
    }
  }

  /* ── Network Status ─────────────────────────────────────────────── */
  function initNetworkStatus() {
    function handler() {
      if (!navigator.onLine) {
        // Show a floating toast
        var toast = window.__ftToast;
        if (toast) {
          toast({ message: 'No internet connection. Some features may be unavailable.', type: 'warning', duration: 0 });
        }
      }
    }
    window.addEventListener('offline', handler);
    window.addEventListener('online', function () {
      emit('ft:online');
    });
  }

  /* ── Smooth Scroll ──────────────────────────────────────────────── */
  function initSmoothScroll() {
    $$('a[href^="#"]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        var id = this.getAttribute('href').slice(1);
        var target = document.getElementById(id);
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        target.focus({ preventScroll: true });
      });
    });
  }

  /* ── Init on DOM ready ──────────────────────────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initNav();
      initFAQ();
      initModal();
      initToast();
      initTooltip();
      initPaymentPoll();
      initFormValidation();
      initNetworkStatus();
      initSmoothScroll();
    });
  } else {
    initNav();
    initFAQ();
    initModal();
    initToast();
    initTooltip();
    initPaymentPoll();
    initFormValidation();
    initNetworkStatus();
    initSmoothScroll();
  }
})();
