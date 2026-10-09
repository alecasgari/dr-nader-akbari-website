(function () {
  const grid = document.getElementById("pub-grid");
  if (!grid) return;

  const searchEl = document.getElementById("pub-search");
  const yearEl = document.getElementById("pub-year");
  const topicEl = document.getElementById("pub-topic");
  const sortEl = document.getElementById("pub-sort");
  const countEl = document.getElementById("pub-count");
  const statsEl = document.getElementById("pub-stats");
  const updatedEl = document.getElementById("pub-updated");
  const scholarEl = document.getElementById("pub-scholar-link");
  const emptyEl = document.getElementById("pub-empty");
  const errorEl = document.getElementById("pub-error");

  let allPubs = [];
  let debounce = 0;
  const DATA_URL = "/مقالات-علمی/data/index.json";

  const norm = (s) => String(s || "").toLowerCase().replace(/\s+/g, " ").trim();

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

  function populateFilters(pubs) {
    const years = [...new Set(pubs.map((p) => p.year).filter(Boolean))].sort((a, b) => b - a);
    years.forEach((y) => {
      const opt = document.createElement("option");
      opt.value = String(y);
      opt.textContent = y.toLocaleString("fa-IR");
      yearEl.appendChild(opt);
    });
    const topics = [...new Set(pubs.map((p) => p.topic).filter(Boolean))].sort((a, b) => a.localeCompare(b, "fa"));
    topics.forEach((t) => {
      const opt = document.createElement("option");
      opt.value = t;
      opt.textContent = t;
      topicEl.appendChild(opt);
    });
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

  function renderCount(shown, total) {
    if (!countEl) return;
    if (shown === total) {
      countEl.textContent = `${total.toLocaleString("fa-IR")} مقاله`;
    } else {
      countEl.textContent = `نمایش ${shown.toLocaleString("fa-IR")} از ${total.toLocaleString("fa-IR")} مقاله`;
    }
  }

  function render() {
    const list = getFiltered();
    renderCount(list.length, allPubs.length);
    if (emptyEl) emptyEl.hidden = list.length > 0;
    grid.dataset.loading = "false";
    grid.setAttribute("aria-busy", "false");
    if (!list.length) {
      grid.innerHTML = "";
      return;
    }
    grid.innerHTML = list
      .map((p) => {
        const topic = p.topic
          ? `<span class="pub-card__topic">${escapeHtml(p.topic)}</span>`
          : "";
        const year = p.year
          ? `<span class="pub-card__year">${escapeHtml(String(p.year))}</span>`
          : "";
        const cites = Number(p.citations || 0);
        return (
          `<a class="pub-card" href="${escapeAttr(p.url)}" target="_blank" rel="noopener noreferrer">` +
          `<div class="pub-card__top">${topic}${year}</div>` +
          `<h2 class="pub-card__title" dir="ltr" lang="en">${escapeHtml(p.title)}</h2>` +
          `<p class="pub-card__authors" dir="ltr" lang="en">${escapeHtml(truncate(p.authors, 120))}</p>` +
          `<p class="pub-card__journal" dir="ltr" lang="en">${escapeHtml(truncate(p.journal, 100))}</p>` +
          `<div class="pub-card__footer">` +
          `<span class="pub-card__cites">${cites.toLocaleString("fa-IR")} استناد</span>` +
          `<span class="pub-card__arrow" aria-hidden="true">↗</span>` +
          `</div></a>`
        );
      })
      .join("");
  }

  function injectSchema(data) {
    const items = (data.publications || []).slice(0, 50).map((p, i) => ({
      "@type": "ScholarlyArticle",
      position: i + 1,
      name: p.title,
      author: p.authors,
      datePublished: p.year ? String(p.year) : undefined,
      isPartOf: p.journal || undefined,
      url: p.url,
    }));
    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.textContent = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "ItemList",
      itemListElement: items,
    });
    document.head.appendChild(script);
  }

  function bindEvents() {
    [yearEl, topicEl, sortEl].forEach((el) => el?.addEventListener("change", render));
    searchEl?.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(render, 180);
    });
  }

  function fail() {
    grid.dataset.loading = "false";
    grid.setAttribute("aria-busy", "false");
    grid.innerHTML = "";
    if (errorEl) errorEl.hidden = false;
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
      injectSchema(data);
    } catch {
      fail();
    }
  }

  init();
})();
