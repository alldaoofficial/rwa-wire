import articles from "./articles.json";
export const languages = { en: "English", de: "Deutsch", es: "Español", fr: "Français" } as const;
export type Language = keyof typeof languages;
export const translatedPaths: readonly string[] = ["/", "/learn/rwa-crypto-explained/", "/newsletter/", "/bitunix/", "/news/", ...Object.values(articles).map(article => article.path)];
export function languageOf(path: string): Language {
  const code = path.split("/")[1];
  return code === "de" || code === "es" || code === "fr" ? code : "en";
}
export function originalPath(path: string): string {
  const clean = languageOf(path) === "en" ? path : path.replace(/^\/(de|es|fr)(?=\/|$)/, "");
  return (clean || "/").replace(/\/?$/, "/");
}
export function localizedPath(path: string, lang: Language): string {
  const original = originalPath(path);
  return lang === "en" ? original : `/${lang}${original}`;
}
export function alternates(path: string) {
  const original = originalPath(path);
  if (!(translatedPaths as readonly string[]).includes(original)) return [];
  return (Object.keys(languages) as Language[]).map(lang => ({lang, path: localizedPath(original, lang)}));
}
