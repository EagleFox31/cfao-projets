import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Unites d'ecran compensees de la mise a l'echelle (cf. src/utils/echelle.js).
 * Sous `zoom`, `100vh` ne couvre plus que 80 % de la fenetre : chaque
 * `vh`/`vw` est divise par `--echelle` pour garder sa taille a l'ecran.
 */
const unitesEcran = {
  postcssPlugin: 'unites-ecran',
  Declaration(decl) {
    if (decl.value.includes('--echelle')) return
    decl.value = decl.value.replace(/(^|[^\w.-])(-?\d*\.?\d+)([dsl]?v(?:h|w|min|max))(?![\w-])/g,
      '$1calc($2$3 / var(--echelle, 1))')
  },
}

export default defineConfig(({ mode }) => {
  const env = { ...loadEnv(mode, process.cwd(), ''), ...process.env }
  // Le service d'apercu (LibreOffice) et les comptes rendus en cours
  // tournent a part ; PJ_SERVICE permet de brancher une copie isolee.
  const service = env.PJ_SERVICE || 'http://127.0.0.1:5175'
  return {
    plugins: [react()],
    css: { postcss: { plugins: [unitesEcran] } },
    server: {
      port: 5178,
      proxy: {
        '/apercu': { target: service, changeOrigin: true },
        '/pj-donnees': { target: service, changeOrigin: true },
      },
    },
    build: { outDir: 'dist', sourcemap: false },
  }
})
