import { Link } from "react-router-dom";

function Navbar() {
  return (
    <div
      style={{
        display: "flex",
        gap: "20px",
        padding: "20px",
        background: "#1976d2",
      }}
    >
      <Link to="/" style={{ color: "white" }}>Login</Link>

      <Link to="/dashboard" style={{ color: "white" }}>Dashboard</Link>

      <Link to="/buyers" style={{ color: "white" }}>Buyers</Link>

      

      <Link to="/email" style={{ color: "white" }}>Email</Link>

      <Link to="/settings" style={{ color: "white" }}>Settings</Link>
    </div>
  );
}

export default Navbar;