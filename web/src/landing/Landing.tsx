import { Banner, Nav } from "./components/Chrome";
import { Hero } from "./components/Hero";
import { Principles, Modules, Status, Footer } from "./components/Sections";
import "./landing.css";

export default function Landing() {
  return (
    <div className="cb">
      <a className="cb-skip" href="#main">
        Skip to content
      </a>
      <Banner />
      <Nav />
      <main id="main">
        <Hero />
        <Principles />
        <Modules />
        <Status />
      </main>
      <Footer />
    </div>
  );
}
