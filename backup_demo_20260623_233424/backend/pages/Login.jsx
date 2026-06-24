import { useNavigate } from "react-router-dom";

export default function Login() {
  const nav = useNavigate();

  const handleLogin = () => {
    nav("/packages");
  };

  return (
    <div>
      <h2>Login</h2>
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}
