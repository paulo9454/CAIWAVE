import { useNavigate } from "react-router-dom";

export default function Landing() {
  const nav = useNavigate();

  return (
    <div>
      <h1>CAIWAVE ISP SYSTEM</h1>
      <button onClick={() => nav("/login")}>
        Get Connected
      </button>
    </div>
  );
}
