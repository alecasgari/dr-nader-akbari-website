(() => {
  function openModal(modal) {
    if (!modal || modal.open) return;
    modal.showModal();
    document.body.style.overflow = "hidden";
  }
  window.openModal = openModal;

  document.querySelectorAll("dialog.modal").forEach((modal) => {
    modal.addEventListener("close", () => (document.body.style.overflow = ""));
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.close();
    });
    modal.querySelectorAll("[data-close-modal]").forEach((btn) => btn.addEventListener("click", () => modal.close()));
  });

  const instrFab = document.getElementById("instr-fab");
  const instrModal = document.getElementById("instr-dl-modal");
  if (instrFab && instrModal) {
    const closeInstr = () => {
      instrModal.hidden = true;
      document.body.classList.remove("instr-dl-open");
    };
    const openInstr = () => {
      instrModal.hidden = false;
      document.body.classList.add("instr-dl-open");
    };
    instrFab.addEventListener("click", openInstr);
    instrModal.querySelectorAll("[data-instr-close]").forEach((el) => el.addEventListener("click", closeInstr));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !instrModal.hidden) closeInstr();
    });
  }

  const box = document.getElementById("comments");
  if (!box) return;

  const key = "comments:" + box.dataset.slug;
  const list = box.querySelector("[data-comment-list]");
  const form = box.querySelector(".comment-form");
  const status = form.querySelector(".review-status");
  const modal = document.getElementById("comment-modal");

  function load() {
    try {
      return JSON.parse(localStorage.getItem(key)) || [];
    } catch (e) {
      return [];
    }
  }

  function render() {
    list.querySelectorAll("[data-pending]").forEach((node) => node.remove());
    for (const c of load()) {
      const item = document.createElement("article");
      item.className = "comment";
      item.dataset.pending = "";
      const head = document.createElement("div");
      head.className = "comment-head";
      const name = document.createElement("strong");
      name.textContent = c.name;
      const date = document.createElement("time");
      date.textContent = new Date(c.at).toLocaleDateString("fa-IR");
      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = "در انتظار تأیید";
      head.append(name, date, badge);
      const text = document.createElement("p");
      text.textContent = c.comment;
      item.append(head, text);
      list.append(item);
    }
  }

  render();

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const name = form.elements.name.value.trim();
    const comment = form.elements.comment.value.trim();
    if (!name || !comment) {
      status.textContent = "لطفاً نام و دیدگاه خود را بنویسید.";
      status.className = "review-status is-err";
      (name ? form.elements.comment : form.elements.name).focus();
      return;
    }
    status.textContent = "";
    if (box.dataset.preview !== "1" && !form.elements.website.value) {
      fetch(box.dataset.endpoint, {
        method: "POST",
        keepalive: true,
        headers: { "Content-Type": "text/plain;charset=UTF-8" },
        body: JSON.stringify({
          slug: box.dataset.slug,
          title: box.dataset.title,
          action: "reader",
          name,
          comment,
          url: decodeURI(location.origin + location.pathname),
          website: "",
        }),
      }).catch(() => {});
    }
    try {
      localStorage.setItem(key, JSON.stringify([...load(), { name, comment, at: Date.now() }]));
    } catch (err) {}
    render();
    form.reset();
    openModal(modal);
  });
})();
