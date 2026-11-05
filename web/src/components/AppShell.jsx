import Nav from './portail/Nav'

/** Les pages du module sous la barre du portail (l'accueil a la sienne). */
export default function AppShell({ children }) {
  return (
    <>
      <Nav />
      {children}
    </>
  )
}
