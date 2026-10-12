import Button from './Button';

export default function ErrorState({
  title = 'Unable to load this analysis.',
  message,
  onRetry,
}) {
  return (
    <div
      className="rounded-lg border border-red-200 bg-red-50/60 px-6 py-8"
      role="alert"
    >
      <p className="text-sm font-medium text-red-900">{title}</p>
      {message ? <p className="mt-2 text-sm text-red-800/90">{message}</p> : null}
      {onRetry ? (
        <div className="mt-4">
          <Button variant="secondary" onClick={onRetry}>
            Retry
          </Button>
        </div>
      ) : null}
    </div>
  );
}
