(function () {
  /* ─────────────────────────────────────────────
     Rebrand: replace any "Chainlit" text node with "NexusRAG"
  ───────────────────────────────────────────── */
  function rebrandTextNodes(root) {
    var walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT, null);
    var node;
    while ((node = walker.nextNode())) {
      if (node.nodeValue && /chainlit/i.test(node.nodeValue)) {
        node.nodeValue = node.nodeValue.replace(/Chainlit/g, 'NexusRAG').replace(/chainlit/g, 'NexusRAG');
      }
    }
    // Rebrand title attribute, aria-label, alt
    ['title', 'aria-label', 'alt'].forEach(function (attr) {
      document.querySelectorAll('[' + attr + '*="hainlit"]').forEach(function (el) {
        var v = el.getAttribute(attr);
        if (v) el.setAttribute(attr, v.replace(/Chainlit/g, 'NexusRAG').replace(/chainlit/g, 'NexusRAG'));
      });
    });
    // Also force document title
    if (document.title && /chainlit/i.test(document.title)) {
      document.title = document.title.replace(/Chainlit/g, 'NexusRAG').replace(/chainlit/g, 'NexusRAG');
    }
  }

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
     Detect login page (no chat input present) and enhance it
  ───────────────────────────────────────────── */
  function isLoginPage() {
    return !!document.querySelector('form') &&
           !document.querySelector('textarea[data-testid="messageInput"]') &&
           !document.querySelector('textarea[placeholder]');
  }

  function injectBrandHeader(form) {
    if (document.getElementById('nx-brand')) return;
    var brand = document.createElement('div');
    brand.id = 'nx-brand';
    brand.innerHTML =
      '<div class="nx-logo">' +
        '<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="NexusRAG">' +
          '<defs>' +
            '<linearGradient id="nxg" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">' +
              '<stop offset="0" stop-color="#fecaca"/>' +
              '<stop offset="1" stop-color="#ffffff"/>' +
            '</linearGradient>' +
          '</defs>' +
          '<circle cx="12" cy="12" r="3.2" fill="url(#nxg)"/>' +
          '<circle cx="36" cy="12" r="3.2" fill="url(#nxg)"/>' +
          '<circle cx="24" cy="24" r="4.2" fill="url(#nxg)"/>' +
          '<circle cx="12" cy="36" r="3.2" fill="url(#nxg)"/>' +
          '<circle cx="36" cy="36" r="3.2" fill="url(#nxg)"/>' +
          '<path d="M12 12 L24 24 L36 12 M12 36 L24 24 L36 36 M24 24 L12 12 M24 24 L12 36" ' +
            'stroke="url(#nxg)" stroke-width="1.6" stroke-linecap="round" opacity="0.85"/>' +
        '</svg>' +
      '</div>' +
      '<h1 class="nx-title">Nexus<span class="nx-gradient">RAG</span></h1>' +
      '<p class="nx-sub">Enterprise Intelligence Platform</p>';
    form.insertBefore(brand, form.firstChild);
  }

  function injectFooter(form) {
    if (document.getElementById('nx-footer')) return;
    var foot = document.createElement('div');
    foot.id = 'nx-footer';
    foot.innerHTML =
      '<span class="nx-badge">Qwen 2.5</span>' +
      '<span class="nx-badge">ChromaDB</span>' +
      '<span class="nx-badge">RBAC</span>';
    form.appendChild(foot);
  }

  /* Aggressively kill Chainlit branding on login: top-left logo + right-side image
     This uses inline styles + !important to beat Chainlit's CSS-in-JS specificity. */
  function nukeChainlitBranding() {
    if (!document.body.classList.contains('nx-login')) return;

    // 1. Hide ALL imgs and standalone svgs that aren't part of our injected UI
    document.querySelectorAll('img, svg').forEach(function (el) {
      if (el.closest('#nx-brand') || el.closest('#rag-quick-login') ||
          el.closest('#nx-footer') || el.closest('button[type="submit"]')) return;
      el.style.setProperty('display', 'none', 'important');
    });

    // 2. Hide top-left clickable home links
    document.querySelectorAll('a').forEach(function (a) {
      var href = a.getAttribute('href') || '';
      if (href === '/' || /chainlit/i.test(href)) {
        a.style.setProperty('display', 'none', 'important');
      }
    });

    // 3. Walk up from the form: hide every sibling that doesn't contain it,
    //    so the right-side image column disappears and the form takes full width.
    var form = document.querySelector('form');
    if (!form) return;
    var node = form;
    while (node.parentElement && node.parentElement !== document.body) {
      var parent = node.parentElement;
      Array.from(parent.children).forEach(function (child) {
        if (child !== node && !child.contains(form)) {
          child.style.setProperty('display', 'none', 'important');
        }
      });
      // Make each ancestor a full-width centered flex container
      parent.style.setProperty('display', 'flex', 'important');
      parent.style.setProperty('justify-content', 'center', 'important');
      parent.style.setProperty('align-items', 'center', 'important');
      parent.style.setProperty('width', '100%', 'important');
      parent.style.setProperty('min-height', '100vh', 'important');
      parent.style.setProperty('background', 'transparent', 'important');
      node = parent;
    }
  }

  function injectLogin() {
    if (!isLoginPage()) {
      document.body.classList.remove('nx-login');
      return;
    }
    document.body.classList.add('nx-login');

    var form = document.querySelector('form');
    if (!form) return;

    injectBrandHeader(form);

    if (!document.getElementById('rag-quick-login')) {
      var wrap = document.createElement('div');
      wrap.id  = 'rag-quick-login';

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
        btn.style.cssText = '--rgb:' + hexToRgb(u.hex) + ';';
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

    injectFooter(form);
  }


  function tick() {
    injectLogin();
    nukeChainlitBranding();
    rebrandTextNodes();
  }

  var obs = new MutationObserver(tick);
  function startObs() { obs.observe(document.body, { childList: true, subtree: true }); }

  if (document.body) startObs();
  document.addEventListener('DOMContentLoaded', function () { startObs(); tick(); });
  [400, 1200, 2500].forEach(function (t) { setTimeout(tick, t); });
})();
