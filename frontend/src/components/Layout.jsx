export default function Layout({ children, fullWidth }) {
  return (
    <main className={`flex-1 overflow-auto ${fullWidth ? "" : "p-4 md:p-6"}`}>
      {children}
    </main>
  );
}
