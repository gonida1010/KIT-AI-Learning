export default function Layout({ children }) {
  return (
    <main className="ml-0 md:ml-64 mt-14 md:mt-0 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-4 md:py-8">
        {children}
      </div>
    </main>
  );
}
