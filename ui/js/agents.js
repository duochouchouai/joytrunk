/**
 * 主窗口「其他」面板：Agent 列表、加减员、状态/播放暂停、指示灯配置。
 * 使用方式：MainWindowAgents.init(electronAPI)；依赖 MainWindowUtils.escapeHtml（可选）。
 */
(function () {
  var MAX_AGENTS = 4;

  function init(electronAPI) {
    var api = electronAPI;
    if (!api) return;
    var escapeHtml = window.MainWindowUtils && window.MainWindowUtils.escapeHtml;
    if (typeof escapeHtml !== 'function') {
      escapeHtml = function (s) {
        if (s == null) return '';
        var div = document.createElement('div');
        div.textContent = String(s);
        return div.innerHTML;
      };
    }

    var btnAdd = document.getElementById('btnAdd');
    var btnRemove = document.getElementById('btnRemove');
    var agentList = document.getElementById('agentList');
    if (!agentList) return;

    var agentNamesState = ['Agent 1', 'Agent 2', 'Agent 3', 'Agent 4'];
    var agentStatesState = ['idle', 'idle', 'idle', 'idle'];

    function renderAgents(count, names, states) {
      var namesToUse = names || agentNamesState;
      var statesToUse = states || agentStatesState;
      agentList.innerHTML = '';
      for (var i = 0; i < count; i++) {
        var card = document.createElement('div');
        card.className = 'agent-card';
        var displayName = (namesToUse[i] || '').trim() || ('Agent ' + (i + 1));
        var state = statesToUse[i] || 'idle';
        card.innerHTML =
          '<div class="name-wrap">' +
          '<input type="text" class="agent-name-input" data-index="' + i + '" value="' + escapeHtml(displayName) + '" placeholder="Agent ' + (i + 1) + '" maxlength="32" />' +
          '</div>' +
          '<div class="controls">' +
          '<select class="state-select" data-index="' + i + '" title="状态">' +
          '<option value="idle"' + (state === 'idle' ? ' selected' : '') + '>空闲</option>' +
          '<option value="thinking"' + (state === 'thinking' ? ' selected' : '') + '>思考中</option>' +
          '<option value="running"' + (state === 'running' ? ' selected' : '') + '>执行中</option>' +
          '</select>' +
          '<button type="button" data-action="play" data-index="' + i + '">播放</button>' +
          '<button type="button" data-action="pause" data-index="' + i + '">暂停</button>' +
          '</div>';
        agentList.appendChild(card);
      }
      if (btnAdd) btnAdd.disabled = count >= MAX_AGENTS;
      if (btnRemove) btnRemove.disabled = count <= 1;

      agentList.querySelectorAll('.agent-name-input').forEach(function (input) {
        var index = parseInt(input.dataset.index, 10);
        input.addEventListener('change', function () {
          var val = input.value.trim() || ('Agent ' + (index + 1));
          agentNamesState[index] = val;
          api.setAgentName(index, val);
        });
        input.addEventListener('blur', function () {
          var val = input.value.trim() || ('Agent ' + (index + 1));
          if (agentNamesState[index] !== val) {
            agentNamesState[index] = val;
            api.setAgentName(index, val);
          }
        });
      });
      agentList.querySelectorAll('.state-select').forEach(function (sel) {
        var index = parseInt(sel.dataset.index, 10);
        sel.addEventListener('change', function () {
          var val = sel.value;
          agentStatesState[index] = val;
          api.setAgentState(index, val);
        });
      });
      agentList.querySelectorAll('button[data-action]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var index = parseInt(btn.dataset.index, 10);
          if (btn.dataset.action === 'play') api.agentPlay(index);
          else api.agentPause(index);
        });
      });
    }

    if (api.onAgentCount) {
      api.onAgentCount(function (count) {
        Promise.all([api.getAgentNames(), api.getAgentStates()]).then(function (results) {
          var names = results[0];
          var states = results[1];
          if (names && names.length) agentNamesState = names.slice(0, MAX_AGENTS);
          if (states && states.length) agentStatesState = states.slice(0, MAX_AGENTS);
          renderAgents(count, agentNamesState, agentStatesState);
        });
      });
    }
    if (api.onAgentNames) {
      api.onAgentNames(function (names) {
        if (names && names.length) agentNamesState = names.slice(0, MAX_AGENTS);
        agentList.querySelectorAll('.agent-name-input').forEach(function (input) {
          var index = parseInt(input.dataset.index, 10);
          if (agentNamesState[index] !== undefined) input.value = agentNamesState[index];
        });
      });
    }
    if (api.onAgentStates) {
      api.onAgentStates(function (states) {
        if (states && states.length) agentStatesState = states.slice(0, MAX_AGENTS);
        agentList.querySelectorAll('.state-select').forEach(function (sel) {
          var index = parseInt(sel.dataset.index, 10);
          if (agentStatesState[index] !== undefined) sel.value = agentStatesState[index];
        });
      });
    }

    Promise.all([api.getAgentCount(), api.getAgentNames(), api.getAgentStates()]).then(function (results) {
      var count = results[0];
      var names = results[1];
      var states = results[2];
      if (names && names.length) agentNamesState = names.slice(0, MAX_AGENTS);
      if (states && states.length) agentStatesState = states.slice(0, MAX_AGENTS);
      renderAgents(count, agentNamesState, agentStatesState);
    }).catch(function () {});

    if (btnAdd) btnAdd.addEventListener('click', function () { api.addAgent(); });
    if (btnRemove) btnRemove.addEventListener('click', function () { api.removeAgent(); });

    var spinSpeed = document.getElementById('spinSpeed');
    var spinSpeedValue = document.getElementById('spinSpeedValue');
    var breatheInterval = document.getElementById('breatheInterval');
    var breatheIntervalValue = document.getElementById('breatheIntervalValue');

    function syncIndicatorUI(config, sendToMain) {
      if (!config) return;
      if (typeof config.spinDuration === 'number' && spinSpeed && spinSpeedValue) {
        spinSpeed.value = config.spinDuration;
        spinSpeedValue.textContent = config.spinDuration + ' s';
      }
      if (typeof config.breatheDuration === 'number' && breatheInterval && breatheIntervalValue) {
        breatheInterval.value = config.breatheDuration;
        breatheIntervalValue.textContent = config.breatheDuration + ' s';
      }
      if (sendToMain !== false && api.setIndicatorConfig) {
        api.setIndicatorConfig({
          spinDuration: parseFloat(spinSpeed && spinSpeed.value) || 3,
          breatheDuration: parseFloat(breatheInterval && breatheInterval.value) || 2
        });
      }
    }

    if (spinSpeed && spinSpeedValue) {
      spinSpeed.addEventListener('input', function () {
        spinSpeedValue.textContent = spinSpeed.value + ' s';
        if (api.setIndicatorConfig) api.setIndicatorConfig({ spinDuration: parseFloat(spinSpeed.value) });
      });
      spinSpeed.addEventListener('change', function () {
        syncIndicatorUI({
          spinDuration: parseFloat(spinSpeed.value),
          breatheDuration: parseFloat(breatheInterval && breatheInterval.value) || 2
        });
      });
    }
    if (breatheInterval && breatheIntervalValue) {
      breatheInterval.addEventListener('input', function () {
        breatheIntervalValue.textContent = breatheInterval.value + ' s';
        if (api.setIndicatorConfig) api.setIndicatorConfig({ breatheDuration: parseFloat(breatheInterval.value) });
      });
      breatheInterval.addEventListener('change', function () {
        syncIndicatorUI({
          spinDuration: parseFloat(spinSpeed && spinSpeed.value) || 3,
          breatheDuration: parseFloat(breatheInterval.value)
        });
      });
    }

    if (api.onIndicatorConfig) api.onIndicatorConfig(function (config) { syncIndicatorUI(config, false); });
    if (api.getIndicatorConfig) api.getIndicatorConfig().then(function (config) { syncIndicatorUI(config, false); });
  }

  window.MainWindowAgents = { init: init };
})();
