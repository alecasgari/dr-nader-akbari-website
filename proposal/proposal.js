const PASS_HASH = "23f12628bf77bc26a8bb3199e364d8d64a30506ddf8421ca10429d0d9054b71c";
const KEY = "dna-proposal-ok";
const WELCOME = "سلام دکتر اکبری عزیز، به پروپوزال SEO خوش آمدید.";

const gate = document.getElementById("gate");
const deck = document.getElementById("deck");
const form = document.getElementById("gate-form");
const code = document.getElementById("code");
const err = document.getElementById("gate-err");
const slides = [...document.querySelectorAll(".slide")];
const prev = document.getElementById("prev");
const next = document.getElementById("next");
const progressFill = document.getElementById("progress-fill");
const stepNow = document.getElementById("step-now");
const stepAll = document.getElementById("step-all");
const welcome = document.getElementById("welcome");

let index = 0;
let typed = false;
const counted = new Set();
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

stepAll.textContent = toFa(slides.length);

async function sha256(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function toFa(n) {
  return Number(n).toLocaleString("fa-IR");
}

function unlock() {
  gate.hidden = true;
  deck.hidden = false;
  show(0);
  typeWelcome();
}

function lockFail() {
  err.textContent = "رمز درست نیست.";
  code.classList.remove("shake");
  void code.offsetWidth;
  code.classList.add("shake");
  code.select();
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  err.textContent = "";
  const hash = await sha256(code.value.trim());
  if (hash === PASS_HASH) {
    sessionStorage.setItem(KEY, "1");
    unlock();
    return;
  }
  lockFail();
});

if (sessionStorage.getItem(KEY) === "1") unlock();

function show(i) {
  index = Math.max(0, Math.min(slides.length - 1, i));
  slides.forEach((s, n) => s.classList.toggle("is-on", n === index));
  if (progressFill) {
    progressFill.style.width = ((index + 1) / slides.length * 100) + "%";
  }
  stepNow.textContent = toFa(index + 1);
  slides[index].scrollTop = 0;
  prev.hidden = false;
  next.hidden = false;
  prev.style.visibility = index === 0 ? "hidden" : "visible";
  next.style.visibility = index === slides.length - 1 ? "hidden" : "visible";
  next.textContent = "ادامه";
  animateCounts(slides[index]);
}

function animateCounts(slide) {
  if (counted.has(slide)) return;
  const els = [...slide.querySelectorAll("[data-count]")];
  if (!els.length) return;
  counted.add(slide);
  els.forEach((el) => {
    const to = Number(el.dataset.count);
    const suffix = el.dataset.suffix || "";
    if (reduce) {
      el.textContent = toFa(to) + suffix;
      return;
    }
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - start) / 1100);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = toFa(Math.round(to * eased)) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

function typeWelcome() {
  if (!welcome || typed) return;
  typed = true;
  if (reduce) {
    welcome.textContent = WELCOME;
    return;
  }
  let i = 0;
  const run = () => {
    welcome.innerHTML = WELCOME.slice(0, i) + '<span class="caret"></span>';
    i += 1;
    if (i <= WELCOME.length) setTimeout(run, i < 8 ? 55 : 28);
  };
  run();
}

prev.addEventListener("click", () => show(index - 1));
next.addEventListener("click", () => {
  if (index < slides.length - 1) show(index + 1);
});

document.addEventListener("keydown", (e) => {
  if (deck.hidden) return;
  if (e.key === "ArrowLeft" || e.key === "ArrowDown") show(index + 1);
  if (e.key === "ArrowRight" || e.key === "ArrowUp") show(index - 1);
});

let touchX = null;
deck.addEventListener("touchstart", (e) => {
  touchX = e.changedTouches[0].clientX;
}, { passive: true });
deck.addEventListener("touchend", (e) => {
  if (touchX == null) return;
  const dx = e.changedTouches[0].clientX - touchX;
  if (Math.abs(dx) > 48) show(index + (dx > 0 ? -1 : 1));
  touchX = null;
}, { passive: true });
