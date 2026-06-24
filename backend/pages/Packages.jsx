import { useNavigate } from "react-router-dom";

export default function Packages() {
  const nav = useNavigate();

  const selectPackage = () => {
    nav("/checkout");
  };

  return (
    <div>
      <h2>Select Package</h2>
      <button onClick={selectPackage}>Premium Plan</button>
    </div>
  );
}
