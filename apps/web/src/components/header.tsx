import Link from 'next/link';
import Container from './container';

export default function Header() {
  return (
    <header>
      <Container className="flex h-14 items-center justify-between">
        <Link href="/" className='font-semibold'>Temporary</Link>
        <nav className='flex gap-4 text-sm'>
          <Link href="/">AlsoTmp</Link>
          <Link href="/">AlsoTmp</Link>
        </nav>
      </Container>
    </header>
  );
}