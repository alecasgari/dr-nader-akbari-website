document.documentElement.classList.add("js");

const WA_PHONE = "989054092053";
const WA_HOOK = "https://n8n.alecasgari.com/webhook/35e81ab9-7bdd-4a59-b2c4-c5acee6649e0";
const WA_SERVICES = [
  "پولیپ‌های بینی و سینوس",
  "تومورهای بینی و سینوس",
  "سینوزیت‌های چرکی و قارچی",
  "جراحی آندوسکوپی سینوس",
  "جراحی آترزی کوآن",
  "جراحی کیسه اشکی",
  "ترمیم نشت مایع مغزی‌نخاعی",
  "هیپوفیز و کرانیوفارنژیوما",
  "تومورهای قاعده جمجمه",
  "جراحی غدد بزاقی",
  "رینوپلاستی",
  "سایر",
];

function openSheet(id) {
  const sheet = document.getElementById(id);
  if (!sheet) return;
  sheet.classList.add("is-open");
  sheet.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}

function closeSheets() {
  document.querySelectorAll(".sheet.is-open").forEach((sheet) => {
    sheet.classList.remove("is-open");
    sheet.setAttribute("aria-hidden", "true");
  });
  document.querySelectorAll(".sheet-nav .nav-drop").forEach((drop) => {
    drop.classList.remove("is-open");
    const t = drop.querySelector(".nav-drop-toggle");
    if (t) t.setAttribute("aria-expanded", "false");
  });
  document.body.style.overflow = "";
}

document.querySelectorAll("[data-open]").forEach((el) => {
  el.addEventListener("click", () => openSheet(el.getAttribute("data-open")));
});

document.querySelectorAll("[data-close]").forEach((el) => {
  el.addEventListener("click", closeSheets);
});

document.querySelectorAll(".sheet-nav a").forEach((el) => {
  el.addEventListener("click", (e) => {
    if (el.classList.contains("nav-drop-toggle")) {
      e.preventDefault();
      const drop = el.closest(".nav-drop");
      const open = !drop.classList.contains("is-open");
      document.querySelectorAll(".sheet-nav .nav-drop.is-open").forEach((d) => {
        if (d !== drop) {
          d.classList.remove("is-open");
          const t = d.querySelector(".nav-drop-toggle");
          if (t) t.setAttribute("aria-expanded", "false");
        }
      });
      drop.classList.toggle("is-open", open);
      el.setAttribute("aria-expanded", open ? "true" : "false");
      return;
    }
    const href = el.getAttribute("href") || "";
    if (href.startsWith("#") || href.includes("#")) {
      closeSheets();
    }
  });
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeSheets();
});

document.querySelectorAll(".tablist").forEach((list) => {
  const tabs = [...list.querySelectorAll("[role='tab']")];
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const panelId = tab.getAttribute("aria-controls");
      tabs.forEach((t) => t.setAttribute("aria-selected", "false"));
      tab.setAttribute("aria-selected", "true");
      list.parentElement.querySelectorAll("[role='tabpanel']").forEach((p) => {
        p.classList.toggle("is-open", p.id === panelId);
      });
    });
  });
});

const counters = document.querySelectorAll("[data-count]");
if (counters.length) {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const to = Number(el.dataset.count);
        const suffix = el.dataset.countSuffix !== undefined ? el.dataset.countSuffix : "+";
        const locale = el.dataset.countLocale || "en-US";
        const start = performance.now();
        const dur = 1400;
        const tick = (now) => {
          const p = Math.min(1, (now - start) / dur);
          const eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(to * eased).toLocaleString(locale) + suffix;
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
        io.unobserve(el);
      });
    },
    { threshold: 0.4 }
  );
  counters.forEach((el) => io.observe(el));
}

document.querySelectorAll("[data-wa]").forEach((el) => {
  el.setAttribute("href", "#wa-lead");
  el.setAttribute("role", "button");
});

document.querySelectorAll(".toc").forEach((toc) => {
  const wide = matchMedia("(min-width: 1024px)");
  toc.open = wide.matches;
  toc.addEventListener("click", (e) => {
    if (e.target.closest("a") && !wide.matches) toc.open = false;
  });
});

document.addEventListener("click", (e) => {
  const a = e.target.closest("a");
  if (!a || typeof gtag !== "function") return;
  const href = a.getAttribute("href") || "";
  const where = a.closest(".dock") ? "dock" : a.closest(".site-header") ? "header" : a.closest(".site-footer") ? "footer" : "page";
  const name = a.hasAttribute("data-wa") ? "whatsapp_click"
    : href.startsWith("tel:") ? "phone_click"
    : a.classList.contains("map-link") ? "map_click" : "";
  if (!name) return;
  gtag("event", name, { link_location: where });
  dataLayer.push({ event: name, link_location: where });
});

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const slides = document.querySelectorAll(".hero-slide");
if (slides.length > 1 && !reduceMotion) {
  let i = 0;
  setInterval(() => {
    slides[i].classList.remove("is-active");
    i = (i + 1) % slides.length;
    slides[i].classList.add("is-active");
  }, 4200);
}

const revealEls = document.querySelectorAll(".reveal");
if (revealEls.length) {
  if (reduceMotion) {
    revealEls.forEach((el) => el.classList.add("is-in"));
  } else {
    const rio = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-in");
          rio.unobserve(entry.target);
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -6% 0px" }
    );
    revealEls.forEach((el) => rio.observe(el));
  }
}

(function waLead() {
  const services = WA_SERVICES.map((name) => `<option value="${name}">${name}</option>`).join("");
  const root = document.createElement("div");
  root.innerHTML = `
    <dialog class="modal wa-lead" id="wa-lead" tabindex="-1" aria-labelledby="wa-lead-title">
      <div class="review-panel">
        <button type="button" class="modal-close" data-wa-close aria-label="بستن">×</button>
        <div data-wa-form>
          <h2 id="wa-lead-title">رزرو نوبت</h2>
          <form class="wa-form" autocomplete="off" novalidate>
            <label for="wa-first">نام</label>
            <input id="wa-first" name="first" type="text" maxlength="40" autocomplete="off" required>
            <label for="wa-last">نام خانوادگی</label>
            <input id="wa-last" name="last" type="text" maxlength="40" autocomplete="off" required>
            <fieldset class="wa-gender">
              <legend>جنسیت</legend>
              <div>
                <label><input type="radio" name="gender" value="خانم" required> خانم</label>
                <label><input type="radio" name="gender" value="آقا"> آقا</label>
              </div>
            </fieldset>
            <label for="wa-service">خدمت مورد نیاز</label>
            <select id="wa-service" name="service" autocomplete="off" required>
              <option value="">انتخاب کنید</option>
              ${services}
            </select>
            <label for="wa-phone">شماره واتساپ</label>
            <input id="wa-phone" name="phone" type="tel" inputmode="numeric" dir="ltr" maxlength="11" autocomplete="off" placeholder="0912xxxxxxx" required>
            <label for="wa-message">پیام (اختیاری)</label>
            <textarea id="wa-message" name="message" maxlength="120" rows="2" autocomplete="off"></textarea>
            <span class="wa-count" data-wa-count>0/120</span>
            <button type="submit" class="btn btn-primary">ارسال و ادامه در واتساپ</button>
            <p class="review-status" data-wa-status role="status" aria-live="polite"></p>
          </form>
        </div>
        <div class="review-done" data-wa-thanks hidden>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m7.5 12.5 3 3 6-6.5"/></svg>
          <h2>ممنون</h2>
          <p data-wa-thanks-text>درخواست شما ثبت شد. واتساپ در تب جدید باز شده است.</p>
          <a class="btn btn-primary" data-wa-open hidden target="_blank" rel="noopener">باز کردن واتساپ</a>
          <button type="button" class="btn btn-outline" data-wa-close>بستن</button>
        </div>
      </div>
    </dialog>`;
  document.body.appendChild(root.firstElementChild);

  const dialog = document.getElementById("wa-lead");
  const form = dialog.querySelector("form");
  const formView = dialog.querySelector("[data-wa-form]");
  const thanks = dialog.querySelector("[data-wa-thanks]");
  const thanksText = dialog.querySelector("[data-wa-thanks-text]");
  const openLink = dialog.querySelector("[data-wa-open]");
  const status = dialog.querySelector("[data-wa-status]");
  const counter = dialog.querySelector("[data-wa-count]");
  const message = form.elements.message;
  let submitted = false;
  let from = "page";
  let openGen = 0;
  let userTouched = false;

  form.addEventListener("pointerdown", (e) => {
    const field = e.target.closest("input, textarea, select");
    if (!field) return;
    userTouched = true;
    field.removeAttribute("readonly");
  }, true);
  form.addEventListener("focusin", (e) => {
    if (e.target.matches && e.target.matches("input, textarea")) e.target.removeAttribute("readonly");
  });

  function utms() {
    const params = new URLSearchParams(location.search);
    const current = {};
    params.forEach((value, key) => {
      const name = key.toLowerCase();
      if (name.startsWith("utm_") && value) current[name] = value.slice(0, 200);
    });
    let stored = {};
    try { stored = JSON.parse(sessionStorage.getItem("akbari_utm") || "{}"); } catch (e) {}
    const merged = Object.assign({}, stored, current);
    if (Object.keys(current).length) {
      try { sessionStorage.setItem("akbari_utm", JSON.stringify(merged)); } catch (e) {}
    }
    return merged;
  }
  utms();

  function place(el) {
    if (el.closest(".dock")) return "dock";
    if (el.closest(".site-header")) return "header";
    if (el.closest(".site-footer")) return "footer";
    return "page";
  }

  function armAutofillLock() {
    form.querySelectorAll("input, textarea").forEach((el) => el.setAttribute("readonly", ""));
  }

  function showForm() {
    formView.hidden = false;
    thanks.hidden = true;
    openLink.hidden = true;
  }

  function blurFields() {
    const active = document.activeElement;
    if (active && active !== dialog && dialog.contains(active)) active.blur();
    dialog.focus();
  }

  function openDialog() {
    if (dialog.open) return;
    const gen = ++openGen;
    submitted = false;
    userTouched = false;
    form.reset();
    counter.textContent = "0/120";
    status.textContent = "";
    status.className = "review-status";
    armAutofillLock();
    showForm();
    dialog.showModal();
    blurFields();
    requestAnimationFrame(blurFields);
    setTimeout(() => {
      if (gen !== openGen || !dialog.open || submitted || userTouched) return;
      form.reset();
      armAutofillLock();
      blurFields();
    }, 350);
  }

  function closeDialog() {
    if (submitted) {
      form.reset();
      counter.textContent = "0/120";
      status.textContent = "";
      status.className = "review-status";
      submitted = false;
    }
    showForm();
    dialog.close();
  }

  message.addEventListener("input", () => {
    if (message.value.length > 120) message.value = message.value.slice(0, 120);
    counter.textContent = message.value.length + "/120";
  });

  form.elements.phone.addEventListener("input", () => {
    const phone = form.elements.phone;
    const digits = phone.value.replace(/[^0-9]/g, "").slice(0, 11);
    if (phone.value !== digits) phone.value = digits;
  });

  dialog.querySelectorAll("[data-wa-close]").forEach((btn) => {
    btn.addEventListener("click", closeDialog);
  });
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) closeDialog();
  });
  dialog.addEventListener("cancel", (e) => {
    e.preventDefault();
    closeDialog();
  });

  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-wa]");
    if (!trigger || dialog.contains(trigger)) return;
    e.preventDefault();
    from = place(trigger);
    openDialog();
  }, true);

  function fail(text, field) {
    status.textContent = text;
    status.className = "review-status is-err";
    if (field) field.focus();
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const first = form.elements.first.value.trim();
    const last = form.elements.last.value.trim();
    const gender = (form.querySelector('input[name="gender"]:checked') || {}).value || "";
    const service = form.elements.service.value;
    const phone = form.elements.phone.value;
    const note = message.value.trim().replace(/\s+/g, " ").slice(0, 120);
    if (first.length < 2) return fail("نام را وارد کنید.", form.elements.first);
    if (last.length < 2) return fail("نام خانوادگی را وارد کنید.", form.elements.last);
    if (!gender) return fail("جنسیت را انتخاب کنید.", form.querySelector('input[name="gender"]'));
    if (!service) return fail("خدمت مورد نیاز را انتخاب کنید.", form.elements.service);
    if (!/^09[0-9]{9}$/.test(phone)) return fail("شماره واتساپ باید ۱۱ رقم انگلیسی و با ۰۹ شروع شود.", form.elements.phone);

    const title = gender === "آقا" ? "آقای" : "خانم";
    const clean = (value) => value.replace(/[*_\n\r]/g, " ").replace(/\s+/g, " ").trim();
    const text = [
      "نام: *" + clean(title + " " + first + " " + last) + "*",
      "شماره واتساپ: *" + phone + "*",
      "خدمت مورد نظر: *" + clean(service) + "*",
      "پیام: " + (note ? clean(note) : "بدون پیام"),
      "",
      "*نکته مهم: جهت رزرو، لطفا این متن را تغییر ندهید*",
    ].join("\n");
    const url = "https://wa.me/" + WA_PHONE + "?text=" + encodeURIComponent(text);
    const tags = utms();
    const payload = new URLSearchParams({
      first_name: first,
      last_name: last,
      gender: gender,
      service: service,
      phone: phone,
      message: note,
      page: location.href,
      referrer: document.referrer || "",
      link_location: from,
      utm_source: tags.utm_source || "",
      utm_medium: tags.utm_medium || "",
      utm_campaign: tags.utm_campaign || "",
      utm_term: tags.utm_term || "",
      utm_content: tags.utm_content || "",
      utm_id: tags.utm_id || "",
    });
    fetch(WA_HOOK, {
      method: "POST",
      keepalive: true,
      body: payload,
    }).catch(() => {});

    const opened = window.open(url, "_blank");
    if (opened) opened.opener = null;
    submitted = true;
    formView.hidden = true;
    thanks.hidden = false;
    if (opened) {
      thanksText.textContent = "درخواست شما ثبت شد. واتساپ در تب جدید باز شده است.";
      openLink.hidden = true;
    } else {
      thanksText.textContent = "درخواست شما ثبت شد. اگر واتساپ باز نشد، دکمه زیر را بزنید.";
      openLink.href = url;
      openLink.hidden = false;
    }
    blurFields();
  });
})();
