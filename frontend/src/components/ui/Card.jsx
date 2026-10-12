export default function Card({ children, className = '', as: Tag = 'div', ...props }) {
  return (
    <Tag
      className={`rounded-lg border border-trace-border bg-trace-surface shadow-trace ${className}`}
      {...props}
    >
      {children}
    </Tag>
  );
}
