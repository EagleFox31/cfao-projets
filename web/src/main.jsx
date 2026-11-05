import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App.jsx'
import { suivreEchelle } from './utils/echelle'
import './styles/portail/index.css'
import './styles/portail/academy.css'
import './styles/portail/portal.css'
import './styles/portail/motion.css'
import './styles/pj.css'

suivreEchelle()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
