(() => {
  const form = document.getElementById("review");
  if (!form) return;

  const endpoint = form.dataset.endpoint;
  const key = "review-sent:" + form.dataset.slug;
  const formStep = form.querySelector('[data-step="form"]');
  const doneStep = form.querySelector('[data-step="done"]');
  const status = form.querySelector(".review-status");
  const textarea = form.elements.comment;
  const buttons = [...form.querySelectorAll("[data-action]")];
  const modal = document.getElementById("review-modal");

  document.querySelectorAll("[data-open-review]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      window.openModal(modal);
      if (!formStep.hidden) textarea.focus();
    });
  });
  if (location.hash === "#review") window.openModal(modal);

  function showDone(action) {
    form.querySelector("[data-done-title]").textContent =
      action === "approve" ? "ممنون، تأیید شما ثبت شد" : "ممنون، نظر شما ثبت شد";
    form.querySelector("[data-done-text]").textContent =
      action === "approve"
        ? "مقاله به‌زودی با همین متن منتشر می‌شود."
        : "اصلاحات را اعمال می‌کنیم و نسخه جدید را برایتان می‌فرستیم.";
    formStep.hidden = true;
    doneStep.hidden = false;
  }

  function setStatus(text, ok) {
    status.textContent = text;
    status.classList.toggle("is-ok", ok === true);
    status.classList.toggle("is-err", ok === false);
  }

  try {
    const prev = localStorage.getItem(key);
    if (prev) showDone(prev);
  } catch (e) {}

  form.querySelector("[data-again]").addEventListener("click", () => {
    doneStep.hidden = true;
    formStep.hidden = false;
    textarea.value = "";
    setStatus("");
    textarea.focus();
  });

  async function send(action) {
    const comment = textarea.value.trim();
    if (action === "comment" && !comment) {
      setStatus("لطفاً ابتدا نظر خود را در کادر بنویسید.", false);
      textarea.focus();
      return;
    }
    buttons.forEach((b) => (b.disabled = true));
    setStatus("در حال ارسال...");
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "text/plain;charset=UTF-8" },
        body: JSON.stringify({
          slug: form.dataset.slug,
          title: form.dataset.title,
          action,
          comment,
          url: decodeURI(location.origin + location.pathname),
          website: form.elements.website.value,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) throw new Error(res.status);
      try { localStorage.setItem(key, action); } catch (e) {}
      setStatus("");
      showDone(action);
    } catch (e) {
      setStatus("ارسال انجام نشد. اتصال اینترنت را بررسی کنید و دوباره امتحان کنید.", false);
    } finally {
      buttons.forEach((b) => (b.disabled = false));
    }
  }

  buttons.forEach((b) => b.addEventListener("click", () => send(b.dataset.action)));
  form.addEventListener("submit", (e) => e.preventDefault());
  modal.addEventListener("cancel", () => setStatus(""));
})();
