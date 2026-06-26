import './styles.css';

export const metadata = {
  title: 'RWA Risk Sentinel',
  description: 'Agentic RWA risk oracle on Casper'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
