export function without(set, item) {
  const next = new Set(set);
  next.delete(item);
  return next;
}

export function omit(obj, key) {
  const { [key]: _, ...rest } = obj;
  return rest;
}
