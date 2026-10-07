const LABELS = { pending: "Replying", failed: "Message not sent", unread: "New reply" };

export default function StatusDot({ status }) {
  if (!status) return null;
  return <span className={`status ${status}`} role="img" aria-label={LABELS[status]} />;
}
