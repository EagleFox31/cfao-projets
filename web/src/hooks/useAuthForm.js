import { useCallback, useState } from 'react'
import {
  CODES_ERREUR,
  CODES_SUCCES,
  messageAuth,
  validerConnexion,
  validerOubli,
} from '../utils/authErreurs.js'

const INITIAL_LOGIN = {
  email: '',
  password: '',
  remember: false,
}

const INITIAL_FORGOT = {
  email: '',
}

/**
 * @param onLogin  (identifiant, motDePasse, seSouvenir) => Promise<null | code de refus>
 */
export default function useAuthForm(onLogin) {
  const [panel, setPanel] = useState('login')
  const [login, setLogin] = useState(INITIAL_LOGIN)
  const [forgot, setForgot] = useState(INITIAL_FORGOT)
  const [showPassword, setShowPassword] = useState(false)
  const [fieldErrors, setFieldErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [formSuccess, setFormSuccess] = useState(null)
  const [loading, setLoading] = useState(false)

  const clearFeedback = useCallback(() => {
    setFieldErrors({})
    setFormError(null)
    setFormSuccess(null)
  }, [])

  const openForgot = useCallback(() => {
    clearFeedback()
    setForgot({ email: login.email })
    setPanel('forgot')
  }, [clearFeedback, login.email])

  const closeForgot = useCallback(() => {
    clearFeedback()
    setPanel('login')
  }, [clearFeedback])

  const updateLogin = useCallback((key, value) => {
    setLogin((prev) => ({ ...prev, [key]: value }))
    setFieldErrors((prev) => {
      if (!prev[key]) return prev
      const next = { ...prev }
      delete next[key]
      return next
    })
    setFormError(null)
  }, [])

  const updateForgot = useCallback((value) => {
    setForgot({ email: value })
    setFieldErrors((prev) => {
      if (!prev.email) return prev
      const next = { ...prev }
      delete next.email
      return next
    })
    setFormError(null)
    setFormSuccess(null)
  }, [])

  const submitLogin = useCallback(async (event) => {
    event.preventDefault()
    clearFeedback()

    const result = validerConnexion(login)
    if (!result.ok) {
      setFieldErrors(result.erreurs)
      return
    }

    setLoading(true)
    try {
      const refus = await onLogin(login.email, login.password, login.remember)
      if (refus) setFormError(CODES_ERREUR[refus] ?? CODES_ERREUR.GENERIC)
    } catch {
      setFormError(CODES_ERREUR.NETWORK)
    } finally {
      setLoading(false)
    }
  }, [clearFeedback, login, onLogin])

  const submitForgot = useCallback(async (event) => {
    event.preventDefault()
    clearFeedback()

    const result = validerOubli(forgot)
    if (!result.ok) {
      setFieldErrors(result.erreurs)
      return
    }

    setLoading(true)
    try {
      await new Promise((resolve) => window.setTimeout(resolve, 800))
      setFormSuccess(CODES_SUCCES.FORGOT_EMAIL_SENT)
    } catch {
      setFormError(CODES_ERREUR.NETWORK)
    } finally {
      setLoading(false)
    }
  }, [clearFeedback, forgot])

  return {
    panel,
    login,
    forgot,
    showPassword,
    setShowPassword,
    fieldErrors,
    formError,
    formSuccess,
    loading,
    openForgot,
    closeForgot,
    updateLogin,
    updateForgot,
    submitLogin,
    submitForgot,
    getMessage: messageAuth,
  }
}
