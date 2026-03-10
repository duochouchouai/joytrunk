/**
 * 主窗口入口：检测 electronAPI，初始化标题栏/侧栏/弹窗/分隔条/下拉，并调用 chat、agents 模块。
 * 依赖：js/utils.js、js/chat.js、js/agents.js（按顺序加载）。
 */
(function () {
  var api = window.electronAPI;
  if (!api) {
    document.body.innerHTML = '<div style="padding:20px;font-family:system-ui;color:#c00;">未检测到 electronAPI，请从 <b>ui</b> 目录运行 <code>npm run start</code>。</div>';
    return;
  }

  var mainContent = document.querySelector('.main-content');

  // 标题栏 logo
  (function () {
    var logoEl = document.getElementById('titleBarLogo');
    var url = api.getLogoUrl && api.getLogoUrl();
    if (logoEl && url) {
      logoEl.src = url;
      logoEl.style.display = '';
    }
    var bgUrl = api.getLogoBgUrl && api.getLogoBgUrl();
    if (bgUrl) {
      var chatDetail = document.querySelector('.chat-detail');
      if (chatDetail) chatDetail.style.setProperty('--logo-bg-url', 'url(' + bgUrl + ')');
    }
  })();

  document.getElementById('btnMinimize').addEventListener('click', function () { api.minimizeWindow(); });
  document.getElementById('btnClose').addEventListener('click', function () { api.closeWindow(); });

  var historyBtn = document.getElementById('chatDetailHistoryBtn');
  if (historyBtn) historyBtn.addEventListener('click', function () { /* TODO: 查看记忆 */ });

  var settingsBtn = document.getElementById('chatDetailSettingsBtn');
  var nameWrap = document.getElementById('chatDetailNameWrap');
  if (settingsBtn && nameWrap) {
    settingsBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var agentId = nameWrap.dataset.agentId;
      if (!agentId) return;
      /* TODO: 打开该 agent 设置 */
    });
  }

  // 聊天列表 + 号下拉：展开/收起
  var addBtn = document.getElementById('chatSearchAddBtn');
  var dropdown = document.getElementById('chatSearchDropdown');
  if (addBtn && dropdown) {
    addBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = dropdown.classList.toggle('open');
      addBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    dropdown.querySelectorAll('.chat-list-search-dropdown-item').forEach(function (item) {
      item.addEventListener('click', function () {
        dropdown.classList.remove('open');
        addBtn.setAttribute('aria-expanded', 'false');
      });
    });
    document.addEventListener('click', function () {
      dropdown.classList.remove('open');
      addBtn.setAttribute('aria-expanded', 'false');
    });
  }

  // 左侧菜单切换
  document.querySelectorAll('.sidebar-item').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var panel = btn.getAttribute('data-panel');
      if (!panel || !mainContent) return;
      mainContent.setAttribute('data-panel', panel);
      document.querySelectorAll('.sidebar-item').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
    });
  });

  // 左侧用户：未绑定弹窗 / 已绑定浮层
  (function () {
    var sidebarUser = document.querySelector('.sidebar-user');
    var modalOverlay = document.getElementById('userModalOverlay');
    var modalConfirm = document.getElementById('userModalConfirm');
    var popover = document.getElementById('userPopover');
    var popoverName = document.getElementById('userPopoverName');
    var popoverMeta = document.getElementById('userPopoverMeta');
    var popoverLogout = document.getElementById('userPopoverLogout');
    var sidebarUserName = document.getElementById('sidebarUserName');
    var userBound = false;
    var boundUserInfo = { name: '张三', account: 'zhangsan@example.com', avatar: '👤' };

    if (!sidebarUser || !modalOverlay) return;

    function showModal() { modalOverlay.style.display = 'flex'; }
    function hideModal() { modalOverlay.style.display = 'none'; }
    function showPopover() {
      if (popoverName) popoverName.textContent = boundUserInfo.name;
      if (popoverMeta) popoverMeta.textContent = boundUserInfo.account || '已绑定';
      if (sidebarUserName) sidebarUserName.textContent = boundUserInfo.name;
      if (popover) popover.style.display = 'block';
    }
    function hidePopover() { if (popover) popover.style.display = 'none'; }

    sidebarUser.addEventListener('click', function (e) {
      e.preventDefault();
      if (userBound) { hidePopover(); showPopover(); } else { showModal(); }
    });
    if (modalConfirm) modalConfirm.addEventListener('click', hideModal);
    modalOverlay.addEventListener('click', function (e) {
      if (e.target === modalOverlay) hideModal();
    });
    if (popoverLogout) {
      popoverLogout.addEventListener('click', function () {
        userBound = false;
        if (sidebarUserName) sidebarUserName.textContent = '我';
        hidePopover();
      });
    }
    document.addEventListener('click', function (e) {
      if (popover && popover.style.display === 'block' && !popover.contains(e.target) && !sidebarUser.contains(e.target)) hidePopover();
    });
  })();

  // 聊天列表与详情之间的分隔条
  (function () {
    var chatList = document.querySelector('.chat-list');
    var resizer = document.getElementById('chatResizer');
    if (!chatList || !resizer || !mainContent) return;
    var minW = 120;
    var maxW = 480;
    resizer.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      var startX = e.clientX;
      var startW = parseFloat(window.getComputedStyle(chatList).width) || 260;
      resizer.classList.add('dragging');
      function onMove(ev) {
        var dx = ev.clientX - startX;
        var w = Math.max(minW, Math.min(maxW, Math.round(startW + dx)));
        mainContent.style.setProperty('--chat-list-width', w + 'px');
      }
      function onUp() {
        resizer.classList.remove('dragging');
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      }
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
  })();

  if (window.MainWindowChat && window.MainWindowChat.init) window.MainWindowChat.init(api);
  if (window.MainWindowAgents && window.MainWindowAgents.init) window.MainWindowAgents.init(api);
})();
