(function () {
  const grid = document.getElementById("blog-grid");
  if (!grid) return;

  const cards = [...grid.querySelectorAll(".blog-card")];
  const search = document.getElementById("blog-search");
  const status = document.getElementById("blog-status");
  const empty = document.getElementById("blog-empty");
  const countEl = document.getElementById("blog-count");
  const filters = [...document.querySelectorAll(".blog-filter")];
  let category = "all";
  let timer = 0;

  const norm = (s) => String(s || "").toLowerCase().replace(/\s+/g, " ").trim();

  function setLoading(on) {
    grid.dataset.loading = on ? "true" : "false";
  }

  function apply() {
    const q = norm(search?.value || "");
    let shown = 0;
    cards.forEach((card) => {
      const cat = card.dataset.category || "";
      const blob = norm(card.dataset.search);
      const okCat = category === "all" || cat === category;
      const okQ = !q || blob.includes(q) || norm(card.querySelector(".blog-card-title")?.textContent).includes(q);
      const show = okCat && okQ;
      card.hidden = !show;
      if (show) shown += 1;
    });
    if (countEl) countEl.textContent = `${shown.toLocaleString("fa-IR")} مطلب`;
    if (status) status.textContent = q ? `نتیجه جستجو: ${shown.toLocaleString("fa-IR")} مطلب` : "";
    if (empty) empty.hidden = shown > 0;
    setLoading(false);
  }

  function schedule() {
    setLoading(true);
    clearTimeout(timer);
    timer = setTimeout(apply, 180);
  }

  filters.forEach((btn) => {
    btn.addEventListener("click", () => {
      category = btn.dataset.filter || "all";
      filters.forEach((b) => b.classList.toggle("is-active", b === btn));
      schedule();
    });
  });

  search?.addEventListener("input", schedule);
  apply();
})();
