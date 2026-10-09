(function () {
  const grid = document.getElementById("pub-grid");
  if (!grid) return;

  const searchEl = document.getElementById("pub-search");
  const yearEl = document.getElementById("pub-year");
  const topicEl = document.getElementById("pub-topic");
  const sortEl = document.getElementById("pub-sort");
  const searchM = document.getElementById("pub-search-m");
  const yearM = document.getElementById("pub-year-m");
  const topicM = document.getElementById("pub-topic-m");
  const sortM = document.getElementById("pub-sort-m");
  const countEl = document.getElementById("pub-count");
  const statsEl = document.getElementById("pub-stats");
  const updatedEl = document.getElementById("pub-updated");
  const scholarEl = document.getElementById("pub-scholar-link");
  const emptyEl = document.getElementById("pub-empty");
  const errorEl = document.getElementById("pub-error");
  const paginationEl = document.getElementById("pub-pagination");
  const fab = document.getElementById("pub-fab");
  const modal = document.getElementById("pub-modal");
  const modalApply = document.getElementById("pub-modal-apply");

  const DATA_URL = "/مقالات-علمی/data/index.json";
  const PAGE_SIZE = 12;
  const mobileMq = window.matchMedia("(max-width: 767px)");

  let allPubs = [];
  let currentPage = 1;
  let debounce = 0;

  const norm = (s) => String(s || "").toLowerCase().replace(/\s+/g, " ").trim();
  const FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹";
  const AR_DIGITS = "٠١٢٣٤٥٦٧٨٩";

  function toEnDigits(s) {
    let out = String(s || "");
    for (let i = 0; i <= 9; i += 1) {
      out = out.replaceAll(FA_DIGITS[i], String(i)).replaceAll(AR_DIGITS[i], String(i));
    }
    return out;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function escapeAttr(s) {
    return escapeHtml(s).replace(/'/g, "&#39;");
  }

  function truncate(s, max) {
    const t = String(s || "").trim();
    if (t.length <= max) return t;
    return t.slice(0, max - 1).trimEnd() + "…";
  }

  function formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso + "T12:00:00");
    if (Number.isNaN(d.getTime())) return "";
    return `به‌روزرسانی داده: ${d.toLocaleDateString("fa-IR", { year: "numeric", month: "long", day: "numeric" })}`;
  }

  function skeletonCard() {
    return (
      '<div class="pub-card pub-card--skeleton" aria-hidden="true">' +
      '<span class="pub-skel pub-skel-topic"></span>' +
      '<span class="pub-skel pub-skel-title"></span>' +
      '<span class="pub-skel pub-skel-line"></span>' +
      '<span class="pub-skel pub-skel-line short"></span>' +
      "</div>"
    );
  }

  function showSkeleton() {
    grid.setAttribute("aria-busy", "true");
    grid.dataset.loading = "true";
    grid.innerHTML = skeletonCard().repeat(6);
    if (paginationEl) paginationEl.hidden = true;
  }

  function renderStats(stats, updated) {
    if (!statsEl) return;
    const parts = [
      `${stats.total.toLocaleString("fa-IR")} مقاله`,
      `${stats.citations.toLocaleString("fa-IR")} استناد`,
      `h-index ${stats.hIndex.toLocaleString("fa-IR")}`,
      `i10-index ${stats.i10Index.toLocaleString("fa-IR")}`,
    ];
    statsEl.textContent = parts.join(" · ");
    if (updatedEl) updatedEl.textContent = formatDate(updated);
    if (scholarEl && stats.scholarUrl) scholarEl.href = stats.scholarUrl;
  }

  function fillSelect(select, options, formatter) {
    if (!select) return;
    const keep = select.querySelector("option");
    select.innerHTML = "";
    if (keep) select.appendChild(keep);
    options.forEach((v) => {
      const opt = document.createElement("option");
      opt.value = String(v);
      opt.textContent = formatter ? formatter(v) : v;
      select.appendChild(opt);
    });
  }

  function populateFilters(pubs) {
    const years = [...new Set(pubs.map((p) => p.year).filter(Boolean))].sort((a, b) => b - a);
    const topics = [...new Set(pubs.map((p) => p.topic).filter(Boolean))].sort((a, b) => a.localeCompare(b, "fa"));
    [yearEl, yearM].forEach((el) => fillSelect(el, years, (y) => String(y)));
    [topicEl, topicM].forEach((el) => fillSelect(el, topics));
  }

  function getFiltered() {
    const q = norm(searchEl?.value || "");
    const year = yearEl?.value || "";
    const topic = topicEl?.value || "";
    const sort = sortEl?.value || "year";
    let list = allPubs.filter((p) => {
      if (year && String(p.year) !== year) return false;
      if (topic && p.topic !== topic) return false;
      if (q) {
        const hay = norm(`${p.title} ${p.authors} ${p.journal} ${p.topic}`);
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    list.sort((a, b) => {
      if (sort === "citations") {
        if (b.citations !== a.citations) return b.citations - a.citations;
        return (b.year || 0) - (a.year || 0);
      }
      if ((b.year || 0) !== (a.year || 0)) return (b.year || 0) - (a.year || 0);
      return b.citations - a.citations;
    });
    return list;
  }

  function renderCount(shown, total, page, pages) {
    if (!countEl) return;
    let text;
    if (shown === total) {
      text = `${total.toLocaleString("fa-IR")} مقاله`;
    } else {
      text = `نمایش ${shown.toLocaleString("fa-IR")} از ${total.toLocaleString("fa-IR")} مقاله`;
    }
    if (pages > 1) {
      text += ` · صفحه ${page.toLocaleString("fa-IR")} از ${pages.toLocaleString("fa-IR")}`;
    }
    countEl.textContent = text;
  }

  function cardHtml(p) {
    const topic = p.topic ? `<span class="pub-card__topic">${escapeHtml(p.topic)}</span>` : "";
    const year = p.year ? `<span class="pub-card__year">${escapeHtml(toEnDigits(String(p.year)))}</span>` : "";
    const cites = Number(p.citations || 0);
    const title = escapeHtml(toEnDigits(p.title));
    const authors = escapeHtml(toEnDigits(truncate(p.authors, 120)));
    const journal = escapeHtml(toEnDigits(truncate(p.journal, 100)));
    return (
      `<article class="pub-card">` +
      `<div class="pub-card__top">${topic}${year}</div>` +
      `<h3 class="pub-card__title" dir="ltr" lang="en">${title}</h3>` +
      `<p class="pub-card__authors" dir="ltr" lang="en">${authors}</p>` +
      `<p class="pub-card__journal" dir="ltr" lang="en">${journal}</p>` +
      `<div class="pub-card__footer">` +
      `<span class="pub-card__cites">${cites.toLocaleString("en-US")} استناد</span>` +
      `<a class="pub-card__cta" href="${escapeAttr(p.url)}" target="_blank" rel="noopener noreferrer">مشاهده مقاله</a>` +
      `</div></article>`
    );
  }

  function renderPagination(totalPages) {
    if (!paginationEl) return;
    if (totalPages <= 1) {
      paginationEl.hidden = true;
      paginationEl.innerHTML = "";
      return;
    }
    paginationEl.hidden = false;
    const prevDisabled = currentPage <= 1;
    const nextDisabled = currentPage >= totalPages;
    const buttons = [];
    buttons.push(
      `<button type="button" class="pub-page-btn" data-page="prev" ${prevDisabled ? "disabled" : ""}>قبلی</button>`
    );
    const window = 5;
    let start = Math.max(1, currentPage - Math.floor(window / 2));
    let end = Math.min(totalPages, start + window - 1);
    start = Math.max(1, end - window + 1);
    for (let i = start; i <= end; i += 1) {
      const active = i === currentPage ? ' aria-current="page"' : "";
      buttons.push(
        `<button type="button" class="pub-page-btn${i === currentPage ? " is-active" : ""}" data-page="${i}"${active}>${i.toLocaleString("fa-IR")}</button>`
      );
    }
    buttons.push(
      `<button type="button" class="pub-page-btn" data-page="next" ${nextDisabled ? "disabled" : ""}>بعدی</button>`
    );
    paginationEl.innerHTML = buttons.join("");
  }

  function render({ scroll } = {}) {
    const list = getFiltered();
    const totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;
    const start = (currentPage - 1) * PAGE_SIZE;
    const slice = list.slice(start, start + PAGE_SIZE);

    renderCount(list.length, allPubs.length, currentPage, totalPages);
    if (emptyEl) emptyEl.hidden = list.length > 0;
    grid.dataset.loading = "false";
    grid.setAttribute("aria-busy", "false");

    if (!list.length) {
      grid.innerHTML = "";
      renderPagination(0);
      return;
    }

    grid.innerHTML = slice.map(cardHtml).join("");
    renderPagination(totalPages);
    if (scroll) {
      document.getElementById("pub-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function resetPage() {
    currentPage = 1;
  }

  function syncModalFromMain() {
    if (searchM) searchM.value = searchEl?.value || "";
    if (yearM) yearM.value = yearEl?.value || "";
    if (topicM) topicM.value = topicEl?.value || "";
    if (sortM) sortM.value = sortEl?.value || "year";
  }

  function applyModalToMain() {
    if (searchEl && searchM) searchEl.value = searchM.value;
    if (yearEl && yearM) yearEl.value = yearM.value;
    if (topicEl && topicM) topicEl.value = topicM.value;
    if (sortEl && sortM) sortEl.value = sortM.value;
    resetPage();
    render({ scroll: true });
  }

  function openModal() {
    if (!modal) return;
    syncModalFromMain();
    modal.hidden = false;
    document.body.classList.add("pub-modal-open");
    if (fab) fab.hidden = true;
    modalApply?.focus();
  }

  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    document.body.classList.remove("pub-modal-open");
    updateFabVisibility();
    if (fab && !fab.hidden) fab.focus();
  }

  function updateFabVisibility() {
    if (!fab) return;
    fab.hidden = !mobileMq.matches;
  }

  function bindEvents() {
    [yearEl, topicEl, sortEl].forEach((el) => {
      el?.addEventListener("change", () => {
        resetPage();
        render();
      });
    });
    searchEl?.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        resetPage();
        render();
      }, 180);
    });

    paginationEl?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-page]");
      if (!btn || btn.disabled) return;
      const raw = btn.getAttribute("data-page");
      const totalPages = Math.max(1, Math.ceil(getFiltered().length / PAGE_SIZE));
      if (raw === "prev") currentPage -= 1;
      else if (raw === "next") currentPage += 1;
      else currentPage = Number(raw) || 1;
      currentPage = Math.min(Math.max(1, currentPage), totalPages);
      render({ scroll: true });
    });

    fab?.addEventListener("click", openModal);
    modalApply?.addEventListener("click", () => {
      applyModalToMain();
      closeModal();
    });
    modal?.querySelectorAll("[data-pub-close]").forEach((el) => {
      el.addEventListener("click", closeModal);
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal && !modal.hidden) closeModal();
    });
    mobileMq.addEventListener("change", updateFabVisibility);
    updateFabVisibility();
  }

  function fail() {
    grid.dataset.loading = "false";
    grid.setAttribute("aria-busy", "false");
    grid.innerHTML = "";
    if (errorEl) errorEl.hidden = false;
    if (paginationEl) paginationEl.hidden = true;
  }

  async function init() {
    showSkeleton();
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error("bad status");
      const data = await res.json();
      allPubs = data.publications || [];
      renderStats(data.stats || {}, data.updated);
      populateFilters(allPubs);
      render();
      bindEvents();
    } catch {
      fail();
    }
  }

  init();
})();
