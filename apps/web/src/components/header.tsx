import Link from 'next/link';
import Container from './container';

export default function Header() {
  return (
    <header className="header">
      <Container className="flex h-14 items-center justify-between">
        <Link href="/" className="font-semibold" style={{ color: '#fff' }}>Home</Link>
        <nav className="flex gap-4 text-sm">
          <Link href="/about" style={{ color: '#fff' }}>About</Link>
          <Link href="/contact" style={{ color: '#fff' }}>Contact</Link>
          <Link href="/simulation" style={{ color: '#fff' }}>Simulation</Link>
        </nav>
      </Container>
    </header>
  );
}
