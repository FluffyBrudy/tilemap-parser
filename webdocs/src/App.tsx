import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { SearchModal } from "./components/SearchModal";
import { Seo } from "./components/Seo";
import { Home } from "./pages/Home";
import { Installation } from "./pages/Installation";
import { QuickStart } from "./pages/QuickStart";
import { Examples } from "./pages/Examples";
import { ApiReference } from "./pages/ApiReference";
import { CollisionPage } from "./pages/CollisionPage";
import { CollisionRunnerPage } from "./pages/CollisionRunnerPage";
import { JsonFormatsPage } from "./pages/JsonFormatsPage";
import { TechnicalPage } from "./pages/TechnicalPage";

function App() {
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-zinc-900 text-zinc-100 font-sans">
        <Seo />
        <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
        <Sidebar onSearchOpen={() => setSearchOpen(true)} />
        <main className="ml-64 p-8 lg:p-12">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/installation" element={<Installation />} />
            <Route path="/quickstart" element={<QuickStart />} />
            <Route path="/examples" element={<Examples />} />
            <Route path="/examples/:exampleId" element={<Examples />} />
            <Route path="/api" element={<ApiReference />} />
            <Route path="/api/:section" element={<ApiReference />} />
            <Route path="/collision" element={<CollisionPage />} />
            <Route path="/collision/:section" element={<CollisionPage />} />
            <Route path="/collision-runner" element={<CollisionRunnerPage />} />
            <Route
              path="/collision-runner/:section"
              element={<CollisionRunnerPage />}
            />
            <Route path="/json-formats" element={<JsonFormatsPage />} />
            <Route path="/technical" element={<TechnicalPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
