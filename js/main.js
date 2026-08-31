document.documentElement.classList.add("js");

const WA =
  "https://wa.me/989054092053?text=" +
  encodeURIComponent(
    "سلام. من از سایت دکتر نادر اکبری دیلمقانی برای نوبت‌دهی پیام می‌دهم. لطفاً راهنمایی‌ام کنید. با تشکر."
  );

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
  document.body.style.overflow = "";
}

document.querySelectorAll("[data-open]").forEach((el) => {
  el.addEventListener("click", () => openSheet(el.getAttribute("data-open")));
});

document.querySelectorAll("[data-close]").forEach((el) => {
  el.addEventListener("click", closeSheets);
});

document.querySelectorAll(".sheet-nav a").forEach((el) => {
  el.addEventListener("click", () => {
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
        const start = performance.now();
        const dur = 1400;
        const tick = (now) => {
          const p = Math.min(1, (now - start) / dur);
          const eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(to * eased).toLocaleString("en-US") + "+";
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
  el.setAttribute("href", WA);
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
