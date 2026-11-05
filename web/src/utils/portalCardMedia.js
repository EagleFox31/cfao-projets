/**
 * Marque d'une carte de session : logo, ou à défaut un libellé texte.
 * Même table et mêmes règles que le portail (`cardBrandBadge.js`), réduite
 * à ce qu'affichent les cartes du formateur.
 */
const LOGOS_MARQUES = [
  ['Toyota', '/assets/logos/toyota.png'],
  ['Mercedes-Benz', '/assets/logos/mercedes.png'],
  ['Suzuki', '/assets/logos/suzuki.png'],
  ['BYD', '/assets/logos/byd.png'],
  ['Mitsubishi', '/assets/logos/mitsubishi.png'],
  ['Omoda & Jaecoo', '/assets/logos/omoda.png'],
  ['Stellantis', '/assets/logos/stellantis.png'],
  ['Citroën', '/assets/logos/citroen.png'],
  ['Yamaha', '/assets/logos/yamaha.png'],
  ['Renault Trucks', '/assets/logos/renault-trucks.png'],
  ['Hino', '/assets/logos/hino.png'],
  ['Fuso', '/assets/logos/fuso.png'],
  ['Sinotruk', '/assets/logos/sinotruk.png'],
  ['Shacman', '/assets/logos/shacman.png'],
  ['Mercedes Trucks', '/assets/logos/mercedes.png'],
  ['King Long', '/assets/logos/kinglong.png'],
  ['BT', '/assets/logos/bt.png'],
  ['Toyota Material', '/assets/logos/toyota-forklift.png'],
  ['JCB', '/assets/logos/jcb.png'],
  ['Lovol', '/assets/logos/lovol.png'],
]

const LOGOS = Object.fromEntries(LOGOS_MARQUES.map(([nom, logo]) => [nom.toUpperCase(), logo]))

const ALIAS = {
  'MERCEDES-BENZ': 'MERCEDES-BENZ',
  MERCEDES: 'MERCEDES-BENZ',
  'OMODA & JAECCO': 'OMODA & JAECCO',
  'OMODA-JAECCO': 'OMODA & JAECCO',
  'OMODA-JAECOO': 'OMODA & JAECCO',
  'TOYOTA FORKLIFT': 'TOYOTA MATERIAL',
  'TOYOTA-FORKLIFT': 'TOYOTA MATERIAL',
  'TOYOTA MATERIAL': 'TOYOTA MATERIAL',
  'RENAULT TRUCKS': 'RENAULT TRUCKS',
  'RENAULT-TRUCKS': 'RENAULT TRUCKS',
  'KING LONG': 'KING LONG',
  'KING-LONG': 'KING LONG',
  'MERCEDES TRUCKS': 'MERCEDES TRUCKS',
}

const LIBELLES = {
  'TOUTES MARQUES': 'Toutes marques',
  'TOUTES MARQUES VL': 'Toutes marques',
  CARROSSERIE: 'Carrosserie',
  'PROCESS SAV': 'Process SAV',
  'PROCESS SAV & PARTS': 'Process SAV',
  'PARTS & PROCESS': 'Parts & Process',
  'PARTS & PROCESS MOTORS': 'SAV Motors',
  'PARTS & PROCESS EQUIPMENT': 'SAV Equipment',
  'RENAULT-TRUCKS': 'Renault Trucks',
  'KING-LONG': 'King Long',
  'TOYOTA-FORKLIFT': 'Toyota Material',
  'OMODA-JAECCO': 'Omoda & Jaecoo',
  'OMODA-JAECOO': 'Omoda & Jaecoo',
}

function norm(s) {
  return (s ?? '').trim().toUpperCase()
}

function chercherLogo(brut) {
  const cle = norm(brut)
  const espace = cle.replace(/-/g, ' ')
  const alias = ALIAS[cle] ?? ALIAS[espace] ?? cle
  return LOGOS[alias] ?? LOGOS[espace] ?? LOGOS[alias.split(' ')[0]] ?? null
}

function libelle(brut) {
  const cle = norm(brut)
  if (LIBELLES[cle]) return LIBELLES[cle]
  if (cle.startsWith('TOUTES MARQUES')) return 'Toutes marques'
  if (cle.includes('CARROSSERIE')) return 'Carrosserie'
  if (/PROCESS/.test(cle) && /SAV|PARTS/.test(cle)) return 'Process SAV'

  return brut
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ')
}

/** Logo marque pour le corps de carte (comme SessionCard). */
export function resolvePortalCardBrand(brand) {
  const brut = brand?.trim()
  if (!brut) return {}
  const logo = chercherLogo(brut)
  return logo ? { logo } : { label: libelle(brut) }
}
