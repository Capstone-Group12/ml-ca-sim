import Link from "next/link";
import Container from "./container";

export default function Header() {
  return (
    <header className="header">
      <Container className="flex h-14 items-center justify-between text-white">
        <Link href="/" className="text-lg font-semibold hover:opacity-90">
          CA Sim
        </Link>
      </Container>
    </header>
  );
}
