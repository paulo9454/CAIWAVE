import { useNavigate } from "react-router-dom";
import { demoPay } from "../services/demoApi";

export default function Checkout() {
  const nav = useNavigate();

  const pay = async () => {
    await demoPay({ amount: 100, phone: "0700000000" });
    nav("/connecting");
  };

  return (
    <div>
      <h2>Checkout</h2>
      <button onClick={pay}>Pay Now</button>
    </div>
  );
}
