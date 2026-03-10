/**
 * 主窗口聊天模块：员工列表、聊天详情、发送消息、新建员工。依赖 MainWindowUtils。
 * 使用方式：MainWindowChat.init(electronAPI)；electronAPI.serverAPI 为 server API。
 */
(function () {
  function init(electronAPI) {
    var api = electronAPI && electronAPI.serverAPI;
    if (!api) {
      var ph = document.getElementById('chatListPlaceholder');
      if (ph) ph.textContent = 'API 不可用';
      return;
    }
    var escapeHtml = window.MainWindowUtils && window.MainWindowUtils.escapeHtml || function (s) { return String(s == null ? '' : s); };
    var parseThinkReply = window.MainWindowUtils && window.MainWindowUtils.parseThinkReply || function (t) { return { thinking: '', content: String(t == null ? '' : t) }; };
    var formatMessageContent = window.MainWindowUtils && window.MainWindowUtils.formatMessageContent || function (s) { return escapeHtml(String(s == null ? '' : s)).replace(/\n/g, '<br>'); };
    var chatListBody = document.getElementById('chatListBody');
    var chatListPlaceholder = document.getElementById('chatListPlaceholder');
    var chatDetailBody = document.querySelector('.chat-detail-body');
    if (!chatListBody || !chatDetailBody) return;

    var employees = [];
    var activeEmployeeId = null;
    var connectionError = false;

    function setPlaceholder(msg) {
      if (chatListPlaceholder) {
        chatListPlaceholder.textContent = msg || '暂无会话，点击下方 + 新建员工';
        chatListPlaceholder.style.display = 'block';
      }
    }

    function loadOwnerAndEmployees() {
      connectionError = false;
      api.getOwnersMe().then(function (owner) {
        if (owner && owner.id) api.setOwnerId(owner.id);
      }).catch(function () {});
      return api.getEmployees().then(function (list) {
        employees = Array.isArray(list) ? list : [];
        renderChatList(activeEmployeeId);
        if (employees.length === 0) setPlaceholder('暂无员工，点击下方 + 新建');
        else if (!activeEmployeeId && employees[0]) selectEmployee(employees[0].id);
      }).catch(function (err) {
        connectionError = true;
        employees = [];
        setPlaceholder('无法连接服务，请确认 joytrunk server 已启动');
        if (chatListBody) {
          var existing = chatListBody.querySelectorAll('.chat-list-item');
          existing.forEach(function (el) { el.remove(); });
        }
      });
    }

    function renderChatList(activeId) {
      chatListPlaceholder.style.display = employees.length ? 'none' : 'block';
      var existing = chatListBody.querySelectorAll('.chat-list-item');
      existing.forEach(function (el) { el.remove(); });
      var fragment = document.createDocumentFragment();
      employees.forEach(function (emp) {
        var item = document.createElement('div');
        item.className = 'chat-list-item' + (emp.id === activeId ? ' active' : '');
        item.dataset.employeeId = emp.id;
        var name = (emp.name || '').trim() || ('员工 ' + emp.id);
        var preview = '点击查看';
        item.innerHTML =
          '<div class="chat-list-item-avatar">' + escapeHtml((name.charAt(0) || '?')) + '</div>' +
          '<div class="chat-list-item-main">' +
          '<div class="chat-list-item-title">' + escapeHtml(name) + '</div>' +
          '<div class="chat-list-item-meta">' +
          '<span class="chat-list-item-preview">' + escapeHtml(preview) + '</span>' +
          '</div></div>';
        fragment.appendChild(item);
      });
      chatListBody.insertBefore(fragment, chatListPlaceholder);
      chatListBody.querySelectorAll('.chat-list-item').forEach(function (el) {
        el.addEventListener('click', function () {
          var id = this.dataset.employeeId;
          if (id) selectEmployee(id);
        });
      });
    }

    function selectEmployee(id) {
      activeEmployeeId = id;
      chatListBody.querySelectorAll('.chat-list-item').forEach(function (i) {
        i.classList.toggle('active', i.dataset.employeeId === id);
      });
      loadChatDetail(id);
    }

    function getEmployeeById(id) {
      for (var i = 0; i < employees.length; i++) {
        if (employees[i].id === id) return employees[i];
      }
      return null;
    }

    function loadChatDetail(employeeId) {
      var emp = getEmployeeById(employeeId);
      var headerEl = document.getElementById('chatDetailHeader');
      var nameWrap = document.getElementById('chatDetailNameWrap');
      var nameInput = document.getElementById('chatDetailNameInput');
      if (headerEl) headerEl.textContent = emp ? ((emp.name || '').trim() || emp.id) : '员工';
      if (nameWrap) {
        nameWrap.dataset.agentId = employeeId || '';
        nameWrap.dataset.chatId = employeeId || '';
      }
      if (nameInput) nameInput.value = emp ? ((emp.name || '').trim() || emp.id) : '';
      chatDetailBody.innerHTML = '<div class="chat-list-placeholder">加载中…</div>';
      api.getChatHistory(employeeId).then(function (data) {
        var messages = (data && data.messages) ? data.messages : [];
        renderChatDetail(employeeId, emp, messages);
      }).catch(function (err) {
        chatDetailBody.innerHTML = '<div class="chat-list-placeholder">加载失败：' + escapeHtml(err.message || err.status) + '</div>';
      });
    }

    function renderChatDetail(employeeId, employee, messages) {
      var emp = employee || getEmployeeById(employeeId);
      var name = emp ? ((emp.name || '').trim() || emp.id) : '员工';
      var headerEl = document.getElementById('chatDetailHeader');
      var nameWrap = document.getElementById('chatDetailNameWrap');
      var nameInput = document.getElementById('chatDetailNameInput');
      if (headerEl) headerEl.textContent = name;
      if (nameWrap) {
        nameWrap.dataset.agentId = employeeId;
        nameWrap.dataset.chatId = employeeId;
      }
      if (nameInput) nameInput.value = name;
      var avatarChar = (name.charAt(0) || '?');
      var html = '';
      messages.forEach(function (m) {
        var role = m.role === 'user' ? 'user' : 'assistant';
        var content = (m.content != null) ? String(m.content) : '';
        var thinking = (m.extra && m.extra.thinking) ? m.extra.thinking : (m.thinking || '');
        if (role === 'assistant' && !thinking) {
          var parsed = parseThinkReply(content);
          thinking = parsed.thinking;
          content = parsed.content;
        }
        var avatarCharMsg = role === 'user' ? '我' : avatarChar;
        var bodyInner = '';
        if (role === 'user') {
          bodyInner = '<div class="chat-msg-content">' + formatMessageContent(content) + '</div>';
        } else {
          var bubbleInner = '';
          if (thinking) {
            bubbleInner =
              '<div class="chat-msg-thinking">' +
              '<div class="chat-msg-thinking-header" role="button" tabindex="0" aria-expanded="false">' +
              '思考 <span class="chat-msg-thinking-chevron">▼</span></div>' +
              '<div class="chat-msg-thinking-body">' + formatMessageContent(thinking) + '</div></div>';
          }
          bubbleInner += '<div class="chat-msg-content">' + formatMessageContent(content) + '</div>';
          bodyInner = '<div class="chat-msg-bubble">' + bubbleInner + '</div>';
        }
        html +=
          '<div class="chat-msg chat-msg-' + role + '">' +
          '<div class="chat-msg-avatar">' + escapeHtml(avatarCharMsg) + '</div>' +
          '<div class="chat-msg-body">' + bodyInner + '</div></div>';
      });
      chatDetailBody.innerHTML = html || '<div class="chat-list-placeholder">暂无消息</div>';
      chatDetailBody.querySelectorAll('.chat-msg-thinking-header').forEach(function (header) {
        header.addEventListener('click', function () {
          var block = this.closest('.chat-msg-thinking');
          if (block) block.classList.toggle('open');
        });
      });
      chatDetailBody.scrollTop = chatDetailBody.scrollHeight;
    }

    var chatDetailInput = document.getElementById('chatDetailInput');
    var chatDetailSend = document.getElementById('chatDetailSend');
    var fileInput = document.getElementById('chatDetailFileInput');
    var imageBtn = document.getElementById('chatDetailImageBtn');
    var previewWrap = document.getElementById('chatDetailPreview');
    var previewImg = document.getElementById('chatDetailPreviewImg');
    var previewRemove = document.getElementById('chatDetailPreviewRemove');
    var pendingImageDataUrl = null;

    function clearPendingImage() {
      pendingImageDataUrl = null;
      if (previewImg) previewImg.removeAttribute('src');
      if (previewWrap) previewWrap.classList.remove('has-image');
      if (fileInput) fileInput.value = '';
    }
    if (imageBtn && fileInput) {
      imageBtn.addEventListener('click', function () { fileInput.click(); });
      fileInput.addEventListener('change', function () {
        var file = this.files && this.files[0];
        if (!file || !file.type.startsWith('image/')) return;
        var reader = new FileReader();
        reader.onload = function () {
          pendingImageDataUrl = reader.result;
          if (previewImg) { previewImg.src = pendingImageDataUrl; previewImg.alt = file.name; }
          if (previewWrap) previewWrap.classList.add('has-image');
        };
        reader.readAsDataURL(file);
      });
    }
    if (previewRemove) previewRemove.addEventListener('click', clearPendingImage);

    function sendMessage() {
      var text = (chatDetailInput && chatDetailInput.value || '').trim();
      if (!text && !pendingImageDataUrl) return;
      if (!activeEmployeeId) return;
      var sendBtn = chatDetailSend;
      if (sendBtn) sendBtn.disabled = true;
      var div = document.createElement('div');
      div.className = 'chat-msg chat-msg-user';
      var contentEl = document.createElement('div');
      contentEl.className = 'chat-msg-content';
      if (text) {
        var textEl = document.createElement('div');
        textEl.className = 'chat-msg-text';
        textEl.textContent = text;
        contentEl.appendChild(textEl);
      }
      if (pendingImageDataUrl) {
        var img = document.createElement('img');
        img.className = 'chat-msg-image';
        img.src = pendingImageDataUrl;
        img.alt = '';
        contentEl.appendChild(img);
      }
      div.innerHTML = '<div class="chat-msg-avatar">我</div><div class="chat-msg-body"></div>';
      div.querySelector('.chat-msg-body').appendChild(contentEl);
      chatDetailBody.appendChild(div);
      if (chatDetailInput) chatDetailInput.value = '';
      clearPendingImage();
      chatDetailBody.scrollTop = chatDetailBody.scrollHeight;

      api.postChat(activeEmployeeId, { content: text }).then(function (data) {
        var reply = (data && data.reply != null) ? String(data.reply) : '';
        var parsed = parseThinkReply(reply);
        var emp = getEmployeeById(activeEmployeeId);
        var avatarChar = emp ? ((emp.name || '').trim() || emp.id).charAt(0) || '?' : '?';
        var bubbleInner = '';
        if (parsed.thinking) {
          bubbleInner =
            '<div class="chat-msg-thinking">' +
            '<div class="chat-msg-thinking-header" role="button" tabindex="0" aria-expanded="false">' +
            '思考 <span class="chat-msg-thinking-chevron">▼</span></div>' +
            '<div class="chat-msg-thinking-body">' + formatMessageContent(parsed.thinking) + '</div></div>';
        }
        bubbleInner += '<div class="chat-msg-content">' + formatMessageContent(parsed.content) + '</div>';
        var replyDiv = document.createElement('div');
        replyDiv.className = 'chat-msg chat-msg-assistant';
        replyDiv.innerHTML =
          '<div class="chat-msg-avatar">' + escapeHtml(avatarChar) + '</div>' +
          '<div class="chat-msg-body"><div class="chat-msg-bubble">' + bubbleInner + '</div></div>';
        chatDetailBody.appendChild(replyDiv);
        var thinkingHeader = replyDiv.querySelector('.chat-msg-thinking-header');
        if (thinkingHeader) {
          thinkingHeader.addEventListener('click', function () {
            var block = this.closest('.chat-msg-thinking');
            if (block) block.classList.toggle('open');
          });
        }
        chatDetailBody.scrollTop = chatDetailBody.scrollHeight;
      }).catch(function (err) {
        var errMsg = (err && err.message) ? err.message : ('请求失败 ' + (err.status || ''));
        var errDiv = document.createElement('div');
        errDiv.className = 'chat-msg chat-msg-assistant';
        errDiv.innerHTML =
          '<div class="chat-msg-avatar">!</div>' +
          '<div class="chat-msg-body"><div class="chat-msg-bubble"><div class="chat-msg-content" style="color:#c00">' + escapeHtml(errMsg) + '</div></div></div>';
        chatDetailBody.appendChild(errDiv);
        chatDetailBody.scrollTop = chatDetailBody.scrollHeight;
      }).finally(function () {
        if (sendBtn) sendBtn.disabled = false;
      });
    }
    if (chatDetailSend) chatDetailSend.addEventListener('click', sendMessage);
    if (chatDetailInput) {
      chatDetailInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
      });
    }

    var nameWrap = document.getElementById('chatDetailNameWrap');
    var titleEl = document.getElementById('chatDetailHeader');
    var nameInput = document.getElementById('chatDetailNameInput');
    var editBtn = document.getElementById('chatDetailEditNameBtn');
    if (nameWrap && titleEl && nameInput) {
      function saveName() {
        var val = (nameInput.value || '').trim();
        var eid = nameWrap.dataset.agentId;
        if (val && eid) {
          var emp = getEmployeeById(eid);
          if (emp) emp.name = val;
          titleEl.textContent = val;
          var listItem = chatListBody.querySelector('.chat-list-item[data-employee-id="' + eid + '"]');
          var titleInList = listItem && listItem.querySelector('.chat-list-item-title');
          if (titleInList) titleInList.textContent = val;
        }
        nameWrap.classList.remove('editing');
      }
      nameInput.addEventListener('blur', saveName);
      nameInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); nameInput.blur(); }
      });
      if (editBtn) {
        editBtn.addEventListener('click', function (e) {
          e.stopPropagation();
          nameWrap.classList.add('editing');
          nameInput.value = titleEl.textContent || '';
          nameInput.style.width = Math.max(80, (nameInput.value.length + 1) * 10) + 'px';
          nameInput.focus();
        });
      }
    }

    var addChatBtn = document.querySelector('.chat-list-search-add-btn');
    var dropdown = document.getElementById('chatSearchDropdown');
    function closeAddDropdown() {
      if (dropdown) dropdown.classList.remove('open');
      if (addChatBtn) addChatBtn.setAttribute('aria-expanded', 'false');
    }
    function createEmployeeAction() {
      api.createEmployee({ name: '新员工' }).then(function (created) {
        employees.push(created);
        renderChatList(activeEmployeeId);
        if (created && created.id) selectEmployee(created.id);
        closeAddDropdown();
      }).catch(function (err) {
        alert('新建失败：' + (err.message || err.status || ''));
      });
    }
    var newEmployeeItem = dropdown && dropdown.querySelector('[data-action="new-employee"]');
    if (newEmployeeItem) {
      newEmployeeItem.addEventListener('click', function () {
        createEmployeeAction();
      });
    }

    loadOwnerAndEmployees();
  }

  window.MainWindowChat = { init: init };
})();
