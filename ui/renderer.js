/**
 * 悬浮窗渲染进程：多 agent 视频网格播放、缩放、拖拽、指示灯、悬停高亮。
 * - 与 main.js 的 CELL_1/CELL_2/CELL_3_4 对应，保证每格视频完整显示。
 * - 视频流程：先播 intro 一次，结束后按状态播 working/zoneOut；状态变化时仅在当前片结束时切换；同片循环用 currentTime=0+play 避免闪烁。
 * - 指示灯：状态切换时按“小球到达最高点”的时刻依次变色（与 performance.now 相位同步）。
 * - 悬停：鼠标移入某 slot 时该格添加 .hover，由 CSS ::after 绘制绿色框（叠在视频上）。
 */
(function () {
  const CELL_1 = 100;
  const CELL_2 = 70;
  const CELL_3_4 = 60;
  const MAX_AGENTS = 4;
  const LIGHT_COUNT = 6;
  const DEG_PER_CIRCLE = 360;
  const CLICK_THRESHOLD_PX = 5;
  const CLICK_MAX_MS = 400;

  /** 悬停高亮时给 slot 添加的 class，与 index.html 中 .agent-slot.hover::after 对应 */
  const SLOT_HOVER_CLASS = 'hover';

  /** 视频类型：状态视频（working/zoneOut）需记录到 slotStateVideo，用于同片循环判定 */
  const STATE_VIDEO_KEYS = ['working', 'zoneOut'];

  /** 各状态对应颜色（idle 绿 / thinking 黄 / running 红） */
  const STATE_COLORS = { idle: '#43a047', thinking: '#fbc02d', running: '#e53935' };
  /** 第 n 个小球（索引 0..5）处于最高点时，容器的旋转角度（度） */
  const LIGHT_TOP_PHASE_DEG = [0, 300, 240, 180, 120, 60];

  const overlayRoot = document.querySelector('.overlay-root');
  const videos = [
    document.getElementById('video0'),
    document.getElementById('video1'),
    document.getElementById('video2'),
    document.getElementById('video3'),
  ];
  const scalers = overlayRoot.querySelectorAll('.agent-slot .scaler');
  const agentNameEls = overlayRoot.querySelectorAll('.agent-name');
  const agentStatusEls = overlayRoot.querySelectorAll('.agent-status');

  let agentCount = 0;
  /** 视频源 URL：intro 播一次，working/zoneOut 按状态循环 */
  let sources = { intro: null, working: null, zoneOut: null };
  /** 每 slot：'intro' 播欢迎片 | 'state-video' 按状态播 working/zoneOut */
  const slotPhase = ['intro', 'intro', 'intro', 'intro'];
  /** 当前正在播的状态视频：'working' | 'zoneOut' | null（intro 时为 null） */
  const slotStateVideo = [null, null, null, null];
  /** 状态变化后，当前片播完时要切到的视频，播完后清空 */
  const slotPendingVideo = [null, null, null, null];
  const playingState = [true, true, true, true];
  let spinDurationSec = 2;
  let previousStates = ['idle', 'idle', 'idle', 'idle'];
  let transitionTimeouts = [];

  function normalizeState(s) {
    return s === 'running' || s === 'thinking' || s === 'idle' ? s : 'idle';
  }

  /** 当前布局下每格边长（px），与主进程窗口尺寸一致 */
  function getCellSize() {
    if (agentCount <= 1) return CELL_1;
    if (agentCount === 2) return CELL_2;
    return CELL_3_4;
  }

  /** 根据状态返回要播的状态视频：running/thinking → working，idle → zoneOut */
  function getVideoForState(state) {
    return state === 'running' || state === 'thinking' ? 'working' : 'zoneOut';
  }

  /** 在 working/zoneOut 中选一个可用的，优先 preferred */
  function pickStateVideoKey(preferred) {
    if (sources[preferred]) return preferred;
    return preferred === 'working' ? 'zoneOut' : 'working';
  }

  function isStateVideoKey(which) {
    return STATE_VIDEO_KEYS.indexOf(which) !== -1;
  }

  /** 为指定 slot 播放某类视频（直接在当前 video 上 load，canplay 后显示并播放） */
  function playVideo(slotIndex, which) {
    const v = videos[slotIndex];
    const scaler = scalers[slotIndex];
    const url = sources[which];
    if (!v || !scaler || !url) return;
    v.src = url;
    v.load();
    if (isStateVideoKey(which)) slotStateVideo[slotIndex] = which;
    v.addEventListener(
      'canplay',
      (function (idx) {
        return function () {
          scalers[idx].classList.add('ready');
          fitVideo(idx);
          if (playingState[idx]) videos[idx].play().catch(function () {});
        };
      })(slotIndex),
      { once: true }
    );
  }

  /** 同一视频循环：不重新 load，直接 currentTime=0 并 play，避免闪烁 */
  function replayCurrentVideo(slotIndex) {
    const v = videos[slotIndex];
    if (!v) return;
    v.currentTime = 0;
    if (playingState[slotIndex]) v.play().catch(function () {});
  }

  /** 当前片播完时的处理：intro 后切状态视频；state-video 时若有 pending 则切换，否则同片循环（不 reload） */
  function onSlotEnded(slotIndex) {
    if (!playingState[slotIndex]) return;
    if (slotPhase[slotIndex] === 'intro') {
      slotPhase[slotIndex] = 'state-video';
      const which = pickStateVideoKey(getVideoForState(previousStates[slotIndex]));
      if (sources[which]) playVideo(slotIndex, which);
      return;
    }
    if (slotPhase[slotIndex] === 'state-video') {
      const next = slotPendingVideo[slotIndex];
      slotPendingVideo[slotIndex] = null;
      if (next) {
        const key = pickStateVideoKey(next);
        if (sources[key]) { playVideo(slotIndex, key); return; }
      }
      const current = slotStateVideo[slotIndex];
      if (current && sources[current]) {
        replayCurrentVideo(slotIndex);
      }
    }
  }

  /** 按当前格子尺寸缩放该 slot 的视频，保持比例完整显示 */
  function fitVideo(slotIndex) {
    const video = videos[slotIndex];
    const scaler = scalers[slotIndex];
    if (!video || !scaler) return;
    const w = video.videoWidth;
    const h = video.videoHeight;
    if (!w || !h) return;
    const cell = getCellSize();
    const scale = Math.min(cell / w, cell / h);
    scaler.style.width = w + 'px';
    scaler.style.height = h + 'px';
    scaler.style.transform = 'scale(' + scale + ')';
    video.style.width = w + 'px';
    video.style.height = h + 'px';
  }

  /** 对当前所有可见 slot 重新计算缩放 */
  function refitVisibleVideos() {
    for (let i = 0; i < agentCount; i++) {
      const v = videos[i];
      if (v && v.videoWidth && v.videoHeight) fitVideo(i);
    }
  }

  function setupEndedListeners() {
    videos.forEach(function (v, i) {
      if (!v) return;
      v.addEventListener('ended', function () {
        onSlotEnded(i);
      });
    });
  }

  /** 收到视频源后：为每个可见 slot 先播 intro，播完后按状态播 working/zoneOut；切换仅在当前片结束时进行 */
  function applyVideoSources(newSources) {
    if (!newSources || typeof newSources !== 'object') return;
    sources = {
      intro: newSources.intro || null,
      working: newSources.working || null,
      zoneOut: newSources.zoneOut || null,
    };
    const hasIntro = !!sources.intro;
    const hasState = !!sources.working || !!sources.zoneOut;
    if (!hasIntro && !hasState) return;
    setupEndedListeners();
    for (let k = 0; k < agentCount; k++) {
      slotPhase[k] = 'intro';
      slotStateVideo[k] = null;
      slotPendingVideo[k] = null;
      if (hasIntro) {
        playVideo(k, 'intro');
      } else if (hasState) {
        slotPhase[k] = 'state-video';
        const which = pickStateVideoKey(getVideoForState(previousStates[k]));
        if (sources[which]) playVideo(k, which);
      }
    }
  }

  window.electronAPI.onVideoSources?.(applyVideoSources);

  window.electronAPI.onAgentNames?.((names) => {
    if (!names || !Array.isArray(names)) return;
    names.forEach((name, i) => {
      if (agentNameEls[i]) {
        agentNameEls[i].textContent = (name && String(name).trim()) || 'Agent ' + (i + 1);
      }
    });
  });

  window.electronAPI.onAgentStates?.((states) => {
    if (!states || !Array.isArray(states)) return;
    transitionTimeouts.forEach(clearTimeout);
    transitionTimeouts = [];
    states.forEach((newState, slotIndex) => {
      const statusEl = agentStatusEls[slotIndex];
      if (!statusEl) return;
      const s = normalizeState(newState);
      const prev = previousStates[slotIndex];
      const isValidPrev = prev === 'idle' || prev === 'thinking' || prev === 'running';
      if (prev === s) {
        previousStates[slotIndex] = s;
        statusEl.setAttribute('data-state', s);
        return;
      }
      if (!isValidPrev) {
        previousStates[slotIndex] = s;
        statusEl.setAttribute('data-state', s);
        return;
      }
      const lights = statusEl.querySelectorAll('.light');
      if (lights.length !== LIGHT_COUNT) return;
      scheduleColorTransitionByTopPhase(slotIndex, statusEl, lights, s);
      const desiredVideo = getVideoForState(s);
      if (slotPhase[slotIndex] === 'state-video' && slotStateVideo[slotIndex] !== desiredVideo) {
        slotPendingVideo[slotIndex] = desiredVideo;
      }
    });
  });

  /**
   * 按“每个小球到达最高点的时刻”依次切色：与 CSS 旋转相位同步，用 setTimeout 在对应时刻设 inline background。
   */
  function scheduleColorTransitionByTopPhase(slotIndex, statusEl, lights, toState) {
    const newColor = STATE_COLORS[toState];
    const tSec = performance.now() / 1000;
    const currentPhaseDeg = ((tSec / spinDurationSec) * DEG_PER_CIRCLE) % DEG_PER_CIRCLE;
    for (let n = 0; n < LIGHT_COUNT; n++) {
      const delaySec = ((LIGHT_TOP_PHASE_DEG[n] - currentPhaseDeg + DEG_PER_CIRCLE) % DEG_PER_CIRCLE) / DEG_PER_CIRCLE * spinDurationSec;
      const delayMs = Math.round(delaySec * 1000);
      transitionTimeouts.push(
        setTimeout(function () { lights[n].style.background = newColor; }, delayMs)
      );
    }
    const fullCycleMs = Math.round(spinDurationSec * 1000);
    transitionTimeouts.push(
      setTimeout(function () {
        previousStates[slotIndex] = toState;
        statusEl.setAttribute('data-state', toState);
        lights.forEach(function (light) { light.style.removeProperty('background'); });
      }, fullCycleMs)
    );
  }

  window.electronAPI.onIndicatorConfig?.((config) => {
    if (!config) return;
    if (typeof config.spinDuration === 'number') {
      spinDurationSec = config.spinDuration;
      overlayRoot.style.setProperty('--spin-duration', config.spinDuration + 's');
    }
    if (typeof config.breatheDuration === 'number') {
      overlayRoot.style.setProperty('--breathe-duration', config.breatheDuration + 's');
    }
  });

  window.electronAPI.onAgentCount?.((count) => {
    const prevCount = agentCount;
    agentCount = Math.min(MAX_AGENTS, Math.max(0, count));
    if (overlayRoot) overlayRoot.setAttribute('data-agent-count', String(agentCount));
    if (count > prevCount && (sources.intro || sources.working || sources.zoneOut)) {
      for (let i = prevCount; i < agentCount; i++) {
        slotPhase[i] = 'intro';
        slotStateVideo[i] = null;
        slotPendingVideo[i] = null;
        if (sources.intro) {
          playVideo(i, 'intro');
        } else {
          slotPhase[i] = 'state-video';
          const which = pickStateVideoKey(getVideoForState(previousStates[i]));
          if (sources[which]) playVideo(i, which);
        }
      }
    }
    refitVisibleVideos();
  });

  window.electronAPI.onPlayerCmd?.((cmd, index) => {
    const v = videos[index];
    if (!v || index >= agentCount) return;
    if (cmd === 'play') {
      playingState[index] = true;
      v.play().catch(function () {});
    } else if (cmd === 'pause') {
      playingState[index] = false;
      v.pause();
    }
  });

  (function setupOverlayDragAndClick() {
    if (!overlayRoot || !window.electronAPI.openMain) return;
    overlayRoot.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      if (e.target.closest('.overlay-menu-btn')) return;
      if (e.target.closest('.agent-slot-close')) return;
      const onDragBar = e.target.closest('.overlay-menu-drag');
      if (overlayRoot.getAttribute('data-agent-count') === '0' && !onDragBar) return;
      const isOnDragBar = !!onDragBar;
      const startX = e.screenX;
      const startY = e.screenY;
      const startTime = Date.now();
      let maxDist = 0;

      function onMove(ev) {
        maxDist = Math.max(maxDist, Math.hypot(ev.screenX - startX, ev.screenY - startY));
        window.electronAPI.overlayDragMove?.(ev.screenX, ev.screenY);
      }
      function onUp() {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        window.electronAPI.overlayDragEnd?.();
        if (!isOnDragBar && maxDist < CLICK_THRESHOLD_PX && Date.now() - startTime < CLICK_MAX_MS) {
          window.electronAPI.openMain();
        }
      }
      window.electronAPI.overlayDragStart?.(startX, startY);
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
  })();

  /** 为每个 agent-slot 绑定 mouseenter/mouseleave，切换 .hover 表示当前鼠标所在格；悬停时清除根 title 避免显示“点击打开主页面” */
  (function setupSlotHover() {
    if (!overlayRoot) return;
    const OVERLAY_TITLE = '点击打开主页面';
    const slotEls = overlayRoot.querySelectorAll('.agent-slot');
    slotEls.forEach(function (el) {
      el.addEventListener('mouseenter', function () {
        slotEls.forEach(function (s) { s.classList.remove(SLOT_HOVER_CLASS); });
        el.classList.add(SLOT_HOVER_CLASS);
        overlayRoot.title = '';
      });
      el.addEventListener('mouseleave', function () {
        el.classList.remove(SLOT_HOVER_CLASS);
        setTimeout(function () {
          if (!overlayRoot.querySelector('.agent-slot.' + SLOT_HOVER_CLASS)) overlayRoot.title = OVERLAY_TITLE;
        }, 0);
      });
    });
  })();

  /** 关闭按钮：点击后通知主进程移除该索引的 agent，阻止事件冒泡避免触发打开主窗口 */
  (function setupSlotCloseButtons() {
    if (!overlayRoot || !window.electronAPI.removeAgentAt) return;
    overlayRoot.querySelectorAll('.agent-slot-close').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        e.preventDefault();
        const index = parseInt(btn.getAttribute('data-slot'), 10);
        if (!isNaN(index) && index >= 0) window.electronAPI.removeAgentAt(index);
      });
    });
  })();

  /** 小菜单：状态区点击打开主页面；加号添加 agent；放大图标打开主页面 */
  (function setupOverlayMenu() {
    const menu = overlayRoot?.querySelector('.overlay-menu');
    if (!menu) return;
    menu.addEventListener('click', function (e) {
      if (e.target.closest('.overlay-menu-status')) {
        e.preventDefault();
        e.stopPropagation();
        window.electronAPI.openMain?.();
        return;
      }
      const btn = e.target.closest('.overlay-menu-btn');
      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();
      const action = btn.getAttribute('data-action');
      if (action === 'open-main') {
        window.electronAPI.openMain?.();
        return;
      }
      if (action === 'add-agent') {
        window.electronAPI.addAgent?.();
      }
      if (action === 'start') {
        const n = parseInt(btn.getAttribute('data-count'), 10);
        if (n >= 1 && n <= 3) window.electronAPI.startWithAgents?.(n);
      }
    });
  })();
})();
