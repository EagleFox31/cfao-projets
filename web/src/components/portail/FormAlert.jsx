export function FormFieldError({ id, error }) {
  if (!error) return null
  return (
    <p id={id} className="form-field-error" role="alert">
      {error}
    </p>
  )
}

export default function FormAlert({ type = 'error', message }) {
  if (!message) return null
  return (
    <div
      className={`form-alert form-alert--${type}`}
      role={type === 'error' ? 'alert' : 'status'}
      aria-live="polite"
    >
      {message}
    </div>
  )
}
