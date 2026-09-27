/** Build a site-internal URL that respects Astro\'s configured base path. */
export function sitePath(path = "/"): string {
  const base = import.meta.env.BASE_URL || "/";
  const cleanBase = base.endsWith("/") ? base.slice(0, -1) : base;
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${cleanBase}${cleanPath === "/" ? "/" : cleanPath}`;
}
