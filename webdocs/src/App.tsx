import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Installation from "./pages/Installation";
import QuickStart from "./pages/QuickStart";
import Examples from "./pages/Examples";
import PhysicsBodies from "./pages/PhysicsBodies";
import RunnerGuide from "./pages/RunnerGuide";
import ObjectCollision from "./pages/ObjectCollision";
import Pipeline from "./pages/Pipeline";
import MapParsing from "./pages/MapParsing";
import Animations from "./pages/Animations";
import CameraGuide from "./pages/Camera";
import Particles from "./pages/Particles";
import Pathfinding from "./pages/Pathfinding";
import ApiReference from "./pages/ApiReference";
import FullCollision from "./pages/FullCollision";
import FullPathfinding from "./pages/FullPathfinding";
import FullPhysicsWorld from "./pages/FullPhysicsWorld";
import JsonFormats from "./pages/JsonFormats";
import TechnicalNotes from "./pages/TechnicalNotes";
import { SEO, SITE_DESCRIPTION } from "./seo";

function ScrollManager() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    const seoPath = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
    const seo = SEO[seoPath];
    document.title = seo?.title ?? "tilemap-parser — docs";
    const desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute("content", seo?.description ?? SITE_DESCRIPTION);
  }, [pathname]);
  useEffect(() => {
    if (hash) {
      const el = document.getElementById(hash.slice(1));
      if (el) {
        el.scrollIntoView();
        return;
      }
    }
    window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}

export default function App() {
  return (
    <>
      <ScrollManager />
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/install" element={<Installation />} />
          <Route path="/quick-start" element={<QuickStart />} />
          <Route path="/examples" element={<Examples />} />
          <Route
            path="/examples/full-physics-world"
            element={<FullPhysicsWorld />}
          />
          <Route path="/examples/full-collision" element={<FullCollision />} />
          <Route
            path="/examples/full-pathfinding"
            element={<FullPathfinding />}
          />
          <Route path="/physics" element={<PhysicsBodies />} />
          <Route path="/runner" element={<RunnerGuide />} />
          <Route path="/object-collision" element={<ObjectCollision />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/map-parsing" element={<MapParsing />} />
          <Route path="/animations" element={<Animations />} />
          <Route path="/camera" element={<CameraGuide />} />
          <Route path="/particles" element={<Particles />} />
          <Route path="/pathfinding" element={<Pathfinding />} />
          <Route path="/api" element={<ApiReference />} />
          <Route path="/json" element={<JsonFormats />} />
          <Route path="/notes" element={<TechnicalNotes />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </Layout>
    </>
  );
}
