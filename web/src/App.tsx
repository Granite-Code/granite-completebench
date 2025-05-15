import { BrowserRouter, Routes, Route, NavLink } from "react-router";
import "./App.css";
import { About } from "./components/About";
import { Samples } from "./components/Samples";
import { Metrics } from "./components/Metrics";

function App() {
  return (
    <BrowserRouter>
      <div id="header">
        <img src="/granitecode.svg" id="headerLogo" />
        <div id="headerTitle">granite-completebench</div>
        <NavLink className="headerLink" to="/">
          About
        </NavLink>
        <NavLink className="headerLink" to="/metrics">
          Metrics
        </NavLink>
        <NavLink className="headerLink" to="/samples">
          Samples
        </NavLink>
        <a
          className="headerLink"
          href="https://github.com/Granite-Code/granite-completebench"
        >
          GitHub
        </a>
      </div>
      <div id="main">
        <Routes>
          <Route path="/" element={<About />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/samples" element={<Samples />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
