(function () {
  /* ── Quick-login credentials ── */
  var USERS = [
    { username: 'alice', password: 'alice123', role: 'Admin',    emoji: '🔴', hex: '#ef4444' },
    { username: 'bob',   password: 'bob123',   role: 'HR Staff', emoji: '🟡', hex: '#f59e0b' },
    { username: 'carol', password: 'carol123', role: 'Finance',  emoji: '🟢', hex: '#10b981' },
    { username: 'dave',  password: 'dave123',  role: 'IT Ops',   emoji: '🔵', hex: '#3b82f6' },
    { username: 'eve',   password: 'eve123',   role: 'Employee', emoji: '⚪', hex: '#6b7280' },
  ];

  /* Simulate React controlled-input change */
  function setInputVal(input, value) {
    var proto = input instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
    var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    setter.call(input, value);
    input.dispatchEvent(new Event('input',  { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function hexToRgb(hex) {
    return parseInt(hex.slice(1,3),16)+','+parseInt(hex.slice(3,5),16)+','+parseInt(hex.slice(5,7),16);
  }

  /* ─────────────────────────────────────────────
     Sample-query buttons (inside chat messages)
     Clicking one fills the textarea and submits —
     so the query appears as a real user message.
  ───────────────────────────────────────────── */
  function findChatInput() {
    return document.querySelector('textarea[data-testid="messageInput"]') ||
           document.querySelector('textarea[placeholder]') ||
           document.querySelector('textarea');
  }

  function findSendButton(ta) {
    var form = ta && ta.closest('form');
    return (form && form.querySelector('button[type="submit"]')) ||
           document.querySelector('button[aria-label*="send" i]') ||
           document.querySelector('button[data-testid*="send" i]');
  }

  function sqFire(query) {
    var ta = findChatInput();
    if (!ta) return;
    setInputVal(ta, query);
    ta.focus();
    /* give React one tick to register the state change, then click Send */
    setTimeout(function () {
      var btn = findSendButton(ta);
      if (btn) {
        btn.click();
      } else {
        /* fallback: dispatch Enter key */
        ta.dispatchEvent(new KeyboardEvent('keydown', {
          key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
          bubbles: true, cancelable: true
        }));
      }
    }, 120);
  }

  /* Event delegation — works even for HTML injected after page load */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.sq-btn');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    var query = btn.getAttribute('data-query');
    if (query) sqFire(query);
  }, true);

  /* ─────────────────────────────────────────────
     Quick-login panel (login page only)
  ───────────────────────────────────────────── */
  function injectLogin() {
    if (document.getElementById('rag-quick-login')) return;
    var form = document.querySelector('form');
    if (!form) return;

    var wrap    = document.createElement('div');
    wrap.id     = 'rag-quick-login';

    var divider = document.createElement('div');
    divider.className = 'rag-divider';
    divider.innerHTML = '<span>⚡ Quick Login</span>';
    wrap.appendChild(divider);

    var hint = document.createElement('p');
    hint.className = 'rag-hint';
    hint.textContent = 'Password = username + "123"  (e.g. alice / alice123)';
    wrap.appendChild(hint);

    var grid = document.createElement('div');
    grid.className = 'rag-grid';

    USERS.forEach(function (u) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'rag-btn';
      btn.style.cssText = '--rgb:' + hexToRgb(u.hex) + ';' +
        'border-color:rgba(var(--rgb),0.35);background:rgba(var(--rgb),0.12);';
      btn.innerHTML =
        '<span class="rag-e">' + u.emoji + '</span>' +
        '<span class="rag-i"><strong>' + u.username + '</strong><small>' + u.role + '</small></span>';

      btn.addEventListener('click', function (ev) {
        ev.preventDefault();
        var inputs  = form.querySelectorAll('input');
        var userInp = form.querySelector('input[name="username"]') || inputs[0];
        var passInp = form.querySelector('input[type="password"]') ||
                      form.querySelector('input[name="password"]') || inputs[1];
        if (userInp) setInputVal(userInp, u.username);
        if (passInp) setInputVal(passInp, u.password);
        setTimeout(function () {
          var sub = form.querySelector('button[type="submit"]');
          if (sub) sub.click();
        }, 180);
      });
      grid.appendChild(btn);
    });

    wrap.appendChild(grid);
    form.appendChild(wrap);
  }

  var obs = new MutationObserver(injectLogin);
  function startObs() { obs.observe(document.body, { childList: true, subtree: true }); }

  if (document.body) startObs();
  document.addEventListener('DOMContentLoaded', function () { startObs(); injectLogin(); });
  [400, 1200, 2500].forEach(function (t) { setTimeout(injectLogin, t); });
})();
