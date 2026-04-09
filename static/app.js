const state = {
  members: [],
  leaders: [],
  mappings: {},
  latestDetectedSenders: [],
  latestLeaveNames: "",
};

const dom = {
  imageInput: document.getElementById("imageInput"),
  leaveNames: document.getElementById("leaveNames"),
  analyzeButton: document.getElementById("analyzeButton"),
  progressBox: document.getElementById("progressBox"),
  leaderList: document.getElementById("leaderList"),
  resultEmpty: document.getElementById("resultEmpty"),
  resultContent: document.getElementById("resultContent"),
  summaryBadge: document.getElementById("summaryBadge"),
  activeCount: document.getElementById("activeCount"),
  presentCount: document.getElementById("presentCount"),
  missingCount: document.getElementById("missingCount"),
  missingList: document.getElementById("missingList"),
  presentList: document.getElementById("presentList"),
  excludedList: document.getElementById("excludedList"),
  mappingPanel: document.getElementById("mappingPanel"),
  mappingList: document.getElementById("mappingList"),
  detailsList: document.getElementById("detailsList"),
};

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `请求失败: ${response.status}`);
  }
  return response.json();
}

function setProgress(message, visible = true) {
  dom.progressBox.textContent = message;
  dom.progressBox.classList.toggle("hidden", !visible);
}

function renderTags(target, items, className = "") {
  target.innerHTML = "";
  if (!items.length) {
    target.innerHTML = '<span class="tag muted">无</span>';
    return;
  }

  for (const item of items) {
    const tag = document.createElement("span");
    tag.className = `tag ${className}`.trim();
    tag.textContent = item;
    target.appendChild(tag);
  }
}

function renderLeaderList(leaders) {
  dom.leaderList.innerHTML = "";
  for (const leader of leaders) {
    const li = document.createElement("li");
    li.textContent = leader;
    dom.leaderList.appendChild(li);
  }
}

function renderDetails(details) {
  dom.detailsList.innerHTML = "";
  if (!details.length) {
    dom.detailsList.innerHTML = '<div class="detail-item">当前没有识别明细。</div>';
    return;
  }

  for (const item of details) {
    const div = document.createElement("div");
    div.className = "detail-item";
    const matchText = item.member ? `${item.member} (${item.status})` : `未匹配 (${item.status})`;
    const hintText = item.member_hint ? ` | 提示: ${item.member_hint}` : "";
    div.textContent = `${item.raw_name} -> ${matchText}${hintText} | 来源: ${item.source || "未知"}`;
    dom.detailsList.appendChild(div);
  }
}

function createMappingItem(entry) {
  const wrapper = document.createElement("div");
  wrapper.className = "mapping-item";

  const info = document.createElement("div");
  info.innerHTML = `<strong>${entry.raw_name}</strong><p class="subtle">可选成员：${(entry.candidates || []).join("、") || "暂无自动候选"}</p>`;

  const actions = document.createElement("div");
  actions.className = "mapping-actions";

  const select = document.createElement("select");
  const placeholder = document.createElement("option");
  placeholder.textContent = "选择要映射的成员";
  placeholder.value = "";
  select.appendChild(placeholder);

  for (const member of state.members) {
    const option = document.createElement("option");
    option.value = member;
    option.textContent = member;
    if ((entry.candidates || []).includes(member)) {
      option.selected = true;
    }
    select.appendChild(option);
  }

  const button = document.createElement("button");
  button.className = "secondary-button";
  button.textContent = "保存映射";
  button.addEventListener("click", async () => {
    if (!select.value) {
      setProgress(`请先为 ${entry.raw_name} 选择成员`, true);
      return;
    }

    button.disabled = true;
    try {
      const payload = await requestJson("/api/mappings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_name: entry.raw_name, member_name: select.value }),
      });
      state.mappings = payload.mappings;
      setProgress(`已保存映射：${entry.raw_name} -> ${select.value}`);
      await submitAnalysis();
    } catch (error) {
      setProgress(error.message, true);
    } finally {
      button.disabled = false;
    }
  });

  actions.appendChild(select);
  actions.appendChild(button);
  wrapper.appendChild(info);
  wrapper.appendChild(actions);
  return wrapper;
}

function renderMappings(unresolved) {
  dom.mappingList.innerHTML = "";
  dom.mappingPanel.classList.toggle("hidden", unresolved.length === 0);
  if (!unresolved.length) {
    return;
  }

  for (const entry of unresolved) {
    dom.mappingList.appendChild(createMappingItem(entry));
  }
}

function renderResult(result) {
  dom.resultEmpty.classList.add("hidden");
  dom.resultContent.classList.remove("hidden");
  dom.summaryBadge.textContent = `已出现 ${result.present_count} / ${result.active_count}`;
  dom.activeCount.textContent = String(result.active_count);
  dom.presentCount.textContent = String(result.present_count);
  dom.missingCount.textContent = String(result.missing_count);

  renderTags(dom.missingList, result.missing_members, "danger");
  renderTags(dom.presentList, result.present_members, "success");
  renderTags(dom.excludedList, result.excluded_members, "muted");
  renderMappings(result.unresolved);
  renderDetails(result.recognized_details);
}

async function submitAnalysis() {
  const result = await requestJson("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      detected_senders: state.latestDetectedSenders,
      leave_names: state.latestLeaveNames,
      manual_present_members: [],
    }),
  });
  renderResult(result);
}

async function scanImages(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  return requestJson("/api/scan", {
    method: "POST",
    body: formData,
  });
}

async function analyzeImages() {
  const files = [...dom.imageInput.files];
  if (!files.length) {
    setProgress("请先选择至少一张聊天截图", true);
    return;
  }

  dom.analyzeButton.disabled = true;
  try {
    setProgress(`正在上传并识别 ${files.length} 张截图...`, true);
    const scanResult = await scanImages(files);
    state.latestDetectedSenders = scanResult.detected_senders || [];
    state.latestLeaveNames = dom.leaveNames.value.trim();

    await submitAnalysis();
    setProgress(`分析完成，共提取 ${state.latestDetectedSenders.length} 条昵称记录。`, true);
  } catch (error) {
    console.error("Analyze failed", error);
    setProgress(error.message || "识别失败，请稍后重试", true);
  } finally {
    dom.analyzeButton.disabled = false;
  }
}

async function bootstrap() {
  setProgress("正在加载成员名单...", true);
  try {
    const config = await requestJson("/api/config");
    state.members = config.members;
    state.leaders = config.leaders;
    state.mappings = config.mappings;
    renderLeaderList(config.leaders);
    setProgress("页面已就绪，可以开始分析。", true);
  } catch (error) {
    setProgress(error.message || "初始化失败", true);
  }
}

dom.analyzeButton.addEventListener("click", analyzeImages);
bootstrap();
