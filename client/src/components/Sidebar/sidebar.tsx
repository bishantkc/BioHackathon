import logo from "../../icons/calogo.jpg";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

const Sidebar = () => {
  const location = useLocation();

  // Define a function to check if a given path matches the current URL pathname
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  useEffect(() => {
    const body = document.querySelector("body") as HTMLBodyElement | null;
    if (!body) return;

    const sidebar = body.querySelector(".sidebar") as HTMLBodyElement | null;
    const toggle = body.querySelector(".toggle");
    const modeText = body.querySelector(".mode-text") as HTMLBodyElement | null;

    // Retrieve dark mode state from local storage
    const isDarkMode = localStorage.getItem("darkMode") === "true";
    // Set dark mode based on stored value
    if (isDarkMode) {
      body.classList.add("dark");
      if (modeText) {
        modeText.innerText = "Light Mode";
      }
    }

    // Retrieve sidebar state from local storage
    const isSidebarClosed = localStorage.getItem("sidebarClosed") === "true";
    // Set sidebar state based on stored value
    if (isSidebarClosed && sidebar) {
      if (window.innerWidth <= 1000) {
        sidebar.style.display = "none";
      } else {
        sidebar.classList.add("close");
      }
    }

    toggle?.addEventListener("click", () => {
      if (sidebar) {
        if (window.innerWidth <= 1000) {
          sidebar.style.display = "none";
        } else {
          sidebar.classList.toggle("close");

          /* This line checks whether it have close or not and return true or false */
          localStorage.setItem(
            "sidebarClosed",
            String(sidebar.classList.contains("close"))
          );
        }
      }
    });
  }, []);

  return (
    <div className="sidebar">
      <header>
        <div className="image-text">
          <span className="image">
            <img src={logo} alt="logo" style={{marginLeft: "10px"}} />
          </span>

          <div className="text header-text" style={{marginLeft: "20px"}}>
            BioInfo Hub
          </div>
        </div>
        <i className="bx bxs-chevron-right toggle"></i>
      </header>

      <div className="menu-bar">
        <div className="menu">
          <ul className="menu-links">
            <li className="menu-head">Main</li>
            <li
              className={`nav-link ${
                isActive("/gene") ? "active" : ""
              }`}
            >
              <Link to="/gene">
                <i className="bx bxs-file icon"></i>
                <span className="text nav-text">View Gene Information</span>
              </Link>
            </li>

            <li
              className={`nav-link ${
                isActive("/protein") ? "active" : ""
              }`}
            >
              <Link to="/protein">
                <i className="bx bxs-file icon"></i>
                <span className="text nav-text">View Protein Information</span>
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
