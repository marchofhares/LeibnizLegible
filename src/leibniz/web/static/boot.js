// boot.js — runs synchronously in <head>, before first paint.
//
// Flips the `no-js` class so the fallback notice and the static layout never
// flash for JS users. It lives in its own file rather than inline so the
// Content-Security-Policy the server sends (`script-src 'self'`) can stay
// free of inline-script exceptions.
document.documentElement.classList.remove('no-js');
