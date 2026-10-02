export function without(set, item) {
  const next = new Set(set);
  next.delete(item);
  return next;
}
