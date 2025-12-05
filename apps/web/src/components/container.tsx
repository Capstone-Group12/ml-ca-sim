type Props = React.PropsWithChildren<{ className?: string }>;

export default function Container({ className = '', children }: Props) {
  return <div className={`mx-auto w-full max-w-5xl px-4 ${className}`}>{children}</div>;
}