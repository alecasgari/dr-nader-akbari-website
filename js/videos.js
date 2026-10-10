(function () {
  const dataEl = document.getElementById("vg-data");
  const grid = document.getElementById("vg-grid");
  const modal = document.getElementById("vg-modal");
  if (!dataEl || !grid || !modal) return;

  const videos = JSON.parse(dataEl.textContent);
  const byId = Object.fromEntries(videos.map((v) => [v.id, v]));
  const isHub = document.body.classList.contains("is-videos-hub");
  const videoEl = document.getElementById("vg-modal-video");
  const titleEl = document.getElementById("vg-modal-title");
  const kickerEl = document.getElementById("vg-modal-kicker");
  const bodyEl = document.getElementById("vg-modal-body");
  const linksEl = document.getElementById("vg-modal-links");
  const hubPath = "/ویدیو/";
  let activeId = null;
  let hoverTimer = 0;

  function fillLinks(v) {
    const bits = (v.related || []).map(
      (r) => `<a href="${r.href}">${r.title}</a>`
    );
    if (v.instagram) {
      bits.push(
        `<a href="${v.instagram}" target="_blank" rel="noopener">پست اینستاگرام</a>`
      );
    }
    linksEl.innerHTML = bits.join("");
  }

  function openModal(v, push) {
    if (!v) return;
    activeId = v.id;
    kickerEl.textContent = v.kicker || "";
    titleEl.textContent = v.title;
    bodyEl.innerHTML = v.bodyHtml || "";
    fillLinks(v);
    videoEl.poster = v.poster || "";
    if (videoEl.src !== v.src) videoEl.src = v.src;
    modal.hidden = false;
    document.body.classList.add("vg-lock");
    videoEl.play().catch(() => {});
    if (push && isHub) history.pushState({ vg: v.id }, "", v.path);
  }

  function closeModal(back) {
    videoEl.pause();
    modal.hidden = true;
    document.body.classList.remove("vg-lock");
    activeId = null;
    if (back && isHub && location.pathname !== hubPath) {
      history.pushState({ vg: null }, "", hubPath);
    }
  }

  grid.querySelectorAll(".vg-tile").forEach((tile) => {
    const media = tile.querySelector("video");
    const src = tile.getAttribute("data-src");

    tile.addEventListener("mouseenter", () => {
      if (!media || window.matchMedia("(hover: none)").matches) return;
      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => {
        if (!media.src) media.src = src;
        media.muted = true;
        media.play().catch(() => {});
        tile.classList.add("is-playing");
      }, 180);
    });
    tile.addEventListener("mouseleave", () => {
      clearTimeout(hoverTimer);
      if (!media) return;
      media.pause();
      media.currentTime = 0;
      tile.classList.remove("is-playing");
    });

    tile.addEventListener("click", (e) => {
      if (!isHub) return;
      const v = byId[tile.getAttribute("data-id")];
      if (!v) return;
      e.preventDefault();
      openModal(v, true);
    });
  });

  modal.querySelectorAll("[data-vg-close]").forEach((btn) => {
    btn.addEventListener("click", () => closeModal(true));
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.hidden) closeModal(true);
  });

  window.addEventListener("popstate", (e) => {
    const id = e.state && e.state.vg;
    if (id && byId[id]) openModal(byId[id], false);
    else closeModal(false);
  });

  document.querySelectorAll(".vg-filters [data-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.getAttribute("data-filter");
      document.querySelectorAll(".vg-filters [data-filter]").forEach((b) => {
        b.classList.toggle("is-active", b === btn);
      });
      grid.querySelectorAll(".vg-tile").forEach((tile) => {
        const show = key === "all" || tile.getAttribute("data-kicker") === key;
        tile.hidden = !show;
      });
    });
  });
})();
