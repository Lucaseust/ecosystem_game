/* The server supplies a session language and a local, offline catalogue. */
"use strict";
window.EcoI18n = (() => {
  const language = document.documentElement.lang === "en" ? "en" : "fr";
  let phrases = {}, pattern = null;
  function configure(catalogue) {
    phrases = catalogue;
    const keys = Object.keys(phrases).sort((a, b) => b.length - a.length);
    pattern = keys.length ? new RegExp(keys.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"), "g") : null;
  }
  function t(text) {
    return language === "en" && pattern ? text.replace(pattern, match => phrases[match]) : text;
  }
  return {language, locale: language === "en" ? "en-GB" : "fr-FR", t, configure};
})();
