"use strict";

const API_BASE = ["localhost", "127.0.0.1"].includes(window.location.hostname)
  ? "https://arenapulse-api.vercel.app"
  : "";

const state = {
  token: window.localStorage.getItem("arenapulse_token"),
  user: null,
  games: [],
  challenges: [],
  participations: [],
  activeChallengeId: null,
  filter: "all",
};

const elements = {
  challengeList: document.querySelector("#challenge-list"),
  challengeCount: document.querySelector("#challenge-count"),
  rankingList: document.querySelector("#ranking-list"),
  rankingSubtitle: document.querySelector("#ranking .panel-head p"),
  toast: document.querySelector("#toast"),
  authDialog: document.querySelector("#auth-dialog"),
  searchDialog: document.querySelector("#search-dialog"),
  createDialog: document.querySelector("#create-dialog"),
  resultDialog: document.querySelector("#result-dialog"),
  playerPanel: document.querySelector("#player-panel"),
  gameSelect: document.querySelector("#game-select"),
  participationSelect: document.querySelector("#participation-select"),
};

function showToast(message, type = "success") {
  window.clearTimeout(showToast.timeout);
  elements.toast.textContent = message;
  elements.toast.dataset.state = type;
  elements.toast.hidden = false;
  showToast.timeout = window.setTimeout(() => {
    elements.toast.hidden = true;
  }, 4200);
}

function errorMessage(error) {
  if (typeof error?.message === "string") return error.message;
  return "Não foi possível concluir. Tente novamente.";
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.json !== undefined)
    headers.set("Content-Type", "application/json");
  if (options.auth !== false && state.token)
    headers.set("Authorization", `Bearer ${state.token}`);
  const response = await fetch(`${API_BASE}/api/v1${path}`, {
    ...options,
    headers,
    body:
      options.json !== undefined ? JSON.stringify(options.json) : options.body,
  });
  let payload = null;
  if (response.status !== 204) {
    const contentType = response.headers.get("content-type") || "";
    payload = contentType.includes("application/json")
      ? await response.json()
      : null;
  }
  if (!response.ok) {
    if (response.status === 401 && state.token) clearSession(false);
    const detail = payload?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(" · ")
      : detail || "A API não respondeu como esperado.";
    throw new Error(message);
  }
  return payload;
}

function setButtonState(button, status, label) {
  if (!button.dataset.defaultLabel)
    button.dataset.defaultLabel = button.textContent;
  button.dataset.state = status || "";
  button.disabled = status === "loading";
  button.textContent = label || button.dataset.defaultLabel;
}

function setFormMessage(form, message = "", type = "") {
  const target = form.querySelector("[data-form-message]");
  if (!target) return;
  target.textContent = message;
  target.dataset.state = type;
}

function formatRemaining(endsAt) {
  const remaining = new Date(endsAt).getTime() - Date.now();
  if (remaining <= 0) return "Encerrado";
  const days = Math.ceil(remaining / 86400000);
  return days === 1 ? "1 dia" : `${days} dias`;
}

function sigilFor(game) {
  if (game.slug === "ea-sports-fc") return "FC";
  if (game.slug === "counter-strike-2") return "CS";
  return game.name.slice(0, 1).toUpperCase();
}

function addText(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = value;
  return node;
}

function renderChallenges() {
  elements.challengeList.replaceChildren();
  const visible = state.challenges.filter(
    (challenge) =>
      state.filter === "all" || challenge.game.category === state.filter,
  );
  elements.challengeCount.textContent = String(state.challenges.length);
  if (!visible.length) {
    elements.challengeList.append(
      addText("p", "empty-state", "Nenhum desafio nesta fila."),
    );
    return;
  }
  visible.forEach((challenge) => {
    const row = document.createElement("article");
    row.className = "challenge-row";
    row.dataset.game = challenge.game.category;
    row.dataset.challengeId = String(challenge.id);
    const sigil = addText("div", "game-sigil", sigilFor(challenge.game));
    sigil.setAttribute("aria-hidden", "true");
    const main = document.createElement("div");
    main.className = "challenge-row__main";
    main.append(
      addText("span", "game-name", challenge.game.name),
      addText("h3", "", challenge.title),
      addText("p", "", challenge.description),
    );
    const meta = document.createElement("dl");
    meta.className = "challenge-meta";
    [
      ["Recompensa", challenge.reward || "Prestígio"],
      ["Janela", formatRemaining(challenge.ends_at)],
    ].forEach(([term, value]) => {
      const group = document.createElement("div");
      group.append(addText("dt", "", term), addText("dd", "", value));
      meta.append(group);
    });
    const joined = state.participations.some(
      (item) => item.challenge_id === challenge.id,
    );
    const action = addText(
      "button",
      "button button--join",
      joined ? "Inscrito" : "Entrar",
    );
    action.type = "button";
    action.dataset.challengeId = String(challenge.id);
    action.disabled = joined;
    if (joined) action.dataset.state = "success";
    row.append(sigil, main, meta, action);
    elements.challengeList.append(row);
  });
}

async function loadChallenges() {
  const [games, challenges] = await Promise.all([
    api("/games", { auth: false }),
    api("/challenges?status=published&limit=50", { auth: false }),
  ]);
  state.games = games;
  state.challenges = challenges;
  state.activeChallengeId ||= challenges[0]?.id || null;
  renderChallenges();
  renderGameOptions();
  renderParticipationOptions();
}

function renderGameOptions() {
  elements.gameSelect.replaceChildren();
  state.games.forEach((game) => {
    const option = document.createElement("option");
    option.value = String(game.id);
    option.textContent = game.name;
    elements.gameSelect.append(option);
  });
}

function renderParticipationOptions() {
  elements.participationSelect.replaceChildren();
  state.participations.forEach((participation) => {
    const challenge = state.challenges.find(
      (item) => item.id === participation.challenge_id,
    );
    if (!challenge) return;
    const option = document.createElement("option");
    option.value = String(challenge.id);
    option.textContent = `${challenge.game.name} · ${challenge.title}`;
    elements.participationSelect.append(option);
  });
}

async function loadRanking(challengeId = state.activeChallengeId) {
  if (!challengeId) return;
  state.activeChallengeId = Number(challengeId);
  const challenge = state.challenges.find(
    (item) => item.id === state.activeChallengeId,
  );
  elements.rankingSubtitle.textContent =
    challenge?.title || "Desafio selecionado";
  try {
    const ranking = await api(
      `/challenges/${state.activeChallengeId}/leaderboard`,
      { auth: false },
    );
    elements.rankingList.replaceChildren();
    if (!ranking.length) {
      const empty = document.createElement("li");
      empty.className = "empty-state";
      empty.textContent = "Seja a primeira pessoa no ranking.";
      elements.rankingList.append(empty);
      return;
    }
    ranking.forEach((entry) => {
      const item = document.createElement("li");
      const player = document.createElement("span");
      player.className = "player";
      player.append(
        addText("strong", "", entry.username),
        addText(
          "small",
          "",
          `${entry.matches_played} partidas · ${entry.wins} vitórias`,
        ),
      );
      const points = addText("span", "points", String(entry.points));
      points.append(addText("small", "", " pts"));
      item.append(
        addText("span", "rank", String(entry.position).padStart(2, "0")),
        player,
        points,
      );
      elements.rankingList.append(item);
    });
  } catch (error) {
    showToast(errorMessage(error), "error");
  }
}

function setAuthenticatedUI(dashboard) {
  elements.playerPanel.hidden = false;
  document.querySelector("[data-open-auth]").textContent = state.user.username;
  document.querySelector("#player-name").textContent = state.user.username;
  document.querySelector("#stat-challenges").textContent = String(
    dashboard.challenges_joined,
  );
  document.querySelector("#stat-points").textContent = String(
    dashboard.total_points,
  );
  document.querySelector("#stat-matches").textContent = String(
    dashboard.total_matches,
  );
  document.querySelector("#stat-wins").textContent = String(
    dashboard.total_wins,
  );
}

async function restoreSession() {
  if (!state.token) return;
  try {
    const [user, dashboard, participations] = await Promise.all([
      api("/me"),
      api("/me/dashboard"),
      api("/me/participations"),
    ]);
    state.user = user;
    state.participations = participations;
    setAuthenticatedUI(dashboard);
    renderChallenges();
    renderParticipationOptions();
  } catch {
    clearSession(false);
  }
}

function clearSession(notify = true) {
  state.token = null;
  state.user = null;
  state.participations = [];
  window.localStorage.removeItem("arenapulse_token");
  elements.playerPanel.hidden = true;
  document.querySelector("[data-open-auth]").textContent = "Entrar";
  renderChallenges();
  renderParticipationOptions();
  if (notify) showToast("Sessão encerrada.");
}

async function login(username, password) {
  const body = new URLSearchParams({ username, password });
  const result = await api("/auth/login", {
    method: "POST",
    auth: false,
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  state.token = result.access_token;
  window.localStorage.setItem("arenapulse_token", state.token);
  await restoreSession();
}

async function joinChallenge(challengeId) {
  if (!state.token) {
    elements.authDialog.showModal();
    showToast("Entre na sua conta para participar.", "error");
    return { ok: false, reason: "authentication_required" };
  }
  try {
    await api(`/challenges/${challengeId}/join`, { method: "POST" });
    state.participations = await api("/me/participations");
    const dashboard = await api("/me/dashboard");
    setAuthenticatedUI(dashboard);
    renderChallenges();
    renderParticipationOptions();
    showToast("Inscrição confirmada. Boa partida!");
    return { ok: true, challengeId };
  } catch (error) {
    showToast(errorMessage(error), "error");
    return { ok: false, reason: errorMessage(error) };
  }
}

function openSearch() {
  elements.searchDialog.showModal();
  const input = document.querySelector("#search-input");
  input.value = "";
  renderSearchResults("");
  window.setTimeout(() => input.focus(), 0);
}

function renderSearchResults(query) {
  const target = document.querySelector("#search-results");
  target.replaceChildren();
  const normalized = query.trim().toLocaleLowerCase("pt-BR");
  const matches = state.challenges.filter((challenge) =>
    [
      challenge.title,
      challenge.description,
      challenge.reward,
      challenge.game.name,
    ]
      .filter(Boolean)
      .some((value) => value.toLocaleLowerCase("pt-BR").includes(normalized)),
  );
  if (!matches.length) {
    target.append(addText("p", "empty-state", "Nenhum desafio encontrado."));
    return;
  }
  matches.forEach((challenge) => {
    const button = document.createElement("button");
    button.className = "search-result";
    button.type = "button";
    button.dataset.searchChallenge = String(challenge.id);
    button.append(
      addText("strong", "", challenge.title),
      addText("small", "", challenge.game.name),
    );
    target.append(button);
  });
}

function focusChallenge(challengeId) {
  state.filter = "all";
  document.querySelectorAll("[data-filter]").forEach((button) => {
    const active = button.dataset.filter === "all";
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  renderChallenges();
  const row = document.querySelector(
    `[data-challenge-id="${challengeId}"].challenge-row`,
  );
  row?.classList.add("is-highlighted");
  row?.scrollIntoView({ behavior: "smooth", block: "center" });
  window.setTimeout(() => row?.classList.remove("is-highlighted"), 1600);
  loadRanking(challengeId);
}

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((item) => {
      const active = item === button;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", String(active));
    });
    renderChallenges();
  });
});

elements.challengeList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-challenge-id]");
  if (button) joinChallenge(Number(button.dataset.challengeId));
});

document
  .querySelector("[data-refresh-ranking]")
  .addEventListener("click", () => loadRanking());
document.querySelector(".search-trigger").addEventListener("click", openSearch);
document
  .querySelector("#search-input")
  .addEventListener("input", (event) =>
    renderSearchResults(event.target.value),
  );
document.querySelector("#search-results").addEventListener("click", (event) => {
  const button = event.target.closest("[data-search-challenge]");
  if (!button) return;
  elements.searchDialog.close();
  focusChallenge(Number(button.dataset.searchChallenge));
});

document.addEventListener("keydown", (event) => {
  if (
    (event.ctrlKey || event.metaKey) &&
    event.key.toLocaleLowerCase() === "k"
  ) {
    event.preventDefault();
    if (!elements.searchDialog.open) openSearch();
  }
});

document.querySelector("[data-open-auth]").addEventListener("click", () => {
  if (state.user) elements.playerPanel.scrollIntoView({ behavior: "smooth" });
  else elements.authDialog.showModal();
});

document.querySelectorAll("[data-close-dialog]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});

document.querySelectorAll("[data-auth-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    const mode = button.dataset.authMode;
    document.querySelector("#login-form").hidden = mode !== "login";
    document.querySelector("#register-form").hidden = mode !== "register";
    document.querySelectorAll("[data-auth-mode]").forEach((item) => {
      const active = item === button;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", String(active));
    });
  });
});

document
  .querySelector("#login-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("[type=submit]");
    const values = new FormData(form);
    setButtonState(button, "loading", "Entrando…");
    setFormMessage(form);
    try {
      await login(values.get("username"), values.get("password"));
      elements.authDialog.close();
      form.reset();
      showToast(`Bem-vindo, ${state.user.username}.`);
    } catch (error) {
      setFormMessage(form, errorMessage(error), "error");
    } finally {
      setButtonState(button, "");
    }
  });

document
  .querySelector("#register-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("[type=submit]");
    const values = Object.fromEntries(new FormData(form));
    setButtonState(button, "loading", "Criando conta…");
    setFormMessage(form);
    try {
      await api("/auth/register", {
        method: "POST",
        auth: false,
        json: values,
      });
      await login(values.username, values.password);
      elements.authDialog.close();
      form.reset();
      showToast("Conta criada. Sua arena está pronta.");
    } catch (error) {
      setFormMessage(form, errorMessage(error), "error");
    } finally {
      setButtonState(button, "");
    }
  });

document.querySelector("[data-open-create]").addEventListener("click", () => {
  const form = document.querySelector("#create-form");
  const start = new Date(Date.now() + 3600000);
  const end = new Date(Date.now() + 7 * 86400000);
  form.elements.starts_at.value = start.toISOString().slice(0, 16);
  form.elements.ends_at.value = end.toISOString().slice(0, 16);
  elements.createDialog.showModal();
});

document
  .querySelector("#create-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("[type=submit]");
    const values = Object.fromEntries(new FormData(form));
    const payload = {
      ...values,
      game_id: Number(values.game_id),
      starts_at: new Date(values.starts_at).toISOString(),
      ends_at: new Date(values.ends_at).toISOString(),
    };
    setButtonState(button, "loading", "Publicando…");
    setFormMessage(form);
    try {
      const created = await api("/challenges", {
        method: "POST",
        json: payload,
      });
      elements.createDialog.close();
      form.reset();
      await loadChallenges();
      focusChallenge(created.id);
      showToast("Desafio publicado na arena.");
    } catch (error) {
      setFormMessage(form, errorMessage(error), "error");
    } finally {
      setButtonState(button, "");
    }
  });

document.querySelector("[data-open-result]").addEventListener("click", () => {
  if (!state.participations.length) {
    showToast("Entre em um desafio antes de registrar um placar.", "error");
    document
      .querySelector("#challenges-title")
      .scrollIntoView({ behavior: "smooth" });
    return;
  }
  renderParticipationOptions();
  elements.resultDialog.showModal();
});

document
  .querySelector("#result-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("[type=submit]");
    const values = Object.fromEntries(new FormData(form));
    const challengeId = Number(values.challenge_id);
    const payload = {
      score_for: Number(values.score_for),
      score_against: Number(values.score_against),
      notes: values.notes || null,
    };
    setButtonState(button, "loading", "Calculando pontos…");
    setFormMessage(form);
    try {
      const result = await api(`/challenges/${challengeId}/results`, {
        method: "POST",
        json: payload,
      });
      const dashboard = await api("/me/dashboard");
      state.participations = await api("/me/participations");
      setAuthenticatedUI(dashboard);
      elements.resultDialog.close();
      form.reset();
      await loadRanking(challengeId);
      showToast(`Resultado registrado: +${result.points_awarded} pontos.`);
    } catch (error) {
      setFormMessage(form, errorMessage(error), "error");
    } finally {
      setButtonState(button, "");
    }
  });

document
  .querySelector("[data-logout]")
  .addEventListener("click", () => clearSession());

function registerWebMCP() {
  if (!window.navigator.modelContext?.registerTool) return;
  window.navigator.modelContext.registerTool({
    name: "list_open_challenges",
    description: "Lista os desafios publicados que aparecem na ArenaPulse.",
    inputSchema: { type: "object", properties: {} },
    annotations: { readOnlyHint: true },
    execute: async () => ({
      content: state.challenges.map((challenge) => ({
        id: challenge.id,
        title: challenge.title,
        game: challenge.game.name,
        reward: challenge.reward,
        endsAt: challenge.ends_at,
      })),
    }),
  });
  window.navigator.modelContext.registerTool({
    name: "join_challenge",
    description: "Inscreve a pessoa autenticada em um desafio da ArenaPulse.",
    inputSchema: {
      type: "object",
      properties: {
        challengeId: { type: "integer", description: "ID do desafio" },
      },
      required: ["challengeId"],
    },
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: true,
    },
    execute: async ({ challengeId }) => ({
      content: await joinChallenge(challengeId),
    }),
  });
}

async function initialize() {
  try {
    await loadChallenges();
    await restoreSession();
    await loadRanking();
    registerWebMCP();
  } catch (error) {
    showToast(`Falha ao abrir a arena: ${errorMessage(error)}`, "error");
  }
}

initialize();
